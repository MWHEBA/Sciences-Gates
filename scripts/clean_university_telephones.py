#!/usr/bin/env python
"""
Migration & Audit Script for cleaning company telephone numbers from University and Institute records.
"""
import os
import sys
import django
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.universities.models import University
from apps.institutes.models import Institute

COMPANY_PHONE_PATTERNS = ["601128195437", "00601128195437", "+601128195437"]

def run_telephone_migration():
    print("=" * 80)
    print(f"STARTING UNIVERSITY & INSTITUTE TELEPHONE AUDIT AT {datetime.now().isoformat()}")
    print("=" * 80)

    # 1. Audit Universities
    total_univ_cleared = 0
    for univ in University.objects.all():
        if getattr(univ, 'telephone', None):
            for pattern in COMPANY_PHONE_PATTERNS:
                if pattern in str(univ.telephone):
                    print(f"University '{univ.name}' (ID: {univ.id}) has company phone '{univ.telephone}'. Clearing.")
                    univ.telephone = ""
                    univ.save()
                    total_univ_cleared += 1
                    break
    
    # 2. Audit Institutes
    total_inst_cleared = 0
    for inst in Institute.objects.all():
        if getattr(inst, 'telephone', None):
            for pattern in COMPANY_PHONE_PATTERNS:
                if pattern in str(inst.telephone):
                    print(f"Institute '{inst.name}' (ID: {inst.id}) has company phone '{inst.telephone}'. Clearing.")
                    inst.telephone = ""
                    inst.save()
                    total_inst_cleared += 1
                    break

    print("-" * 80)
    print(f"Cleared company telephone from {total_univ_cleared} University records.")
    print(f"Cleared company telephone from {total_inst_cleared} Institute records.")
    print("=" * 80)

if __name__ == "__main__":
    run_telephone_migration()
