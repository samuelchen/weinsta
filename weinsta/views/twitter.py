#!/usr/bin/env python
# coding: utf-8


from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
import requests
from .base import BaseViewMixin
from ..models import MediaType, SocialProviders, SocialUser, Media, LikedMedia, MyMedia
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


class TwitterView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(TwitterView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super(TwitterView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TwitterView, self).get_context_data(**kwargs)

        user = self.request.user
        req = self.request.GET
        tab = req.get('tab', '1')
        context['tab'] = tab

        # liked_medias = None

        def on_likes(likes):
            for md in likes:
                m = client.save_media(md, user, update_if_exists=False, cache_to_local=True)
                if m:
                    like, created = LikedMedia.objects.get_or_create(user=user, media=m)
                    if created:
                        like.save()

        def on_my_medias(my_medias):
            for md in my_medias:
                m = client.save_media(md, self.request.user, update_if_exists=False, cache_to_local=True)
                mine, created = MyMedia.objects.get_or_create(user=self.request.user, media=m)
                if created:
                    mine.save()

        token = TwitterClient.get_token(user, request=self.request)
        if not token:
            return context

        client = TwitterClient(token=token)

        # async-call
        client.fetch_favorites(callback=on_likes)
        # client.fetch_my_own_medias(callback=on_my_medias)

        if tab == '1':
            # favorites sync-call
            # context['medias'] = client.fetch_favorites()
            # on_likes(context['medias'])

            context['medias'] = LikedMedia.objects.filter(user=self.request.user,
                                                          media__provider=SocialProviders.TWITTER
                                                          ).select_related('media')
        elif tab == '2':
            # search tags
            pass
        elif tab == '3':
            # locations
            pass

        return context

