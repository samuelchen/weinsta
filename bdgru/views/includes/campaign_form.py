#!/usr/bin/env python
# coding: utf-8

"""
A campaign form view mixin.
Co-work with includes:
    - campaign-form.html
    - campaign-action-buttons.html
"""
from django.urls import reverse

from django.utils.translation import ugettext as _
from django.utils import timezone
from django.views import View
from django.contrib.messages import error, success, warning
from dateutil import parser as dtparser
from urllib.request import urlparse

from django.conf import settings
from ...clients import CampaignGeneral, SocialClientManager
from ...models import Campaign, Media, CampaignStatus, SocialProviders, Battle

import logging
from weinsta.clients.base import SocialTokenExpiredException
from weinsta.clients.campaign import BattleObserver, BattleUnsupportedUrlException, BattleChannelExistedException

log = logging.getLogger(__name__)


# TODO: move all campaign methods to CampaignGeneral (client/campaign.py)
class CampaignFormViewMixin(View):

    def handle_campaign_action(self, action, campaign=None):

        camp = campaign

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
        elif action == 'track' and camp:
            self.track_campaign(camp)
        elif action == 'add' and camp:
            self.add_battle_to_campaign(camp)
        else:
            log.error('Unknown action "%s" to campaign %s .' % (action, campaign))

        return camp

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

        if 'camp_provider' in req:
            camp_provider = req.getlist('camp_provider')
            camp.providers = ','.join(camp_provider)

        camp.name = req.get('camp_name', camp.name)
        camp.text = req.get('camp_text', camp.text)

        t = req.get('camp_begin')
        if t:
            camp.begin = timezone.make_aware(dtparser.parse(t))

        t = req.get('camp_end')
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
            tracer = CampaignGeneral(campaign=camp, request=request)
            results, started = tracer.start()

            if started:
                camp.status = CampaignStatus.IN_PROGRESS
                camp.save()
                success(request, _('Campaign "%s" is started.') % camp)

            log.debug(results)
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

    def track_campaign(self, camp):
        request = self.request
        try:
            general = CampaignGeneral(campaign=camp, request=request)
            general.track()
        except SocialTokenExpiredException as err:
            provider = str(err)
            error(request, _('Your %s token expired. Please <a href="%s">re-connect</a> your social account.') %
                  (SocialProviders.get_text(provider), reverse('socialaccount_connections')))
        except Exception as err:
            log.exception(err)
            error(request, str(err))

    def add_battle_to_campaign(self, camp):

        assert camp is not None
        request = self.request

        if camp.status > CampaignStatus.IN_PROGRESS:
            error(request, _('Can not add channel to finished campaign.'))
            return

        req = request.POST
        url = req['channel_url'] if 'channel_url' in req else ''

        general = CampaignGeneral(campaign=camp, request=request)

        try:
            battle = general.add_battle_from_url(url)
            log.debug('Battle %s added.' % battle)
        except BattleUnsupportedUrlException as err:
            url = str(err)
            error(request, _('Url "%s" is not from a supported social platform.') % url)
            return
        except BattleChannelExistedException as err:
            provider = str(err)
            error(request, _('You have a channel on %s already.') % SocialProviders.get_text(provider))
            pass
        except SocialTokenExpiredException as err:
            provider = str(err)
            error(request, _('Your %s token expired. Please <a href="%s">re-connect</a> your social account.') %
                  (SocialProviders.get_text(provider), reverse('socialaccount_connections')))
