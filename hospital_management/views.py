from django.shortcuts import render
from django.utils import timezone
from appointments.models import Appointment


def home_view(request):
    context = {}
    if request.user.is_authenticated:
        today = timezone.localdate()
        # patient upcoming
        if hasattr(request.user, 'patient'):
            upcoming = Appointment.objects.filter(patient=request.user.patient, appointment_date__gte=today, status__in=['PENDING','CONFIRMED']).order_by('appointment_date','appointment_time')
        # doctor upcoming
        elif hasattr(request.user, 'doctor'):
            upcoming = Appointment.objects.filter(doctor=request.user.doctor, appointment_date__gte=today, status__in=['PENDING','CONFIRMED']).order_by('appointment_date','appointment_time')
        else:
            upcoming = Appointment.objects.none()
        context['upcoming_count'] = upcoming.count()
        context['upcoming_list'] = list(upcoming[:3])
    return render(request, 'home.html', context)
