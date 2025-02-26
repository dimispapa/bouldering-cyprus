from rest_framework import serializers
from .models import Crashpad, Booking, CrashpadGalleryImage


class CrashpadGalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrashpadGalleryImage
        fields = ['image']


class CrashpadSerializer(serializers.ModelSerializer):
    availability_status = serializers.SerializerMethodField()
    gallery_images = CrashpadGalleryImageSerializer(many=True, read_only=True)

    class Meta:
        model = Crashpad
        fields = [
            'id', 'name', 'description', 'day_rate', 'seven_day_rate',
            'fourteen_day_rate', 'image', 'availability_status',
            'gallery_images'
        ]

    def get_availability_status(self, obj):
        check_in = self.context.get('check_in')
        check_out = self.context.get('check_out')

        if not (check_in and check_out):
            return 'unknown'

        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            crashpad=obj,
            status='confirmed',
            check_out__gt=check_in,
            check_in__lt=check_out).exists()

        return 'unavailable' if overlapping_bookings else 'available'


class BookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Booking
        fields = [
            'id', 'crashpad', 'user', 'check_in', 'check_out', 'status',
            'booking_number', 'first_name', 'last_name', 'email', 'phone',
            'address_line1', 'address_line2', 'town_or_city', 'postal_code',
            'country'
        ]
        read_only_fields = ['status', 'user']
