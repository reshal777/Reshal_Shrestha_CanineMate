from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def send_order_email(order):
    """Send order confirmation email to the user."""
    try:
        subject = f'Order Confirmation - {order.order_id} | CanineMate 🐾'
        context = {
            'order': order,
            'user': order.user,
            'items': order.items.all()
        }
        html_message = render_to_string('emails/order_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send order email for {order.order_id}: {str(e)}")

def send_appointment_email(appointment):
    """Send vet appointment confirmation email to the user."""
    try:
        subject = f'Appointment Confirmed: {appointment.service_type} | CanineMate 🐾'
        context = {
            'appointment': appointment,
            'user': appointment.user
        }
        html_message = render_to_string('emails/appointment_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send appointment email for APPT-{appointment.id}: {str(e)}")

def send_grooming_email(booking):
    """Send grooming booking confirmation email to the user."""
    try:
        service_name = booking.service.name if booking.service else "Grooming Service"
        subject = f'Grooming Booking Scheduled: {service_name} | CanineMate 🐾'
        context = {
            'booking': booking,
            'user': booking.user,
            'service_name': service_name
        }
        html_message = render_to_string('emails/grooming_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send grooming email for GRM-{booking.id}: {str(e)}")
