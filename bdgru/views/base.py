#!/usr/bin/env python
# coding: utf-8
from django.template import loader
from django.http import HttpResponse
from django.views.generic.base import ContextMixin
from django.utils.translation import gettext as _


def index(request):
    context = {}
    template = loader.get_template('app/index.html')
    return HttpResponse(template.render(context, request))


def gentella_html(request):
    context = {}
    # The template to be loaded as per gentelella.
    # All resource paths for gentelella end in .html.

    # Pick out the html file name from the url. And load that template.
    load_template = request.path.split('/')[-1]
    template = loader.get_template('app/' + load_template)
    return HttpResponse(template.render(context, request))


class BaseViewMixin(ContextMixin):

    def get_context_data(self, **kwargs):
        context = super(BaseViewMixin, self).get_context_data(**kwargs)

        context['website'] = {
            "domain": "bdgru.com",
            "name": _("BDGRU"),
            "fullname": _('Business Development GuRU')
        }

        return context
