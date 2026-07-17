from django.db import transaction
from django.utils.html import strip_tags
import re

def normalize_arabic(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower()

def _make_valid_json_string(val):
    import json
    if val is None:
        return '[]'
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    if isinstance(val, str):
        val_stripped = val.strip()
        if not val_stripped or val_stripped in ['غير محدد', 'لا يوجد', 'null', 'NULL', '-']:
            return '[]'
        try:
            parsed = json.loads(val_stripped)
            if isinstance(parsed, (list, dict)):
                return val_stripped
            else:
                table = {
                    'title': 'الرسوم الدراسية',
                    'headers': ['الرسوم'],
                    'rows': [[str(parsed)]]
                }
                return json.dumps([table])
        except json.JSONDecodeError:
            table = {
                'title': 'الرسوم الدراسية',
                'headers': ['الرسوم'],
                'rows': [[val_stripped]]
            }
            return json.dumps([table])
    return '[]'

def parse_wp_datetime(date_str):
    if not date_str or date_str == '0000-00-00 00:00:00':
        return None
    from django.utils.dateparse import parse_datetime
    from django.utils.timezone import make_aware
    from django.utils import timezone
    from datetime import timezone as datetime_timezone
    try:
        dt = parse_datetime(date_str)
        if dt and timezone.is_naive(dt):
            return make_aware(dt, datetime_timezone.utc)
        return dt
    except Exception:
        return None

def save_imported_content(content_type, mapped_data, user=None):
    """
    Validates and saves the imported content to the database using Django Forms and Formsets.
    This guarantees that all validation, clean() methods (including duplicate faculty prevention),
    M2M relations, and nested structures are saved exactly like manual submissions.
    """
    if content_type == 'university':
        return _save_university(mapped_data, user)
    elif content_type == 'institute':
        return _save_institute(mapped_data, user)
    elif content_type == 'major':
        return _save_major(mapped_data, user)
    elif content_type == 'article':
        return _save_article(mapped_data, user)
    else:
        raise ValueError(f"Unknown content type: {content_type}")

def _save_university(mapped_data, user):
    from apps.universities.models import University, Faculty
    from apps.dashboard.forms.university import UniversityForm, UniversityFAQFormSet, UniversityFacultyFormSet
    
    form_initial = mapped_data['form_initial']
    slug = form_initial.get('slug', '').strip()
    from django.utils.text import slugify
    slug = slugify(slug, allow_unicode=True)
    form_initial['slug'] = slug
    
    existing_obj = University.objects.filter(slug=slug).first()
    if not existing_obj:
        name_val = form_initial.get('name', '').strip()
        if name_val:
            existing_obj = University.objects.filter(name__iexact=name_val).first()
            if existing_obj:
                slug = existing_obj.slug
                form_initial['slug'] = slug
                
    action_type = 'updated' if existing_obj else 'created'
    form_data = {**form_initial}
    
    # Ensure one_time_fees is serialized to a valid JSON string
    form_data['one_time_fees'] = _make_valid_json_string(form_data.get('one_time_fees'))

    if 'publish_status' not in form_data or not form_data['publish_status']:
        form_data['publish_status'] = 'published'
    if user:
        form_data['user'] = user.id
        
    for img_key, img_path in mapped_data.get('image_paths', {}).items():
        if img_path:
            form_data[f'imported_{img_key}_path'] = img_path
            
    # University FAQs
    existing_faqs = list(existing_obj.faqs.all()) if existing_obj else []
    faqs_count = len(existing_faqs)
    
    # Clean and filter imported FAQs to avoid validation failures on empty fields
    raw_imported_faqs = mapped_data.get('faqs_data', [])
    imported_faqs = []
    for faq_item in raw_imported_faqs:
        q = (faq_item.get('question') or '').strip()
        a = (faq_item.get('answer') or '').strip()
        if not q and not a:
            continue
        if not q:
            q = 'غير محدد'
        if not a:
            a = 'غير محدد'
        imported_faqs.append({'question': q, 'answer': a})
        
    total_faqs = faqs_count + len(imported_faqs)
    
    form_data.update({
        'faqs-TOTAL_FORMS': str(total_faqs),
        'faqs-INITIAL_FORMS': str(faqs_count),
        'faqs-MIN_NUM_FORMS': '0',
        'faqs-MAX_NUM_FORMS': '1000',
    })
    for i, faq in enumerate(existing_faqs):
        form_data.update({
            f'faqs-{i}-id': str(faq.id),
            f'faqs-{i}-question': faq.question,
            f'faqs-{i}-answer': faq.answer,
            f'faqs-{i}-sort_order': str(faq.sort_order),
            f'faqs-{i}-DELETE': 'on',
        })
    for j, faq_item in enumerate(imported_faqs):
        i = faqs_count + j
        form_data.update({
            f'faqs-{i}-id': '',
            f'faqs-{i}-question': faq_item['question'],
            f'faqs-{i}-answer': faq_item['answer'],
            f'faqs-{i}-sort_order': str(i),
        })

    # Faculties & Programs
    existing_facs = list(existing_obj.faculties.all()) if existing_obj else []
    facs_count = len(existing_facs)
    imported_facs = mapped_data.get('faculties_data', [])
    total_facs = facs_count + len(imported_facs)
    
    form_data.update({
        'faculties-TOTAL_FORMS': str(total_facs),
        'faculties-INITIAL_FORMS': str(facs_count),
        'faculties-MIN_NUM_FORMS': '0',
        'faculties-MAX_NUM_FORMS': '1000',
    })
    
    # Mark existing for deletion (BaseFacultyFormSet.clean will rescue matches)
    for i, fac in enumerate(existing_facs):
        form_data.update({
            f'faculties-{i}-id': str(fac.id),
            f'faculties-{i}-name': fac.name,
            f'faculties-{i}-sort_order': str(fac.sort_order),
            f'faculties-{i}-DELETE': 'on',
        })
        existing_progs = list(fac.programs.all())
        form_data.update({
            f'faculty-{i}-programs-TOTAL_FORMS': str(len(existing_progs)),
            f'faculty-{i}-programs-INITIAL_FORMS': str(len(existing_progs)),
            f'faculty-{i}-programs-MIN_NUM_FORMS': '0',
            f'faculty-{i}-programs-MAX_NUM_FORMS': '1000',
        })
        for p_idx, prog in enumerate(existing_progs):
            form_data.update({
                f'faculty-{i}-programs-{p_idx}-id': str(prog.id),
                f'faculty-{i}-programs-{p_idx}-DELETE': 'on',
            })
            
    for j, fac_item in enumerate(imported_facs):
        i = facs_count + j
        form_data.update({
            f'faculties-{i}-id': '',
            f'faculties-{i}-name': fac_item.get('name', ''),
            f'faculties-{i}-sort_order': str(i),
        })
        imported_progs = fac_item.get('programs', [])
        valid_progs = []
        for prog_item in imported_progs:
            prog_name = prog_item.get('name', '').strip()
            if prog_name:
                valid_progs.append({
                    'name': prog_name[:200],  # Truncate to model limit
                    'duration': prog_item.get('duration', '').strip() or 'غير محدد',
                    'tuition_fees': prog_item.get('tuition_fees', '').strip() or 'غير محدد'
                })
        form_data.update({
            f'faculty-{i}-programs-TOTAL_FORMS': str(len(valid_progs)),
            f'faculty-{i}-programs-INITIAL_FORMS': '0',
            f'faculty-{i}-programs-MIN_NUM_FORMS': '0',
            f'faculty-{i}-programs-MAX_NUM_FORMS': '1000',
        })
        for p_idx, prog in enumerate(valid_progs):
            form_data.update({
                f'faculty-{i}-programs-{p_idx}-id': '',
                f'faculty-{i}-programs-{p_idx}-name': prog['name'],
                f'faculty-{i}-programs-{p_idx}-duration': prog['duration'],
                f'faculty-{i}-programs-{p_idx}-tuition_fees': prog['tuition_fees'],
                f'faculty-{i}-programs-{p_idx}-sort_order': str(p_idx),
            })

    with transaction.atomic():
        form = UniversityForm(form_data, instance=existing_obj)
        for field_name in ['logo', 'main_image', 'og_image']:
            if field_name in form.fields:
                form.fields[field_name].required = False
        faq_formset = UniversityFAQFormSet(form_data, instance=existing_obj)
        faculty_formset = UniversityFacultyFormSet(form_data, instance=existing_obj)
        
        # Attach nested program formsets
        for idx, faculty_form in enumerate(faculty_formset):
            from apps.dashboard.forms.university import NestedProgramFormSet
            if faculty_form.instance.pk:
                faculty_form.program_formset = NestedProgramFormSet(
                    form_data, instance=faculty_form.instance, prefix=f'faculty-{idx}-programs'
                )
            else:
                faculty_form.program_formset = NestedProgramFormSet(
                    form_data, prefix=f'faculty-{idx}-programs'
                )
                
        # Validate all forms/formsets
        all_valid = form.is_valid()
        
        if not faq_formset.is_valid():
            all_valid = False
            
        if not faculty_formset.is_valid():
            all_valid = False
            
        program_errors = {}
        for idx, faculty_form in enumerate(faculty_formset):
            if hasattr(faculty_form, 'program_formset'):
                if not faculty_form.program_formset.is_valid():
                    all_valid = False
                    program_errors[f'faculty-{idx}'] = faculty_form.program_formset.errors
                    
        if not all_valid:
            errors = {}
            if form.errors: errors['form'] = form.errors
            if faq_formset.errors: errors['faq'] = faq_formset.errors
            if faculty_formset.errors: errors['faculty'] = faculty_formset.errors
            if program_errors: errors['programs'] = program_errors
            raise ValueError(f"Validation failed: {errors}")
            
        saved_instance = form.save()
        
        faq_formset.instance = saved_instance
        faq_formset.save()
        
        faculty_formset.instance = saved_instance
        faculty_formset.save()
        
        for faculty_form in faculty_formset:
            if hasattr(faculty_form, 'program_formset') and faculty_form.instance.pk:
                faculty_form.program_formset.instance = faculty_form.instance
                faculty_form.program_formset.save()
                
        dt = parse_wp_datetime(mapped_data.get('created_at'))
        if dt:
            University.objects.filter(pk=saved_instance.pk).update(created_at=dt)
                
        return saved_instance, action_type

def _save_institute(mapped_data, user):
    from apps.institutes.models import Institute
    from apps.dashboard.forms.institute import InstituteForm, CourseFormSet, InstituteFAQFormSet
    
    form_initial = mapped_data['form_initial']
    slug = form_initial.get('slug', '').strip()
    from django.utils.text import slugify
    slug = slugify(slug, allow_unicode=True)
    form_initial['slug'] = slug
    
    existing_obj = Institute.objects.filter(slug=slug).first()
    if not existing_obj:
        name_val = form_initial.get('name', '').strip()
        if name_val:
            existing_obj = Institute.objects.filter(name__iexact=name_val).first()
            if existing_obj:
                slug = existing_obj.slug
                form_initial['slug'] = slug
                
    action_type = 'updated' if existing_obj else 'created'
    form_data = {**form_initial}
    if 'publish_status' not in form_data or not form_data['publish_status']:
        form_data['publish_status'] = 'published'
    for img_key, img_path in mapped_data.get('image_paths', {}).items():
        if img_path:
            form_data[f'imported_{img_key}_path'] = img_path
            
    # Institute FAQs
    existing_faqs = list(existing_obj.faqs.all()) if existing_obj else []
    faqs_count = len(existing_faqs)
    
    # Clean and filter imported FAQs
    raw_imported_faqs = mapped_data.get('faqs_data', [])
    imported_faqs = []
    for faq_item in raw_imported_faqs:
        q = (faq_item.get('question') or '').strip()
        a = (faq_item.get('answer') or '').strip()
        if not q and not a:
            continue
        if not q:
            q = 'غير محدد'
        if not a:
            a = 'غير محدد'
        imported_faqs.append({'question': q, 'answer': a})
        
    total_faqs = faqs_count + len(imported_faqs)
    
    form_data.update({
        'faqs-TOTAL_FORMS': str(total_faqs),
        'faqs-INITIAL_FORMS': str(faqs_count),
        'faqs-MIN_NUM_FORMS': '0',
        'faqs-MAX_NUM_FORMS': '1000',
    })
    for i, faq in enumerate(existing_faqs):
        form_data.update({
            f'faqs-{i}-id': str(faq.id),
            f'faqs-{i}-question': faq.question,
            f'faqs-{i}-answer': faq.answer,
            f'faqs-{i}-sort_order': str(faq.sort_order),
            f'faqs-{i}-DELETE': 'on',
        })
    for j, faq_item in enumerate(imported_faqs):
        i = faqs_count + j
        form_data.update({
            f'faqs-{i}-id': '',
            f'faqs-{i}-question': faq_item['question'],
            f'faqs-{i}-answer': faq_item['answer'],
            f'faqs-{i}-sort_order': str(i),
        })

    # Preserve or update courses
    existing_courses = list(existing_obj.courses.all()) if existing_obj else []
    courses_count = len(existing_courses)
    raw_imported_courses = mapped_data.get('courses_data', [])
    
    imported_courses = []
    for course_item in raw_imported_courses:
        dur = (course_item.get('duration') or '').strip()
        f_myr = (course_item.get('fees_myr') or '').strip()
        # Skip completely empty course rows
        if not dur and not f_myr:
            continue
        if not dur:
            dur = 'غير محدد'
        if not f_myr:
            f_myr = 'غير محدد'
        imported_courses.append({
            'course_type': course_item.get('course_type', 'undefined'),
            'duration': dur,
            'fees_myr': f_myr,
            'fees_usd': (course_item.get('fees_usd') or '').strip(),
            'fees_sar': (course_item.get('fees_sar') or '').strip(),
            'visa_duration': (course_item.get('visa_duration') or '').strip(),
        })
    
    if imported_courses:
        total_courses = courses_count + len(imported_courses)
        form_data.update({
            'courses-TOTAL_FORMS': str(total_courses),
            'courses-INITIAL_FORMS': str(courses_count),
            'courses-MIN_NUM_FORMS': '0',
            'courses-MAX_NUM_FORMS': '1000',
        })
        # Mark existing courses for deletion
        for i, course in enumerate(existing_courses):
            form_data.update({
                f'courses-{i}-id': str(course.id),
                f'courses-{i}-course_type': course.course_type,
                f'courses-{i}-duration': course.duration,
                f'courses-{i}-fees_myr': course.fees_myr,
                f'courses-{i}-fees_usd': course.fees_usd,
                f'courses-{i}-fees_sar': course.fees_sar,
                f'courses-{i}-visa_duration': course.visa_duration,
                f'courses-{i}-sort_order': str(course.sort_order),
                f'courses-{i}-DELETE': 'on',
            })
        # Add imported courses
        for j, course_item in enumerate(imported_courses):
            i = courses_count + j
            form_data.update({
                f'courses-{i}-id': '',
                f'courses-{i}-course_type': course_item['course_type'],
                f'courses-{i}-duration': course_item['duration'],
                f'courses-{i}-fees_myr': course_item['fees_myr'],
                f'courses-{i}-fees_usd': course_item['fees_usd'],
                f'courses-{i}-fees_sar': course_item['fees_sar'],
                f'courses-{i}-visa_duration': course_item['visa_duration'],
                f'courses-{i}-sort_order': str(i),
            })
    else:
        # Preserve existing courses
        form_data.update({
            'courses-TOTAL_FORMS': str(courses_count),
            'courses-INITIAL_FORMS': str(courses_count),
            'courses-MIN_NUM_FORMS': '0',
            'courses-MAX_NUM_FORMS': '1000',
        })
        for i, course in enumerate(existing_courses):
            form_data.update({
                f'courses-{i}-id': str(course.id),
                f'courses-{i}-course_type': course.course_type,
                f'courses-{i}-duration': course.duration,
                f'courses-{i}-fees_myr': course.fees_myr,
                f'courses-{i}-fees_usd': course.fees_usd,
                f'courses-{i}-fees_sar': course.fees_sar,
                f'courses-{i}-visa_duration': course.visa_duration,
                f'courses-{i}-sort_order': str(course.sort_order),
            })

    with transaction.atomic():
        form = InstituteForm(form_data, instance=existing_obj)
        for field_name in ['logo', 'main_image', 'og_image']:
            if field_name in form.fields:
                form.fields[field_name].required = False
        course_formset = CourseFormSet(form_data, instance=existing_obj)
        faq_formset = InstituteFAQFormSet(form_data, instance=existing_obj)
        
        all_valid = form.is_valid()
        if not course_formset.is_valid():
            all_valid = False
        if not faq_formset.is_valid():
            all_valid = False
            
        if all_valid:
            saved_instance = form.save()
            course_formset.instance = saved_instance
            course_formset.save()
            faq_formset.instance = saved_instance
            faq_formset.save()
            
            dt = parse_wp_datetime(mapped_data.get('created_at'))
            if dt:
                Institute.objects.filter(pk=saved_instance.pk).update(created_at=dt)
                
            return saved_instance, action_type
        else:
            errors = {}
            if form.errors: errors['form'] = form.errors
            if course_formset.errors: errors['courses'] = course_formset.errors
            if faq_formset.errors: errors['faq'] = faq_formset.errors
            raise ValueError(f"Validation failed: {errors}")

def _save_major(mapped_data, user):
    from apps.majors.models import Major
    from apps.dashboard.forms.major import (
        MajorForm, SubjectsTableFormSet, SalaryTableFormSet, 
        CountriesTableFormSet, MajorFAQFormSet, MajorAttachmentFormSet
    )
    from bs4 import BeautifulSoup
    import re
    
    form_initial = mapped_data['form_initial']
    slug = form_initial.get('slug', '').strip()
    from django.utils.text import slugify
    slug = slugify(slug, allow_unicode=True)
    form_initial['slug'] = slug
    
    existing_obj = Major.objects.filter(slug=slug).first()
    if not existing_obj:
        name_val = form_initial.get('name', '').strip()
        if name_val:
            existing_obj = Major.objects.filter(name__iexact=name_val).first()
            if existing_obj:
                slug = existing_obj.slug
                form_initial['slug'] = slug
                
    action_type = 'updated' if existing_obj else 'created'
    form_data = {**form_initial}
    
    # Resolve category ForeignKey
    from apps.majors.models import MajorCategory
    wp_categories = mapped_data.get('categories', [])
    matched_cat = None
    
    # 1. Try to find a MajorCategory that matches the WP categories exactly by name
    for cat_name in wp_categories:
        cat_obj = MajorCategory.objects.filter(name=cat_name).first()
        if cat_obj:
            matched_cat = cat_obj
            break
            
    # 2. Try to map based on major name keywords (same logic as migration 0013)
    if not matched_cat:
        name_lower = form_data.get('name', '').lower()
        if any(w in name_lower for w in ['طب', 'صيدلة', 'تمريض', 'علاج طبيعي', 'بصريات']):
            matched_cat = MajorCategory.objects.filter(name='الطب و الصحة').first()
        elif 'علاقات عامة' in name_lower or 'العلاقات العامة' in name_lower:
            matched_cat = MajorCategory.objects.filter(name='العلاقات العامة').first()
        elif 'هندسة' in name_lower and not any(w in name_lower for w in ['برمجيات', 'مالية']):
            matched_cat = MajorCategory.objects.filter(name='الهندسة').first()
        elif any(w in name_lower for w in ['حاسوب', 'ذكاء اصطناعي', 'بيانات', 'أمن سيبراني', 'برمجيات', 'تكنولوجيا المعلومات']):
            matched_cat = MajorCategory.objects.filter(name='علوم الحاسوب').first()
        elif any(w in name_lower for w in ['فندقة', 'سياحة', 'لوجستيات', 'أعمال', 'مالية', 'تجارة', 'محاسبة', 'اقتصاد', 'تسويق']):
            matched_cat = MajorCategory.objects.filter(name='العلوم الادارية و الاقتصادية').first()
        elif any(w in name_lower for w in ['تصميم', 'موسيقى', 'أزياء', 'رسوم متحركة', 'أفلام', 'فيديو']):
            matched_cat = MajorCategory.objects.filter(name='الفنون و التصميم').first()
        elif any(w in name_lower for w in ['نفس', 'اتصال', 'علاقات دولية', 'رياضية', 'انجليزية', 'أحياء', 'بيئية']):
            matched_cat = MajorCategory.objects.filter(name='الاداب و العلوم').first()
        elif 'قانون' in name_lower:
            matched_cat = MajorCategory.objects.filter(name='القانون').first()
        elif 'عن بعد' in name_lower:
            matched_cat = MajorCategory.objects.filter(name='التخصصات عن بعد في ماليزيا').first()
        elif 'وسائط' in name_lower:
            matched_cat = MajorCategory.objects.filter(name='الوسائط المتعددة').first()
        elif 'تحضيرية' in name_lower:
            matched_cat = MajorCategory.objects.filter(name='السنة التحضيرية').first()

    # 3. Fallback to old major_category mapping
    if not matched_cat:
        old_cat = form_data.get('major_category', 'other')
        mapping_old = {
            'medical': 'الطب و الصحة',
            'engineering': 'الهندسة',
            'cs': 'علوم الحاسوب',
            'business': 'العلوم الادارية و الاقتصادية',
            'science': 'الاداب و العلوم',
            'other': 'الوسائط المتعددة'
        }
        target_name = mapping_old.get(old_cat, 'الوسائط المتعددة')
        matched_cat = MajorCategory.objects.filter(name=target_name).first()

    # If still not found, fallback to first category or None
    if not matched_cat:
        matched_cat = MajorCategory.objects.first()

    if matched_cat:
        form_data['category'] = str(matched_cat.id)

    if 'publish_status' not in form_data or not form_data['publish_status']:
        form_data['publish_status'] = 'published'
    if not form_data.get('study_duration'):
        form_data['study_duration'] = 'غير محدد'
        
    for img_key, img_path in mapped_data.get('image_paths', {}).items():
        if img_path:
            form_data[f'imported_{img_key}_path'] = img_path
            
    # Subjects Table (Parse from faculties_raw_html using BeautifulSoup if available)
    faculties_raw_html = mapped_data.get('faculties_raw_html', '')
    parsed_subjects = []
    if faculties_raw_html:
        soup = BeautifulSoup(faculties_raw_html, 'html.parser')
        accordion_items = soup.find_all(class_='elementor-accordion-item')
        for item in accordion_items:
            title_el = item.find(class_='elementor-accordion-title')
            track_name = title_el.get_text(strip=True) if title_el else ''
            # Clean emojis from track name
            track_name = re.sub(r'^[\s\W\U00010000-\U0010ffff]+', '', track_name).strip()
            
            content_el = item.find(class_='elementor-tab-content')
            if not content_el:
                continue
            tables = content_el.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 2:
                        year = tds[0].get_text(strip=True)
                        subjects_text = tds[1].get_text(strip=True)
                        if year == "السنة" or "المواد" in year or "المواد" in subjects_text:
                            continue
                        if year and subjects_text:
                            parsed_subjects.append({
                                'track_name': track_name,
                                'academic_year': year,
                                'subjects': subjects_text,
                            })
                            
    existing_subjects = list(existing_obj.subjects_tables.all()) if existing_obj else []
    raw_imported_subjects = parsed_subjects if parsed_subjects else mapped_data.get('subjects_tables', [])
    
    # Clean, map key/value if needed, and filter imported subjects to prevent validation errors
    imported_subjects = []
    for item in raw_imported_subjects:
        academic_year = (item.get('academic_year') or item.get('key') or '').strip()
        subjects = (item.get('subjects') or item.get('value') or '').strip()
        track_name = (item.get('track_name') or '').strip()
        
        if not academic_year and not subjects:
            continue
        if not academic_year:
            academic_year = 'غير محدد'
        if not subjects:
            subjects = 'غير محدد'
        imported_subjects.append({
            'track_name': track_name,
            'academic_year': academic_year,
            'subjects': subjects,
        })
        
    subjects_count = len(existing_subjects)
    total_subjects = subjects_count + len(imported_subjects)
    
    form_data.update({
        'subjects_tables-TOTAL_FORMS': str(total_subjects),
        'subjects_tables-INITIAL_FORMS': str(subjects_count),
        'subjects_tables-MIN_NUM_FORMS': '0',
        'subjects_tables-MAX_NUM_FORMS': '1000',
    })
    for i, sub in enumerate(existing_subjects):
        form_data.update({
            f'subjects_tables-{i}-id': str(sub.id),
            f'subjects_tables-{i}-track_name': sub.track_name,
            f'subjects_tables-{i}-academic_year': sub.academic_year,
            f'subjects_tables-{i}-subjects': sub.subjects,
            f'subjects_tables-{i}-sort_order': str(sub.sort_order),
            f'subjects_tables-{i}-DELETE': 'on',
        })
    for j, item in enumerate(imported_subjects):
        i = subjects_count + j
        form_data.update({
            f'subjects_tables-{i}-id': '',
            f'subjects_tables-{i}-track_name': item['track_name'],
            f'subjects_tables-{i}-academic_year': item['academic_year'],
            f'subjects_tables-{i}-subjects': item['subjects'],
            f'subjects_tables-{i}-sort_order': str(j),
        })

    # Salary Table
    existing_salaries = list(existing_obj.salary_tables.all()) if existing_obj else []
    raw_imported_salaries = []
    
    def clean_text_tags(html_str):
        if not html_str:
            return ""
        # Strip all HTML tags
        return re.sub(r'<[^>]+>', '', html_str).strip()

    for sal in mapped_data.get('salary_tables', []):
        cells = sal.get('cells', [])
        if cells:
            if len(cells) >= 3:
                job_title = clean_text_tags(cells[0])
                job_description = cells[1].strip()  # description can have HTML/styling
                average_monthly_salary = clean_text_tags(cells[2])
            elif len(cells) == 2:
                job_title = clean_text_tags(cells[0])
                job_description = ''
                average_monthly_salary = clean_text_tags(cells[1])
            else:
                job_title = clean_text_tags(cells[0])
                job_description = ''
                average_monthly_salary = ''
        else:
            key = sal.get('key', '').strip()
            val = sal.get('value', '').strip()
            job_title = key
            job_description = ''
            average_monthly_salary = val

        if not job_title or job_title in ['المسمى الوظيفي', 'الوظيفة', 'المهنة'] or 'المسمى' in job_title:
            continue
            
        job_title = job_title.strip()
        average_monthly_salary = average_monthly_salary.strip()
        
        if not job_title and not average_monthly_salary:
            continue
        if not job_title:
            job_title = 'غير محدد'
        if not average_monthly_salary:
            average_monthly_salary = 'غير محدد'
            
        raw_imported_salaries.append({
            'job_title': job_title,
            'job_description': job_description,
            'average_monthly_salary': average_monthly_salary,
        })
        
    imported_salaries = raw_imported_salaries
    salaries_count = len(existing_salaries)
    total_salaries = salaries_count + len(imported_salaries)
    
    form_data.update({
        'salary_tables-TOTAL_FORMS': str(total_salaries),
        'salary_tables-INITIAL_FORMS': str(salaries_count),
        'salary_tables-MIN_NUM_FORMS': '0',
        'salary_tables-MAX_NUM_FORMS': '1000',
    })
    for i, sal in enumerate(existing_salaries):
        form_data.update({
            f'salary_tables-{i}-id': str(sal.id),
            f'salary_tables-{i}-job_title': sal.job_title,
            f'salary_tables-{i}-job_description': sal.job_description,
            f'salary_tables-{i}-average_monthly_salary': sal.average_monthly_salary,
            f'salary_tables-{i}-sort_order': str(sal.sort_order),
            f'salary_tables-{i}-DELETE': 'on',
        })
    for j, item in enumerate(imported_salaries):
        i = salaries_count + j
        form_data.update({
            f'salary_tables-{i}-id': '',
            f'salary_tables-{i}-job_title': item['job_title'],
            f'salary_tables-{i}-job_description': item['job_description'],
            f'salary_tables-{i}-average_monthly_salary': item['average_monthly_salary'],
            f'salary_tables-{i}-sort_order': str(j),
        })

    # Countries Table
    existing_countries = list(existing_obj.countries_tables.all()) if existing_obj else []
    raw_imported_countries = []
    for cnt in mapped_data.get('countries_tables', []):
        cells = cnt.get('cells', [])
        if cells:
            if len(cells) >= 4:
                destination = clean_text_tags(cells[0])
                study_duration = clean_text_tags(cells[1])
                annual_fees = clean_text_tags(cells[2])
                living_cost = clean_text_tags(cells[3])
            elif len(cells) == 3:
                destination = clean_text_tags(cells[0])
                study_duration = clean_text_tags(cells[1])
                annual_fees = clean_text_tags(cells[2])
                living_cost = ''
            elif len(cells) == 2:
                destination = clean_text_tags(cells[0])
                study_duration = ''
                annual_fees = clean_text_tags(cells[1])
                living_cost = ''
            else:
                destination = clean_text_tags(cells[0])
                study_duration = ''
                annual_fees = ''
                living_cost = ''
        else:
            key = cnt.get('key', '').strip()
            val = cnt.get('value', '').strip()
            destination = key
            study_duration = ''
            annual_fees = val
            living_cost = ''

        if not destination or destination in ['الوجهة', 'الدولة', 'البلد'] or 'البلد' in destination:
            continue
            
        destination = destination.strip()
        study_duration = study_duration.strip()
        annual_fees = annual_fees.strip()
        living_cost = living_cost.strip()
        
        if not destination and not study_duration and not annual_fees and not living_cost:
            continue
        if not destination:
            destination = 'غير محدد'
        if not study_duration:
            study_duration = 'غير محدد'
        if not annual_fees:
            annual_fees = 'غير محدد'
        if not living_cost:
            living_cost = 'غير محدد'
            
        raw_imported_countries.append({
            'destination': destination,
            'study_duration': study_duration,
            'annual_fees': annual_fees,
            'living_cost': living_cost,
        })
        
    imported_countries = raw_imported_countries
    countries_count = len(existing_countries)
    total_countries = countries_count + len(imported_countries)
    
    form_data.update({
        'countries_tables-TOTAL_FORMS': str(total_countries),
        'countries_tables-INITIAL_FORMS': str(countries_count),
        'countries_tables-MIN_NUM_FORMS': '0',
        'countries_tables-MAX_NUM_FORMS': '1000',
    })
    for i, cnt in enumerate(existing_countries):
        form_data.update({
            f'countries_tables-{i}-id': str(cnt.id),
            f'countries_tables-{i}-destination': cnt.destination,
            f'countries_tables-{i}-study_duration': cnt.study_duration,
            f'countries_tables-{i}-annual_fees': cnt.annual_fees,
            f'countries_tables-{i}-living_cost': cnt.living_cost,
            f'countries_tables-{i}-sort_order': str(cnt.sort_order),
            f'countries_tables-{i}-DELETE': 'on',
        })
    for j, item in enumerate(imported_countries):
        i = countries_count + j
        form_data.update({
            f'countries_tables-{i}-id': '',
            f'countries_tables-{i}-destination': item['destination'],
            f'countries_tables-{i}-study_duration': item['study_duration'],
            f'countries_tables-{i}-annual_fees': item['annual_fees'],
            f'countries_tables-{i}-living_cost': item['living_cost'],
            f'countries_tables-{i}-sort_order': str(j),
        })

    # FAQs
    existing_faqs = list(existing_obj.faqs.all()) if existing_obj else []
    raw_imported_faqs = mapped_data.get('faqs_data', [])
    imported_faqs = []
    for item in raw_imported_faqs:
        q = (item.get('question') or '').strip()
        a = (item.get('answer') or '').strip()
        if not q and not a:
            continue
        if not q:
            q = 'غير محدد'
        if not a:
            a = 'غير محدد'
        imported_faqs.append({
            'question': q,
            'answer': a,
        })
        
    faqs_count = len(existing_faqs)
    total_faqs = faqs_count + len(imported_faqs)
    
    form_data.update({
        'faqs-TOTAL_FORMS': str(total_faqs),
        'faqs-INITIAL_FORMS': str(faqs_count),
        'faqs-MIN_NUM_FORMS': '0',
        'faqs-MAX_NUM_FORMS': '1000',
    })
    for i, faq in enumerate(existing_faqs):
        form_data.update({
            f'faqs-{i}-id': str(faq.id),
            f'faqs-{i}-question': faq.question,
            f'faqs-{i}-answer': faq.answer,
            f'faqs-{i}-sort_order': str(faq.sort_order),
            f'faqs-{i}-DELETE': 'on',
        })
    for j, item in enumerate(imported_faqs):
        i = faqs_count + j
        form_data.update({
            f'faqs-{i}-id': '',
            f'faqs-{i}-question': item['question'],
            f'faqs-{i}-answer': item['answer'],
            f'faqs-{i}-sort_order': str(j),
        })

    # Attachments
    existing_attachments = list(existing_obj.attachments.all()) if existing_obj else []
    attachments_count = len(existing_attachments)
    form_data.update({
        'attachments-TOTAL_FORMS': str(attachments_count),
        'attachments-INITIAL_FORMS': str(attachments_count),
        'attachments-MIN_NUM_FORMS': '0',
        'attachments-MAX_NUM_FORMS': '1000',
    })
    for i, att in enumerate(existing_attachments):
        form_data.update({
            f'attachments-{i}-id': str(att.id),
            f'attachments-{i}-title': att.title,
            f'attachments-{i}-DELETE': 'on',
        })

    with transaction.atomic():
        form = MajorForm(form_data, instance=existing_obj)
        for field_name in ['main_image', 'og_image']:
            if field_name in form.fields:
                form.fields[field_name].required = False
        subjects_formset = SubjectsTableFormSet(form_data, instance=existing_obj)
        salary_formset = SalaryTableFormSet(form_data, instance=existing_obj)
        countries_formset = CountriesTableFormSet(form_data, instance=existing_obj)
        faqs_formset = MajorFAQFormSet(form_data, instance=existing_obj)
        attachments_formset = MajorAttachmentFormSet(form_data, instance=existing_obj)
        
        all_valid = (
            form.is_valid() and 
            subjects_formset.is_valid() and 
            salary_formset.is_valid() and 
            countries_formset.is_valid() and
            faqs_formset.is_valid() and
            attachments_formset.is_valid()
        )
        if all_valid:
            saved_instance = form.save()
            
            subjects_formset.instance = saved_instance
            subjects_formset.save()
            
            salary_formset.instance = saved_instance
            salary_formset.save()
            
            countries_formset.instance = saved_instance
            countries_formset.save()
            
            faqs_formset.instance = saved_instance
            faqs_formset.save()
            
            attachments_formset.instance = saved_instance
            attachments_formset.save()
            
            # Smart link existing programs to this major
            from apps.universities.models import Program
            from django.db.models import Q
            
            major_name = saved_instance.name.strip()
            keywords = [k for k in major_name.split() if len(k) > 2 and k not in ['في', 'من', 'عن', 'على', 'إلى', 'مع']]
            
            english_terms = set()
            for sub in imported_subjects:
                subj_text = sub.get('subjects', '')
                track = sub.get('track_name', '')
                matches = re.findall(r'\(([^)]+)\)', subj_text + " " + track)
                for match in matches:
                    if len(match) > 3:
                        english_terms.add(match.strip())
                        
            term_queries = Q()
            for kw in keywords:
                term_queries |= Q(name__icontains=kw)
            for term in english_terms:
                term_queries |= Q(name__icontains=term)
                
            if keywords or english_terms:
                matching_programs = Program.objects.filter(term_queries).filter(major__isnull=True)
                for prog in matching_programs:
                    prog.major = saved_instance
                    prog.save()
            
            dt = parse_wp_datetime(mapped_data.get('created_at'))
            if dt:
                Major.objects.filter(pk=saved_instance.pk).update(created_at=dt)
            
            return saved_instance, action_type
        else:
            errors = {}
            if form.errors: errors['form'] = form.errors
            if subjects_formset.errors: errors['subjects'] = subjects_formset.errors
            if salary_formset.errors: errors['salary'] = salary_formset.errors
            if countries_formset.errors: errors['countries'] = countries_formset.errors
            if faqs_formset.errors: errors['faqs'] = faqs_formset.errors
            if attachments_formset.errors: errors['attachments'] = attachments_formset.errors
            raise ValueError(f"Validation failed: {errors}")

def _save_article(mapped_data, user):
    from apps.articles.models import Article
    from apps.dashboard.forms.article import ArticleForm, ArticleFAQFormSet
    
    form_initial = mapped_data['form_initial']
    slug = form_initial.get('slug', '').strip()
    from django.utils.text import slugify
    slug = slugify(slug, allow_unicode=True)
    form_initial['slug'] = slug
    
    existing_obj = Article.objects.filter(slug=slug).first()
    action_type = 'updated' if existing_obj else 'created'
    form_data = {**form_initial}
    if 'publish_status' not in form_data or not form_data['publish_status']:
        form_data['publish_status'] = 'published'
    for img_key, img_path in mapped_data.get('image_paths', {}).items():
        if img_path:
            key = 'featured_image' if img_key == 'main_image' else img_key
            form_data[f'imported_{key}_path'] = img_path
            
    # Article FAQs
    existing_faqs = list(existing_obj.faqs.all()) if existing_obj else []
    faqs_count = len(existing_faqs)
    
    raw_imported_faqs = mapped_data.get('faqs_data', [])
    imported_faqs = []
    for faq_item in raw_imported_faqs:
        q = (faq_item.get('question') or '').strip()
        a = (faq_item.get('answer') or '').strip()
        if not q and not a:
            continue
        if not q:
            q = 'غير محدد'
        if not a:
            a = 'غير محدد'
        imported_faqs.append({'question': q, 'answer': a})
        
    total_faqs = faqs_count + len(imported_faqs)
    
    form_data.update({
        'faqs-TOTAL_FORMS': str(total_faqs),
        'faqs-INITIAL_FORMS': str(faqs_count),
        'faqs-MIN_NUM_FORMS': '0',
        'faqs-MAX_NUM_FORMS': '1000',
    })
    for i, faq in enumerate(existing_faqs):
        form_data.update({
            f'faqs-{i}-id': str(faq.id),
            f'faqs-{i}-question': faq.question,
            f'faqs-{i}-answer': faq.answer,
            f'faqs-{i}-sort_order': str(faq.sort_order),
            f'faqs-{i}-DELETE': 'on',
        })
    for j, faq_item in enumerate(imported_faqs):
        i = faqs_count + j
        form_data.update({
            f'faqs-{i}-id': '',
            f'faqs-{i}-question': faq_item['question'],
            f'faqs-{i}-answer': faq_item['answer'],
            f'faqs-{i}-sort_order': str(i),
        })
            
    with transaction.atomic():
        form = ArticleForm(form_data, instance=existing_obj)
        for field_name in ['featured_image', 'og_image']:
            if field_name in form.fields:
                form.fields[field_name].required = False
        faq_formset = ArticleFAQFormSet(form_data, instance=existing_obj)
        
        all_valid = form.is_valid() and faq_formset.is_valid()
        if all_valid:
            # Sanitize HTML content before saving (same as views.py)
            from apps.html_editor.sanitizer import sanitize_article_html
            instance = form.save(commit=False)
            instance.content = sanitize_article_html(instance.content)
            
            dt = parse_wp_datetime(mapped_data.get('created_at'))
            if dt:
                instance.publish_date = dt
                
            instance.save()
            form.save_m2m()
            
            faq_formset.instance = instance
            faq_formset.save()
            
            return instance, action_type
        else:
            errors = {}
            if form.errors: errors['form'] = form.errors
            if faq_formset.errors: errors['faq'] = faq_formset.errors
            raise ValueError(f"Validation failed: {errors}")
