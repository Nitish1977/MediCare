from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.test import Client
from datetime import date, timedelta

from doctors.models import Doctor, Schedule
from patients.models import Patient
from appointments.models import Appointment


class Command(BaseCommand):
    help = 'Smoke test: create test users, schedule, book appointment, check pages and logout'

    def handle(self, *args, **options):
        out = self.stdout
        out.write('Starting smoke test...')

        doctors_group, _ = Group.objects.get_or_create(name='Doctors')
        patients_group, _ = Group.objects.get_or_create(name='Patients')

        # create doctor
        doctor_username = 'doctor1'
        doctor_password = 'doctorpass'
        if not User.objects.filter(username=doctor_username).exists():
            du = User.objects.create_user(username=doctor_username, password=doctor_password, first_name='Doc', last_name='One', email='doc1@example.com')
            dr = Doctor.objects.create(user=du, specialization='Cardiology', phone_number='1234567890', address='Clinic Address')
            du.groups.add(doctors_group)
            out.write(f'Created doctor user: {doctor_username}')
        else:
            du = User.objects.get(username=doctor_username)
            try:
                dr = du.doctor
            except Doctor.DoesNotExist:
                dr = Doctor.objects.create(user=du, specialization='Cardiology', phone_number='1234567890', address='Clinic Address')
            out.write(f'Doctor exists: {doctor_username}')

        # create patient
        patient_username = 'patient1'
        patient_password = 'patientpass'
        if not User.objects.filter(username=patient_username).exists():
            pu = User.objects.create_user(username=patient_username, password=patient_password, first_name='Pat', last_name='One', email='pat1@example.com')
            # Provide required patient fields
            pt = Patient.objects.create(
                user=pu,
                date_of_birth=(date.today() - timedelta(days=365*30)),
                blood_group='O+',
                phone_number='0987654321',
                address='Home Address',
                emergency_contact='1112223333'
            )
            pu.groups.add(patients_group)
            out.write(f'Created patient user: {patient_username}')
        else:
            pu = User.objects.get(username=patient_username)
            try:
                pt = pu.patient
            except Patient.DoesNotExist:
                pt = Patient.objects.create(
                    user=pu,
                    date_of_birth=(date.today() - timedelta(days=365*30)),
                    blood_group='O+',
                    phone_number='0987654321',
                    address='Home Address',
                    emergency_contact='1112223333'
                )
            out.write(f'Patient exists: {patient_username}')

        # add a schedule for tomorrow if missing
        tomorrow = date.today() + timedelta(days=1)
        weekday = tomorrow.strftime('%A')
        if not Schedule.objects.filter(doctor=dr, day=weekday).exists():
            Schedule.objects.create(doctor=dr, day=weekday, start_time='09:00', end_time='12:00')
            out.write(f'Created schedule for {dr} on {weekday}')
        else:
            out.write(f'Schedule already exists for {dr} on {weekday}')

        client = Client()
        login_ok = client.login(username=patient_username, password=patient_password)
        out.write(f'Patient login: {login_ok}')

        # Step 1: find slots
        find_resp = client.post('/patients/book-appointment/', {'action': 'find_slots', 'doctor': dr.id, 'appointment_date': tomorrow.isoformat()})
        out.write(f'Find slots response status: {find_resp.status_code}')
        slots = None
        try:
            slots = find_resp.context.get('slots')
        except Exception:
            slots = None
        out.write(f'Slots found: {bool(slots)}')

        # extra debug: list context keys and schedules/appointments for the doctor on that date
        try:
            ctx_keys = list(find_resp.context.keys())
            out.write(f'Find response context keys: {ctx_keys}')
        except Exception:
            out.write('No context available on response')

        # print schedule entries for that weekday
        out.write('Doctor schedules for that weekday:')
        for s in Schedule.objects.filter(doctor=dr, day=weekday):
            out.write(f' - {s.day} {s.start_time}-{s.end_time}')

        # print existing appointments for that date
        out.write('Existing appointments on that date:')
        for a in Appointment.objects.filter(doctor=dr, appointment_date=tomorrow):
            out.write(f' - {a.appointment_time} status={a.status} patient={a.patient}')
        # compute available slots locally (30-minute intervals)
        from datetime import datetime, timedelta
        slots_local = []
        slot_length = timedelta(minutes=30)
        for sched in Schedule.objects.filter(doctor=dr, day=weekday):
            start_dt = datetime.combine(tomorrow, sched.start_time)
            end_dt = datetime.combine(tomorrow, sched.end_time)
            current = start_dt
            while current + slot_length <= end_dt:
                t = current.time()
                conflict = Appointment.objects.filter(
                    doctor=dr,
                    appointment_date=tomorrow,
                    appointment_time=t,
                    status__in=['PENDING', 'CONFIRMED']
                ).exists()
                if not conflict:
                    slots_local.append(t.strftime('%H:%M'))
                current += slot_length
        out.write(f'Locally computed slots ({len(slots_local)}): {slots_local}')

        if slots:
            selected_time = slots[0]
            book_resp = client.post('/patients/book-appointment/', {
                'action': 'book_slot',
                'doctor': str(dr.id),
                'appointment_date': tomorrow.isoformat(),
                'appointment_time': selected_time,
                'reason': 'Routine checkup'
            })
            out.write(f'Book slot response status: {book_resp.status_code}')
            exists = Appointment.objects.filter(doctor=dr, patient=pt, appointment_date=tomorrow, appointment_time=selected_time).exists()
            out.write(f'Appointment created: {exists}')
        else:
            out.write('No slots available to book')

        # doctor pages
        client.logout()
        login_ok = client.login(username=doctor_username, password=doctor_password)
        out.write(f'Doctor login: {login_ok}')
        doc_resp = client.get('/doctors/schedule/')
        out.write(f'Doctor schedule page status: {doc_resp.status_code}')

        # test logout
        logout_resp = client.post('/logout/')
        out.write(f'Logout response status: {logout_resp.status_code}')

        out.write('Smoke test finished.')
