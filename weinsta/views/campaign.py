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
from ..models import Campaign, SocialProviders, Media, MediaType, CampaignStatus

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

        # req = request.POST
        action = kwargs['action'] if 'action' in kwargs else ''
        id = kwargs['id'] if 'id' in kwargs else ''
        camp = None

        if id:
            try:
                camp = Campaign.objects.get(id=id, user=request.user)
            except Campaign.DoesNotExist as err:
                return HttpResponseBadRequest(_('Campaign %s of yours is not found.') % id)

        if action == 'new':
            camp = self.create_campaign()
            # return HttpResponseRedirect(reverse(CampaignView.view_name, kwargs={'id': camp.id}))
        elif action == 'renew' and camp:
            self.renew_campaign(camp)
        elif action == 'del' and camp:
            if self.del_campaign(camp):
                camp = None
        elif action == 'ready' and camp:
            self.ready_campaign(camp)
        elif action == 'start' and camp:
            self.start_campaign(camp)
        elif action == 'done' and camp:
            self.done_campaign(camp)
        elif action == 'update' and camp:
            self.update_campaign(camp)

        if camp:
            context['thecampaign'] = camp

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(CampaignView, self).get_context_data(**kwargs)

        context['providers'] = SocialProviders
        context['mediatypes'] = MediaType
        context['campaignstatus'] = CampaignStatus

        context['campaigns'] = Campaign.objects.filter(user=self.request.user).order_by('-timestamp')
        return context

    # TODO: the following campaign methods can be optimized (multiple-saves)
    def update_campaign(self, camp):

        request = self.request

        if camp.status in [CampaignStatus.READY, CampaignStatus.IN_PROGRESS, CampaignStatus.DONE]:
            msg = 'Campaign "%s" with status "%s" can not be updated.'
            log.warn(msg % (camp, camp.get_status_text()))
            error(request, _(msg) % (camp, camp.get_status_text()))
            return

        req = request.POST
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

        success(request, _('Campaign "%s" updated.') % camp)

        return True

    def start_campaign(self, camp):

        # only work for DEBUG
        if not settings.DEBUG:
            return False

        request = self.request
        if camp.status != CampaignStatus.READY:
            error(request, _('Campaign must be ready then you can start.'))
            return False

        log.debug('Starting campaign %s' % camp)
        try:
            tracer = CampaignGeneral(campaign=camp, user=request.user, request=request)
            results, started = tracer.start()

            if started:
                camp.status = CampaignStatus.IN_PROGRESS
                camp.save()
                success(request, _('Campaign "%s" is started.') % camp)

            print(results)
            for provider, r in results.items():
                if 'error' in r:
                    error(request, _('Campaign "%s" fail to start on "%s". Error(%s): %s') % (
                        camp, provider, r['code'], r['error']))
                else:
                    success(request, _('Campaign "%s" successfully started on "%s".') % (camp, provider))
            return True
        except Exception as err:
            error(request, str(err))
            log.exception(err)
            return False

    def ready_campaign(self, camp):

        # TODO: if ready or in progress

        # need to update first
        self.update_campaign(camp)

        request = self.request
        if not camp.providers:
            error(request, _('You must select at least 1 channel to publish to.'))
            return False
        else:
            log.debug('Marking campaign %s ready.' % camp)
            camp.status = CampaignStatus.READY
            camp.save()
            success(request, _('Campaign "%s" is ready to go.') % camp)
            return True

    def done_campaign(self, camp):

        self.update_campaign(camp)

        request = self.request
        log.debug('Marking campaign %s done.' % camp)
        camp.status = CampaignStatus.DONE
        camp.save()
        success(request, _('Campaign "%s" is marked done.') % camp)
        return True

    def renew_campaign(self, camp):

        request = self.request

        if camp.status in [CampaignStatus.IN_PROGRESS, ]:
            msg = 'Campaign "%s" with status "%s" can not renew. Mark it done first.'
            log.warn(msg % (camp, camp.get_status_text()))
            error(request, _(msg) % (camp, camp.get_status_text()))
            return False

        log.debug('Renew campaign %s.' % camp)
        camp.status = CampaignStatus.NEW
        #TODO: clean battles and others
        camp.battles.all().delete()
        camp.save()
        success(request, _('Campaign "%s" is new now.') % camp)

        return True

    def del_campaign(self, camp):
        request = self.request

        if camp.status == CampaignStatus.IN_PROGRESS:
            warning(request, _('Campaign "%s" is in progress. Please "Mark Done" it before deleting' % camp))
            return False

        msg = _('Campaign "%s" deleted.') % camp
        log.debug('Deleting campaign %s' % camp)
        camp.delete()
        success(request, msg)
        return True

    def create_campaign(self):
        request = self.request
        camp = Campaign.objects.create(user=request.user, name=_('New Campaign'))
        success(request, _('New campaign "%s" created.') % camp)
        return camp

