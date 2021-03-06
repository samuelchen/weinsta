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
from ..models import Campaign, SocialProviders, Media, MediaType, CampaignStatus, ActivityType, Battle
from .includes.campaign_form import CampaignFormViewMixin
log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class CampaignView(TemplateView, BaseViewMixin, CampaignFormViewMixin):

    view_name = 'campaign'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''
        battle_id = kwargs['battle_id'] if 'battle_id' in kwargs else ''

        if action and action not in ['detail', 'battle']:
            return HttpResponseRedirect(reverse(CampaignView.view_name, kwargs={'id': id}))

        if id:
            camp = Campaign.objects.get(id=id)
            context['thecampaign'] = camp

            if battle_id:
                battle = Battle.objects.get(id=battle_id)
                context['thebattle'] = battle

                # TODO: optimization required. (because activity grows fast)
                data = {}
                for t in ActivityType.Metas.keys():
                    data[t] = {}
                    data[t]['data'] = []
                    data[t]['labels'] = []

                for act in battle.activities.all():
                    label = act.datetime.strftime('%Y-%m-%d %H')
                    data[act.type]['labels'].append(label)
                    data[act.type]['data'].append(act.count)
                context['chart_data'] = data

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        # req = request.POST
        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''
        camp = None

        if id:
            try:
                camp = Campaign.objects.get(id=id, user=request.user)
            except Campaign.DoesNotExist as err:
                return HttpResponseNotFound(_('Campaign %s is not found in your list.') % id)

        camp = self.handle_campaign_action(action=action, campaign=camp)

        if camp:
            context['thecampaign'] = camp
            # id = camp.id

        if action in ['del', ]:
            return HttpResponseRedirect(reverse(CampaignView.view_name))
        # elif action in ['new', ]:
        #     return HttpResponseRedirect(reverse(CampaignView.view_name, kwargs={'id': id}))

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(CampaignView, self).get_context_data(**kwargs)

        action = kwargs['action'] if 'action' in kwargs else ''

        context['providers'] = SocialProviders
        context['mediatypes'] = MediaType
        context['campaignstatus'] = CampaignStatus
        context['activitytypes'] = ActivityType

        context['campaigns'] = Campaign.objects.filter(user=self.request.user).order_by('-timestamp')

        context['disabled_buttons'] = [] if action == 'detail' else ['SAVE', 'RESET']

        return context
