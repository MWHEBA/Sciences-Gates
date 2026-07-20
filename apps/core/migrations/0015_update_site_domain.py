from django.db import migrations

def update_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(id=1).update(
        domain='sciencesgates.com',
        name='Sciences Gates'
    )

def reverse_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(id=1).update(
        domain='example.com',
        name='example.com'
    )

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_userprofile_receive_inquiry_emails_and_more'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(update_site_domain, reverse_code=reverse_site_domain),
    ]
