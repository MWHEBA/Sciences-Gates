"""
Management command to remove HTML comments from model fields.
"""
import re
from django.core.management.base import BaseCommand
from apps.universities.models import University
from apps.institutes.models import Institute, Course
from apps.majors.models import Major


class Command(BaseCommand):
    help = 'Remove HTML comments from description and location fields'

    def handle(self, *args, **options):
        """Remove HTML comments from all models."""
        pattern = r'<!--.*?-->'
        
        # Clean Universities
        universities = University.objects.all()
        updated_count = 0
        
        for uni in universities:
            original_desc = uni.description
            original_loc = uni.location
            
            uni.description = re.sub(pattern, '', uni.description, flags=re.DOTALL) if uni.description else ''
            uni.location = re.sub(pattern, '', uni.location, flags=re.DOTALL) if uni.location else ''
            
            if uni.description != original_desc or uni.location != original_loc:
                uni.save()
                updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} universities'))
        
        # Clean Institutes
        institutes = Institute.objects.all()
        updated_count = 0
        
        for inst in institutes:
            original_desc = inst.description
            original_loc = inst.location
            
            inst.description = re.sub(pattern, '', inst.description, flags=re.DOTALL) if inst.description else ''
            inst.location = re.sub(pattern, '', inst.location, flags=re.DOTALL) if inst.location else ''
            
            if inst.description != original_desc or inst.location != original_loc:
                inst.save()
                updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} institutes'))
        
        # Clean Majors
        majors = Major.objects.all()
        updated_count = 0
        
        for major in majors:
            original_desc = major.description
            
            major.description = re.sub(pattern, '', major.description, flags=re.DOTALL) if major.description else ''
            
            if major.description != original_desc:
                major.save()
                updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} majors'))
        self.stdout.write(self.style.SUCCESS('All HTML comments removed successfully!'))
