from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0009_merge_0008_auto_20250905_1452_0008_auto_20250905_1453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='time_in',
            field=models.TimeField(),  # wala na auto_now_add
        ),
    ]