#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _, ugettext_noop
from django.views.generic import TemplateView
from .base import BaseViewMixin
from ..models import Media, MediaType, MyMedia, LikedMedia
from collections import OrderedDict
import logging
import os
from django.conf import settings
log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class MediaView(TemplateView, BaseViewMixin):

    tabs = OrderedDict((
        ('1', ugettext_noop('My Medias')),
        ('2', ugettext_noop('Liked Medias')),
        # ('3', ugettext_noop('Media Library')),
    ))

    def get(self, request, *args, **kwargs):
        return super(MediaView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MediaView, self).get_context_data(**kwargs)

        # request = self.request
        # user = request.user
        req = self.request.GET
        tab = req.get('tab', '1')
        context['tab'] = tab
        context['tabs'] = MediaView.tabs
        log.debug('Switch to tab %s' % MediaView.tabs[tab])

        context['mediatypes'] = MediaType

        if tab == '1':
            # public medias from social platforms
            context['medias'] = MyMedia.objects.filter(user=self.request.user).select_related('media')
        elif tab == '2':
            # local library
            context['medias'] = LikedMedia.objects.filter(user=self.request.user,
                                                          ).select_related('media')
        else:
            context['medias'] = []

        return context
