#!/usr/bin/env python
# coding: utf-8

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext as _, override

import logging
import hashlib
from .media import Media

log = logging.getLogger(__name__)
UserModel = get_user_model()


class CampaignStatus(object):
    NEW = 0
    READY = 10
    IN_PROGRESS = 20
    DONE = 100

    _texts = {
        NEW: _('new'),
        READY: _('ready'),
        IN_PROGRESS: _('in progress'),
        DONE: _('done'),
    }
    _icons = {
        NEW: 'fa fa-gift',
        READY: 'fa fa-cube',
        IN_PROGRESS: 'fa fa-spin fa-circle-o-notch',
        DONE: 'fa fa-check-circle',
    }
    Choices = _texts.items()
    Icons = _icons.items()

    @classmethod
    def get_text(cls, code):
        return cls._texts.get(code)

    @classmethod
    def get_slug(cls, code):
        slug = cls._texts.get(code)
        with override('en'):
            return slug

    @classmethod
    def get_icon(cls, code):
        return cls._icons.get(code)


class Campaign(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserModel)

    name = models.CharField(max_length=100)
    begin = models.DateTimeField(help_text='When will the campaign begin.')
    end = models.DateTimeField(help_text='When will the campaign end.')
    status = models.IntegerField(db_index=True, choices=CampaignStatus.Choices)

    providers = models.TextField(help_text='Comma separated provider codes')
    medias = models.ManyToManyField(Media)
    text = models.TextField()

    created_at = models.DateTimeField(auto_created=True, help_text='When the campaign created.')
    timestamp = models.DateTimeField(auto_now=True, help_text='When the campaign modified.')

    def get_status_text(self):
        return CampaignStatus.get_text(self.status)
