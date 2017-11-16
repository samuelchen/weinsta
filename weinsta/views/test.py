#!/usr/bin/env python
# coding: utf-8

from django.views.generic import TemplateView
from .base import BaseViewMixin
from weinsta.celery import debug_task
import logging

log = logging.getLogger(__name__)


# @method_decorator(login_required, name='dispatch')
class TestView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        debug_task.delay()
        return super(TestView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TestView, self).get_context_data(**kwargs)
        return context
