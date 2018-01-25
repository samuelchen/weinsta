#!/usr/bin/env python
# coding: utf-8
from ..models import SocialProviders
from .twitter import TwitterClient
from .instagram import InstagramClient
from .weibo import WeiboClient


class SocialClientManager(object):

    __clients = {}

    @classmethod
    def get_client(cls, provider, user, request=None):

        user_clients = cls.__clients.get(user, {})
        client = user_clients.get(provider)
        if client:
            return client

        if provider == SocialProviders.TWITTER:
            ClientClass = TwitterClient
        elif provider == SocialProviders.INSTAGRAM:
            ClientClass = InstagramClient
        elif provider == SocialProviders.WEIBO:
            ClientClass = WeiboClient
        else:
            return None

        token = ClientClass.get_token(user=user, request=request)
        if not token:
            return None

        client = ClientClass(token=token)
        user_clients[provider] = client
        cls.__clients[user] = user_clients
        return client

    @classmethod
    def get_clients(cls, provider_ids, user, request=None):
        for provider in provider_ids:
            client = cls.get_client(provider, user=user, request=request)

        return cls.__clients.get(user, {})