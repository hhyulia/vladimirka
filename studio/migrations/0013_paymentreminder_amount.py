from decimal import Decimal

from django.db import migrations, models

import studio.models


class Migration(migrations.Migration):

    dependencies = [
        ('studio', '0012_paymentreminder_paid_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentreminder',
            name='amount',
            field=models.DecimalField(
                decimal_places=2,
                default=studio.models.default_reminder_amount,
                help_text='Индивидуальная сумма для этого ученика; уходит в ЮKassa при онлайн-оплате.',
                max_digits=10,
                verbose_name='Сумма к оплате, ₽',
            ),
        ),
    ]
