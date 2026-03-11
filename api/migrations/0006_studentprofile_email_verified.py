from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_notification_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='email_verified',
            field=models.BooleanField(default=True),
        ),
    ]
