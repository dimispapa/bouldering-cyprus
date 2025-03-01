from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('delete-account/', views.delete_account, name='delete_account'),
]
