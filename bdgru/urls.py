from django.conf.urls import url
from bdgru import views


def t(template):
    return 'dashboard/' + template

urlpatterns = [


    # The home page
    # url(r'^$', views.index, name='index'),

    url(r'^$', views.IndexView.as_view(template_name=t('index.html')), name='dash_home'),

    url(r'^campaign/$', views.CampaignView.as_view(template_name=t('campaign.html')),
        name=views.CampaignView.view_name),
    url(r'^campaign/(?P<id>[0-9]+)/$', views.CampaignView.as_view(template_name=t('campaign.html')),
        name=views.CampaignView.view_name),
    url(r'^campaign/(?P<id>[0-9]+)/(?P<action>(update|del|ready|start|done|renew|detail|track|add))/$', views.CampaignView.as_view(
        template_name=t('campaign.html')), name=views.CampaignView.view_name),
    url(r'^campaign/(?P<action>new)/$', views.CampaignView.as_view(template_name=t('campaign.html')),
        name=views.CampaignView.view_name),
    url(r'^campaign/(?P<id>[0-9]+)/(?P<action>(battle))/(?P<battle_id>[0-9]+)/$', views.CampaignView.as_view(
        template_name=t('campaign.html')), name=views.CampaignView.view_name),

    # Matches any html file - to be used for gentella
    # Avoid using your .html in your resources.
    # Or create a separate django app.
    url(r'^.*\.html', views.gentella_html, name='gentella'),
]