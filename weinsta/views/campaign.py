#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views.generic import TemplateView
from .base import BaseViewMixin
import logging
from ..clients import InstagramClient
from ..models import Campaign, SocialProviders, Media, MediaType

log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class CampaignView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(CampaignView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super(CampaignView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CampaignView, self).get_context_data(**kwargs)

        req = self.request.POST

        sel_medias = []
        if 'sel_media' in req:
            sel_medias = req.getlist('sel_media')
        sel_medias = list(map(lambda x: int(x), sel_medias))
        print(sel_medias)
        if not sel_medias:
            sel_medias = [25, 26, 27]

        sel_providers = []
        if 'sel_provider' in req:
            sel_providers = req.getlist('sel_provider')
        # sel_providers = list(map(lambda x: int(x), sel_providers))

        context['sel_providers'] = sel_providers
        context['sel_medias'] = sel_medias

        context['providers'] = SocialProviders
        context['mediatypes'] = MediaType

        context['medias'] = Media.objects.filter(id__in=sel_medias).all()

        context['campaigns'] = Campaign.objects.all()
        return context
