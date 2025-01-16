from django.urls import path
from . import views

urlpatterns = [
    path('cy-guidebook/', views.shop_view, name='cy_guidebook'),
]
