#!/usr/bin/env python
# coding: utf-8

from urllib.parse import quote
from django.views.generic import TemplateView
from django.conf import settings
from django.contrib.messages import success, error
from django.utils.translation import ugettext as _
from .base import BaseViewMixin
from ..models import MediaType, SocialProviders, SocialUser, Media, LikedMedia, MyMedia
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
import requests
from allauth.socialaccount.providers import registry
import logging
from weinsta.clients import TwitterClient

log = logging.getLogger(__name__)


class PubView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(PubView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # context = self.get_context_data()
        # media = context['media']
        id = kwargs['media_id']
        media = Media.objects.get(id=id)
        text = request.POST.get('text')
        owner = request.POST.get('owner')
        text = '%s #%s# http://instagram.com/%s \n%s' % (owner, media.provider, owner, text)

        if SocialProviders.WEIBO in request.POST:
            self.pub_to_weibo(media.thumb, text)

        if SocialProviders.TWITTER in request.POST:
            token = TwitterClient.get_my_token(request)
            client = TwitterClient(token=token)
            client.post_status(text, media.thumb)

        return super(PubView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PubView, self).get_context_data(**kwargs)
        media_id = kwargs['media_id']
        context['media'] = Media.objects.get(id=media_id)
        context['providers'] = SocialProviders
        return context

    def pub_to_weibo(self, img_field, text):

        provider = registry.by_id(SocialProviders.WEIBO, self.request)
        log.debug('Provider is :' + str(provider))
        app = SocialApp.objects.get(provider=provider.id)
        acc = SocialAccount.objects.get(provider=provider.id, user=self.request.user)
        token = SocialToken.objects.get(app=app, account=acc)
        payload = {
            "access_token": token.token,
            "status": quote(text),

        }
        # print(img_field)
        # print(dir(img_field))
        # print(img_field.storage)
        print(img_field.path)
        files = {
            "pic": (img_field.name, open(img_field.path, 'rb'))

        }
        print(payload)
        r = requests.post('https://api.weibo.com/2/statuses/share.json',
                          proxies=settings.PROXIES, data=payload, files=files)
        print(r.status_code)
        print(r.headers)
        print(r.json())

        if 200 <= r.status_code < 400:
            success(self.request, _('You media is successfully post to Weibo.'))
            success(self.request, r.json())
        else:
            error(self.request, '%s %s' % (r.status_code, r.reason))
            error(self.request, r.json())
