from django.db import models
from django.contrib.auth.models import User
from doctors.models import Doctor
from patients.models import Patient
from django.urls import reverse

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
    
    def __str__(self):
        return f"{self.patient} - Dr. {self.doctor} ({self.appointment_date})"

    @property
    def status_badge(self):
        mapping = {
            'PENDING': 'warning',
            'CONFIRMED': 'success',
            'COMPLETED': 'secondary',
            'CANCELLED': 'danger',
        }
        return mapping.get(self.status, 'light')


class Notification(models.Model):
    """Simple notification model for users."""
    NOTIF_TYPE_CHOICES = [
        ('INFO', 'Info'),
        ('SUCCESS', 'Success'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actor_notifications')
    verb = models.CharField(max_length=255)
    target_appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    url = models.CharField(max_length=512, blank=True)
    notif_type = models.CharField(max_length=10, choices=NOTIF_TYPE_CHOICES, default='INFO')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.user}: {self.verb[:50]}"

    def get_absolute_url(self):
        if self.url:
            return self.url
        if self.target_appointment:
            try:
                return reverse('appointments:appointment_detail', args=[self.target_appointment.id])
            except Exception:
                return '#'
        return '#'
