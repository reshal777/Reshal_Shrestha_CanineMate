import os
import django
from django.core.mail import send_mail
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CanineMate.settings')
django.setup()

def test_email():
    print(f"Attempting to send email from: {settings.EMAIL_HOST_USER}")
    try:
        send_mail(
            'Test Email - CanineMate',
            'This is a test email to verify SMTP settings.',
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER], # Sending it to yourself
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")

if __name__ == "__main__":
    test_email()
