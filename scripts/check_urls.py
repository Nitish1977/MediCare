from django import setup
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','hospital_management.settings')
setup()
from django.urls import reverse
names = ['logout','doctors:register','doctors:schedule','appointments:manage_schedule','patients:book_appointment','appointments:list_appointments']
for n in names:
    try:
        print(n, '->', reverse(n))
    except Exception as e:
        print(n, 'ERROR ->', type(e).__name__, str(e))
