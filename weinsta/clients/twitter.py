#!/usr/bin/env python
# coding: utf-8
import os
from django.db import IntegrityError
from django.urls import reverse
from django.conf import settings
from django.contrib.messages import error
from django.utils import timezone
from django.utils.translation import ugettext as _
from email.utils import parsedate_to_datetime
from allauth.socialaccount.providers import registry
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
from requests_oauthlib import OAuth1
from .base import SocialClient
from ..models import SocialProviders, Media, MediaInstance, MediaQuality, MediaType
import simplejson as json
import logging

log = logging.getLogger(__name__)


class TwitterClient(SocialClient):

    # ------ overrides
    def __init__(self, token, provider=SocialProviders.TWITTER, api_root='https://api.twitter.com/1.1',
                 download_root=settings.MEDIA_ROOT, proxies=settings.PROXIES, **kwargs):
        super(TwitterClient, self).__init__(token=token, provider=provider, api_root=api_root,
                                            download_root=download_root,
                                            proxies=proxies, **kwargs)

    def prepare_invoking(self, requests_session):
        # http://docs.python-requests.org/en/master/user/advanced/#session-objects

        s = requests_session
        token = self._token
        s.auth = OAuth1(token['consumer_key'], token['consumer_secret'],
                        token['token'], token['token_secret'])
        return s

    def get_token_hash(self):
        return self.token['token']

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
                # log.debug('Provider is :' + provider.__class__.__name__)
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

        if token is None:
            error(request, _(
                'Token is not found. Check your registered APP or <a href="%s">re-connect</a> Instagram account.'
            ) % reverse('socialaccount_connections'))

        if settings.DEBUG:
            print(token)
        return token

    def fetch_favorites(self, callback=None):
        endpoint = 'favorites/list.json'

        if callback:
            self.invoke_async(endpoint=endpoint, callback=callback)
        else:
            result = self.invoke(endpoint=endpoint)
            # with open(os.path.join('./temp', 'twitter_favorites.json'), 'wt') as f:
            #     f.write(json.dumps(result))
            # result = open(os.path.join('./temp', 'twitter_favorites.json')).read()
            # result = json.loads(result)
            return result

    def save_media(self, media_dict, request, update_if_exists=False, cache_to_local=False):
        md = media_dict
        m = None

        # shared values for all medias
        rid = md['id_str']
        created_at = parsedate_to_datetime(md['created_at'])
        tags = md['entities']['hashtags']
        text = md['text']
        social_user = self.save_author(rid=md['user']['id_str'], username=md['user']['screen_name'],
                                       fullname=md['user'].get('full_name') or md['user'].get('name'),
                                       pic_url=md['user'].get('profile_image_url'),
                                       update_if_exists=update_if_exists,
                                       cache_pic_to_local=cache_to_local)

        loc = md.get('place')
        loc_name = None
        loc_lat = None
        loc_lng = None
        if loc:
            loc_name = loc.get('full_name', None)
            bound = loc['bounding_box']['coordinates'][0]
            lat = 0
            lng = 0
            if bound:
                for point in bound:
                    lat += int(point[0])
                    lng += int(point[1])
            loc_lat = lat / 4
            loc_lng = lng / 4

        if 'extended_entities' in md:
            entities = md['extended_entities']
            if 'media' in entities:
                # code should be obtain from expended_url/url/media_url. but always "1"
                # Now use auto-increased code.
                code = 0

                # a tweet contains multiple medias
                # all media uses same idstr(rid) with different code(rcode)
                for obj in entities['media']:

                    dirty = False
                    code += 1
                    t = MediaType.from_str(obj['type'])
                    if t == MediaType.UNKNOWN:
                        log.warn('Media type "%s" is not supported. %s' % (obj['type'], obj))
                    assert t != MediaType.UNKNOWN

                    # create a Media object for this media.
                    m, created = Media.objects.get_or_create(user=request.user, provider=SocialProviders.TWITTER,
                                                             rid=rid, rcode=str(code))

                    if created or update_if_exists:

                        m.type = MediaType.from_str(t)
                        m.rlink = obj['expanded_url']
                        # m.rcode = self.get_code_from_link(obj['expanded_url'])
                        # m.rcode = str(code)
                        m.created_at = created_at
                        m.tags = tags
                        m.text = text
                        if code == 1:
                            m.rjson = json.dumps(md)
                        else:
                            m.rjson = json.dumps(obj)
                        m.owner = social_user
                        m.author = m.owner  # TODO: check if a forwarded post to correct author
                        m.location = loc_name
                        m.latitude = loc_lat
                        m.longitude = loc_lng

                        dirty = True

                    # # save thumb
                    # if 'entities' in md and 'media' in md['entities']:
                    #     # thumbnail (only 1)
                    #     img = md['entities']['media'][0]
                    #     t1 = MediaType.from_str(img['type'])
                    #     log.debug('Thumbnail type is "%s" for "%s"' % (t1, img['url']))
                    #     assert t1 == MediaType.PHOTO
                    #     m.thumb = self.save_media_instance(media=m, url=img['media_url'],
                    #                                        media_type=t1,
                    #                                        quality=MediaQuality.THUMB,
                    #                                        update_if_exists=update_if_exists,
                    #                                        cache_to_local=cache_to_local)

                    # save media
                    if t == MediaType.PHOTO:
                        m.origin = self.save_media_instance(media=m, url=obj['media_url'], media_type=t,
                                                            quality=MediaQuality.ORIGIN,
                                                            update_if_exists=update_if_exists,
                                                            cache_to_local=False)
                        m.thumb = m.origin

                        dirty = True

                    elif t == MediaType.VIDEO:
                        if 'video_info' in obj:
                            videos = sorted(obj['video_info']['variants'], key=lambda v: v.get('bitrate', -1))
                            del videos[0]
                            mis = {}
                            for v in videos:
                                width, height = v['url'].split('/')[-2].split('x')
                                quality = self.get_quality(v['bitrate'])
                                mis[quality] = self.save_media_instance(media=m, url=v['url'], media_type=t,
                                                                        quality=quality, width=int(width),
                                                                        height=int(height),
                                                                        update_if_exists=update_if_exists,
                                                                        cache_to_local=False)
                            m.origin = mis[MediaQuality.ORIGIN] if MediaQuality.ORIGIN in mis else None
                            m.low = mis[MediaQuality.LOW] if MediaQuality.LOW in mis else None
                            m.high = mis[MediaQuality.HIGH] if MediaQuality.HIGH in mis else None
                            m.thumb = self.save_media_instance(media=m, url=obj['media_url'],
                                                               media_type=MediaType.PHOTO,
                                                               quality=MediaQuality.THUMB,
                                                               update_if_exists=update_if_exists,
                                                               cache_to_local=cache_to_local)
                            dirty = True
                        else:
                            log.error('No video instance found ("video_info" not found. rid=%s)' % rid)
                    else:
                        log.error('Unsupported media type "%s" can not be saved.' % t)

                    if dirty:
                        m.save()

                    # many to many field must be updated before so that will check pk
                    if m.pk and 'entities' in md and 'user_mentions' in md['entities']:
                        for u in md['entities']['user_mentions']:
                            su = self.save_author(rid=u['id_str'], username=u['screen_name'],
                                                  fullname=u.get('name'),
                                                  pic_url=None,
                                                  update_if_exists=False,
                                                  cache_pic_to_local=False)
                            m.mentions.add(su)

        return m

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

    def get_code_from_link(self, link):
        code = link.split('/')[-1]

        return code

    def get_quality(self, bitrate):
        if bitrate < 832000:
            return MediaQuality.LOW
        elif 832000 <= bitrate < 2176000:
            return MediaQuality.HIGH
        elif bitrate >= 2176000:
            return MediaQuality.ORIGIN