#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views.generic import TemplateView
from .base import BaseViewMixin
from ..models import Media
import logging
import os
from django.conf import settings
log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class MediasView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(MediasView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MediasView, self).get_context_data(**kwargs)

        # request = self.request
        # user = request.user

        context['medias'] = Media.objects.all()

        return context
