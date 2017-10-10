#!/usr/bin/env python
# coding: utf-8

"""
customer tags for template
"""
import datetime

from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

import re

register = Library()


@stringfilter
@register.filter(needs_autoescape=True)
def spacify(value, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(re.sub('\s', '&' + 'nbsp;', esc(value)))


@stringfilter
@register.filter
def _2space(value):
    """
    Convert underscores to spaces for a string.
    :param value:
    :return:
    """
    return value.replace('_', ' ')


@stringfilter
@register.filter
def space2_(value):
    """
    Convert spaces to underscores for a string.
    :param value:
    :return:
    """
    return value.replace(' ', '_')


@register.simple_tag
def key_from_var(obj, *args):
    """
    Obtain values from dict/object with given key variables in template.
    e.g.
    If you want to render user.name.first_name in Django template,
    Use {% key_from_var user name first_name %}
    :param obj:
    :param args:
    :return:
    """
    val = obj
    for key in args:
        if key in val:
            val = val[key]
        elif hasattr(val, key):
            val = getattr(val, key)
        else:
            return ''
    return val

@register.simple_tag
def call_with_args(obj, *args, **kwargs):
    assert callable(obj)
    return obj(*args, **kwargs)

@register.filter
def call_with_func_and_args(obj, method, *args, **kwargs):
    assert hasattr(obj, method)
    func = getattr(obj, method)
    assert callable(func)
    return func(*args, **kwargs)


@register.filter
@stringfilter
def trim(value):
    return value.strip()

# @register.simple_tag
# def setting(name):
#     """
#     get setting value
#     :param name:
#     :return:
#     """
#     return getattr(settings, name, "")

# re_isurl = re.compile(r"(?isu)(http[s]\://[a-zA-Z0-9\.\?/&\=\:]+)")
re_isurl = re.compile(r"(?isu)(http[s]\://[a-zA-Z0-9\.\?/&\=\:\-_]+)")
@register.filter
@stringfilter
def url2link(value):
    """
    Replace URLs in value to LINKs.
    e.g.
    value = "Please go to http://www.google.com to search."
    retuns: "Please go to <a href="http://www.google.com">http://www.google.com</a> to search."
    :param value:
    :return:
    """
    return re_isurl.sub(lambda m: '<a href="%s">%s</a>' % (m.group(0), m.group(0)), value)


re_ishash = re.compile(r'(?:\A|\s)(?P<hash>#(?:\w|\.|_)+)(?:\s|\Z)', re.IGNORECASE + re.MULTILINE)
@register.filter
@stringfilter
def hash2link(value):
    """
    Replace URLs in value to LINKs.
    e.g.
    value = "Buy a pen tomorrow #todo."
    retuns: "Buy a pen tomorrow <a href="#">#todo</a>."
    :param value:
    :return:
    """
    return re_ishash.sub(lambda m: '<a href="/hash/%s">%s</a>' % (m.group(0), m.group(0)), value)

@register.filter
def utc(value):
    if not value:
        return value
    assert isinstance(value, datetime.datetime) or isinstance(value, datetime.date) or isinstance(value, datetime.time)
    return value.isoformat()
