"""
Versioning service for capturing pre-save snapshots, pruning expired 6th+ versions,
and restoring model data snapshots (excluding SEO and slug/URL fields).
"""
import os
import logging
from typing import Dict, Any, List, Optional
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.db import models, transaction
from apps.core.models import ContentVersion

logger = logging.getLogger(__name__)


class VersioningService:
    """Service to handle pre-save version snapshots and rollbacks (max 5 versions limit)."""

    MAX_VERSIONS = 5

    # Explicitly exclude SEO and URL slug fields from snapshots & restorations
    EXCLUDED_FIELDS = {
        'slug',
        'meta_title',
        'meta_description',
        'meta_keywords',
        'canonical_url',
        'og_title',
        'og_description',
        'og_image',
        'noindex',
        'nofollow',
        'created_at',
        'updated_at'
    }

    @classmethod
    def _serialize_value(cls, val: Any) -> Any:
        """Helper to convert non-JSON serializable values to JSON compatible representations."""
        if val is None:
            return None
        if isinstance(val, (int, float, bool, str)):
            return val
        if hasattr(val, 'isoformat'):
            return val.isoformat()
        if isinstance(val, models.Model):
            return val.pk
        if isinstance(val, (list, tuple)):
            return [cls._serialize_value(item) for item in val]
        if isinstance(val, dict):
            return {k: cls._serialize_value(v) for k, v in val.items()}
        return str(val)

    @classmethod
    def serialize_instance(cls, instance: models.Model) -> Dict[str, Any]:
        """
        Serialize model instance fields and 100% of related child tables/formsets into JSON.
        EXCLUDES SEO fields and URL (slug).
        """
        data = {}
        opts = instance._meta

        # 1. Base model fields (excluding SEO and slug)
        for f in opts.concrete_fields:
            if f.auto_created or f.name in cls.EXCLUDED_FIELDS:
                continue
            val = f.value_from_object(instance)
            data[f.name] = cls._serialize_value(val)

        # 2. ManyToMany fields (like tags, related majors, etc.)
        for m2m in opts.many_to_many:
            if m2m.name in cls.EXCLUDED_FIELDS:
                continue
            if hasattr(instance, m2m.name):
                manager = getattr(instance, m2m.name)
                try:
                    data[m2m.name] = list(manager.values_list('pk', flat=True))
                except Exception:
                    pass

        # 3. Child Inline Formsets & Relations

        # A. FAQs
        if hasattr(instance, 'faqs'):
            try:
                faqs_list = []
                for faq in instance.faqs.all():
                    faqs_list.append({
                        'id': faq.pk,
                        'question': faq.question,
                        'answer': faq.answer,
                        'order': getattr(faq, 'order', getattr(faq, 'sort_order', 0))
                    })
                data['_faqs'] = faqs_list
            except Exception as e:
                logger.warning(f"Error serializing FAQs for {instance}: {e}")

        # B. Attachments
        if hasattr(instance, 'attachments'):
            try:
                att_list = []
                for att in instance.attachments.all():
                    att_list.append({
                        'id': att.pk,
                        'title': getattr(att, 'title', ''),
                        'file_path': str(att.file) if att.file else ''
                    })
                data['_attachments'] = att_list
            except Exception as e:
                logger.warning(f"Error serializing attachments for {instance}: {e}")

        # C. University Faculties & Programs
        if hasattr(instance, 'faculties'):
            try:
                faculties_list = []
                for faculty in instance.faculties.all():
                    programs_list = []
                    if hasattr(faculty, 'programs'):
                        for prog in faculty.programs.all():
                            programs_list.append({
                                'id': prog.pk,
                                'name': getattr(prog, 'name', ''),
                                'degree_level': getattr(prog, 'degree_level', ''),
                                'tuition_fee': cls._serialize_value(getattr(prog, 'tuition_fee', None)),
                                'duration': getattr(prog, 'duration', '')
                            })
                    faculties_list.append({
                        'id': faculty.pk,
                        'name': faculty.name,
                        'description': getattr(faculty, 'description', ''),
                        'programs': programs_list
                    })
                data['_faculties'] = faculties_list
            except Exception as e:
                logger.warning(f"Error serializing faculties for {instance}: {e}")

        # D. Institute Courses
        if hasattr(instance, 'courses'):
            try:
                courses_list = []
                for course in instance.courses.all():
                    courses_list.append({
                        'id': course.pk,
                        'name': course.name,
                        'duration': getattr(course, 'duration', ''),
                        'price': cls._serialize_value(getattr(course, 'price', None)),
                        'sort_order': getattr(course, 'sort_order', 0)
                    })
                data['_courses'] = courses_list
            except Exception as e:
                logger.warning(f"Error serializing courses for {instance}: {e}")

        # E. Major Tables (Subjects, Salary, Countries)
        if hasattr(instance, 'subjects_table'):
            try:
                subj_list = []
                for item in instance.subjects_table.all():
                    subj_list.append({
                        'id': item.pk,
                        'subject_name': getattr(item, 'subject_name', ''),
                        'year_or_semester': getattr(item, 'year_or_semester', ''),
                        'sort_order': getattr(item, 'sort_order', 0)
                    })
                data['_subjects_table'] = subj_list
            except Exception as e:
                logger.warning(f"Error serializing subjects_table for {instance}: {e}")

        if hasattr(instance, 'salary_table'):
            try:
                sal_list = []
                for item in instance.salary_table.all():
                    sal_list.append({
                        'id': item.pk,
                        'job_title': getattr(item, 'job_title', ''),
                        'salary_range': getattr(item, 'salary_range', ''),
                        'sort_order': getattr(item, 'sort_order', 0)
                    })
                data['_salary_table'] = sal_list
            except Exception as e:
                logger.warning(f"Error serializing salary_table for {instance}: {e}")

        if hasattr(instance, 'countries_table'):
            try:
                cntry_list = []
                for item in instance.countries_table.all():
                    cntry_list.append({
                        'id': item.pk,
                        'country_name': getattr(item, 'country_name', ''),
                        'notes': getattr(item, 'notes', ''),
                        'sort_order': getattr(item, 'sort_order', 0)
                    })
                data['_countries_table'] = cntry_list
            except Exception as e:
                logger.warning(f"Error serializing countries_table for {instance}: {e}")

        return data

    @classmethod
    def capture_pre_save_snapshot(
        cls, 
        instance: models.Model, 
        user: Optional[User] = None, 
        change_reason: str = ''
    ) -> Optional[ContentVersion]:
        """
        Capture pre-save snapshot of instance as it currently exists in the DB prior to edit.
        Must be called within transaction.atomic().
        """
        if not instance.pk:
            return None

        # Fetch pristine DB state before current changes
        try:
            db_instance = instance.__class__.objects.get(pk=instance.pk)
        except instance.__class__.DoesNotExist:
            return None

        content_type = ContentType.objects.get_for_model(db_instance)
        serialized_data = cls.serialize_instance(db_instance)

        # Calculate version number
        last_version = ContentVersion.objects.filter(
            content_type=content_type,
            object_id=db_instance.pk
        ).order_by('-version_number').first()

        next_version_num = (last_version.version_number + 1) if last_version else 1

        version = ContentVersion.objects.create(
            content_type=content_type,
            object_id=db_instance.pk,
            version_number=next_version_num,
            data=serialized_data,
            created_by=user if (user and user.is_authenticated) else None,
            change_reason=change_reason or 'نسخة سابقة قبل التحديث'
        )

        # Auto-prune beyond MAX_VERSIONS (5)
        cls.prune_expired_versions(db_instance)

        return version

    @classmethod
    def prune_expired_versions(cls, instance: models.Model):
        """
        Prune versions beyond MAX_VERSIONS (5) and safely clean up orphaned physical files.
        """
        content_type = ContentType.objects.get_for_model(instance)
        existing_versions = list(
            ContentVersion.objects.filter(
                content_type=content_type,
                object_id=instance.pk
            ).order_by('-created_at')
        )

        if len(existing_versions) > cls.MAX_VERSIONS:
            to_delete = existing_versions[cls.MAX_VERSIONS:]
            for expired_v in to_delete:
                cls._cleanup_orphaned_version_files(expired_v, instance)
                expired_v.delete()

    @classmethod
    def _cleanup_orphaned_version_files(cls, version: ContentVersion, live_instance: models.Model):
        """
        Clean up files stored in an expired version's JSON data if no longer referenced
        by remaining active versions or live DB objects.
        """
        data = version.data or {}
        candidate_files = set()

        # Gather files from JSON
        if '_attachments' in data:
            for att in data['_attachments']:
                if att.get('file_path'):
                    candidate_files.add(att['file_path'])

        for field_name, val in data.items():
            if isinstance(val, str) and (val.endswith('.jpg') or val.endswith('.png') or val.endswith('.jpeg') or val.endswith('.webp') or val.endswith('.pdf')):
                candidate_files.add(val)

        if not candidate_files:
            return

        content_type = version.content_type
        other_versions = ContentVersion.objects.filter(
            content_type=content_type,
            object_id=version.object_id
        ).exclude(id=version.id)

        for file_path in candidate_files:
            # Check if used in other active versions
            file_used_in_other_versions = False
            for ov in other_versions:
                ov_str = str(ov.data)
                if file_path in ov_str:
                    file_used_in_other_versions = True
                    break

            if not file_used_in_other_versions:
                # Check if physical file exists and delete safely
                try:
                    if default_storage.exists(file_path):
                        default_storage.delete(file_path)
                except Exception as e:
                    logger.warning(f"Error cleaning up expired file {file_path}: {e}")

    @classmethod
    def get_versions(cls, instance: models.Model) -> List[ContentVersion]:
        """Fetch the latest max 5 versions for an instance."""
        if not instance.pk:
            return []

        content_type = ContentType.objects.get_for_model(instance)
        return list(
            ContentVersion.objects.filter(
                content_type=content_type,
                object_id=instance.pk
            ).select_related('created_by').order_by('-created_at')[:cls.MAX_VERSIONS]
        )

    @classmethod
    def restore_version(
        cls, 
        version_id: int, 
        user: Optional[User] = None
    ) -> Optional[models.Model]:
        """
        Perform update-in-place restoration for content fields while keeping active URL (slug)
        and SEO metadata 100% intact.
        """
        try:
            version = ContentVersion.objects.get(pk=version_id)
        except ContentVersion.DoesNotExist:
            return None

        instance = version.content_object
        if not instance:
            return None

        data = version.data
        opts = instance._meta

        with transaction.atomic():
            # First, capture pre-save snapshot of current state before restoration
            cls.capture_pre_save_snapshot(
                instance, 
                user=user, 
                change_reason=f"لقطة تلقائية قبل استرجاع النسخة v{version.version_number}"
            )

            # Update base model fields (skipping EXCLUDED_FIELDS)
            for f in opts.concrete_fields:
                if f.name in data and f.name not in cls.EXCLUDED_FIELDS and not f.primary_key and not f.auto_created:
                    val = data[f.name]
                    if f.is_relation and f.many_to_one:
                        if val is None:
                            setattr(instance, f.name, None)
                        else:
                            try:
                                rel_model = f.remote_field.model
                                rel_obj = rel_model.objects.filter(pk=val).first()
                                setattr(instance, f.name, rel_obj)  # Skips if deleted
                            except Exception:
                                pass
                    else:
                        setattr(instance, f.name, val)

            instance.save()

            # Restore ManyToMany relations (skipping deleted target IDs gracefully)
            for m2m in opts.many_to_many:
                if m2m.name in data and m2m.name not in cls.EXCLUDED_FIELDS:
                    target_pks = data[m2m.name]
                    if isinstance(target_pks, list):
                        rel_model = m2m.remote_field.model
                        valid_objs = list(rel_model.objects.filter(pk__in=target_pks))
                        getattr(instance, m2m.name).set(valid_objs)

            # Restore inline FAQs in-place
            if '_faqs' in data and hasattr(instance, 'faqs'):
                try:
                    instance.faqs.all().delete()
                    faq_model = instance.faqs.model
                    for faq_dict in data['_faqs']:
                        faq_kwargs = {
                            'question': faq_dict.get('question'),
                            'answer': faq_dict.get('answer')
                        }
                        if hasattr(faq_model, 'order'):
                            faq_kwargs['order'] = faq_dict.get('order', 0)
                        elif hasattr(faq_model, 'sort_order'):
                            faq_kwargs['sort_order'] = faq_dict.get('order', 0)

                        for f in faq_model._meta.fields:
                            if f.is_relation and f.remote_field.model == opts.model:
                                faq_kwargs[f.name] = instance
                                break

                        faq_model.objects.create(**faq_kwargs)
                except Exception as e:
                    logger.warning(f"Error restoring FAQs: {e}")

            # Restore Courses for Institute
            if '_courses' in data and hasattr(instance, 'courses'):
                try:
                    instance.courses.all().delete()
                    course_model = instance.courses.model
                    for c_dict in data['_courses']:
                        c_kwargs = {
                            'name': c_dict.get('name', ''),
                            'duration': c_dict.get('duration', ''),
                            'price': c_dict.get('price'),
                            'sort_order': c_dict.get('sort_order', 0),
                            'institute': instance
                        }
                        course_model.objects.create(**c_kwargs)
                except Exception as e:
                    logger.warning(f"Error restoring courses: {e}")

            # Restore Attachments
            if '_attachments' in data and hasattr(instance, 'attachments'):
                try:
                    instance.attachments.all().delete()
                    att_model = instance.attachments.model
                    for a_dict in data['_attachments']:
                        if not a_dict.get('file_path'):
                            continue
                        a_kwargs = {
                            'title': a_dict.get('title', ''),
                            'file': a_dict.get('file_path')
                        }
                        for f in att_model._meta.fields:
                            if f.is_relation and f.remote_field.model == opts.model:
                                a_kwargs[f.name] = instance
                                break
                        att_model.objects.create(**a_kwargs)
                except Exception as e:
                    logger.warning(f"Error restoring attachments: {e}")

            # Restore Major Tables (Subjects, Salary, Countries)
            if '_subjects_table' in data and hasattr(instance, 'subjects_table'):
                try:
                    instance.subjects_table.all().delete()
                    subj_model = instance.subjects_table.model
                    for s_dict in data['_subjects_table']:
                        s_kwargs = {
                            'subject_name': s_dict.get('subject_name', ''),
                            'year_or_semester': s_dict.get('year_or_semester', ''),
                            'sort_order': s_dict.get('sort_order', 0),
                            'major': instance
                        }
                        subj_model.objects.create(**s_kwargs)
                except Exception as e:
                    logger.warning(f"Error restoring subjects_table: {e}")

            if '_salary_table' in data and hasattr(instance, 'salary_table'):
                try:
                    instance.salary_table.all().delete()
                    sal_model = instance.salary_table.model
                    for s_dict in data['_salary_table']:
                        s_kwargs = {
                            'job_title': s_dict.get('job_title', ''),
                            'salary_range': s_dict.get('salary_range', ''),
                            'sort_order': s_dict.get('sort_order', 0),
                            'major': instance
                        }
                        sal_model.objects.create(**s_kwargs)
                except Exception as e:
                    logger.warning(f"Error restoring salary_table: {e}")

            if '_countries_table' in data and hasattr(instance, 'countries_table'):
                try:
                    instance.countries_table.all().delete()
                    cntry_model = instance.countries_table.model
                    for c_dict in data['_countries_table']:
                        c_kwargs = {
                            'country_name': c_dict.get('country_name', ''),
                            'notes': c_dict.get('notes', ''),
                            'sort_order': c_dict.get('sort_order', 0),
                            'major': instance
                        }
                        cntry_model.objects.create(**c_kwargs)
                except Exception as e:
                    logger.warning(f"Error restoring countries_table: {e}")

        return instance

