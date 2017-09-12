#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views.generic import TemplateView
from .base import BaseViewMixin
import logging
from ..clients import InstagramClient
from .insta import InstaView

log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(IndexView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        token = InstaView.get_my_insta_token(self.request)
        if token:
            client = InstagramClient(token=token)
            context['medias'] = client.fetch_my_timeline()
        return context
