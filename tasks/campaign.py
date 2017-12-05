#!/usr/bin/env python
# coding: utf-8
from celery import shared_task
from celery.utils.log import get_task_logger
import time
from weinsta.clients import CampaignGeneral
from weinsta.clients.campaign import BattleCommander
from weinsta.models import Battle

log = get_task_logger(__name__)


@shared_task(bind=True)
def track_all_activities(self):
    """
    Track activities of a campaign (with all its battles).
    :param campaign: Campaign model instance. The campaign to track
    :return:
    """
    log.info('tracking all battles.')
    battles = Battle.objects.filter(started=True, finished=False).all()
    for battle in battles:
        try:
            track_battle(battle)
        except Exception as err:
            log.error(str(err))
            battle.finished = True
            battle.save()

@shared_task(bind=True)
def track_campaign(self, campaign):
    """
    Track activities of a campaign (with all its battles).
    :param campaign: Campaign model instance. The campaign to track
    :return:
    """
    log.info('tracking campaign %s' % campaign)
    general = CampaignGeneral(campaign=campaign)
    try:
        general.track()
    except Exception as err:
        log.exception(err)


@shared_task(bind=True)
def track_battle(self, battle):
    """
    Track activities of a battle (social channel).
    :param battle: Battle model instance. The battle to track
    :return:
    """
    log.info('tracking battle %s' % battle)
    cmder = BattleCommander(battle=battle)
    try:
        cmder.track()
    except Exception as err:
        log.exception(err)


@shared_task(bind=True)
def test(self):
    log.info('test')
    print('testing...')
    time.sleep(2)
    print('test done')