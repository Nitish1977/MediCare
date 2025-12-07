from django import setup
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','hospital_management.settings')
setup()
from doctors.models import Doctor, Schedule
from appointments.models import Appointment
from datetime import date, timedelta

d = Doctor.objects.get(user__username='doctor1')
print('Doctor:', d)
print('Schedules:')
for s in Schedule.objects.filter(doctor=d):
    print(' -', s.day, s.start_time, s.end_time)

print('Upcoming appointments:')
for a in Appointment.objects.filter(doctor=d).order_by('appointment_date','appointment_time')[:20]:
    print(' -', a.appointment_date, a.appointment_time, a.status, a.patient)

# Print schedules for tomorrow
tomorrow = date.today() + timedelta(days=1)
weekday = tomorrow.strftime('%A')
print('Tomorrow:', tomorrow, weekday)
for s in Schedule.objects.filter(doctor=d, day=weekday):
    print('Tomorrow schedule:', s.start_time, s.end_time)
