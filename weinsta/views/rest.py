#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.generic import View
import logging
from ..models import Media, SocialProviders, MyMedia, Activity
from django.conf import settings

log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class MediasJsonView(View):

    def get(self, request, *args, **kwargs):
        rc = []
        if settings.DEBUG:
            medias = MyMedia.objects.filter()
        else:
            medias = MyMedia.objects.filter(user=request.user)
        for mm in medias:
            m = mm.media
            rc.append(
                {
                    'id': m.id,
                    # 'rid': m.rid,
                    # 'rlink': m.rlink,
                    'url': m.get_thumb_url(),
                    'type': m.type,
                    'text': m.text or '',
                    'provider': {
                        'code': m.provider,
                        'icon': SocialProviders.get_icon(m.provider)
                    },
                    'owner': {
                        'id': m.owner.id,
                        'name': m.owner.get_name()
                    }
                }
            )
        return JsonResponse(rc, safe=False)




# @method_decorator(login_required, name='dispatch')
# class BattleActivityChartJsonView(View):
#
#     def get(self, request, *args, **kwargs):
#         rc = []
#         battle_id = 8
#         activities = Activity.objects.filter(battle_id=battle_id).order_by('-date', '-time')
#         for act in activities:
#             rc.append(
#                 {
#                     'type': act.type,
#                     'dates': '',
#                     'data': ''
#                 }
#             )
#         return JsonResponse(rc, safe=False)
