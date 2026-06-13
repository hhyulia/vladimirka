from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('studio', '0016_achievementalbum_featured'),
    ]

    operations = [
        migrations.AddField(
            model_name='achievementalbum',
            name='image_focus_x',
            field=models.PositiveSmallIntegerField(
                default=50,
                help_text='0 — левый край, 50 — центр, 100 — правый край видимой области.',
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                verbose_name='Фокус по горизонтали (%)',
            ),
        ),
        migrations.AddField(
            model_name='achievementalbum',
            name='image_focus_y',
            field=models.PositiveSmallIntegerField(
                default=20,
                help_text='0 — верх, 50 — центр, 100 — низ. Для портретов обычно 15–30.',
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                verbose_name='Фокус по вертикали (%)',
            ),
        ),
        migrations.AddField(
            model_name='achievementphoto',
            name='image_focus_x',
            field=models.PositiveSmallIntegerField(
                default=50,
                help_text='0 — левый край, 50 — центр, 100 — правый край видимой области.',
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                verbose_name='Фокус по горизонтали (%)',
            ),
        ),
        migrations.AddField(
            model_name='achievementphoto',
            name='image_focus_y',
            field=models.PositiveSmallIntegerField(
                default=20,
                help_text='0 — верх, 50 — центр, 100 — низ. Для портретов обычно 15–30.',
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                verbose_name='Фокус по вертикали (%)',
            ),
        ),
        migrations.AddField(
            model_name='dancedirection',
            name='image_focus_x',
            field=models.PositiveSmallIntegerField(
                default=50,
                help_text='0 — левый край, 50 — центр, 100 — правый край видимой области.',
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                verbose_name='Фокус по горизонтали (%)',
            ),
        ),
        migrations.AddField(
            model_name='dancedirection',
            name='image_focus_y',
            field=models.PositiveSmallIntegerField(
                default=20,
                help_text='0 — верх, 50 — центр, 100 — низ. Для портретов обычно 15–30.',
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                verbose_name='Фокус по вертикали (%)',
            ),
        ),
        migrations.AddField(
            model_name='trainer',
            name='image_focus_x',
            field=models.PositiveSmallIntegerField(
                default=50,
                help_text='0 — левый край, 50 — центр, 100 — правый край видимой области.',
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                verbose_name='Фокус по горизонтали (%)',
            ),
        ),
        migrations.AddField(
            model_name='trainer',
            name='image_focus_y',
            field=models.PositiveSmallIntegerField(
                default=20,
                help_text='0 — верх, 50 — центр, 100 — низ. Для портретов обычно 15–30.',
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                verbose_name='Фокус по вертикали (%)',
            ),
        ),
    ]
