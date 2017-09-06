#!/usr/bin/env python
# coding: utf-8
from django.views.generic.base import ContextMixin
from django.contrib import messages
from django.utils.translation import pgettext_lazy, ugettext_lazy as _


class BaseViewMixin(ContextMixin):

    def get_context_data(self, **kwargs):
        context = super(BaseViewMixin, self).get_context_data(**kwargs)

        context['website'] = {
            "domain": "bdgru.com",
            "name": "BDGRU",
            "fullname": _('Business Development Guru')
        }

        return context

    def info(self, message, tags=''):
        messages.info(request=self.request, message=message, extra_tags=tags)

    def warn(self, message, tags=''):
        messages.warning(request=self.request, message=message, extra_tags=tags)

    def error(self, message, tags=''):
        messages.error(request=self.request, message=message, extra_tags=tags)

    def success(self, message, tags=''):
        messages.success(request=self.request, message=message, extra_tags=tags)

    def debug(self, message, tags=''):
        messages.set_level(self.request, messages.DEBUG)
        messages.debug(request=self.request, message=message, extra_tags=tags)

