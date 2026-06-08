"""
Management command to sync existing media files into MediaFile model.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from PIL import Image

from apps.core.models import MediaFile
from apps.universities.models import University
from apps.institutes.models import Institute
from apps.majors.models import Major
from apps.articles.models import Article


class Command(BaseCommand):
    help = 'Sync existing media files into the MediaFile model'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting sync of media files...'))
        
        # 1. Sync University Logo
        self.stdout.write('Syncing University logos...')
        uni_ct = ContentType.objects.get_for_model(University)
        uni_logo_count = 0
        for uni in University.objects.all():
            if uni.logo:
                exists = MediaFile.objects.filter(
                    content_type=uni_ct,
                    object_id=uni.id,
                    source_type=MediaFile.SourceType.UNIVERSITY_LOGO
                ).exists()
                if not exists:
                    file_size, width, height = self._get_image_info(uni.logo)
                    MediaFile.objects.create(
                        file=uni.logo,
                        original_filename=os.path.basename(uni.logo.name),
                        file_size=file_size,
                        width=width,
                        height=height,
                        alt_text=uni.logo_alt,
                        title=uni.name,
                        source_type=MediaFile.SourceType.UNIVERSITY_LOGO,
                        content_type=uni_ct,
                        object_id=uni.id
                    )
                    uni_logo_count += 1
        self.stdout.write(self.style.SUCCESS(f'OK: Synced {uni_logo_count} University logos.'))

        # 2. Sync University Main Images
        self.stdout.write('Syncing University main images...')
        uni_img_count = 0
        for uni in University.objects.all():
            if uni.main_image:
                exists = MediaFile.objects.filter(
                    content_type=uni_ct,
                    object_id=uni.id,
                    source_type=MediaFile.SourceType.UNIVERSITY_IMAGE
                ).exists()
                if not exists:
                    file_size, width, height = self._get_image_info(uni.main_image)
                    MediaFile.objects.create(
                        file=uni.main_image,
                        original_filename=os.path.basename(uni.main_image.name),
                        file_size=file_size,
                        width=width,
                        height=height,
                        alt_text=uni.main_image_alt,
                        title=uni.name,
                        source_type=MediaFile.SourceType.UNIVERSITY_IMAGE,
                        content_type=uni_ct,
                        object_id=uni.id
                    )
                    uni_img_count += 1
        self.stdout.write(self.style.SUCCESS(f'OK: Synced {uni_img_count} University main images.'))

        # 3. Sync Institute Main Images
        self.stdout.write('Syncing Institute main images...')
        inst_ct = ContentType.objects.get_for_model(Institute)
        inst_count = 0
        for inst in Institute.objects.all():
            if inst.main_image:
                exists = MediaFile.objects.filter(
                    content_type=inst_ct,
                    object_id=inst.id,
                    source_type=MediaFile.SourceType.INSTITUTE_IMAGE
                ).exists()
                if not exists:
                    file_size, width, height = self._get_image_info(inst.main_image)
                    MediaFile.objects.create(
                        file=inst.main_image,
                        original_filename=os.path.basename(inst.main_image.name),
                        file_size=file_size,
                        width=width,
                        height=height,
                        alt_text=inst.main_image_alt,
                        title=inst.name,
                        source_type=MediaFile.SourceType.INSTITUTE_IMAGE,
                        content_type=inst_ct,
                        object_id=inst.id
                    )
                    inst_count += 1
        self.stdout.write(self.style.SUCCESS(f'OK: Synced {inst_count} Institute main images.'))

        # 4. Sync Major Main Images
        self.stdout.write('Syncing Major main images...')
        major_ct = ContentType.objects.get_for_model(Major)
        major_count = 0
        for major in Major.objects.all():
            if major.main_image:
                exists = MediaFile.objects.filter(
                    content_type=major_ct,
                    object_id=major.id,
                    source_type=MediaFile.SourceType.MAJOR_IMAGE
                ).exists()
                if not exists:
                    file_size, width, height = self._get_image_info(major.main_image)
                    MediaFile.objects.create(
                        file=major.main_image,
                        original_filename=os.path.basename(major.main_image.name),
                        file_size=file_size,
                        width=width,
                        height=height,
                        alt_text=major.main_image_alt,
                        title=major.name,
                        source_type=MediaFile.SourceType.MAJOR_IMAGE,
                        content_type=major_ct,
                        object_id=major.id
                    )
                    major_count += 1
        self.stdout.write(self.style.SUCCESS(f'OK: Synced {major_count} Major main images.'))

        # 5. Sync Article Featured Images
        self.stdout.write('Syncing Article featured images...')
        art_ct = ContentType.objects.get_for_model(Article)
        art_count = 0
        for art in Article.objects.all():
            if art.featured_image:
                exists = MediaFile.objects.filter(
                    content_type=art_ct,
                    object_id=art.id,
                    source_type=MediaFile.SourceType.ARTICLE_IMAGE
                ).exists()
                if not exists:
                    file_size, width, height = self._get_image_info(art.featured_image)
                    MediaFile.objects.create(
                        file=art.featured_image,
                        original_filename=os.path.basename(art.featured_image.name),
                        file_size=file_size,
                        width=width,
                        height=height,
                        alt_text=art.featured_image_alt,
                        title=art.title,
                        source_type=MediaFile.SourceType.ARTICLE_IMAGE,
                        content_type=art_ct,
                        object_id=art.id,
                        uploaded_by=art.author
                    )
                    art_count += 1
        self.stdout.write(self.style.SUCCESS(f'OK: Synced {art_count} Article featured images.'))

        # 6. Sync Editor uploads from disk
        self.stdout.write('Syncing editor upload files from disk...')
        editor_count = 0
        editor_dir = os.path.join(settings.MEDIA_ROOT, 'editor')
        if os.path.exists(editor_dir):
            for root, dirs, files in os.walk(editor_dir):
                for filename in files:
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                        abs_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(abs_path, settings.MEDIA_ROOT)
                        # Normalize path delimiters for Django
                        rel_path = rel_path.replace('\\', '/')
                        
                        exists = MediaFile.objects.filter(
                            file=rel_path,
                            source_type=MediaFile.SourceType.EDITOR
                        ).exists()
                        if not exists:
                            file_size = os.path.getsize(abs_path)
                            width, height = None, None
                            try:
                                with Image.open(abs_path) as img:
                                    width, height = img.size
                            except Exception:
                                pass
                                
                            MediaFile.objects.create(
                                file=rel_path,
                                original_filename=filename,
                                file_size=file_size,
                                width=width,
                                height=height,
                                alt_text='',
                                title=os.path.splitext(filename)[0],
                                source_type=MediaFile.SourceType.EDITOR
                            )
                            editor_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'OK: Synced {editor_count} editor upload images.'))
        self.stdout.write(self.style.SUCCESS('Media files synchronization completed successfully!'))

    def _get_image_info(self, image_field):
        file_size = 0
        width = None
        height = None
        try:
            if image_field.storage.exists(image_field.name):
                file_size = image_field.size
                width = image_field.width
                height = image_field.height
        except Exception:
            pass
        return file_size, width, height
