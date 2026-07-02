from django.db import migrations

def copy_hardcoded_fees_includes(apps, schema_editor):
    Institute = apps.get_model('institutes', 'Institute')
    default_includes = 'تكاليف الدراسة، ورسوم تأشيرة الطالب، ورسوم التأمين الصحي، واختبار تحديد المستوى، والتوصيل من المطار.'
    for inst in Institute.objects.all():
        if not inst.fees_includes:
            inst.fees_includes = default_includes
            inst.save()

def reverse_copy_hardcoded_fees_includes(apps, schema_editor):
    Institute = apps.get_model('institutes', 'Institute')
    default_includes = 'تكاليف الدراسة، ورسوم تأشيرة الطالب، ورسوم التأمين الصحي، واختبار تحديد المستوى، والتوصيل من المطار.'
    for inst in Institute.objects.all():
        if inst.fees_includes == default_includes:
            inst.fees_includes = ''
            inst.save()

class Migration(migrations.Migration):
    dependencies = [
        ('institutes', '0020_institute_fees_excludes_institute_fees_includes'),
    ]
    operations = [
        migrations.RunPython(copy_hardcoded_fees_includes, reverse_copy_hardcoded_fees_includes),
    ]
