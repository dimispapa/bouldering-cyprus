from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'crashpads', views.CrashpadViewSet, basename='crashpad')
router.register(r'bookings', views.BookingViewSet, basename='booking')

app_name = 'rentals'

urlpatterns = [
    path('book/', views.BookingView.as_view(), name='booking'),
    path('api/', include(router.urls)),
]
