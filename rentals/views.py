from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.dateparse import parse_date
from .models import Crashpad, CrashpadBooking
from .serializers import CrashpadSerializer, BookingSerializer
from django.views.generic import TemplateView
from datetime import datetime
import logging
from django.contrib import messages

logger = logging.getLogger(__name__)


def validate_dates(check_in, check_out):
    """
    Validate the dates provided in the query parameters.
    """
    now = datetime.now().date()

    if check_in > check_out:
        return False, 'Check-in date cannot be after check-out date'

    if check_in < now:
        return False, f'Check-in date cannot be in the past. ' \
                      f'Please select a date from {now} onwards.'

    return True, None


class CrashpadViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for listing and retrieving crashpads.
    """
    queryset = Crashpad.objects.all().prefetch_related('gallery_images')
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
            if not (check_in_date and check_out_date):
                raise ValueError('Invalid date format')

            # Validate dates
            is_valid, error_message = validate_dates(check_in_date,
                                                     check_out_date)
            if not is_valid:
                return Response({'error': error_message},
                                status=status.HTTP_400_BAD_REQUEST)

            # Get booked crashpad IDs for the date range
            unavailable_crashpad_ids = \
                CrashpadBooking.get_unavailable_crashpads_ids(
                    check_in_date, check_out_date)

            # Get available crashpads by excluding booked crashpad IDs
            # Use prefetch_related to avoid N+1 queries for gallery images
            available_crashpads = self.get_queryset().exclude(
                id__in=unavailable_crashpad_ids)
            logger.info(f'Available crashpads: {available_crashpads}')

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
        return CrashpadBooking.objects.filter(
            user=self.request.user).select_related('crashpad', 'order')

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get check-in and check-out dates from URL parameters
        check_in = self.request.GET.get('check_in')
        check_out = self.request.GET.get('check_out')

        # If dates are provided, validate and add to context
        if check_in and check_out:
            try:
                check_in_date = parse_date(check_in)
                check_out_date = parse_date(check_out)

                if not (check_in_date and check_out_date):
                    raise ValueError('Invalid date format')

                # Validate dates
                is_valid, error_message = validate_dates(
                    check_in_date, check_out_date)
                if is_valid:
                    context['check_in'] = check_in
                    context['check_out'] = check_out

                    # Get available crashpads with prefetched gallery images
                    unavailable_crashpad_ids = \
                        CrashpadBooking.get_unavailable_crashpads_ids(
                            check_in_date, check_out_date)

                    # Prefetch related gallery images to avoid N+1 queries
                    available_crashpads = Crashpad.objects.exclude(
                        id__in=unavailable_crashpad_ids).prefetch_related(
                            'gallery_images')

                    context['available_crashpads'] = available_crashpads
                else:
                    messages.error(self.request, error_message)
                    logger.error(f'Invalid dates: {error_message}')
                    context['date_error'] = error_message

            except (ValueError, TypeError) as e:
                messages.error(self.request, 'Invalid date format')
                logger.error(f'Date parsing error: {e}')
                context['date_error'] = 'Invalid date format'

        else:
            # If no dates provided,
            # show all crashpads with prefetched gallery images
            context['all_crashpads'] = Crashpad.objects.all().prefetch_related(
                'gallery_images')

        return context
