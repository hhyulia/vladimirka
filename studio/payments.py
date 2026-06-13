from __future__ import annotations

import logging
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from .models import LessonPayment, PaymentReminder, get_active_payment_reminder

logger = logging.getLogger(__name__)


def is_yookassa_configured() -> bool:
    return bool(getattr(settings, 'YOOKASSA_ENABLED', False))


def _configure_client() -> None:
    from yookassa import Configuration

    Configuration.configure(settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY)


def _amount_value(amount: Decimal) -> str:
    return f'{amount.quantize(Decimal("0.01")):.2f}'


def create_remote_payment(local_payment: LessonPayment):
    from yookassa import Payment

    _configure_client()
    return Payment.create({
        'amount': {
            'value': _amount_value(local_payment.amount),
            'currency': 'RUB',
        },
        'confirmation': {
            'type': 'redirect',
            'return_url': settings.YOOKASSA_RETURN_URL,
        },
        'capture': True,
        'description': local_payment.description[:128],
        'metadata': {
            'lesson_payment_id': str(local_payment.pk),
        },
    })


def fetch_remote_payment(yookassa_payment_id: str):
    from yookassa import Payment

    _configure_client()
    return Payment.find_one(yookassa_payment_id)


def apply_remote_status(local_payment: LessonPayment, remote_status: str) -> LessonPayment:
    if remote_status == 'succeeded' and local_payment.status != LessonPayment.Status.SUCCEEDED:
        local_payment.status = LessonPayment.Status.SUCCEEDED
        local_payment.paid_at = timezone.now()
        local_payment.save(update_fields=['status', 'paid_at'])
        reminder = get_active_payment_reminder(local_payment.student)
        if reminder:
            reminder.show_reminder = False
            reminder.paid_at = timezone.now()
            reminder.lesson_payment = local_payment
            reminder.save(update_fields=['show_reminder', 'paid_at', 'lesson_payment'])
    elif remote_status == 'canceled' and local_payment.status == LessonPayment.Status.PENDING:
        local_payment.status = LessonPayment.Status.CANCELED
        local_payment.save(update_fields=['status'])
    return local_payment


def sync_lesson_payment(local_payment: LessonPayment) -> LessonPayment:
    if not local_payment.yookassa_payment_id:
        return local_payment
    try:
        remote = fetch_remote_payment(local_payment.yookassa_payment_id)
        return apply_remote_status(local_payment, remote.status)
    except Exception:
        logger.exception('Не удалось синхронизировать платёж %s', local_payment.pk)
        return local_payment
