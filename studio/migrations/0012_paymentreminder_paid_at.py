from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def mark_hidden_as_paid(apps, schema_editor):
    PaymentReminder = apps.get_model('studio', 'PaymentReminder')
    now = timezone.now()
    for reminder in PaymentReminder.objects.filter(show_reminder=False, paid_at__isnull=True):
        reminder.paid_at = reminder.updated_at or now
        reminder.save(update_fields=['paid_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('studio', '0011_lesson_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentreminder',
            name='paid_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Заполняется при онлайн-оплате или когда администратор снимает напоминание.',
                null=True,
                verbose_name='Оплачено',
            ),
        ),
        migrations.AddField(
            model_name='paymentreminder',
            name='lesson_payment',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payment_reminders',
                to='studio.lessonpayment',
                verbose_name='Платёж ЮKassa',
            ),
        ),
        migrations.CreateModel(
            name='PaidPaymentReminder',
            fields=[],
            options={
                'verbose_name': 'Оплаченное занятие',
                'verbose_name_plural': 'Оплаченные занятия',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('studio.paymentreminder',),
        ),
        migrations.RunPython(mark_hidden_as_paid, migrations.RunPython.noop),
    ]
