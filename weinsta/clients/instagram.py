#!/usr/bin/env python
# coding: utf-8

from .base import SocialClient
from ..models import SocialProviders, SocialUser, Media, MediaType
from django.conf import settings
from django.contrib.messages import error
from django.utils import timezone
import logging
import os
import simplejson as json

log = logging.getLogger(__name__)


class InstagramClient(SocialClient):

    # api_root = 'https://api.instagram.com/v1'
    # ------ overrides

    def __init__(self, token, provider=SocialProviders.INSTAGRAM, api_root='https://api.instagram.com/v1',
                 download_root=settings.MEDIA_ROOT, proxies=settings.PROXIES, **kwargs):
        super(InstagramClient, self).__init__(provider=provider, api_root=api_root,
                                              download_root=download_root, proxies=proxies, **kwargs)

        self._token = token

    def prepare_invoking(self, requests_session):
        # do nothing
        # token will be in url
        return requests_session

    # ------ overrides end

    @property
    def token(self):
        return self._token

    def fetch_my_timeline(self, callback=None):
        all_medias = []

        def on_author_retrieved(result):
            follows = result

            url1 = 'users/%s/media/recent/?access_token=' + self.token + '&count=2'
            for user in follows['data']:
                print(user['username'])
                medias = self.invoke(url1 % user['id'])
                if medias:
                    all_medias.extend(medias['data'])

            if callback:
                callback(all_medias)

        url = 'users/self/follows?access_token=' + self.token
        if callback:
            self.invoke_async(url, callback=on_author_retrieved)
        else:
            followers = self.invoke(url)
            on_author_retrieved(followers)
            return all_medias

    def fetch_my_likes(self, callback=None):
        likes = []
        endpoint = 'users/self/media/liked?access_token=' + self.token

        def on_result(result):
            if result:
                if 'error' in result:
                    error(result['message'])
                    return []
                else:
                    for media in result['data']:
                        #url, filename=None, folder='./', file_field=None, delete_if_exists=True):
                        # m = self.download(media, self.request.user)
                        likes.append(media)

            if callback:
                callback(likes)

        if callback:
            self.invoke_async(endpoint, callback=on_result)
        else:
            # r = open(os.path.join('./temp', 'favorites.json')).read()
            # r = json.loads(result)
            r = self.invoke(endpoint)
            on_result(r)
            return likes

    def fetch_my_own_medias(self, callback=None):
        my_medias = []
        endpoint = 'users/self/media/recent/?access_token=' + self.token

        def on_result(result):
            if result:
                if 'error' in result:
                    error(result['message'])
                    return []
                else:
                    for media in result['data']:
                        my_medias.append(media)

            if callback:
                callback(my_medias)

        if callback:
            self.invoke_async(endpoint, callback=on_result)
        else:
            # r = open(os.path.join('./temp', 'my_medias.json')).read()
            # r = json.loads(result)
            r = self.invoke(endpoint)
            on_result(r)
            return my_medias

    def save_media(self, media_dict, request, cache_to_local=False):
        md = media_dict
        t = md['type']

        MEDIA_MODEL = Media

        try:
            m = MEDIA_MODEL.objects.get(user=request.user, provider=SocialProviders.INSTAGRAM, rid=md['id'])
            return m
            log.info('Updating media %s' % m.id)
        except MEDIA_MODEL.DoesNotExist:
            m = MEDIA_MODEL(user=request.user, provider=SocialProviders.INSTAGRAM, rid=md['id'])
            log.info('Creating media for %s' % md['link'])

        m.type = MediaType.from_str(t)
        m.rlink = md['link']
        # m.user = user
        # m.provider = SocialProviders.INSTAGRAM
        # m.rid = media['id']
        m.rcode = InstagramClient.get_insta_code_from_link(m.rlink)
        m.created_at = timezone.make_aware(timezone.datetime.utcfromtimestamp(int(md['created_time'])))
        m.tags = md['tags']
        if md['caption']:
            m.text = md['caption'].get('text', None)

        owner = md['user']
        if owner and (not m.owner or m.owner.rid != md['user']['id']):
            m.owner = self.save_author(owner)
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
                    if cache_to_local:
                        path = '%s/thumb' % request.user
                        file_ext = url[url.rindex('.'):]
                        filename = m.rcode + file_ext
                        filename = os.path.join(path, filename)
                        self.download(url=url, filename=filename, file_field=m.thumb)

        m.rjson = json.dumps(md)

        # many to many field must update after
        if m.pk:
            for u in md['users_in_photo']:
                ud = u['user']
                su = self.save_author(ud, cache_to_local)
                m.mentions.add(su)

        m.save()

        return m

    def save_author(self, user_dict, cache_pic_to_local=False):
        rid = user_dict['id']
        username = user_dict['username']
        url = user_dict['profile_picture']
        provider = SocialProviders.INSTAGRAM
        u, created = SocialUser.objects.get_or_create(provider=provider, rid=rid)
        if not created:
            return u
        log.info('%s social user: %s' % ('Creating new' if created else 'Updating', username))
        u.username = username
        u.fullname = user_dict['full_name']
        if not (u.picture and u.picture_url == url):
            u.picture_url = url
            if cache_pic_to_local:
                file_ext = url[url.rindex('.'):]
                filename = username + file_ext
                filename = os.path.join(provider, filename)
                self.download(url=url, filename=filename, file_field=u.picture)
                log.debug('Social user picture downloaded. %s' % u.picture)

        u.save()
        return u

    @staticmethod
    def get_insta_code_from_link(link):
        code = link.split('/')[-2]
        return code