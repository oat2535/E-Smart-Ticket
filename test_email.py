import os
import sys
import django

# Set up Django environment
sys.path.append(r'c:\E-Smart-Ticket-main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("Testing email configuration...")
print(f"Host: {settings.EMAIL_HOST}")
print(f"User: {settings.EMAIL_HOST_USER}")

try:
    send_mail(
        subject="Test Email from Django",
        message="This is a test email to verify SMTP configuration.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['oat_2535@outlook.co.th'],
        fail_silently=False,
    )
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email. Error:")
    print(e)
