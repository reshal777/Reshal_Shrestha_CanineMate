from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def get_base_url():
    """Get base URL for email links from settings or fallback to localhost."""
    return settings.BASE_URL or 'http://127.0.0.1:8000'

def send_order_email(order):
    """Send order confirmation email to the user."""
    try:
        subject = f'Order Confirmation - {order.order_id} | CanineMate 🐾'
        context = {
            'order': order,
            'user': order.user,
            'items': order.items.all(),
            'base_url': get_base_url()
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
            'user': appointment.user,
            'base_url': get_base_url()
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
            'service_name': service_name,
            'base_url': get_base_url()
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

def send_medicine_reminder_email(reminder):
    """Send medicine reminder email to the user."""
    try:
        subject = f'Medicine Reminder: {reminder.name} for {reminder.dog.name} | CanineMate 🐾'
        context = {
            'reminder': reminder,
            'user': reminder.dog.owner,
            'dog': reminder.dog,
            'base_url': get_base_url()
        }
        html_message = render_to_string('emails/medicine_reminder.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [reminder.dog.owner.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send medicine reminder email for {reminder.name}: {str(e)}")


def send_appointment_cancellation_email(appointment):
    """Send appointment cancellation email to the user."""
    try:
        subject = f'Appointment Cancelled: {appointment.service_type} | CanineMate 🐾'
        context = {
            'appointment': appointment,
            'user': appointment.user
        }
        html_message = f'''
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Appointment Cancelled</h2>
                <p>Hi {appointment.user.username},</p>
                <p>Your appointment scheduled for <strong>{appointment.appointment_date} at {appointment.appointment_time}</strong> has been cancelled.</p>
                <p><strong>Service Type:</strong> {appointment.service_type}</p>
                <p><strong>Veterinarian:</strong> {appointment.veterinarian.name}</p>
                <p>If you would like to reschedule or have any questions, please contact us.</p>
                <p>Best regards,<br>CanineMate Team</p>
            </body>
        </html>
        '''
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
        logger.error(f"Failed to send appointment cancellation email for APPT-{appointment.id}: {str(e)}")


def send_grooming_cancellation_email(booking):
    """Send grooming cancellation email to the user."""
    try:
        service_name = booking.service.name if booking.service else "Grooming Service"
        subject = f'Grooming Booking Cancelled: {service_name} | CanineMate 🐾'
        context = {
            'booking': booking,
            'user': booking.user,
            'service_name': service_name
        }
        html_message = f'''
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Grooming Booking Cancelled</h2>
                <p>Hi {booking.user.username},</p>
                <p>Your grooming booking for <strong>{booking.booking_date} at {booking.booking_time}</strong> has been cancelled.</p>
                <p><strong>Service:</strong> {service_name}</p>
                <p><strong>Dog:</strong> {booking.dog.name}</p>
                <p>If you would like to reschedule or have any questions, please contact us.</p>
                <p>Best regards,<br>CanineMate Team</p>
            </body>
        </html>
        '''
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
        logger.error(f"Failed to send grooming cancellation email for GRM-{booking.id}: {str(e)}")


def send_appointment_reminder_email(appointment):
    """Send appointment reminder email (day before appointment)."""
    try:
        subject = f'Reminder: Your Appointment Tomorrow | CanineMate 🐾'
        context = {
            'appointment': appointment,
            'user': appointment.user
        }
        html_message = f'''
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Appointment Reminder 🐾</h2>
                <p>Hi {appointment.user.username},</p>
                <p>This is a reminder that you have an appointment scheduled for tomorrow!</p>
                <p><strong>Date:</strong> {appointment.appointment_date}</p>
                <p><strong>Time:</strong> {appointment.appointment_time}</p>
                <p><strong>Service Type:</strong> {appointment.service_type}</p>
                <p><strong>Veterinarian:</strong> {appointment.veterinarian.name}</p>
                <p><strong>Fee:</strong> NPR {appointment.amount}</p>
                <p>Please arrive 10 minutes early. If you need to cancel or reschedule, please contact us as soon as possible.</p>
                <p>Best regards,<br>CanineMate Team</p>
            </body>
        </html>
        '''
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
        logger.error(f"Failed to send appointment reminder email for APPT-{appointment.id}: {str(e)}")


def send_grooming_reminder_email(booking):
    """Send grooming booking reminder email (day before booking)."""
    try:
        service_name = booking.service.name if booking.service else "Grooming Service"
        subject = f'Reminder: Your Grooming Session Tomorrow | CanineMate 🐾'
        context = {
            'booking': booking,
            'user': booking.user,
            'service_name': service_name
        }
        html_message = f'''
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Grooming Session Reminder 🐾</h2>
                <p>Hi {booking.user.username},</p>
                <p>This is a reminder that you have a grooming session scheduled for tomorrow!</p>
                <p><strong>Date:</strong> {booking.booking_date}</p>
                <p><strong>Time:</strong> {booking.booking_time}</p>
                <p><strong>Service:</strong> {service_name}</p>
                <p><strong>Dog:</strong> {booking.dog.name}</p>
                <p><strong>Salon:</strong> {booking.salon.name if booking.salon else 'CanineMate Salon'}</p>
                <p><strong>Fee:</strong> NPR {booking.amount}</p>
                <p>Please bring your dog well-groomed and ready. If you need to cancel or reschedule, please contact us as soon as possible.</p>
                <p>Best regards,<br>CanineMate Team</p>
            </body>
        </html>
        '''
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
        logger.error(f"Failed to send grooming reminder email for GRM-{booking.id}: {str(e)}")

def send_adoption_approval_email_to_poster(adoption_request):
    """Send an email to the original poster when their dog's adoption request is approved."""
    try:
        dog = adoption_request.dog
        poster = dog.owner  # The user who posted the dog
        adopter = adoption_request.user  # The user who is adopting the dog
        
        subject = f'Your Dog {dog.name} has been Adopted! | CanineMate 🐾'
        
        html_message = f'''
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #4FBDBA 0%, #3da5a2 100%); padding: 30px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 24px;">Adoption Approved! 🐾</h1>
                </div>
                <div style="padding: 30px; background: #ffffff;">
                    <h2 style="color: #333; margin-top: 0;">Hi {poster.username},</h2>
                    <p>Exciting news! The adoption request for <strong>{dog.name}</strong> has been <strong>approved</strong> by the CanineMate admin.</p>
                    
                    <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4FBDBA;">
                        <p style="margin: 0; font-weight: bold; color: #475569;">Adoption Details:</p>
                        <p style="margin: 10px 0 0 0;"><strong>Dog:</strong> {dog.name} ({dog.breed})</p>
                        <p style="margin: 5px 0 0 0;"><strong>Adopter:</strong> {adopter.get_full_name() or adopter.username}</p>
                        <p style="margin: 5px 0 0 0;"><strong>Adopter Email:</strong> {adopter.email}</p>
                    </div>
                    
                    <p>The adopter will be in touch with you shortly to coordinate the next steps. Thank you for using CanineMate to find a loving home for {dog.name}!</p>
                    
                    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 25px 0;">
                    
                    <p style="font-size: 0.9em; color: #64748b;">Warm regards,<br><strong>The CanineMate Team</strong></p>
                </div>
                <div style="background: #f1f5f9; padding: 15px; text-align: center; font-size: 0.8em; color: #94a3b8;">
                    &copy; {timezone.now().year} CanineMate. All rights reserved.
                </div>
            </body>
        </html>
        '''
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [poster.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Adoption approval email sent to poster {poster.email} for dog {dog.name}")
    except Exception as e:
        logger.error(f"Failed to send adoption approval email to poster: {str(e)}")
