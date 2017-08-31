#!/usr/bin/env python
# coding: utf-8
from concurrent.futures import ThreadPoolExecutor

from django.views.generic import TemplateView
from django.conf import settings
from django.utils import timezone
import requests
from .models import MediaType, SocialProviders, SocialUser, Media
from urllib.parse import quote
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp

import logging
import os
import simplejson as json
import logging

from allauth.socialaccount.providers import registry

log = logging.getLogger(__name__)


class MediaDownloader(object):

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)


class InstagramMediaDownloader(MediaDownloader):

    api_root = 'https://api.instagram.com/v1'

    def __init__(self):
        super(InstagramMediaDownloader, self).__init__()

    def download(self, media_dict, user):
        self.executor.submit(InstagramMediaDownloader.fetch_media,
                             media_dict, user)

    @staticmethod
    def fetch_media(media_dict, user):
        md = media_dict
        t = md['type']

        MEDIA_MODEL = Media

        try:
            m = MEDIA_MODEL.objects.get(user=user, provider=SocialProviders.INSTAGRAM, rid=md['id'])
        except MEDIA_MODEL.DoesNotExist:
            m = MEDIA_MODEL(user=user, provider=SocialProviders.INSTAGRAM, rid=md['id'])

        m.type = MediaType.from_str(t)
        m.rlink = md['link']
        # m.user = user
        # m.provider = SocialProviders.INSTAGRAM
        # m.rid = media['id']
        m.rcode = InstagramMediaDownloader.get_insta_code_from_link(m.rlink)
        m.created_at = timezone.datetime.utcfromtimestamp(int(md['created_time']))
        m.tags = md['tags']

        # m.authors = self.convert_author(media['user'])

        caption = md['caption']
        if caption:
            m.text = md['caption'].get('text', None)
            owner = md['caption'].get('from', None)
            if owner:
                m.owner = InstagramMediaDownloader.get_or_create_social_user(owner)
                # by default author is owner
                # TODO: check if a forwarded post to correct author
                m.author = m.owner

        loc = md['location']
        if loc:
            m.location = loc.get('name', None)
            m.latitude = loc.get('latitude', None)
            m.longitude = loc.get('longitude', None)

        # download thumbnail
        if 'images' in md:
            if 'thumbnail' in md['images']:
                img = md['images']['thumbnail']
                url = img['url']
                if m.thumb_url != url or not m.thumb:
                    m.thumb_url = url
                    m.thumb_width = int(img['width'])
                    m.thumb_height = int(img['height'])
                    path = '%s/thumb' % user
                    file_ext = url[url.rindex('.'):]
                    filename = m.rcode + file_ext
                    filename = os.path.join(path, filename)
                    InstagramMediaDownloader._download_media(file_field=m.thumb, url=url, filename=filename)

        m.rjson = json.dumps(md)
        m.save()

        # many to many field must update after
        if m.pk:
            for u in md['users_in_photo']:
                ud = u['user']
                su = InstagramMediaDownloader.get_or_create_social_user(u['user'])
                m.mentions.add(su)

        return m

    @staticmethod
    def get_or_create_social_user(user_dict):
        rid = user_dict['id']
        username = user_dict['username']
        url = user_dict['profile_picture']
        provider = SocialProviders.INSTAGRAM
        u, created = SocialUser.objects.get_or_create(provider=provider, rid=rid)
        if not (u.picture and u.picture_url == url):
            u.username = username
            u.fullname = user_dict['full_name']
            u.picture_url = url
            file_ext = url[url.rindex('.'):]
            filename = username + file_ext
            filename = os.path.join(provider, filename)
            InstagramMediaDownloader._download_media(file_field=u.picture, url=url, filename=filename)
            u.save()

        return u


    @staticmethod
    def get_insta_code_from_link(link):
        code = link.split('/')[-2]
        return code

    @staticmethod
    def _download_media(file_field, url, filename=None, delete_if_exists=True):
        log.debug('Downloading %s' % url)
        r = requests.get(url, stream=True, proxies=settings.PROXIES)

        if r.status_code != requests.codes.ok:
            log.error('%d %s. Downloading %s' % (r.status_code, r.reason, url))
            return None

        if not filename:
            filename = url.split('/')[-1]

        if delete_if_exists:
            fulpath = os.path.join(settings.MEDIA_ROOT, filename)
            if os.path.exists(fulpath):
                try:
                    os.remove(fulpath)
                except Exception as err:
                    log.exception(err)

        file_field.save(filename, r.raw)