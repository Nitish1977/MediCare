from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    # keep the same URL name for compatibility but show available slots page instead
    path('book-appointment/', views.available_slots, name='book_appointment'),
    path('available-slots/', views.available_slots, name='available_slots'),
    path('request-slot/', views.request_slot, name='request_slot'),
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
]