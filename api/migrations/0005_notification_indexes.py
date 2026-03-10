from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_resource_written_content'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', '-created_at'], name='api_notific_recipie_f34798_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read', '-created_at'], name='api_notific_recipie_286696_idx'),
        ),
    ]
