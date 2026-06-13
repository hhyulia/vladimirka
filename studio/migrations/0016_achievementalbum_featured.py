# Generated for achievements page redesign

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studio', '0015_trainer_alter_weeklyclass_teacher_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='achievementalbum',
            name='is_featured',
            field=models.BooleanField(
                default=False,
                help_text='Отметьте, чтобы альбом попал в блок из 4 крупных карточек вверху страницы «Достижения». Порядок карточек задаётся полем «Порядок».',
                verbose_name='Показывать в карточках достижений',
            ),
        ),
        migrations.AddField(
            model_name='achievementalbum',
            name='featured_text',
            field=models.TextField(
                blank=True,
                help_text='Короткое описание для крупной карточки вверху страницы. Если пусто — используется обычное «Описание».',
                verbose_name='Текст для карточки достижения',
            ),
        ),
    ]
