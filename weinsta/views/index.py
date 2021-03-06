#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views.generic import TemplateView
from .base import BaseViewMixin
import logging
from ..clients import InstagramClient

log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(IndexView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        token = InstagramClient.get_token(self.request.user, self.request)
        if token:
            client = InstagramClient(token=token)
            context['medias'] = client.fetch_my_timeline()
            for md in context['medias']:
                client.save_media(md, self.request.user, update_if_exists=False, cache_to_local=True)
        return context
