import os
import django
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.db import transaction
from apps.universities.models import University, Faculty, Program, UniversityFAQ
from apps.institutes.models import Institute, Course
from apps.articles.models import Article, Category, Tag
from apps.majors.models import Major, SubjectsTable, SalaryTable, CountriesTable
from apps.core.models import MediaFile
from apps.importer.services.wp_client import WPImporterClient
from apps.importer.services.image_downloader import download_and_optimize_image
from apps.importer.services.content_mapper import ContentMapper

def clean_database():
    print("--- Cleaning local database ---")
    
    # 1. Delete Universities and cascading elements
    u_count = University.objects.count()
    f_count = Faculty.objects.count()
    p_count = Program.objects.count()
    faq_count = UniversityFAQ.objects.count()
    
    University.objects.all().delete()
    print(f"Deleted {u_count} Universities, {f_count} Faculties, {p_count} Programs, {faq_count} FAQs.")
    
    # 2. Delete Institutes and cascading elements
    inst_count = Institute.objects.count()
    course_count = Course.objects.count()
    Institute.objects.all().delete()
    print(f"Deleted {inst_count} Institutes, {course_count} Courses.")
    
    # 3. Delete Articles, Categories, Tags
    art_count = Article.objects.count()
    cat_count = Category.objects.count()
    tag_count = Tag.objects.count()
    Article.objects.all().delete()
    Category.objects.all().delete()
    Tag.objects.all().delete()
    print(f"Deleted {art_count} Articles, {cat_count} Categories, {tag_count} Tags.")
    
    # 4. Delete Majors and cascading elements
    maj_count = Major.objects.count()
    sub_count = SubjectsTable.objects.count()
    sal_count = SalaryTable.objects.count()
    cnt_count = CountriesTable.objects.count()
    Major.objects.all().delete()
    print(f"Deleted {maj_count} Majors, {sub_count} Subject Tables, {sal_count} Salary Tables, {cnt_count} Country Tables.")
    
    # 5. Delete Media Files to start fresh
    media_count = MediaFile.objects.count()
    MediaFile.objects.all().delete()
    print(f"Deleted {media_count} Media Library Files.")
    print("Database cleaned successfully!\n")

