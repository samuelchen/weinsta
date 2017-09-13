#!/usr/bin/env python
# coding: utf-8
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp

from .base import SocialClient
from ..models import SocialProviders
from django.conf import settings
from allauth.socialaccount.providers import registry
from requests_oauthlib import OAuth1

import logging

log = logging.getLogger(__name__)


class TwitterClient(SocialClient):

    # ------ overrides
    def __init__(self, token, provider=SocialProviders.TWITTER, api_root='https://api.twitter.com/1.1',
                 download_root=settings.MEDIA_ROOT, proxies=settings.PROXIES, **kwargs):
        super(TwitterClient, self).__init__(provider=provider, api_root=api_root,
                                            download_root=download_root,
                                            proxies=proxies, **kwargs)

        self._token = token

    def prepare_invoking(self, requests_session):
        # http://docs.python-requests.org/en/master/user/advanced/#session-objects

        s = requests_session
        token = self._token
        s.auth = OAuth1(token['consumer_key'], token['consumer_secret'],
                        token['token'], token['token_secret'])
        return s

    # ------- overrides end

    @staticmethod
    def get_my_token(request):

        provider_id = 'twitter'
        tokens = request.session.get('token', None)
        if not tokens:
            tokens = request.session['token'] = {}
        token = tokens.get(provider_id, None)
        if not token:
            try:
                provider = registry.by_id(provider_id, request)
                log.debug('Provider is :' + str(provider))
                app = SocialApp.objects.get(provider=provider.id)
                acc = SocialAccount.objects.get(provider=provider.id, user=request.user)
                token = SocialToken.objects.get(app=app, account=acc)

                token = {
                    'consumer_key': app.client_id,
                    'consumer_secret': app.secret,
                    'token': token.token,
                    'token_secret': token.token_secret
                }
                request.session[provider_id] = token
            except KeyError as err:
                log.exception('Instagram provider is not installed.', err)
            except SocialApp.DoesNotExist:
                log.warn('Instagram app is not registered. Register it in admin console.')
            except SocialAccount.DoesNotExist:
                log.warn('Instagram account is not connected.')
            except SocialToken.DoesNotExist:
                log.warn('Instagram token is not obtained. Login with Instagram first.')

        # if token is None:
        #     self.error('Token is not found. Check your registered APP and Instagram account.')

        if settings.DEBUG:
            print(token)
        return token

    def fetch_favorites(self, callback=None):
        endpoint = 'favorites/list.json'

        if callback:
            self.invoke_async(endpoint=endpoint, callback=callback)
        else:
            result = self.invoke(endpoint=endpoint)
            # result = open(os.path.join('./temp', 'twitter_favorites.json')).read()
            # result = json.loads(result)
            return result

    def post_status(self, text, img_field=None):

        media_ids = []
        if img_field is not None:
            endpoint = 'https://upload.twitter.com/1.1/media/upload.json'

            files = {'media': open(img_field.path, 'rb')}
            result = self.invoke(endpoint=endpoint, method='post', files=files)
            media_id = result['media_id']
            media_ids.append(media_id)
            media_size = result['size']

        endpoint1 = 'statuses/update.json'
        payload = {
            'status': text,
            'media_ids': media_ids
        }
        r = self.invoke(endpoint1, method='post', data=payload)
        return r


    # def save_media(self, media_dict):
    #     md = media_dict
    #     t = md['type']
    #
    #     MEDIA_MODEL = Media
    #
    #     try:
    #         m = MEDIA_MODEL.objects.get(user=user, provider=SocialProviders.INSTAGRAM, rid=md['id'])
    #         log.info('Updating media %s' % m.id)
    #     except MEDIA_MODEL.DoesNotExist:
    #         m = MEDIA_MODEL(user=user, provider=SocialProviders.INSTAGRAM, rid=md['id'])
    #         log.info('Creating media for %s' % md['link'])
    #
    #     m.type = MediaType.from_str(t)
    #     m.rlink = md['link']
    #     # m.user = user
    #     # m.provider = SocialProviders.INSTAGRAM
    #     # m.rid = media['id']
    #     m.rcode = InstagramMediaDownloader.get_insta_code_from_link(m.rlink)
    #     m.created_at = timezone.make_aware(timezone.datetime.utcfromtimestamp(int(md['created_time'])))
    #     m.tags = md['tags']
    #     if md['caption']:
    #         m.text = md['caption'].get('text', None)
    #
    #     owner = md['user']
    #     if owner:
    #         m.owner = InstagramMediaDownloader.get_or_create_social_user(owner)
    #         # by default author is owner
    #         # TODO: check if a forwarded post to correct author
    #         m.author = m.owner
    #
    #     loc = md['location']
    #     if loc:
    #         m.location = loc.get('name', None)
    #         m.latitude = loc.get('latitude', None)
    #         m.longitude = loc.get('longitude', None)
    #
    #     # download thumbnail
    #     if 'images' in md:
    #         if 'thumbnail' in md['images']:
    #             img = md['images']['thumbnail']
    #             url = img['url']
    #             if m.thumb_url != url or not m.thumb:
    #                 m.thumb_url = url
    #                 m.thumb_width = int(img['width'])
    #                 m.thumb_height = int(img['height'])
    #                 path = '%s/thumb' % user
    #                 file_ext = url[url.rindex('.'):]
    #                 filename = m.rcode + file_ext
    #                 filename = os.path.join(path, filename)
    #                 InstagramMediaDownloader._download_media(file_field=m.thumb, url=url, filename=filename)
    #
    #     m.rjson = json.dumps(md)
    #
    #     # many to many field must update after
    #     if m.pk:
    #         for u in md['users_in_photo']:
    #             ud = u['user']
    #             su = InstagramMediaDownloader.get_or_create_social_user(u['user'])
    #             m.mentions.add(su)
    #
    #     m.save()
    #
    #     return m


    # def get_token(self, request):
    #
    #     tokens = request.session.get('token', None)
    #     if not tokens:
    #         tokens = request.session['token'] = {}
    #     token = tokens.get(self.provider, None)
    #     if not token:
    #         try:
    #             provider = registry.by_id(self.provider, request)
    #             log.debug('Provider is :' + str(provider))
    #             app = SocialApp.objects.get(provider=provider.id)
    #             acc = SocialAccount.objects.get(provider=provider.id, user=request.user)
    #             token = SocialToken.objects.get(app=app, account=acc)
    #
    #             token = {
    #                 'consumer_key': app.client_id,
    #                 'consumer_secret': app.secret,
    #                 'token': token.token,
    #                 'token_secret': token.token_secret
    #             }
    #             request.session[self.provider] = token
    #         except KeyError as err:
    #             log.exception('Instagram provider is not installed.', err)
    #         except SocialApp.DoesNotExist:
    #             log.warn('Instagram app is not registered. Register it in admin console.')
    #         except SocialAccount.DoesNotExist:
    #             log.warn('Instagram account is not connected.')
    #         except SocialToken.DoesNotExist:
    #             log.warn('Instagram token is not obtained. Login with Instagram first.')
    #
    #     # if token is None:
    #     #     self.error('Token is not found. Check your registered APP and Instagram account.')
    #
    #     if settings.DEBUG:
    #         print(token)
    #     return token
