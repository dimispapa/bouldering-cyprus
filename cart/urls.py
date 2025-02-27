from django.urls import path
from . import views

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("add/<str:item_type>/", views.cart_add, name="cart_add"),
    path("remove/<str:item_type>/<int:item_id>/",
         views.cart_remove,
         name="cart_remove"),
    path("update/", views.cart_update, name="cart_update"),
]
