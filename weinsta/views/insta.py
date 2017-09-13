#!/usr/bin/env python
# coding: utf-8
from django.urls import reverse

from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
from django.contrib.messages import error
from django.utils.translation import ugettext as _
from .base import BaseViewMixin
from ..models import MediaType, SocialProviders, SocialUser, Media, LikedMedia, MyMedia
from ..clients import InstagramClient

import logging
import os
import simplejson as json

log = logging.getLogger(__name__)


class InstaView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(InstaView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super(InstaView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InstaView, self).get_context_data(**kwargs)

        token = InstagramClient.get_my_token(self.request)
        if token:
            client = InstagramClient(token=token)

            def on_likes(likes):
                for md in likes:
                    m = client.save_media(md, self.request, cache_to_local=True)
                    like, created = LikedMedia.objects.get_or_create(user=self.request.user, media=m)
                    if created:
                        like.save()

            def on_my_medias(my_medias):
                for md in my_medias:
                    m = client.save_media(md, self.request, cache_to_local=True)
                    mine, created = MyMedia.objects.get_or_create(user=self.request.user, media=m)
                    if created:
                        mine.save()

            client.fetch_my_likes(callback=on_likes)
            client.fetch_my_own_medias(callback=on_my_medias)

        req = self.request.GET
        tab = req.get('tab', 'medias')
        context['tab'] = tab

        if tab == 'medias':
            context['medias'] = MyMedia.objects.filter(user=self.request.user).select_related('media')
        elif tab == 'likes':
            # my instagram likes
            context['medias'] = LikedMedia.objects.filter(user=self.request.user).select_related('media')
        elif tab == 'tags':
            # search tags
            pass
        elif tab == 'locations':
            # locations
            pass

        context['mediatypes'] = MediaType

        return context


class InstaLocView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):

        resp = open(os.path.join(settings.BASE_DIR, 'temp/loc_medias.json'), 'rt').read()
        obj = json.loads(resp)
        return JsonResponse(obj)

        req = request.GET
        lat = req.get('lat', None)
        lng = req.get('lng', None)

        if lat and lng:
            token = InstagramClient.get_my_token(request)
            if token:
                client = InstagramClient(token=token)
                url = 'locations/search?lat=%s&lng=%s' % (lat, lng)
                obj = client.invoke(url, token)
                print('resp:', obj)

                if obj and 'data' in obj:
                    for loc in obj['data']:
                        print('loc', loc['id'])
                        url = 'locations/%s/media/recent' % loc['id']
                        obj1 = client.invoke(url, token)

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
