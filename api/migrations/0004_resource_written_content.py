from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_badge_studentprofile_current_level_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='written_content',
            field=models.TextField(blank=True, default=''),
        ),
    ]
