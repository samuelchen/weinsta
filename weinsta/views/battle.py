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
from ..models import Campaign, SocialProviders, Media, MediaType, CampaignStatus, ActivityType, Battle, Activity
from weinsta.clients.base import SocialTokenException

log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class BattleView(TemplateView, BaseViewMixin):

    view_name = 'battle'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if 'error' in kwargs:
            error(request, kwargs['error'])
            print(kwargs['error'])
            del kwargs['error']

        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''
        battle_id = kwargs['battle_id'] if 'battle_id' in kwargs else ''

        if action == 'battle':
            pass
        else:
            return HttpResponseRedirect(reverse(BattleView.view_name, kwargs={'id': id, 'action': 'battle'}))

        if id:
            camp = Campaign.objects.get(id=id)
            context['thecampaign'] = camp
            context['battles'] = camp.battles

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
                # print(data)

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        # context = self.get_context_data(**kwargs)

        # req = request.POST
        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''
        battle_id = kwargs['battle_id'] if 'battle_id' in kwargs else ''
        camp = None

        if id:
            try:
                camp = Campaign.objects.get(id=id, user=request.user)
            except Campaign.DoesNotExist:
                return HttpResponseBadRequest(_('Campaign %s of yours is not found.') % id)

        if action == 'track' and camp:
            try:
                general = CampaignGeneral(campaign=camp, request=request)
                general.track()
            except Exception as err:
                log.exception(err)
                s = str(err)
                if isinstance(err, SocialTokenException):
                    s += _(' Please <a href="%s">re-connect</a> your social account.') % reverse('socialaccount_connections')
                error(request, s)
        # if camp:
        #     context['thecampaign'] = camp

        # return self.render_to_response(context)
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BattleView, self).get_context_data(**kwargs)

        context['activitytypes'] = ActivityType
        context['providers'] = SocialProviders
        context['mediatypes'] = MediaType
        context['campaignstatus'] = CampaignStatus

        # context['campaigns'] = Campaign.objects.filter(user=self.request.user).order_by('-timestamp')
        return context
