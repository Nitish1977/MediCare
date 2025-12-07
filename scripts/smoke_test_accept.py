import os
from django import setup
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_management.settings')
setup()

from django.contrib.auth.models import User
from django.test import Client
from appointments.models import Appointment, Notification

print('Starting accept-slot smoke test...')

# Assume doctor1 exists
doctor_username = 'doctor1'
try:
    du = User.objects.get(username=doctor_username)
except User.DoesNotExist:
    print('Doctor user not found')
    raise SystemExit(1)

# Find a pending appointment for this doctor
appt = Appointment.objects.filter(doctor=du.doctor, status='PENDING').order_by('created_at').first()
if not appt:
    print('No pending appointment found for doctor')
    raise SystemExit(0)

print('Found pending appointment id', appt.id)

client = Client()
login_ok = client.login(username=doctor_username, password='doctorpass')
print('Doctor login:', login_ok)

resp = client.post(f'/appointments/{appt.id}/update-status/', {'status': 'CONFIRMED'})
print('Update status response:', resp.status_code)

# Refresh
appt.refresh_from_db()
print('Appointment status now:', appt.status)

# Check patient notifications
pat_user = appt.patient.user
notifs = Notification.objects.filter(user=pat_user).order_by('-created_at')
print('Patient notifications count:', notifs.count())
for n in notifs[:5]:
    print('-', n.verb, 'read=', n.is_read)

print('Done.')
