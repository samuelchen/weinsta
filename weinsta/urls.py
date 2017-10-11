"""weinsta URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from weinsta import views


def t(template):
    return 'weinsta/' + template

# ^accounts/ ^ ^signup/$ [name='account_signup']
# ^accounts/ ^ ^login/$ [name='account_login']
# ^accounts/ ^ ^logout/$ [name='account_logout']
# ^accounts/ ^ ^password/change/$ [name='account_change_password']
# ^accounts/ ^ ^password/set/$ [name='account_set_password']
# ^accounts/ ^ ^inactive/$ [name='account_inactive']
# ^accounts/ ^ ^email/$ [name='account_email']
# ^accounts/ ^ ^confirm-email/$ [name='account_email_verification_sent']
# ^accounts/ ^ ^confirm-email/(?P<key>[-:\w]+)/$ [name='account_confirm_email']
# ^accounts/ ^ ^password/reset/$ [name='account_reset_password']
# ^accounts/ ^ ^password/reset/done/$ [name='account_reset_password_done']
# ^accounts/ ^ ^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$ [name='account_reset_password_from_key']
# ^accounts/ ^ ^password/reset/key/done/$ [name='account_reset_password_from_key_done']
# ^accounts/ ^social/ ^login/cancelled/$ [name='socialaccount_login_cancelled']
# ^accounts/ ^social/ ^login/error/$ [name='socialaccount_login_error']
# ^accounts/ ^social/ ^signup/$ [name='socialaccount_signup']
# ^accounts/ ^social/ ^connections/$ [name='socialaccount_connections']

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('allauth.urls')),

    url(r'^$', views.IndexView.as_view(template_name=t('index.html')), name='index'),
    url(r'^media/$', views.MediaView.as_view(template_name=t('media.html')), name='media'),
    url(r'^author/$', views.AuthorView.as_view(template_name=t('author.html')), name='author'),
    url(r'^insta/$', views.InstaView.as_view(template_name=t('insta.html')), name='insta'),
    url(r'^insta/loc/$', views.InstaLocView.as_view(), name='insta_loc'),
    url(r'^weibo/$', views. WeiboView.as_view(template_name=t('weibo.html')), name='weibo'),
    url(r'^twitter/$', views. TwitterView.as_view(template_name=t('twitter.html')), name='twitter'),
    url(r'^pub/(?P<media_id>[0-9]+)/$', views.PubView.as_view(template_name=t('pub.html')), name='pub'),

    # campaign views
    url(r'^campaign/$', views.CampaignView.as_view(template_name=t('campaign.html')),
        name=views.CampaignView.view_name),
    url(r'^campaign/(?P<id>[0-9]+)/$', views.CampaignView.as_view(template_name=t('campaign.html')),
        name=views.CampaignView.view_name),
    url(r'^campaign/(?P<id>[0-9]+)/(?P<action>(update|del))/$', views.CampaignView.as_view(
        template_name=t('campaign.html')), name=views.CampaignView.view_name),
    url(r'^campaign/(?P<action>new)/$', views.CampaignView.as_view(template_name=t('campaign.html')),
        name=views.CampaignView.view_name),

    # RESTFul RPC views
    url(r'^api/medias/$', views.rest.MediasJsonView.as_view(), name='rest_medias'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
