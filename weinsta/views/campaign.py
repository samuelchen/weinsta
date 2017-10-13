#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.urls import reverse
from django.views.generic import TemplateView
from .base import BaseViewMixin
from ..models import Campaign, SocialProviders, Media, MediaType, CampaignStatus
from dateutil import parser as dtparser
import logging

log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class CampaignView(TemplateView, BaseViewMixin):

    view_name = 'campaign'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''

        if action:
            return HttpResponseRedirect(reverse(CampaignView.view_name, kwargs={'id': id}))

        if id:
            camp = Campaign.objects.get(id=id)
            context['thecampaign'] = camp

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        req = request.POST
        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''
        camp = None

        if id:
            try:
                camp = Campaign.objects.get(id=id, user=request.user)
            except Campaign.DoesNotExist as err:
                return HttpResponseBadRequest(_('Campaign %s of yours is not found.') % id)

        if action == 'new':
            camp = Campaign.objects.create(user=request.user, name=_('New Campaign'))
            # return HttpResponseRedirect(reverse(CampaignView.view_name, kwargs={'id': camp.id}))
        elif action == 'del' and camp:
            log.debug('Deleting campaign %s' % camp)
            camp.delete()
            camp = None
        elif action == 'ready' and camp:
            log.debug('Making campaign %s ready.' % camp)
            camp.status = CampaignStatus.READY
            camp.save()
        elif action == 'start' and camp:
            log.debug('Starting campaign %s' % camp)
            camp.status = CampaignStatus.IN_PROGRESS
            camp.save()
        elif action == 'done' and camp:
            log.debug('Marking campaign %s done.' % camp)
            camp.status = CampaignStatus.DONE
            camp.save()
        elif action == 'update' and camp:
            log.debug('Updating campaign %s' % camp)

            if 'sel_media' in req:
                sel_medias = req.getlist('sel_media')
                sel_medias = list(map(lambda x: int(x), sel_medias))
                camp.medias = Media.objects.filter(id__in=sel_medias)

            if 'sel_provider' in req:
                sel_providers = req.getlist('sel_provider')
                camp.providers = ','.join(sel_providers)

            camp.name = req.get('name', camp.name)
            camp.text = req.get('text', camp.text)

            t = req.get('begin')
            if t:
                camp.begin = timezone.make_aware(dtparser.parse(t))

            t = req.get('end')
            if t:
                camp.end = timezone.make_aware(dtparser.parse(t))

            camp.save()

        if camp:
            context['thecampaign'] = camp

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(CampaignView, self).get_context_data(**kwargs)

        # req = self.request.POST

        # action = kwargs['action'] if 'action' in kwargs else ''
        # id = kwargs['id'] if 'id' in kwargs else ''
        #
        # if action == 'new':
        #     camp = Campaign.objects.create()
        #     context['thecampaign'] = camp
        #     HttpResponseRedirect

        # sel_medias = []
        # if 'sel_media' in req:
        #     sel_medias = req.getlist('sel_media')
        #     sel_medias = list(map(lambda x: int(x), sel_medias))
        #
        # sel_providers = []
        # if 'sel_provider' in req:
        #     sel_providers = req.getlist('sel_provider')

        # context['sel_providers'] = sel_providers
        # context['sel_medias'] = sel_medias

        context['providers'] = SocialProviders
        context['mediatypes'] = MediaType
        context['campaignstatus'] = CampaignStatus

        context['campaigns'] = Campaign.objects.filter(user=self.request.user).order_by('-timestamp')
        return context