def import_university(slug):
    print(f"Importing university from WordPress with slug: {slug} ...")
    
    # 1. Fetch data from WordPress API
    client = WPImporterClient()
    try:
        wp_data = client.fetch(slug)
        print("WordPress data fetched successfully.")
    except Exception as e:
        print(f"Error fetching data from WP: {e}")
        return
        
    content_type = wp_data.get('content_type', 'university')
    
    # 2. Resolve image source types
    main_image_source = MediaFile.SourceType.UNIVERSITY_IMAGE
    
    # 3. Download images
    images_to_download = wp_data.get('images', {})
    downloaded_images = {}
    image_warnings = []
    
    print("Downloading and optimizing images...")
    # Download Logo
    logo_data = images_to_download.get('logo', {})
    if logo_data and logo_data.get('url'):
        media_file, warning = download_and_optimize_image(
            url=logo_data['url'],
            alt_text=logo_data.get('alt', ''),
            caption=logo_data.get('caption', ''),
            description=logo_data.get('description', ''),
            title=logo_data.get('title', ''),
            source_type=MediaFile.SourceType.UNIVERSITY_LOGO
        )
        if media_file:
            downloaded_images['logo'] = media_file
            print(f"Logo downloaded: {media_file.file.name}")
        else:
            image_warnings.append(warning)
            print(f"Logo warning: {warning}")

    # Download Main Image
    main_img_data = images_to_download.get('main_image', {})
    if main_img_data and main_img_data.get('url'):
        media_file, warning = download_and_optimize_image(
            url=main_img_data['url'],
            alt_text=main_img_data.get('alt', ''),
            caption=main_img_data.get('caption', ''),
            description=main_img_data.get('description', ''),
            title=main_img_data.get('title', ''),
            source_type=main_image_source
        )
        if media_file:
            downloaded_images['main_image'] = media_file
            print(f"Main Image downloaded: {media_file.file.name}")
        else:
            image_warnings.append(warning)
            print(f"Main Image warning: {warning}")

    # Download OG Image
    og_img_data = images_to_download.get('og_image', {})
    if og_img_data and og_img_data.get('url'):
        media_file, warning = download_and_optimize_image(
            url=og_img_data['url'],
            alt_text=og_img_data.get('alt', ''),
            caption=og_img_data.get('caption', ''),
            description=og_img_data.get('description', ''),
            title=og_img_data.get('title', ''),
            source_type=MediaFile.SourceType.EDITOR
        )
        if media_file:
            downloaded_images['og_image'] = media_file
            print(f"OG Image downloaded: {media_file.file.name}")
        else:
            image_warnings.append(warning)
            print(f"OG Image warning: {warning}")

    # 4. Map content schema
    print("Mapping content schema...")
    mapper = ContentMapper()
    mapped_data = mapper.map_data(wp_data, downloaded_images, image_warnings)
    form_initial = mapped_data['form_initial']
    
    # 5. Save University instance
    with transaction.atomic():
        u = University()
        for field, val in form_initial.items():
            if hasattr(u, field):
                setattr(u, field, val)
        
        # Attach image fields
        if 'logo' in downloaded_images:
            u.logo = downloaded_images['logo'].file.name
        if 'main_image' in downloaded_images:
            u.main_image = downloaded_images['main_image'].file.name
        if 'og_image' in downloaded_images:
            u.og_image = downloaded_images['og_image'].file.name
            
        u.publish_status = 'published'
        u.save()
        print(f"University '{u.name}' saved to database (ID: {u.id}).")
        
        # 6. Save Faculties & Programs
        faculties_data = mapped_data.get('faculties_data', [])
        fac_count = 0
        prog_count = 0
        for fac_idx, fac_item in enumerate(faculties_data):
            fac_name = fac_item.get('name', '').strip()
            if not fac_name:
                continue
            faculty = Faculty.objects.create(
                university=u,
                name=fac_name,
                sort_order=fac_idx
            )
            fac_count += 1
            
            programs_data = fac_item.get('programs', [])
            for prog_idx, prog_item in enumerate(programs_data):
                prog_name = prog_item.get('name', '').strip()
                if not prog_name:
                    continue
                Program.objects.create(
                    faculty=faculty,
                    name=prog_name,
                    duration=prog_item.get('duration', '').strip(),
                    tuition_fees=prog_item.get('tuition_fees', '').strip(),
                    sort_order=prog_idx
                )
                prog_count += 1
                
        print(f"Created {fac_count} Faculties with {prog_count} Programs.")

        # 7. Save FAQs
        faqs_data = mapped_data.get('faqs_data', [])
        faq_created = 0
        for faq_idx, faq_item in enumerate(faqs_data):
            q = faq_item.get('question', '').strip()
            ans = faq_item.get('answer', '').strip()
            if not q or not ans:
                continue
            UniversityFAQ.objects.create(
                university=u,
                question=q,
                answer=ans,
                sort_order=faq_idx
            )
            faq_created += 1
            
        print(f"Created {faq_created} FAQs.")
        print(f"Import of completed successfully!\n")

def main():
    clean_database()
    
    # Read slugs from imported_links_summary.md
    slugs = []
    summary_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imported_links_summary.md")
    
    if os.path.exists(summary_path):
        print(f"Reading university slugs from: {summary_path}")
        with open(summary_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        in_universities = False
        for line in lines:
            if "## الجامعات" in line or "## Universities" in line:
                in_universities = True
                continue
            if "## المعاهد" in line or "## Institutes" in line:
                in_universities = False
                break
            if in_universities:
                parts = line.strip().split('|')
                if len(parts) >= 5:
                    slug_col = parts[-2].strip()
                    if slug_col.startswith('`') and slug_col.endswith('`'):
                        slugs.append(slug_col.strip('`').strip())
    else:
        print("Error: imported_links_summary.md not found!")
        return
        
    print(f"Found {len(slugs)} university slugs to import.")
    
    for idx, slug in enumerate(slugs, 1):
        print(f"[{idx}/{len(slugs)}] Starting import of slug: {slug} ...")
        try:
            import_university(slug)
        except Exception as e:
            print(f"Failed to import slug '{slug}': {e}")

if __name__ == "__main__":
    main()
