from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('schedule/', views.schedule, name='schedule'),
    path('schedule/delete/<int:pk>/', views.delete_schedule, name='delete_schedule'),
    path('appointment/<int:appointment_id>/manage/', views.manage_appointment, name='manage_appointment'),
]