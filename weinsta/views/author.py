#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views.generic import TemplateView
from .base import BaseViewMixin
from ..models.media import SocialUser
import logging
log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class AuthorView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(AuthorView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AuthorView, self).get_context_data(**kwargs)

        context['authors'] = SocialUser.objects.all()
        return context

