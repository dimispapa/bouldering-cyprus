from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.dateparse import parse_date
from .models import Crashpad, CrashpadBooking
from .serializers import CrashpadSerializer, BookingSerializer
from django.views.generic import TemplateView
from datetime import datetime


class CrashpadViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for listing and retrieving crashpads.
    """
    queryset = Crashpad.objects.all()
    serializer_class = CrashpadSerializer
    permission_classes = [AllowAny]  # Allow public access to crashpad data

    def get_serializer_context(self):
        """
        Add check-in/out dates to context if provided
        """
        context = super().get_serializer_context()
        # Add check-in/out dates to context if provided
        check_in = self.request.query_params.get('check_in')
        check_out = self.request.query_params.get('check_out')
        if check_in and check_out:
            context.update({
                'check_in': parse_date(check_in),
                'check_out': parse_date(check_out)
            })
        return context

    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Get available crashpads for given dates.
        Query params:
        - check_in: YYYY-MM-DD
        - check_out: YYYY-MM-DD
        """
        check_in = request.query_params.get('check_in')
        check_out = request.query_params.get('check_out')

        # Check if both check-in and check-out dates are provided
        if not (check_in and check_out):
            return Response(
                {'error': 'Both check_in and check_out dates are required'},
                status=status.HTTP_400_BAD_REQUEST)

        # Parse and validate dates
        try:
            check_in_date = parse_date(check_in)
            check_out_date = parse_date(check_out)
            now = datetime.now().date()

            if check_in_date >= check_out_date:
                return Response(
                    {'error': 'Check-out date must be after check-in date'},
                    status=status.HTTP_400_BAD_REQUEST)

            if check_in_date < now:
                return Response(
                    {
                        'error':
                        'Check-in date cannot be in the past. '
                        f'Please select a date from {now} onwards.'
                    },
                    status=status.HTTP_400_BAD_REQUEST)

            # Get booked crashpad IDs for the date range
            booked_crashpad_ids = CrashpadBooking.objects.filter(
                status='confirmed',
                check_out__gt=check_in_date,
                check_in__lt=check_out_date).values_list('crashpad_id',
                                                         flat=True)

            # Get available crashpads by excluding booked crashpad IDs
            available_crashpads = self.get_queryset().exclude(
                id__in=booked_crashpad_ids)

            # Serialize available crashpads
            serializer = self.get_serializer(available_crashpads,
                                             many=True,
                                             context={
                                                 'check_in': check_in_date,
                                                 'check_out': check_out_date
                                             })

            return Response(serializer.data)

        except ValueError as e:
            return Response(
                {
                    'error':
                    f"Error getting available crashpads: {type(e).__name__}"
                },
                status=status.HTTP_400_BAD_REQUEST)


class BookingViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing bookings.
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Users can only see their own bookings
        """
        return CrashpadBooking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically set the user when creating a booking
        """
        serializer.save(user=self.request.user)


class BookingView(TemplateView):
    """
    View for displaying the crashpad booking interface.
    """
    template_name = 'rentals/booking.html'
