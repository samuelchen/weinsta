#!/usr/bin/env python
# coding: utf-8

"""
customer tags for template
"""
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

from django.template import Library
from django.template.defaultfilters import stringfilter

from ..models import SocialUser

register = Library()
UserMode = get_user_model()


@stringfilter
@register.filter
def is_linked_to(social_user, user):
    assert isinstance(social_user, SocialUser)
    assert isinstance(user, UserMode)
    return len(SocialAccount.objects.filter(user=user, uid=social_user.rid)) > 0

@stringfilter
@register.filter
def is_linked_to(social_user, user):
    assert isinstance(social_user, SocialUser)
    assert isinstance(user, UserMode)
    return len(SocialAccount.objects.filter(user=user, uid=social_user.rid)) > 0