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


class TwitterView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(TwitterView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super(TwitterView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TwitterView, self).get_context_data(**kwargs)

        req = self.request.GET
        tab = req.get('tab', '1')
        context['tab'] = tab

        token = TwitterClient.get_my_token(self.request)
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

