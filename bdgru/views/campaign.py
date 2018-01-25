#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.messages import error, success, warning
import logging

from .base import BaseViewMixin
from ..models import Campaign, SocialProviders, Media, MediaType, CampaignStatus, ActivityType, Battle
from .includes.campaign_form import CampaignFormViewMixin
log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class CampaignView(TemplateView, BaseViewMixin, CampaignFormViewMixin):

    view_name = 'dash_campaign'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''
        battle_id = kwargs['battle_id'] if 'battle_id' in kwargs else ''

        if action and action not in ['edit', 'battle']:
            return HttpResponseRedirect(reverse(CampaignView.view_name, kwargs={'id': id}))

        if id:
            camp = Campaign.objects.get(id=id, user=request.user)
            context['thecampaign'] = camp

            if battle_id:
                battle = Battle.objects.get(id=battle_id, campaign=camp.id)
                context['thebattle'] = battle

            # TODO: optimization required. (because activity grows fast)
            chart_data = {}
            labels_done = False
            for btl in camp.battles.all():
                data = {}
                labels = set()
                for t in ActivityType.Metas.keys():
                    data[t] = []

                for act in btl.activities.all():
                    label = act.datetime.strftime('%Y-%m-%d %H')
                    if not labels_done:
                        labels.add(label)
                    data[act.type].append(act.count)
                chart_data[btl.provider] = data
                if not labels_done:
                    chart_data['labels'] = list(sorted(labels))
                    labels_done = True
            context['chart_data'] = chart_data

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


@method_decorator(login_required, name='dispatch')
class CampaignEditView(TemplateView, BaseViewMixin, CampaignFormViewMixin):

    view_name = 'dash_campaign_edit'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''

        if id:
            camp = Campaign.objects.get(id=id, user=request.user)
            context['thecampaign'] = camp

        return self.render_to_response(context)

    # POST action handled by CampaignView

    def get_context_data(self, **kwargs):
        context = super(CampaignEditView, self).get_context_data(**kwargs)

        action = kwargs['action'] if 'action' in kwargs else ''

        context['providers'] = SocialProviders
        context['mediatypes'] = MediaType
        context['campaignstatus'] = CampaignStatus
        context['activitytypes'] = ActivityType

        context['disabled_buttons'] = [] if action == 'edit' else ['SAVE', 'RESET']

        return context
