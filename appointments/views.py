from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Appointment
from .models import Notification
from .forms import AppointmentForm
from doctors.models import Doctor, Schedule
from patients.models import Patient

@login_required
def list_appointments(request):
    if hasattr(request.user, 'doctor'):
        appointments = Appointment.objects.filter(doctor=request.user.doctor).order_by('-appointment_date', '-appointment_time')
    elif hasattr(request.user, 'patient'):
        appointments = Appointment.objects.filter(patient=request.user.patient).order_by('-appointment_date', '-appointment_time')
    else:
        messages.error(request, 'Invalid user type.')
        return redirect('login')
    
    return render(request, 'appointments/list_appointments.html', {'appointments': appointments})

@login_required
def appointment_detail(request, appointment_id):
    if hasattr(request.user, 'doctor'):
        appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor)
    elif hasattr(request.user, 'patient'):
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user.patient)
    else:
        messages.error(request, 'Invalid user type.')
        return redirect('login')
    
    # mark related notifications as read for this user (if any)
    try:
        Notification.objects.filter(target_appointment=appointment, user=request.user, is_read=False).update(is_read=True)
    except Exception:
        pass
    return render(request, 'appointments/appointment_detail.html', {'appointment': appointment})

@login_required
def update_appointment_status(request, appointment_id):
    if not hasattr(request.user, 'doctor'):
        messages.error(request, 'Only doctors can update appointment status.')
        return redirect('appointments:list_appointments')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['CONFIRMED', 'CANCELLED', 'COMPLETED']:
            appointment.status = new_status
            appointment.save()
            # notify patient about the status change
            try:
                Notification.objects.create(
                    user=appointment.patient.user,
                    actor=request.user,
                    verb=f'Your appointment on {appointment.appointment_date} at {appointment.appointment_time} has been {new_status.lower()}.',
                    target_appointment=appointment,
                    notif_type='SUCCESS' if new_status == 'CONFIRMED' else 'WARNING' if new_status == 'CANCELLED' else 'INFO'
                )
            except Exception:
                pass
            messages.success(request, f'Appointment status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('appointments:appointment_detail', appointment_id=appointment.id)

@login_required
def manage_schedule(request):
    if not hasattr(request.user, 'doctor'):
        messages.error(request, 'Only doctors can manage schedules.')
        return redirect('appointments:list_appointments')
    
    doctor = request.user.doctor
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gte=timezone.now().date(),
        status__in=['PENDING', 'CONFIRMED']
    ).order_by('appointment_date', 'appointment_time')
    
    schedules = Schedule.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
    
    return render(request, 'appointments/manage_schedule.html', {
        'upcoming_appointments': upcoming_appointments,
        'schedules': schedules
    })


@login_required
def notifications_list(request):
    # Show notifications for current user and mark unread as read
    qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    try:
        qs.filter(is_read=False).update(is_read=True)
    except Exception:
        pass
    return render(request, 'appointments/notifications_list.html', {'notifications': qs})
