#!/usr/bin/env python
# coding: utf-8

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext as _, override

import logging
import hashlib
from .media import Media, SocialProviders

log = logging.getLogger(__name__)
UserModel = get_user_model()


class CampaignStatus(object):
    NEW = 0
    READY = 10
    IN_PROGRESS = 20
    DONE = 100

    __metas = {
        NEW: (NEW, _('new'), 'fa fa-gift text-secondary'),
        READY: (READY, _('ready'), 'fa fa-cube text-success'),
        IN_PROGRESS: (IN_PROGRESS, _('in progress'), 'fa fa-spin fa-circle-o-notch text-primary'),
        DONE: (DONE, _('done'), 'fa fa-check-circle text-strike'),
    }

    Metas = __metas
    Choices = tuple(map(lambda x: (x[0], x[1]), __metas.values()))

    @classmethod
    def get_text(cls, code):
        meta = cls.__metas.get(code)
        return meta[1] if meta else None

    @classmethod
    def get_slug(cls, code):
        slug = cls.get_text(code)
        with override('en'):
            return slug

    @classmethod
    def get_icon(cls, code):
        meta = cls.__metas.get(code)
        return meta[2] if meta else None


class Campaign(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserModel)

    name = models.CharField(max_length=100)
    begin = models.DateTimeField(help_text='When will the campaign begin.', null=True, blank=True)
    end = models.DateTimeField(help_text='When will the campaign end.', null=True, blank=True)
    status = models.IntegerField(db_index=True, choices=CampaignStatus.Choices, default=CampaignStatus.NEW)
    providers = models.TextField(help_text='Comma separated provider codes')
    medias = models.ManyToManyField(Media)
    text = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False, help_text='When the campaign created.')
    timestamp = models.DateTimeField(auto_now=True, help_text='When the campaign modified.')

    def __str__(self):
        return "#%s %s" % (self.id, self.name)

    def get_status_text(self):
        return CampaignStatus.get_text(self.status)

    def get_status_icon(self):
        return CampaignStatus.get_icon(self.status)

    def get_providers(self):
        return self.providers.split(',') if self.providers else []

    def get_media_ids(self):
        return list(map(lambda x: x.id, self.medias.all()))
