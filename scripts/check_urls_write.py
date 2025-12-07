from django import setup
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','hospital_management.settings')
setup()
from django.urls import reverse
names = ['logout','doctors:register','doctors:schedule','appointments:manage_schedule','patients:book_appointment','appointments:list_appointments']
with open('url_check_results.txt','w') as f:
    for n in names:
        try:
            f.write(f"{n} -> {reverse(n)}\n")
        except Exception as e:
            f.write(f"{n} ERROR -> {type(e).__name__}: {e}\n")
print('wrote url_check_results.txt')
