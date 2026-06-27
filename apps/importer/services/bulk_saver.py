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
    action_type = 'updated' if existing_obj else 'created'
    form_data = {**form_initial}
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
    imported_faqs = mapped_data.get('faqs_data', [])
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
            f'faqs-{i}-question': faq_item.get('question', ''),
            f'faqs-{i}-answer': faq_item.get('answer', ''),
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
                
        return saved_instance, action_type

def _save_institute(mapped_data, user):
    from apps.institutes.models import Institute
    from apps.dashboard.forms.institute import InstituteForm, CourseFormSet
    
    form_initial = mapped_data['form_initial']
    slug = form_initial.get('slug', '').strip()
    from django.utils.text import slugify
    slug = slugify(slug, allow_unicode=True)
    form_initial['slug'] = slug
    
    existing_obj = Institute.objects.filter(slug=slug).first()
    action_type = 'updated' if existing_obj else 'created'
    form_data = {**form_initial}
    if 'publish_status' not in form_data or not form_data['publish_status']:
        form_data['publish_status'] = 'published'
    for img_key, img_path in mapped_data.get('image_paths', {}).items():
        if img_path:
            form_data[f'imported_{img_key}_path'] = img_path
            
    # Preserve existing courses (since importer doesn't fetch courses for institutes)
    existing_courses = list(existing_obj.courses.all()) if existing_obj else []
    courses_count = len(existing_courses)
    
    form_data.update({
        'courses-TOTAL_FORMS': str(courses_count),
        'courses-INITIAL_FORMS': str(courses_count),
        'courses-MIN_NUM_FORMS': '0',
        'courses-MAX_NUM_FORMS': '1000',
    })
    for i, course in enumerate(existing_courses):
        form_data.update({
            f'courses-{i}-id': str(course.id),
            f'courses-{i}-name': course.name,
            f'courses-{i}-duration': course.duration,
            f'courses-{i}-fees': course.fees,
            f'courses-{i}-description': course.description,
            f'courses-{i}-notes': course.notes,
        })

    with transaction.atomic():
        form = InstituteForm(form_data, instance=existing_obj)
        for field_name in ['main_image', 'og_image']:
            if field_name in form.fields:
                form.fields[field_name].required = False
        course_formset = CourseFormSet(form_data, instance=existing_obj)
        
        if form.is_valid() and course_formset.is_valid():
            saved_instance = form.save()
            course_formset.instance = saved_instance
            course_formset.save()
            return saved_instance, action_type
        else:
            errors = {}
            if form.errors: errors['form'] = form.errors
            if course_formset.errors: errors['courses'] = course_formset.errors
            raise ValueError(f"Validation failed: {errors}")

def _save_major(mapped_data, user):
    from apps.majors.models import Major
    from apps.dashboard.forms.major import MajorForm, SubjectsTableFormSet, SalaryTableFormSet, CountriesTableFormSet
    
    form_initial = mapped_data['form_initial']
    slug = form_initial.get('slug', '').strip()
    from django.utils.text import slugify
    slug = slugify(slug, allow_unicode=True)
    form_initial['slug'] = slug
    
    existing_obj = Major.objects.filter(slug=slug).first()
    action_type = 'updated' if existing_obj else 'created'
    form_data = {**form_initial}
    if 'publish_status' not in form_data or not form_data['publish_status']:
        form_data['publish_status'] = 'published'
    for img_key, img_path in mapped_data.get('image_paths', {}).items():
        if img_path:
            form_data[f'imported_{img_key}_path'] = img_path
            
    # Subjects Table
    existing_subjects = list(existing_obj.subjects_tables.all()) if existing_obj else []
    imported_subjects = mapped_data.get('subjects_tables', [])
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
            f'subjects_tables-{i}-academic_year': sub.academic_year,
            f'subjects_tables-{i}-subjects': sub.subjects,
            f'subjects_tables-{i}-DELETE': 'on',
        })
    for j, item in enumerate(imported_subjects):
        i = subjects_count + j
        form_data.update({
            f'subjects_tables-{i}-id': '',
            f'subjects_tables-{i}-academic_year': item.get('academic_year', ''),
            f'subjects_tables-{i}-subjects': item.get('subjects', ''),
        })

    # Salary Table
    existing_salaries = list(existing_obj.salary_tables.all()) if existing_obj else []
    imported_salaries = mapped_data.get('salary_tables', [])
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
            f'salary_tables-{i}-average_monthly_salary': sal.average_monthly_salary,
            f'salary_tables-{i}-DELETE': 'on',
        })
    for j, item in enumerate(imported_salaries):
        i = salaries_count + j
        form_data.update({
            f'salary_tables-{i}-id': '',
            f'salary_tables-{i}-job_title': item.get('job_title', ''),
            f'salary_tables-{i}-average_monthly_salary': item.get('average_monthly_salary', ''),
        })

    # Countries Table
    existing_countries = list(existing_obj.countries_tables.all()) if existing_obj else []
    imported_countries = mapped_data.get('countries_tables', [])
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
            f'countries_tables-{i}-annual_fees': cnt.annual_fees,
            f'countries_tables-{i}-DELETE': 'on',
        })
    for j, item in enumerate(imported_countries):
        i = countries_count + j
        form_data.update({
            f'countries_tables-{i}-id': '',
            f'countries_tables-{i}-destination': item.get('destination', ''),
            f'countries_tables-{i}-annual_fees': item.get('annual_fees', ''),
        })

    with transaction.atomic():
        form = MajorForm(form_data, instance=existing_obj)
        for field_name in ['main_image', 'og_image']:
            if field_name in form.fields:
                form.fields[field_name].required = False
        subjects_formset = SubjectsTableFormSet(form_data, instance=existing_obj)
        salary_formset = SalaryTableFormSet(form_data, instance=existing_obj)
        countries_formset = CountriesTableFormSet(form_data, instance=existing_obj)
        
        all_valid = (
            form.is_valid() and 
            subjects_formset.is_valid() and 
            salary_formset.is_valid() and 
            countries_formset.is_valid()
        )
        if all_valid:
            saved_instance = form.save()
            
            subjects_formset.instance = saved_instance
            subjects_formset.save()
            
            salary_formset.instance = saved_instance
            salary_formset.save()
            
            countries_formset.instance = saved_instance
            countries_formset.save()
            
            return saved_instance, action_type
        else:
            errors = {}
            if form.errors: errors['form'] = form.errors
            if subjects_formset.errors: errors['subjects'] = subjects_formset.errors
            if salary_formset.errors: errors['salary'] = salary_formset.errors
            if countries_formset.errors: errors['countries'] = countries_formset.errors
            raise ValueError(f"Validation failed: {errors}")

def _save_article(mapped_data, user):
    from apps.articles.models import Article
    from apps.dashboard.forms.article import ArticleForm
    
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
            
    with transaction.atomic():
        form = ArticleForm(form_data, instance=existing_obj)
        for field_name in ['featured_image', 'og_image']:
            if field_name in form.fields:
                form.fields[field_name].required = False
        if form.is_valid():
            # Sanitize HTML content before saving (same as views.py)
            from apps.html_editor.sanitizer import sanitize_article_html
            instance = form.save(commit=False)
            instance.content = sanitize_article_html(instance.content)
            instance.save()
            form.save_m2m()
            return instance, action_type
        else:
            raise ValueError(f"Validation failed: {form.errors}")
