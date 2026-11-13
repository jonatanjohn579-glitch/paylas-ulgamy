# Generated migration for storage_quota field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='storage_quota',
            field=models.BigIntegerField(default=1073741824, help_text='Maximum storage allowed in bytes (default: 1GB)'),
        ),
    ]
