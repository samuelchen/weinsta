#!/usr/bin/env python
# coding: utf-8


from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
import requests
from .base import BaseViewMixin
from ..models import MediaType, SocialProviders, SocialUser, Media
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp

import logging
import os
import simplejson as json
from base64 import b64encode
from urllib.parse import quote
from allauth.socialaccount.providers import registry
import oauth2
from requests_oauthlib import OAuth1
from ..clients import TwitterClient


log = logging.getLogger(__name__)

api_root = 'https://api.twitter.com/1.1'



class TwitterView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        # medias = self.fetch_my_insta_favorites()

        return super(TwitterView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super(TwitterView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TwitterView, self).get_context_data(**kwargs)

        req = self.request.GET
        tab = req.get('tab', '1')
        context['tab'] = tab

        token = self.get_my_twitter_token(self.request)
        client = TwitterClient(token=token)

        if tab == '1':
            # favorites
            # context['medias'] = self.fetch_my_twitter_favorites()
            context['medias'] = client.fetch_favorites()
        elif tab == '2':
            # search tags
            pass
        elif tab == '3':
            # locations
            pass

        return context

    def search_insta_by_location(self):
        pass

    def search_insta_by_tag(self, tags):
        pass

    def search_insta_by_user(self, username):
        pass

    # def fetch_my_twitter_favorites(self):
    #     endpoint = 'favorites/list.json'
    #     token = self.get_my_twitter_token(self.request)
    #     result = self.invoke_twitter(endpoint, token=token)
    #     with open(os.path.join('./temp', 'twitter_favorites.json'), 'wt') as f:
    #         f.write(json.dumps(result))
    #     # result = open(os.path.join('./temp', 'twitter_favorites.json')).read()
    #     # result = json.loads(result)
    #
    #     print(result)
    #     if not result:
    #         return []
    #
    #     if 'errors' in result:
    #         for err in result['errors']:
    #             self.error(err)
    #         return []
    #
    #     # for media in result['data']:
    #     #     m = self.downloader.fetch_media(media, self.request.user)
    #     #     favorites.append(m)
    #
    #     return result

    @staticmethod
    def get_my_twitter_token(request):

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

    @staticmethod
    def invoke_twitter(endpoint, token, method='get', body='', **kwargs):
        url = '%s/%s' % (api_root, endpoint)
        func = getattr(requests, method)
        auth = OAuth1(token['consumer_key'], token['consumer_secret'],
                      token['token'], token['token_secret'])
        r = func(url, auth=auth, proxies=settings.PROXIES, **kwargs)
        log.debug('%s invoking %s.' % (r.status_code, url))
        log.debug(r.headers)
        log.debug(r.content)
        obj = r.json()
        if 200 > r.status_code or r.status_code >= 400:
            log.error('%d %s. "%s". %s' % (r.status_code, r.reason, endpoint, obj))
        return obj

