from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from pets.models import Reminder
from home.email_utils import send_medicine_reminder_email
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send medicine reminder emails based on frequency and timing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = timezone.now().date()
        now = timezone.now().time()

        # Get active reminders
        active_reminders = Reminder.objects.filter(is_active=True)

        sent_count = 0
        for reminder in active_reminders:
            should_send = self.should_send_reminder(reminder, today, now)
            
            if should_send:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY RUN] Would send reminder: {reminder.name} for {reminder.dog.name}"
                        )
                    )
                else:
                    try:
                        send_medicine_reminder_email(reminder)
                        sent_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Sent reminder: {reminder.name} for {reminder.dog.name}"
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Failed to send reminder for {reminder.name}: {str(e)}"
                            )
                        )
                        logger.error(f"Failed to send reminder: {str(e)}")

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully sent {sent_count} medicine reminder emails"
                )
            )

    def should_send_reminder(self, reminder, today, now):
        """Determine if reminder should be sent based on frequency and timing"""
        
        # Check if start date has passed
        if reminder.start_date > today:
            return False

        # Check if reminder time matches current time (within 1-hour window)
        hour_diff = abs((now.hour - reminder.reminder_time.hour) * 60 + 
                       (now.minute - reminder.reminder_time.minute))
        if hour_diff > 60:  # Outside 1-hour window
            return False

        # Check frequency
        days_since_start = (today - reminder.start_date).days

        if reminder.frequency == 'Daily':
            return True
        elif reminder.frequency == 'Weekly':
            return days_since_start % 7 == 0
        elif reminder.frequency == 'Monthly':
            return days_since_start % 30 == 0
        elif reminder.frequency == 'Yearly':
            return days_since_start % 365 == 0

        return False
