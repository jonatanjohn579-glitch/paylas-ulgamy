from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_storage_quota'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroom',
            name='storage_quota',
            field=models.BigIntegerField(default=5368709120, help_text='Class storage quota in bytes'),
        ),
    ]
