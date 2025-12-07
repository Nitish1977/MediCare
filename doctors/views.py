from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from .models import Doctor, Schedule
from .forms import DoctorRegistrationForm, DoctorProfileForm, ScheduleForm
from appointments.models import Appointment
from django.utils import timezone
from datetime import date

def register(request):
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Doctor.objects.create(
                user=user,
                specialization=form.cleaned_data['specialization'],
                phone_number=form.cleaned_data['phone_number'],
                address=form.cleaned_data['address']
            )
            doctors_group, _ = Group.objects.get_or_create(name='Doctors')
            user.groups.add(doctors_group)
            messages.success(request, 'Registration successful. Please login.')
            return redirect('login')
    else:
        form = DoctorRegistrationForm()
    return render(request, 'doctors/register.html', {'form': form})

@login_required
def dashboard(request):
    try:
        doctor = request.user.doctor
        # Fetch all appointments for this doctor and split into today's and upcoming
        all_appointments = Appointment.objects.filter(doctor=doctor).order_by('appointment_date', 'appointment_time')
        today = timezone.localdate()
        todays_qs = all_appointments.filter(appointment_date=today)
        upcoming_qs = all_appointments.filter(appointment_date__gt=today)
        context = {
            'doctor': doctor,
            'appointments': {
                'today': todays_qs,
                'upcoming': upcoming_qs,
            }
        }
        return render(request, 'doctors/dashboard.html', context)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('login')

@login_required
def profile(request):
    try:
        doctor = request.user.doctor
        if request.method == 'POST':
            form = DoctorProfileForm(request.POST, instance=doctor)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('doctors:profile')
        else:
            form = DoctorProfileForm(instance=doctor)
        return render(request, 'doctors/profile.html', {'form': form})
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('login')

@login_required
def schedule(request):
    try:
        doctor = request.user.doctor
        if request.method == 'POST':
            form = ScheduleForm(request.POST)
            if form.is_valid():
                schedule = form.save(commit=False)
                schedule.doctor = doctor
                schedule.save()
                messages.success(request, 'Schedule added successfully.')
                return redirect('doctors:schedule')
        else:
            form = ScheduleForm()
        
        schedules = Schedule.objects.filter(doctor=doctor).order_by('day')
        # upcoming appointments for preview on schedule page
        today = timezone.localdate()
        upcoming_appointments = Appointment.objects.filter(doctor=doctor, appointment_date__gte=today).order_by('appointment_date', 'appointment_time')
        return render(request, 'doctors/schedule.html', {
            'form': form,
            'schedules': schedules,
            'upcoming_appointments': upcoming_appointments,
        })
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('login')

@login_required
def delete_schedule(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk, doctor=request.user.doctor)
    schedule.delete()
    messages.success(request, 'Schedule deleted successfully.')
    return redirect('doctors:schedule')

@login_required
def manage_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor)
    if request.method == 'POST':
        if 'confirm' in request.POST:
            appointment.status = 'CONFIRMED'
            appointment.save()
            messages.success(request, 'Appointment confirmed.')
        elif 'complete' in request.POST:
            appointment.status = 'COMPLETED'
            appointment.save()
            messages.success(request, 'Appointment marked as completed.')
        elif 'cancel' in request.POST:
            appointment.status = 'CANCELLED'
            appointment.save()
            messages.success(request, 'Appointment cancelled.')
    return redirect('doctors:dashboard')
