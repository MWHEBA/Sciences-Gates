from django.db import migrations, models
import json

def convert_to_json(apps, schema_editor):
    Major = apps.get_model('majors', 'Major')
    for major in Major.objects.all():
        val = major.tuition_fees
        if not val:
            major.tuition_fees = '[]'
            major.save()
            continue
            
        # Check if it's already a valid JSON list/dict
        if isinstance(val, (list, dict)):
            continue
            
        if isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    continue
            except (json.JSONDecodeError, TypeError):
                pass
                
            # It's a legacy string, convert it to a structured JSON table:
            new_val = [{
                "title": "الرسوم الدراسية",
                "headers": ["الرسوم"],
                "rows": [[val]]
            }]
            major.tuition_fees = json.dumps(new_val, ensure_ascii=False)
            major.save()


class Migration(migrations.Migration):

    dependencies = [
        ('majors', '0016_alter_countriestable_annual_fees_and_more'),
    ]

    operations = [
        migrations.RunPython(convert_to_json, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='major',
            name='tuition_fees',
            field=models.JSONField(blank=True, default=list, help_text='جداول الرسوم الدراسية للجامعات بصيغة JSON', verbose_name='الرسوم الدراسية'),
        ),
    ]
