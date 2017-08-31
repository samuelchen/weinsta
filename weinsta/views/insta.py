#!/usr/bin/env python
# coding: utf-8


from django.views.generic import TemplateView
from django.conf import settings
import requests
from .base import BaseViewMixin
from ..models import MediaType, SocialProviders, SocialUser, Media
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp

import logging
import os
import simplejson as json
from ..downloader import InstagramMediaDownloader
from allauth.socialaccount.providers import registry

log = logging.getLogger(__name__)

api_root = 'https://api.instagram.com/v1'


class InstaView(TemplateView, BaseViewMixin):

    downloader = InstagramMediaDownloader()

    def get(self, request, *args, **kwargs):
        medias = self.fetch_my_insta_favorites()

        return super(InstaView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InstaView, self).get_context_data(**kwargs)
        context['medias'] = Media.objects.all()
        print(context['medias'])
        return context

    def _get_my_insta_token(self):
        insta_id = 'instagram'
        token = None
        try:
            provider = registry.by_id(insta_id, self.request)
            log.debug('Provider is :' + str(provider))
            app = SocialApp.objects.get(provider=provider.id)
            acc = SocialAccount.objects.get(provider=provider.id, user=self.request.user)
            token = SocialToken.objects.get(app=app, account=acc)
        except KeyError as err:
            log.exception('Instagram provider is not installed.', err)
        except SocialApp.DoesNotExist:
            log.warn('Instagram app is not registered. Register it in admin console.')
        except SocialAccount.DoesNotExist:
            log.warn('Instagram account is not connected.')
        except SocialToken.DoesNotExist:
            log.warn('Instagram token is not obtained. Login with Instagram first.')

        if token is None:
            self.error('Token is not found. Check your registered APP and Instagram account.')

        if settings.DEBUG:
            print(token)
        return token

    def search_insta_by_location(self):
        pass

    def search_insta_by_tag(self, tags):
        pass

    def search_insta_by_user(self, username):
        pass

    def fetch_my_insta_favorites(self):
        favorites = []
        endpoint = 'users/self/media/liked'
        result = self._invoke_insta(endpoint)
        # result = open(os.path.join('./temp', 'favorites.json')).read()
        # result = json.loads(result)
        if not result:
            return []

        if 'error' in result:
            self.error(result['message'])
            return []

        for media in result['data']:
            m = self.downloader.fetch_media(media, self.request.user)
            favorites.append(m)

        return favorites

    def convert_author(self, author_dict):
        pass

    def _invoke_insta(self, endpoint, *args, **kwargs):
        token = self._get_my_insta_token()
        url = '%s/%s/?access_token=%s' % (api_root, endpoint, token)
        r = requests.get(url, proxies=settings.PROXIES)
        log.debug(r.status_code)
        log.debug(r.headers)
        log.debug(r.content)
        print(r.content)
        obj = r.json()
        if 200 > r.status_code or r.status_code >= 400:
            obj = {
                "code": obj['meta']['code'],
                "error": obj['meta']['error_type'],
                "message": obj['meta']['error_message']
            }
            log.error('%d %s. "%s". %s' % (r.status_code, r.reason, endpoint, obj['message']))
        return obj

    def _create_author(self):
        pass

