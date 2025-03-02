from django.urls import path
from . import views

app_name = 'newsletter'

urlpatterns = [
    path('unsubscribe/<int:user_id>/',
         views.unsubscribe_view,
         name='unsubscribe'),
    path('manage/', views.manage_subscription, name='manage_subscription'),
]
