from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    location = settings.STATICFILES_LOCATION
    default_acl = "public-read"
    file_overwrite = True  # Ensures old files are replaced
    # custom_domain = settings.AWS_CLOUDFRONT_DOMAIN  # Use CloudFront


class MediaStorage(S3Boto3Storage):
    location = settings.MEDIAFILES_LOCATION
    default_acl = "public-read"
    file_overwrite = False  # Prevents overwriting existing media files
    # custom_domain = settings.AWS_CLOUDFRONT_DOMAIN  # Use CloudFront
