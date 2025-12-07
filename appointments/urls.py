from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.list_appointments, name='list_appointments'),
    path('<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('<int:appointment_id>/update-status/', views.update_appointment_status, name='update_status'),
    path('schedule/', views.manage_schedule, name='manage_schedule'),
    path('notifications/', views.notifications_list, name='notifications_list'),
]