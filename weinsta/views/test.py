#!/usr/bin/env python
# coding: utf-8

from django.views.generic import TemplateView
from .base import BaseViewMixin
from tasks.campaign import track_battle, test
import logging

log = logging.getLogger(__name__)


# @method_decorator(login_required, name='dispatch')
class TestView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        test.delay()
        track_battle.delay()
        return super(TestView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TestView, self).get_context_data(**kwargs)
        return context
