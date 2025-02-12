from django.utils.log import AdminEmailHandler
from datetime import datetime


class SimpleAdminEmailHandler(AdminEmailHandler):
    """
    A custom AdminEmailHandler that sends emails containing only the
    levelname and asctime, excluding the full error message and traceback.
    """

    def emit(self, record):
        """
        Overrides the default emit method to customize the email content.
        """
        # Format the asctime
        asctime = datetime.fromtimestamp(
            record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Create the email subject and message
        subject = f"BOULDERING CY - {record.levelname} at {asctime}"
        message = (f"{record.levelname}: Error detected at {asctime} "
                   "affecting the Bouldering Cy application\n\n"
                   "Check the Sentry log for full details on this error.")

        # Send the email
        self.send_mail(
            subject,
            message,
            fail_silently=True,
            html_message=None
        )
