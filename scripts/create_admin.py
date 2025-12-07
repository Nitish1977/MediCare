"""
Safe helper: create a Django superuser if it does not already exist.
Run from project root with: python scripts/create_admin.py

This script prints one of: EXISTS, CREATED, or ERROR
"""
import os
import sys
import traceback

# Ensure project root is importable
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# Use the same settings module as manage.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_management.settings')

try:
    import django
    django.setup()
    from django.contrib.auth import get_user_model

    User = get_user_model()
    username = 'admin'
    email = 'admin@example.com'
    password = 'AdminPass123!'

    if User.objects.filter(username=username).exists():
        print('EXISTS')
    else:
        User.objects.create_superuser(username, email, password)
        print('CREATED')
except Exception:
    traceback.print_exc()
    print('ERROR')
