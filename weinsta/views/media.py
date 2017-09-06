#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views.generic import TemplateView
from .base import BaseViewMixin
from ..models import Media, MediaType
import logging
import os
from django.conf import settings
log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class MediaView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(MediaView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MediaView, self).get_context_data(**kwargs)

        # request = self.request
        # user = request.user

        context['medias'] = Media.objects.all()
        context['mediatypes'] = MediaType

        return context
