import os
from django import setup
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_management.settings')
setup()

from django.contrib.auth.models import User, Group
from django.test import Client
from doctors.models import Doctor, Schedule
from patients.models import Patient
from appointments.models import Appointment

print('Starting smoke test...')

# create groups
doctors_group, _ = Group.objects.get_or_create(name='Doctors')
patients_group, _ = Group.objects.get_or_create(name='Patients')

# create doctor user
doctor_username = 'doctor1'
doctor_password = 'doctorpass'
if not User.objects.filter(username=doctor_username).exists():
    du = User.objects.create_user(username=doctor_username, password=doctor_password, first_name='Doc', last_name='One', email='doc1@example.com')
    dr = Doctor.objects.create(user=du, specialization='Cardiology', phone_number='1234567890', address='Clinic Address')
    du.groups.add(doctors_group)
    print('Created doctor user and profile:', doctor_username)
else:
    du = User.objects.get(username=doctor_username)
    dr = du.doctor
    print('Doctor exists:', doctor_username)

# create patient user
patient_username = 'patient1'
patient_password = 'patientpass'
if not User.objects.filter(username=patient_username).exists():
    pu = User.objects.create_user(username=patient_username, password=patient_password, first_name='Pat', last_name='One', email='pat1@example.com')
    pt = Patient.objects.create(user=pu, phone_number='0987654321', address='Home Address')
    pu.groups.add(patients_group)
    print('Created patient user and profile:', patient_username)
else:
    pu = User.objects.get(username=patient_username)
    pt = pu.patient
    print('Patient exists:', patient_username)

# add a schedule for tomorrow's weekday if not present
tomorrow = date.today() + timedelta(days=1)
weekday = tomorrow.strftime('%A')
if not Schedule.objects.filter(doctor=dr, day=weekday).exists():
    Schedule.objects.create(doctor=dr, day=weekday, start_time='09:00', end_time='12:00')
    print('Created schedule for', dr, 'on', weekday)
else:
    print('Schedule already exists for', dr, 'on', weekday)

# Use test client to simulate patient booking flow
client = Client()
login_ok = client.login(username=patient_username, password=patient_password)
print('Patient login:', login_ok)

# Step 1: find slots
find_resp = client.post('/patients/book-appointment/', {'action': 'find_slots', 'doctor': dr.id, 'appointment_date': tomorrow.isoformat()})
slots = None
try:
    slots = find_resp.context.get('slots')
except Exception:
    pass
print('Find slots response status:', find_resp.status_code, 'slots found:', bool(slots))
if slots:
    selected_time = slots[0]
    # Step 2: book slot
    book_resp = client.post('/patients/book-appointment/', {
        'action': 'book_slot',
        'doctor': str(dr.id),
        'appointment_date': tomorrow.isoformat(),
        'appointment_time': selected_time,
        'reason': 'Routine checkup'
    })
    print('Book slot response status:', book_resp.status_code)
    # Check appointment exists
    exists = Appointment.objects.filter(doctor=dr, patient=pt, appointment_date=tomorrow, appointment_time=selected_time).exists()
    print('Appointment created:', exists)
else:
    print('No slots available to book')

# Test doctor access to schedule page
client.logout()
login_ok = client.login(username=doctor_username, password=doctor_password)
print('Doctor login:', login_ok)
doc_resp = client.get('/doctors/schedule/')
print('Doctor schedule page status:', doc_resp.status_code)

# Test logout
logout_resp = client.post('/logout/')
print('Logout response status:', logout_resp.status_code)

print('Smoke test finished.')
