#!/usr/bin/env python
# coding: utf-8

from django.contrib import admin
from .media import Media, SocialUser

@admin.register(SocialUser)
class SocialUserAdmin(admin.ModelAdmin):
    """
    Admin page for Author.
    """
    list_display = ('pk', 'picture', 'username', 'provider', 'fullname', 'website')
    list_filter = ('provider',)
    search_fields = ['username', 'fullname']
    # raw_id_fields = ('',)

