#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.messages import error, success, warning
from dateutil import parser as dtparser
import logging

from .base import BaseViewMixin
from .. import settings
from ..clients import CampaignGeneral
from ..models import Campaign, SocialProviders, Media, MediaType, CampaignStatus, ActivityType

log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class ActivityView(TemplateView, BaseViewMixin):

    view_name = 'activity'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''

        if action == 'activities':
            pass
        else:
            return HttpResponseRedirect(reverse(ActivityView.view_name, kwargs={'id': id, 'action': 'activities'}))

        if id:
            camp = Campaign.objects.get(id=id)
            context['thecampaign'] = camp
            context['battles'] = camp.battles

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        # context = self.get_context_data(**kwargs)

        # req = request.POST
        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''
        camp = None

        if id:
            try:
                camp = Campaign.objects.get(id=id, user=request.user)
            except Campaign.DoesNotExist:
                return HttpResponseBadRequest(_('Campaign %s of yours is not found.') % id)

        if action == 'track' and camp:
            general = CampaignGeneral(campaign=camp, user=request.user)
            try:
                general.track()
            except Exception as err:
                log.error(err)
                error(request, str(err))
        # if camp:
        #     context['thecampaign'] = camp

        # return self.render_to_response(context)
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ActivityView, self).get_context_data(**kwargs)

        context['activitytypes'] = ActivityType
        context['providers'] = SocialProviders
        context['mediatypes'] = MediaType
        context['campaignstatus'] = CampaignStatus

        # context['campaigns'] = Campaign.objects.filter(user=self.request.user).order_by('-timestamp')
        return context
