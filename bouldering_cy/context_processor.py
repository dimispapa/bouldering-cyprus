from django.conf import settings


def sentry_settings(request):
    return {
        'SENTRY_ENABLED': settings.SENTRY_ENABLED,
    }
