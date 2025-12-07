from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from .models import Patient
from .forms import PatientRegistrationForm, PatientProfileForm
from appointments.models import Appointment
from appointments.forms import AppointmentForm
from appointments.models import Notification
from doctors.models import Doctor
from doctors.models import Schedule
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.template.defaultfilters import date as _date_filter

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Patient.objects.create(
                user=user,
                date_of_birth=form.cleaned_data['date_of_birth'],
                blood_group=form.cleaned_data['blood_group'],
                phone_number=form.cleaned_data['phone_number'],
                address=form.cleaned_data['address'],
                emergency_contact=form.cleaned_data['emergency_contact']
            )
            patients_group, _ = Group.objects.get_or_create(name='Patients')
            user.groups.add(patients_group)
            messages.success(request, 'Registration successful. Please login.')
            return redirect('login')
    else:
        form = PatientRegistrationForm()
    return render(request, 'patients/register.html', {'form': form})

@login_required
def dashboard(request):
    try:
        patient = request.user.patient
        appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date', '-appointment_time')
        context = {
            'patient': patient,
            'appointments': appointments
        }
        return render(request, 'patients/dashboard.html', context)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('login')

@login_required
def profile(request):
    try:
        patient = request.user.patient
        if request.method == 'POST':
            form = PatientProfileForm(request.POST, instance=patient)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('patients:profile')
        else:
            form = PatientProfileForm(instance=patient)
        return render(request, 'patients/profile.html', {'form': form})
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('login')

@login_required
def book_appointment(request):
    # This legacy view now redirects to the unified available slots page
    return redirect('patients:available_slots')

    try:
        patient = request.user.patient
        # Two-step booking flow:
        # Step 1: patient selects doctor and date -> show available slots
        # Step 2: patient selects a time slot and provides reason -> create appointment
        if request.method == 'POST':
            # Finalize booking
            if request.POST.get('action') == 'book_slot':
                doctor_id = request.POST.get('doctor')
                date_str = request.POST.get('appointment_date')
                time_str = request.POST.get('appointment_time')
                reason = request.POST.get('reason', '')
                try:
                    doctor = Doctor.objects.get(id=doctor_id)
                    appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    appointment_time = datetime.strptime(time_str, '%H:%M').time()
                except Exception as e:
                    messages.error(request, 'Invalid data provided. Please try again.')
                    return redirect('patients:book_appointment')

                # Check if slot is still available
                exists = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    status__in=['PENDING', 'CONFIRMED']
                ).exists()
                if exists:
                    messages.error(request, 'Selected time slot is no longer available. Please choose another.')
                    return redirect('patients:book_appointment')

                appointment = Appointment.objects.create(
                    doctor=doctor,
                    patient=patient,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    reason=reason,
                    status='PENDING'
                )
                # Create notification for the doctor about the new appointment request
                try:
                    Notification.objects.create(
                        user=doctor.user,
                        actor=request.user,
                        verb=f'New appointment request from {patient.user.get_full_name() or patient.user.username} on {appointment_date} at {appointment_time}',
                        target_appointment=appointment,
                        notif_type='INFO'
                    )
                except Exception:
                    # don't block booking if notification creation fails
                    pass
                messages.success(request, 'Appointment booked successfully.')
                return redirect('patients:dashboard')

            # Step 1: show available slots for selected doctor and date
            if request.POST.get('action') == 'find_slots':
                doctor_id = request.POST.get('doctor')
                date_str = request.POST.get('appointment_date')
                try:
                    doctor = Doctor.objects.get(id=doctor_id)
                    appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except Exception:
                    messages.error(request, 'Invalid doctor or date.')
                    return redirect('patients:book_appointment')

                # find schedule entries for that weekday
                weekday = appointment_date.strftime('%A')  # e.g., 'Monday'
                schedules = Schedule.objects.filter(doctor=doctor, day=weekday)
                slots = []
                slot_length = timedelta(minutes=30)
                for sched in schedules:
                    start_dt = datetime.combine(appointment_date, sched.start_time)
                    end_dt = datetime.combine(appointment_date, sched.end_time)
                    current = start_dt
                    while current + slot_length <= end_dt:
                        t = current.time()
                        # check appointment exists
                        conflict = Appointment.objects.filter(
                            doctor=doctor,
                            appointment_date=appointment_date,
                            appointment_time=t,
                            status__in=['PENDING', 'CONFIRMED']
                        ).exists()
                        if not conflict:
                            slots.append(t.strftime('%H:%M'))
                        current += slot_length

                if not slots:
                    messages.info(request, 'No available slots for selected date. Please choose another date or doctor.')

                form = AppointmentForm()
                form.fields['doctor'].queryset = Doctor.objects.filter(is_active=True)
                return render(request, 'patients/book_appointment.html', {
                    'form': form,
                    'slots': slots,
                    'selected_doctor': doctor,
                    'selected_date': appointment_date
                })

        # Default: show selection form
        form = AppointmentForm()
        form.fields['doctor'].queryset = Doctor.objects.filter(is_active=True)
        return render(request, 'patients/book_appointment.html', {'form': form})
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('login')


