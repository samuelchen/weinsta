#!/usr/bin/env python
# coding: utf-8
import os
from django.db import IntegrityError
from django.urls import reverse
from django.conf import settings
from django.contrib.messages import error
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils.dateparse import parse_datetime
from allauth.socialaccount.providers import registry
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
from requests_oauthlib import OAuth1
from .base import SocialClient
from ..models import SocialProviders, Media, MediaInstance, MediaResolution, MediaType
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
        t = md['type']
        dirty = False

        m, created = Media.objects.get_or_create(user=request.user, provider=SocialProviders.TWITTER, rid=md['idstr'])

        if created or update_if_exists:

            m.type = MediaType.from_str(t)
            m.rlink = 'https://twitter.com/%s/status/%s' % (md['user']['screen_name'], m.rid)
            m.rcode = m.rid
            m.created_at = timezone.make_aware(parse_datetime(['created_at']))
            m.tags = md['entities']['hashtags']
            m.text = md['text']
            m.rjson = json.dumps(md)

            owner = md.get('user')
            if owner and (not m.owner or m.owner.rid != md['user']['idstr']):
                m.owner = self.save_author(owner, cache_pic_to_local=cache_to_local)
                # by default author is owner
                # TODO: check if a forwarded post to correct author
                m.author = m.owner

            loc = md.get('place')
            if loc:
                m.location = loc.get('full_name', None)
                bound = loc.get('bounding_box')
                lat = 0
                lng = 0
                if bound:
                    for point in bound:
                        lat += point[0]
                        lng += point[1]
                m.latitude = lat / 4
                m.longitude = lng / 4

            dirty = True

        # download
        if 'entities' in md and 'media' in md['entities']:
            # thumbnail (only 1)
            img = md['entities']['media']
            # save thumbnail
            mtype = MediaType.from_str(img['type'])
            assert mtype == MediaType.PHOTO
            m.thumb = self.save_media_instance(media=m, url=img['media_url'], media_type=mtype,
                                               resolution=MediaResolution.THUMB,
                                               update_if_exists=update_if_exists, cache_to_local=cache_to_local)
            dirty = True

        if 'extended_entities' in md:
            entities = md['extended_entities']
            if 'media' in entities:
                for obj in entities['media']:
                    mtype = MediaType.from_str(obj['type'])
                    assert mtype != MediaType.UNKNOWN
                    if mtype == MediaType.UNKNOWN:
                        log.warn('Media type "%s" is not supported. %s' % (obj['type'], obj))
                    else:
                        mi = self.save_media_instance(media=m, url=img['media_url'], media_type=mtype,
                                                      resolution=MediaResolution.ORIGIN,
                                                      update_if_exists=update_if_exists, cache_to_local=cache_to_local)
                    dirty = True

                if 'standard_resolution' in md['images']:
                    # save mid resolution picture
                    img = md['images']['standard_resolution']
                    m.pic_mid_res = self.save_media_instance(media_dict=img, media=m, media_type=MediaType.PHOTO,
                                                             resolution=MediaResolution.MID,
                                                             update_if_exists=update_if_exists,
                                                             cache_to_local=False)
                    dirty = True

            if 'videos' in md:
                if 'low_resolution' in md['videos']:
                    # save low resolution instance
                    video = md['videos']['low_resolution']
                    m.low_res = self.save_media_instance(media_dict=video, media=m, media_type=MediaType.VIDEO,
                                                         resolution=MediaResolution.LOW, update_if_exists=update_if_exists,
                                                         cache_to_local=False)
                    dirty = True

                if 'standard_resolution' in md['videos']:
                    # save mid resolution instance
                    video = md['videos']['standard_resolution']
                    m.mid_res = self.save_media_instance(media_dict=video, media=m, media_type=MediaType.VIDEO,
                                                         resolution=MediaResolution.MID, update_if_exists=update_if_exists,
                                                         cache_to_local=False)
                    dirty = True

        if dirty:
            m.save()

        # many to many field must be updated before so that will check pk
        if m.pk:
            for u in md['users_in_photo']:
                ud = u['user']
                su = self.save_author(ud, update_if_exists=update_if_exists, cache_pic_to_local=cache_to_local)
                m.mentions.add(su)

        # m.save()

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
        code = link.split('/')[-2]
        return code