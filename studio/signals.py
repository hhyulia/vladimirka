import calendar
from datetime import date

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone


def _next_month(d: date) -> date:
    month = d.month + 1
    year = d.year
    if month > 12:
        month = 1
        year += 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


@receiver(pre_save, sender='studio.PaymentReminder')
def _remember_old_show(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_show_reminder = sender.objects.get(pk=instance.pk).show_reminder
        except sender.DoesNotExist:
            instance._old_show_reminder = None
    else:
        instance._old_show_reminder = None


@receiver(post_save, sender='studio.PaymentReminder')
def _auto_create_next_reminder(sender, instance, created, **kwargs):
    if created:
        return
    old = getattr(instance, '_old_show_reminder', None)
    if old is True and instance.show_reminder is False:
        if not instance.paid_at:
            sender.objects.filter(pk=instance.pk).update(paid_at=timezone.now())
        next_date = _next_month(instance.payment_due_date)
        already_exists = sender.objects.filter(
            student=instance.student,
            payment_due_date=next_date,
        ).exists()
        if not already_exists:
            sender.objects.create(
                student=instance.student,
                payment_due_date=next_date,
                amount=instance.amount,
                show_reminder=True,
                notes=instance.notes,
            )
