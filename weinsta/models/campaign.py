#!/usr/bin/env python
# coding: utf-8
from django.utils import timezone

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext as _, override

import logging
import hashlib
from .media import Media, SocialProviders, SocialUser

log = logging.getLogger(__name__)
UserModel = get_user_model()


class CampaignStatus(object):
    NEW = 0
    READY = 10
    IN_PROGRESS = 20
    DONE = 100

    __metas = {
        NEW: (NEW, _('new'), 'fa fa-fw fa-gift text-primary'),
        READY: (READY, _('ready'), 'fa fa-fw fa-play-circle-o text-success'),
        IN_PROGRESS: (IN_PROGRESS, _('in progress'), 'fa fa-fw fa-spin fa-spinner text-success'),
        DONE: (DONE, _('done'), 'fa fa-fw fa-check-square-o text-secondary'),
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


class ActivityType(object):
    LIKE = 'like'
    COMMENT = 'comment'
    REPOST = 'repost'

    __metas = {
        LIKE: (LIKE, _('like'), 'fa fa-fw fa-thumbs-o-up'),
        COMMENT: (COMMENT, _('comment'), 'fa fa-fw fa-comments-o'),
        REPOST: (REPOST, _('repost'), 'fa fa-fw fa-mail-forward'),
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
        return sorted(self.providers.split(',') if self.providers else [])

    def get_media_ids(self):
        return sorted(list(map(lambda x: x.id, self.medias.all())))

    def get_started_battles(self):
        return self.battles.filter(staretd=True).values('provider')


class Battle(models.Model):
    """
    Battle means marketing activities on specified social provider
    """
    id = models.BigAutoField(primary_key=True)

    campaign = models.ForeignKey(Campaign, related_name='battles')
    provider = models.CharField(max_length=50, choices=SocialProviders.Choices)
    rid = models.CharField(max_length=100, help_text='remote id of posted status for this battle')
    link = models.TextField(help_text='link for the status')

    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    class Meta:
        unique_together = ('provider', 'rid')

    def latest_activities(self):
        return Activity.objects.filter(battle=self).order_by('-id')[0:len(ActivityType.Metas)]


# TODO: Activity grows very fast. Need optimization.
class Activity(models.Model):
    id = models.BigAutoField(primary_key=True)
    battle = models.ForeignKey(Battle, related_name='activities', db_index=True)
    type = models.CharField(max_length=50, choices=ActivityType.Choices)    # , db_index=True

    datetime = models.DateTimeField(help_text='When the activity data was collected')
    # e.g. 2017-10-12 14:32:12 -> "2017-10-12 14" (Note: utc -> string)
    tag = models.CharField(max_length=100,
                           help_text='The date time string (to hour). For grouping, labeling.')
    # e.g. 2017-10-12 14:32:12 -> 2017101214 (Note: utc -> int. no timezone info)
    hour = models.IntegerField(# db_index=True,
                               help_text='Date time in int format (to hour). e.g 2017-10-12 14:32:12 -> 2017101214')

    count = models.IntegerField(default=0)
    person = models.ForeignKey(SocialUser, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    rid = models.CharField(max_length=100, blank=True, null=True,
                           help_text='remote id of comment/repost status for this activity')

    # reposts_count = models.IntegerField(null=True, blank=True)
    # likes_count = models.IntegerField(null=True, blank=True)
    # replies_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return 'id:%s, %s %s (hr:%s), rid:%s, cnt:%s, person:%s, %s' % (self.id, self.date, self.time, self.hour,
                                                                        self.rid, self.count, self.person, self.text)

    def handle_datetime(self):
        self.datetime = timezone.now()
        self.tag = self.datetime.strftime('%H %Y-%m-%d %z')
        self.hour = int(self.datetime.strftime('%Y%m%d%H'))

# class RePostActivity(Activity):
#     count = models.IntegerField()
#
#
# class LikeActivity(Activity):
#     count = models.IntegerField()
#
#
# class CommentActivity(Activity):
#     count = models.IntegerField()
#
#
# class ActivityPerson(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     activity = models.ForeignKey(Activity)
#     person = models.ForeignKey(SocialUser)
#     text = models.TextField(null=True, blank=True)
#
# ActivityClasses = {
#     'likes': LikeActivity,
#     'comments': CommentActivity,
#     'reposts': RePostActivity
# }
