from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0010_alter_lead_address_alter_lead_email_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="is_suspected_spam",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="تم حفظها لأن حقل الحماية (honeypot) امتلأ؛ تُؤرشف تلقائياً ولا تُرسل لها إشعارات",
                verbose_name="مشتبه به كسبام",
            ),
        ),
    ]
