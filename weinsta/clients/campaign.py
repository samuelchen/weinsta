#!/usr/bin/env python
# coding: utf-8
from urllib.parse import urlparse

from .base import CampaignMixin
from ..models import Campaign, Battle, Activity, ActivityType, SocialProviders, CampaignStatus
from .utils import SocialClientManager
import logging

log = logging.getLogger(__name__)


class CampaignException(Exception):
        pass


class BattleException(Exception):
    pass


class BattleUnsupportedUrlException(BattleException):
    pass


class BattleChannelExistedException(BattleException):
    pass


class CampaignGeneral(CampaignMixin):

    def __init__(self, campaign, request=None):
        assert isinstance(campaign, Campaign)
        self._camp = campaign
        self._request = request
        # self._clients = SocialClientManager.get_clients(self._camp.get_providers(), self._camp.user)
        # log.debug('clients: %s' % self._clients)

    @property
    def campaign(self):
        return self._camp

    # ------- Campaign overrides ----------

    def start(self):
        started = False
        rc = {}
        camp = self.campaign
        clients = SocialClientManager.get_clients(self._camp.get_providers(), self._camp.user, request=self._request)
        for provider, cli in clients.items():
            cmder = BattleCommander.get(campaign=camp, provider=provider)
            r = cmder.start()
            if "error" not in r:
                started = True
            rc[provider] = r
        return rc, started

    def stop(self):
        pass

    def track(self):
        camp = self._camp
        for battle in camp.battles.all():
            cmder = BattleCommander(battle)
            cmder.track()

    # ------- Campaign overrides Ends----------

    def add_battle_from_url(self, url):
        camp = self._camp

        r = urlparse(url)
        netloc = r.netloc.lower()
        log.debug('adding channel url from %s' % netloc)

        provider = SocialProviders.UNKNOWN
        for t, m in SocialProviders.Metas.items():
            if netloc in m[4]:
                provider = t
                break

        if provider == SocialProviders.UNKNOWN:
            raise BattleUnsupportedUrlException(url)

        cli = SocialClientManager.get_client(provider=provider, user=self._camp.user, request=self._request)
        rid = cli.get_rid_from_url(url)

        battle, created = Battle.objects.get_or_create(campaign=camp, provider=provider)
        if created:
            if camp.providers:
                providers = camp.providers.split(',')
                providers.append(provider)
                camp.providers = ','.join(providers)
            else:
                camp.providers = provider
            camp.save()

            battle.rid = rid
            if camp.status == CampaignStatus.IN_PROGRESS:
                battle.started = True
                BattleObserver.init(battle)
            battle.save()
        else:
            raise BattleChannelExistedException(provider)

        return battle

    def remove_battle(self, battle):
        pass


class BattleCommander(object):

    def __init__(self, battle):
        self._battle = battle
        self._user = battle.campaign.user
        self._client = SocialClientManager.get_client(provider=battle.provider, user=battle.campaign.user)

    @property
    def battle(self):
        return self._battle

    def start(self):
        battle = self._battle
        if battle.finished or battle.started:
            raise BattleException('Can not start battle which is already started or finished.')

        cli = self._client
        camp = battle.campaign
        if battle.rid is None:
            r = cli.post_status(camp.text, camp.medias.all())
            if 'error' in r:
                log.error('Fail to start campaign "%s" on %s. Error: %s' % (camp, cli.provider, r['error']))
                battle.started = False
            else:
                log.debug('Campaign "%s" started on %s.' % (camp, cli.provider))
                battle.started = True
                battle.rid = r['id']    # TODO: need to add a social object -> model converter (abstracted)
        else:
            battle.started = True
            r = {'succeed': 'The battle was added.'}

        battle.save()
        BattleObserver.init(battle)

        return r

    def stop(self):
        pass

    def track(self):
        BattleObserver.check(self.battle)

    @staticmethod
    def get(campaign, provider):
        battle, created = Battle.objects.get_or_create(campaign=campaign, provider=provider)
        cmder = BattleCommander(battle=battle)
        return cmder


class BattleObserver(object):

    def __init__(self):
        pass

    @staticmethod
    def init(battle):
        # dt = timezone.now()
        # tag = dt.strftime('%Y-%m-%d %H')
        # hr = int(dt.strftime('%Y%m%d%h'))
        for act_type in ActivityType.Metas.keys():
            # act = Activity.objects.create(battle=battle, type=act_type, datetime=dt, tag=tag, hour=hr)
            # act.save()
            act = Activity(battle=battle, type=act_type)
            act.handle_datetime()
            act.save()

    @staticmethod
    def check(battle):
        # dt = timezone.now()
        # tag = dt.strftime('%Y-%m-%d %H')
        # hr = int(dt.strftime('%Y%m%d%h'))
        cli = SocialClientManager.get_client(provider=battle.provider, user=battle.campaign.user)
        data = cli.get_activity_data(rid=battle.rid)
        for act_type in ActivityType.Metas.keys():
            # act = Activity.objects.create(battle=battle, type=act_type, datetime=dt, tag=tag, hour=hr)
            act = Activity(battle=battle, type=act_type)
            act.handle_datetime()
            act.count = data[act_type]['count']
            act.save()
