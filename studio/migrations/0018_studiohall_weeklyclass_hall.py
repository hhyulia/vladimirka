from django.db import migrations, models
import django.db.models.deletion


HALLS = (
    ('Зал №1', 'г. Балашиха, ЖК «Акварели» проспект Ленина 32Д', 1),
    ('Зал №2', 'г. Балашиха, проспект Ленина д.20', 2),
    ('Зал №3', 'г. Балашиха, ул. Фадеева д.8', 3),
)


def seed_halls(apps, schema_editor):
    StudioHall = apps.get_model('studio', 'StudioHall')
    for name, address, sort_order in HALLS:
        StudioHall.objects.get_or_create(
            address=address,
            defaults={'name': name, 'sort_order': sort_order, 'is_active': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('studio', '0017_image_focus_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudioHall',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Например: «Зал №1» — для списка в админке.', max_length=120, verbose_name='Краткое название')),
                ('address', models.CharField(max_length=300, verbose_name='Адрес')),
                ('sort_order', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Зал',
                'verbose_name_plural': 'Залы',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='weeklyclass',
            name='hall',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='weekly_classes',
                to='studio.studiohall',
                verbose_name='Зал',
            ),
        ),
        migrations.RunPython(seed_halls, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='weeklyclass',
            name='room',
        ),
    ]