@login_required
def available_slots(request):
    """Show all doctors' schedules and available slots for a given date range.

    Patients will see slots and a 'Book' button for each slot which creates a pending Appointment request for the doctor to approve.
    """
    try:
        patient = request.user.patient
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found.')
        return redirect('login')

    date_str = request.GET.get('date')
    if date_str:
        try:
            base_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            base_date = datetime.now().date()
    else:
        base_date = datetime.now().date()

    # show next 7 days by default
    days = [base_date]
    for i in range(1, 7):
        days.append(base_date + timedelta(days=i))

    doctors = Doctor.objects.filter(is_active=True)
    slots_by_doctor = []
    slot_length = timedelta(minutes=30)
    for doc in doctors:
        doc_slots = {}
        for day in days:
            weekday = day.strftime('%A')
            schedules = Schedule.objects.filter(doctor=doc, day=weekday)
            available = []
            for sched in schedules:
                start_dt = datetime.combine(day, sched.start_time)
                end_dt = datetime.combine(day, sched.end_time)
                current = start_dt
                while current + slot_length <= end_dt:
                    t = current.time()
                    conflict = Appointment.objects.filter(
                        doctor=doc,
                        appointment_date=day,
                        appointment_time=t,
                        status__in=['PENDING', 'CONFIRMED']
                    ).exists()
                    if not conflict:
                        available.append({'time': t.strftime('%H:%M')})
                    current += slot_length
            doc_slots[day] = available
        slots_by_doctor.append({'doctor': doc, 'slots': doc_slots})

    return render(request, 'patients/available_slots.html', {
        'days': days,
        'slots_by_doctor': slots_by_doctor,
    })


@login_required
def request_slot(request):
    """Endpoint to request/book a specific slot (AJAX or POST).

    Expects: doctor_id, date (YYYY-MM-DD), time (HH:MM)
    Creates an Appointment with status 'PENDING' and notifies the doctor.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
    try:
        patient = request.user.patient
    except Patient.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Patient profile not found'}, status=403)

    doctor_id = request.POST.get('doctor_id')
    date_str = request.POST.get('date')
    time_str = request.POST.get('time')
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(time_str, '%H:%M').time()
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid data'}, status=400)

    # ensure slot still free
    exists = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        status__in=['PENDING', 'CONFIRMED']
    ).exists()
    if exists:
        return JsonResponse({'ok': False, 'error': 'Slot already taken'}, status=409)

    appointment = Appointment.objects.create(
        doctor=doctor,
        patient=patient,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        reason='Requested via available slots',
        status='PENDING'
    )

    # notify doctor
    try:
        Notification.objects.create(
            user=doctor.user,
            actor=request.user,
            verb=f'{patient.user.get_full_name() or patient.user.username} requested an appointment on {appointment_date} at {appointment_time}',
            target_appointment=appointment,
            notif_type='INFO'
        )
    except Exception:
        pass

    return JsonResponse({'ok': True, 'appointment_id': appointment.id})

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user.patient)
    if appointment.status in ['PENDING', 'CONFIRMED']:
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    else:
        messages.error(request, 'Cannot cancel this appointment.')
    return redirect('patients:dashboard')
