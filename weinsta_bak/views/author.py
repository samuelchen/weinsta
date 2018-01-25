#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.decorators import method_decorator

from django.views.generic import TemplateView
from .base import BaseViewMixin
from ..models.media import SocialUser
import logging

log = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class AuthorView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        return super(AuthorView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super(AuthorView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AuthorView, self).get_context_data(**kwargs)

        req = self.request.GET
        filters = context['filters'] = {
            'artist': 'artist' in req,
            'publisher': 'publisher' in req,
            'user': 'user' in req,
            'query': req['query'] if 'query' in req else ''
        }

        terms = Q()
        if filters['user']:
            terms = Q(is_artist=False) & Q(is_publisher=False)
        if filters['artist']:
            terms = terms | Q(is_artist=True)
        if filters['publisher']:
            terms = terms | Q(is_publisher=True)

        authors = SocialUser.objects.filter(terms)
        if filters['query']:
            q = filters['query']
            authors = authors.filter(Q(username__icontains=q) | Q(fullname__icontains=q) | Q(bio__icontains=q))
        context['authors'] = authors
        return context

