from django import setup
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','hospital_management.settings')
setup()
from django.urls import get_resolver
resolver = get_resolver()
with open('all_urls.txt','w', encoding='utf-8') as f:
    def walk_patterns(patterns, prefix=''):
        for p in patterns:
            try:
                regex = getattr(p, 'pattern', None)
                name = getattr(p, 'name', None)
                if name:
                    f.write(f"{prefix}{name}\n")
            except Exception:
                pass
            # dive into url_patterns attribute
            if hasattr(p, 'url_patterns'):
                walk_patterns(p.url_patterns, prefix=prefix)
    walk_patterns(resolver.url_patterns)
print('wrote all_urls.txt')
