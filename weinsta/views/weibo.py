#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views.generic import TemplateView
from django.conf import settings
import requests
from urllib.parse import urlencode, quote
from .base import BaseViewMixin

from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp

import logging

log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class WeiboView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        acc = SocialAccount.objects.get(user=request.user)
        app = SocialApp.objects.get(provider=acc.provider)
        token = SocialToken.objects.get(app=app, account=acc)
        print(token)
        payload = {
            "access_token": token.token,
            "status": quote("Test status from http://mwl2.com/123"),

        }
        files = {
            "pic": ("Desert.jpg",
                         open(r"C:\Users\Public\Pictures\Sample Pictures\Desert.jpg", "rb"))

        }
        print(payload)
        r = requests.post('https://api.weibo.com/2/statuses/share.json',
                          proxies=settings.PROXIES, data=payload, files=files)
        print(r.status_code)
        print(r.headers)
        print(r.json())

        return super(WeiboView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(WeiboView, self).get_context_data(**kwargs)

        return context
