import os
from django import setup
from datetime import date, timedelta, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_management.settings')
setup()

from django.contrib.auth.models import User, Group
from django.test import Client
from doctors.models import Doctor, Schedule
from patients.models import Patient
from appointments.models import Appointment, Notification

print('Starting request-slot smoke test...')

# Ensure users exist
doctor_username = 'doctor1'
patient_username = 'patient1'

du = User.objects.get(username=doctor_username)
pu = User.objects.get(username=patient_username)

doctor = du.doctor
patient = pu.patient

# Ensure schedule exists for tomorrow
tomorrow = date.today() + timedelta(days=1)
weekday = tomorrow.strftime('%A')
if not Schedule.objects.filter(doctor=doctor, day=weekday).exists():
    Schedule.objects.create(doctor=doctor, day=weekday, start_time=time(9,0), end_time=time(10,0))
    print('Added schedule for doctor on', weekday)

# Use client to login as patient and post to request-slot
client = Client()
login_ok = client.login(username=patient_username, password='patientpass')
print('Patient login:', login_ok)

resp = client.post('/patients/request-slot/', {'doctor_id': str(doctor.id), 'date': tomorrow.isoformat(), 'time': '09:00'})
print('Request-slot response status:', resp.status_code)
try:
    print('Response content:', resp.json())
except Exception:
    print('No JSON response')

# Check appointment
exists = Appointment.objects.filter(doctor=doctor, patient=patient, appointment_date=tomorrow, appointment_time='09:00').exists()
print('Appointment exists:', exists)

# Check notifications for doctor
notifs = Notification.objects.filter(user=du).order_by('-created_at')
print('Doctor notifications count:', notifs.count())
for n in notifs[:5]:
    print('-', n.verb, 'read=', n.is_read)

print('Done.')
