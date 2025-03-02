from django.urls import path
from . import views
from .views import CustomSignupView
app_name = 'accounts'

urlpatterns = [
    path('delete-account/', views.delete_account, name='delete_account'),
    path('signup/', CustomSignupView.as_view(), name='account_signup'),
]
