from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import sys

class Command(BaseCommand):
    help = 'Test SMTP email configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            nargs='?',
            default=settings.DEFAULT_FROM_EMAIL,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        recipient_email = options['email']

        self.stdout.write(self.style.WARNING('Testing SMTP Email Configuration...'))
        self.stdout.write(f'Sender: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Recipient: {recipient_email}')
        self.stdout.write(f'SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        self.stdout.write(f'TLS Enabled: {settings.EMAIL_USE_TLS}')
        
        try:
            send_mail(
                subject='CanineMate SMTP Test Email 🐾',
                message='This is a test email from CanineMate to verify SMTP configuration is working correctly.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message='''
                <html>
                    <body>
                        <h2>CanineMate SMTP Test 🐾</h2>
                        <p>Hello!</p>
                        <p>This is a test email from <strong>CanineMate</strong>.</p>
                        <p>If you received this email, your SMTP configuration is <strong style="color: green;">working correctly!</strong></p>
                        <hr>
                        <p><small>Email sent at: {}</small></p>
                    </body>
                </html>
                '''.format(__import__('django.utils.timezone', fromlist=['now']).now()),
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS('[SUCCESS] Test email sent successfully!')
            )
            self.stdout.write(self.style.SUCCESS(f'Check {recipient_email} for the test email.'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'[ERROR] Failed to send test email: {str(e)}')
            )
            sys.exit(1)
