#!/usr/bin/env python
# coding: utf-8
from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken
from allauth.socialaccount.providers import registry
from django.urls import reverse


from .base import SocialClient
from ..models import SocialProviders, SocialUser, Media, MediaType, MediaInstance, MediaQuality
from django.conf import settings
from django.contrib.messages import error
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.db.utils import IntegrityError
import logging
import os
import simplejson as json

log = logging.getLogger(__name__)


class InstagramClient(SocialClient):

    # api_root = 'https://api.instagram.com/v1'

    # ------ overrides

    def __init__(self, token, provider=SocialProviders.INSTAGRAM, api_root='https://api.instagram.com/v1',
                 download_root=settings.MEDIA_ROOT, proxies=settings.PROXIES, **kwargs):
        super(InstagramClient, self).__init__(token=token, provider=provider, api_root=api_root,
                                              download_root=download_root, proxies=proxies, **kwargs)

    def prepare_invoking(self, requests_session):
        # do nothing
        # token will be in url
        return requests_session

    def get_token_hash(self):
        return self.token

    @classmethod
    def get_token(cls, user, request=None):

        if not user and request:
            user = request.user

        provider_id = SocialProviders.INSTAGRAM
        token = None

        if request:
            # get from session first
            tokens = request.session.get('token', None)
            if not tokens:
                tokens = request.session['token'] = {}
            token = tokens.get(provider_id, None)

        if not token:
            try:
                provider = registry.by_id(provider_id, request=request)
                # log.debug('Provider is :' + provider.__class__.__name__)
                app = SocialApp.objects.get(provider=provider.id)
                acc = SocialAccount.objects.get(provider=provider.id, user=user)
                token = SocialToken.objects.get(app=app, account=acc).token

                # cache to session
                if request:
                    request.session[provider_id] = token
            except KeyError as err:
                log.exception('Instagram provider is not installed.', err)
            except SocialApp.DoesNotExist:
                log.warn('Instagram app is not registered. Register it in admin console.')
            except SocialAccount.DoesNotExist:
                log.warn('Instagram account is not connected.')
            except SocialToken.DoesNotExist:
                log.warn('Instagram token is not obtained. Login with Instagram first.')

        if token is None and request:
            error(request, _(
                'Token is not found. Check your registered APP or <a href="%s">re-connect</a> Instagram account.'
            ) % reverse('socialaccount_connections'))

        if settings.DEBUG:
            print(token)
        return token

    # ------ overrides end

    def fetch_my_timeline(self, callback=None):
        all_medias = []

        def on_followers(result):
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
            self.invoke_async(url, callback=on_followers)
        else:
            followers = self.invoke(url)
            on_followers(followers)
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

    def save_media(self, media_dict, user, update_if_exists=False, cache_to_local=False):
        md = media_dict
        dirty = False

        t = MediaType.from_str(md['type'])
        assert t != MediaType.UNKNOWN
        rid = md['id']
        rlink = md['link']
        rcode = InstagramClient.get_insta_code_from_link(rlink)

        m, created = Media.objects.get_or_create(user=user, provider=SocialProviders.INSTAGRAM, rid=rid,
                                                 rcode=rcode)

        if created or update_if_exists:

            m.type = t
            m.rlink = rlink
            # m.rcode = rcode
            m.created_at = timezone.make_aware(timezone.datetime.utcfromtimestamp(int(md['created_time'])))
            m.tags = md['tags']
            if md['caption']:
                m.text = md['caption'].get('text', None)
            m.rjson = json.dumps(md)

            loc = md['location']
            if loc:
                m.location = loc.get('name', None)
                m.latitude = loc.get('latitude', None)
                m.longitude = loc.get('longitude', None)

            dirty = True

        # download author
        owner = md['user']
        if owner and (not m.owner or m.owner.rid != md['user']['id']):
            # m.owner = self.save_author(owner, cache_pic_to_local=cache_to_local)
            m.owner = self.save_author(rid=owner['id'], username=owner['username'], fullname=owner['full_name'],
                                       pic_url=owner['profile_picture'], bio=None, website=None)
            # by default author is owner
            # TODO: check if a forwarded post to correct author
            m.author = m.owner

        # download media
        if 'images' in md:
            if 'thumbnail' in md['images']:
                # save thumbnail
                img = md['images']['thumbnail']
                # m.thumb = self.save_media_instance(media_dict=img, media=m, media_type=MediaType.PHOTO,
                #                                    quality=MediaQuality.THUMB, update_if_exists=update_if_exists,
                #                                    cache_to_local=cache_to_local)
                m.thumb = self.save_media_instance(media=m, url=img['url'], media_type=MediaType.PHOTO,
                                                   quality=MediaQuality.THUMB, update_if_exists=update_if_exists,
                                                   cache_to_local=cache_to_local)
                dirty = True

            if 'low_resolution' in md['images']:
                # save low quality picture
                img = md['images']['low_resolution']
                # m.pic_low_res = self.save_media_instance(media_dict=img, media=m, media_type=MediaType.PHOTO,
                #                                          quality=MediaQuality.LOW,
                #                                          update_if_exists=update_if_exists,
                #                                          cache_to_local=False)
                m.pic_low_res = self.save_media_instance(media=m, url=img['url'], media_type=MediaType.PHOTO,
                                                         quality=MediaQuality.LOW,
                                                         update_if_exists=update_if_exists,
                                                         cache_to_local=False)
                dirty = True

            if 'standard_resolution' in md['images']:
                # save mid quality picture
                img = md['images']['standard_resolution']
                # m.pic_mid_res = self.save_media_instance(media_dict=img, media=m, media_type=MediaType.PHOTO,
                #                                          quality=MediaQuality.HIGH,
                #                                          update_if_exists=update_if_exists,
                #                                          cache_to_local=False)
                m.pic_mid_res = self.save_media_instance(media=m, url=img['url'], media_type=MediaType.PHOTO,
                                                         quality=MediaQuality.HIGH,
                                                         update_if_exists=update_if_exists,
                                                         cache_to_local=False)
                dirty = True

        if 'videos' in md:
            if 'low_resolution' in md['videos']:
                # save low quality instance
                video = md['videos']['low_resolution']
                # m.low_res = self.save_media_instance(media_dict=video, media=m, media_type=MediaType.VIDEO,
                #                                      quality=MediaQuality.LOW, update_if_exists=update_if_exists,
                #                                      cache_to_local=False)
                m.low_res = self.save_media_instance(media=m, url=video['url'], media_type=MediaType.VIDEO,
                                                     quality=MediaQuality.LOW, update_if_exists=update_if_exists,
                                                     cache_to_local=False)
                dirty = True

            if 'standard_resolution' in md['videos']:
                # save mid quality instance
                video = md['videos']['standard_resolution']
                # m.mid_res = self.save_media_instance(media_dict=video, media=m, media_type=MediaType.VIDEO,
                #                                      quality=MediaQuality.HIGH, update_if_exists=update_if_exists,
                #                                      cache_to_local=False)
                m.mid_res = self.save_media_instance(media=m, url=video['url'], media_type=MediaType.VIDEO,
                                                     quality=MediaQuality.HIGH, update_if_exists=update_if_exists,
                                                     cache_to_local=False)
                dirty = True

        if dirty:
            m.save()

        # many to many field must be updated before so that will check pk
        if m.pk:
            for u in md['users_in_photo']:
                ud = u['user']
                # su = self.save_author(ud, update_if_exists=update_if_exists, cache_pic_to_local=cache_to_local)
                su = self.save_author(rid=ud['id'], username=ud['username'], pic_url=ud['profile_picture'],
                                      fullname=ud['full_name'])
                m.mentions.add(su)

        # m.save()

        return m

    # def save_media_instance(self, media_dict, media, media_type, quality,
    #                         update_if_exists=False, cache_to_local=False):
    #
    #     assert isinstance(media, Media) and isinstance(media_dict, dict)
    #     m = media
    #     md = media_dict
    #     url = md['url']
    #     url_hash = MediaInstance.calc_url_hash(url)
    #     mi, created = MediaInstance.objects.get_or_create(url_hash=url_hash)
    #
    #     if created or update_if_exists:
    #         log.debug('%s MediaInstance for %s (hash=%s)' % ('creating' if created else 'updating', url, url_hash))
    #         mi.type = media_type
    #         mi.resolution = quality
    #         mi.origin_url = url
    #         if 'width' in md:
    #             mi.width = int(md['width'])
    #         if 'height' in md:
    #             mi.height = int(md['height'])
    #         try:
    #             mi.save()
    #         except IntegrityError as err:
    #             log.error('%s photo url "%s". Already existed (hash=%s)' % (
    #                 '[create]' if created else '[updated]', url, url_hash))
    #             log.exception(err)
    #             return None
    #
    #     if cache_to_local:
    #         if not (mi.instance and os.path.exists(mi.instance.path)):
    #             file_ext = url[url.rindex('.'):]
    #             filename = os.path.join(m.get_instance_folder(), MediaQuality.get_slug(quality),
    #                 m.rcode + file_ext)
    #             self.download(url=url, filename=filename, file_field=mi.instance)
    #             log.info('[Downloaded] %s' % mi)
    #
    #     return mi
    #
    # def save_author(self, user_dict, update_if_exists=False, cache_pic_to_local=False):
    #     rid = user_dict['id']
    #     username = user_dict['username']
    #     url = user_dict['profile_picture']
    #     provider = SocialProviders.INSTAGRAM
    #     dirty = False
    #
    #     u, created = SocialUser.objects.get_or_create(provider=provider, rid=rid)
    #     if created or update_if_exists:
    #         log.info('%s social user: %s' % ('Creating new' if created else 'Updating', username))
    #         u.username = username
    #         u.fullname = user_dict['full_name']
    #         dirty = True
    #
    #     if u.picture is None:
    #         log.debug('user picture is None. creating...')
    #         url_hash = MediaInstance.calc_url_hash(url)
    #         u.picture, created = MediaInstance.objects.get_or_create(url_hash=url_hash)
    #         dirty = True
    #
    #     mi = u.picture
    #     if created or update_if_exists:
    #         mi.type = MediaType.PHOTO
    #         mi.resolution = MediaQuality.ORIGIN
    #         mi.origin_url = url
    #         mi.save()
    #         log.debug('[SAVED] %s' % mi)
    #
    #     if cache_pic_to_local:
    #         if not (mi and mi.instance and os.path.exists(mi.instance.path)):
    #             file_ext = url[url.rindex('.'):]
    #             filename = username + file_ext
    #             filename = os.path.join(u.get_picture_folder(), filename)
    #             self.download(url=url, filename=filename, file_field=mi.instance)
    #             log.info('[Downloaded] %s' % mi)
    #
    #     if dirty:
    #         u.save()
    #         log.debug('[SAVED] %s' % u)
    #     return u

    @staticmethod
    def get_insta_code_from_link(link):
        code = link.split('/')[-2]
        return code