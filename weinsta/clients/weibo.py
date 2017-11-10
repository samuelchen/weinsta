#!/usr/bin/env python
# coding: utf-8
import os
from urllib.parse import quote
from django.db import IntegrityError
from django.urls import reverse
from django.conf import settings
from django.contrib.messages import error
from django.utils import timezone
from django.utils.translation import ugettext as _
from email.utils import parsedate_to_datetime
from allauth.socialaccount.providers import registry
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
import requests
from requests_oauthlib import OAuth1
from .base import SocialClient, SocialClientException
from ..models import SocialProviders, Media, MediaInstance, MediaQuality, MediaType, ActivityType
import simplejson as json
import logging

log = logging.getLogger(__name__)


class WeiboClient(SocialClient):

    # ------ overrides
    def __init__(self, token, provider=SocialProviders.WEIBO, api_root='https://api.weibo.com/2',
                 download_root=settings.MEDIA_ROOT, proxies=settings.PROXIES, **kwargs):
        super(WeiboClient, self).__init__(token=token, provider=provider, api_root=api_root,
                                          download_root=download_root,
                                          proxies=proxies, **kwargs)

    def prepare_invoking(self, requests_session):
        # http://docs.python-requests.org/en/master/user/advanced/#session-objects

        # do nothing
        return requests_session

    def get_token_hash(self):
        return self.token


    @classmethod
    def get_token(cls, user, request=None):

        if not user and request:
            user = request.user

        provider_id = SocialProviders.WEIBO
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
                log.exception('Weibo provider is not installed.', err)
            except SocialApp.DoesNotExist:
                log.warn('Weibo app is not registered. Register it in admin console.')
            except SocialAccount.DoesNotExist:
                log.warn('Weibo account is not connected.')
            except SocialToken.DoesNotExist:
                log.warn('Weibo token is not obtained. Login with Instagram first.')

        if token is None and request:
            error(request, _(
                'Token is not found. Check your registered APP or <a href="%s">re-connect</a> Weibo account.'
            ) % reverse('socialaccount_connections'))

        return token

    def get_activity_data(self, rid):
        r = self.get_status(rid)
        if 'error' in r:
            log.error(r)
            raise SocialClientException(r)

        # names map to models.ActivityClasses keys
        data = {
            ActivityType.LIKE: {
                'count': int(r['attitudes_count']),
                'entries': [],
            },
            ActivityType.REPOST: {
                'count': int(r['reposts_count']),
                'entries': [],
            },
            ActivityType.COMMENT: {
                'count': int(r['comments_count']),
                'entries': [],
            }
        }

        # r1 = self.get_reposts(rid=rid)
        # if 'error' in r:
        #     log.error(r)
        #     raise SocialClientException(r)
        #
        # for repost in r['reposts']:
        #     rid_repost = repost['id']
        #     text = repost['text']
        #     person = repost['user']
        #     self.save_author(rid=person['id'], username=person['screen_name'], fullname=person['name'],
        #                      pic_url=person['profile_image_url'], bio=person['description'], website=person['url'],
        #                      update_if_exists=True, cache_pic_to_local=True)

        return data

    def get_my_data(self):
        pass

    # ------- overrides end

    def post_status(self, text, medias=[]):
        print(text, medias)
        endpoint = 'statuses/share.json'

        token = self.token
        payload = {
            "access_token": token,
            "status": quote(text),
        }

        files = None
        for m in medias:
            mi = m.get_media_instance(quality=MediaQuality.HIGH)
            if mi is None:
                mi = m.get_pic_instance(quality=MediaQuality.HIGH)
            if mi is not None:
                mii = mi.instance
                files = {
                    "pic": (mii.name, open(mii.path, 'rb'))
                }
            # break       # only support 1 media
            # TODO: to support more medias, visit http://open.weibo.com/wiki/2/statuses/upload_url_text to apply

        rc = {}
        if files:
            r = self.invoke(endpoint, method='post', data=payload, files=files)
        else:
            # r = self.invoke(endpoint, method='post', data=payload)
            r = {
                'error_code': -1,
                'error': 'Weibo need at least 1 media in post.'
            }
        if 'error' in r:
            rc['error'] = r['error']
            rc['code'] = r['error_code']
        else:
            rc = r
        return rc

    def get_status(self, rid):
        endpoint = 'statuses/show.json'
        token = self.token
        # app_key = WeiboClient.get_appkey()

        payload = {
            "access_token": token,
            "id": int(rid),
            # "source": app_key
        }
        r = self.invoke(endpoint, method='get', params=payload)     # must be "params" not "data"
        return r

    def get_reposts(self, rid):
        endpoint = 'statuses/repost_timeline.json'
        token = self.token

        payload = {
            "access_token": token,
            "id": int(rid),
            "count": 200
        }
        r = self.invoke(endpoint, method='get', data=payload)

        return r

    def get_comments(self, rid):
        endpoint = 'statuses/show.json'
        token = self.token

        payload = {
            "access_token": token,
            "id": int(rid)
        }
        r = self.invoke(endpoint, method='get', data=payload)
        return r

    # ----- tool methos -----

    # def get_code_from_link(self, link):
    #     code = link.split('/')[-1]
    #
    #     return code
    #
    # def get_quality(self, bitrate):
    #     if bitrate < 832000:
    #         return MediaQuality.LOW
    #     elif 832000 <= bitrate < 2176000:
    #         return MediaQuality.HIGH
    #     elif bitrate >= 2176000:
    #         return MediaQuality.ORIGIN

    @classmethod
    def get_appkey(cls):

        provider_id = SocialProviders.WEIBO
        provider = registry.by_id(provider_id, request=None)
        app = SocialApp.objects.get(provider=provider.id)
        app_key = app.client_id
        log.debug('App key is %s for %s' % (app_key, SocialProviders.get_text(provider_id)))

        return app_key