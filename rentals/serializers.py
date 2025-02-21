from rest_framework import serializers
from .models import Crashpad, Booking


class CrashpadSerializer(serializers.ModelSerializer):
    availability_status = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Crashpad
        fields = [
            'id', 'model', 'brand', 'name', 'description', 'price_per_day',
            'capacity', 'image', 'image_url', 'availability_status'
        ]
        read_only_fields = ['availability_status', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

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
