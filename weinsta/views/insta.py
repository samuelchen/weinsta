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
from ..downloader import InstagramMediaDownloader
from allauth.socialaccount.providers import registry

log = logging.getLogger(__name__)

api_root = 'https://api.instagram.com/v1'


class InstaView(TemplateView, BaseViewMixin):

    downloader = InstagramMediaDownloader()

    def get(self, request, *args, **kwargs):
        # medias = self.fetch_my_insta_favorites()

        return super(InstaView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super(InstaView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InstaView, self).get_context_data(**kwargs)

        req = self.request.GET
        tab = req.get('tab', '1')
        context['tab'] = tab

        if tab == '1':
            # insta favorites
            context['medias'] = Media.objects.all()
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

    def fetch_my_insta_favorites(self):
        favorites = []
        endpoint = 'users/self/media/liked'
        token = self.get_my_insta_token(self.request)
        result = self.invoke_insta(endpoint, token=token)
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

    @staticmethod
    def get_my_insta_token(request):
        insta_id = 'instagram'
        token = None
        try:
            provider = registry.by_id(insta_id, request)
            log.debug('Provider is :' + str(provider))
            app = SocialApp.objects.get(provider=provider.id)
            acc = SocialAccount.objects.get(provider=provider.id, user=request.user)
            token = SocialToken.objects.get(app=app, account=acc)
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
    def invoke_insta(endpoint, token, **kwargs):
        if '?' in endpoint:
            url = '%s/%s&access_token=%s' % (api_root, endpoint, token)
        else:
            url = '%s/%s?access_token=%s' % (api_root, endpoint, token)
        # url = '%s/%s' % (api_root, endpoint)
        # if 'data' in kwargs:
        #     kwargs['data']['access_token'] = token
        # else:
        #     kwargs['data'] = {
        #         'access_token': token
        #     }
        r = requests.get(url, proxies=settings.PROXIES, **kwargs)
        log.debug('%s invoking %s.' % (r.status_code, url))
        log.debug(r.headers)
        log.debug(r.content)
        obj = r.json()
        if 200 > r.status_code or r.status_code >= 400:
            obj = {
                "code": obj['meta']['code'],
                "error": obj['meta']['error_type'],
                "message": obj['meta']['error_message']
            }
            log.error('%d %s. "%s". %s' % (r.status_code, r.reason, endpoint, obj['message']))
        return obj


class InstaLocView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):

        resp = open(os.path.join(settings.BASE_DIR, 'temp/loc_medias.json'), 'rt').read()
        obj = json.loads(resp)
        return JsonResponse(obj)

        req = request.GET
        lat = req.get('lat', None)
        lng = req.get('lng', None)

        if lat and lng:
            token = InstaView.get_my_insta_token(request)
            url = 'locations/search?lat=%s&lng=%s' % (lat, lng)
            obj = InstaView.invoke_insta(url, token)
            print('resp:', obj)

            if obj and 'data' in obj:
                for loc in obj['data']:
                    print('loc', loc['id'])
                    url = 'locations/%s/media/recent' % loc['id']
                    obj1 = InstaView.invoke_insta(url, token)

                    if obj1:
                        return JsonResponse(obj1)
            elif 'error' in obj:
                return HttpResponse(obj['message'], status=obj['code'])

        return Http404()

    def get_context_data(self, **kwargs):
        context = super(InstaLocView, self).get_context_data(**kwargs)

        req = self.request.GET
        context['lat'] = req.get('lat', None)
        context['lng'] = req.get('lng', None)
        context['location'] = req.get('location', '')
        print(context)
        return context
