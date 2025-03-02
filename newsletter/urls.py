from django.urls import path
from . import views

app_name = 'newsletter'

urlpatterns = [
    path('subscribe/', views.subscribe_view, name='subscribe'),
    path('unsubscribe/<str:email>/',
         views.unsubscribe_view,
         name='unsubscribe'),
    path('ajax-subscribe/', views.ajax_subscribe, name='ajax_subscribe'),
    path('manage/', views.manage_subscription, name='manage_subscription'),
]
