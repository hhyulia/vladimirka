import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from studio.models import PaymentReminder, StudentProfile

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Рассылает email-напоминания об оплате пользователям (за 15 дней до даты оплаты).'

    def handle(self, *args, **options):
        today = date.today()
        target_date = today + timedelta(days=15)

        reminders = PaymentReminder.objects.filter(
            show_reminder=True,
            paid_at__isnull=True,
            payment_due_date=target_date,
        ).select_related('student__user')

        count = 0
        for reminder in reminders:
            student = reminder.student
            recipients = []
            
            if student.user and student.user.email:
                recipients.append((student.user.email, student.full_name, None))
            
            for child_link in student.parent_links.select_related('parent__user'):
                parent = child_link.parent
                if parent.user and parent.user.email:
                    recipients.append((parent.user.email, parent.full_name, student.full_name))

            sent_emails = set()
            for email, user_name, child_name in recipients:
                if email in sent_emails:
                    continue
                
                self._send_email(email, user_name, child_name, reminder)
                sent_emails.add(email)
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Рассылка завершена. Отправлено писем: {count}'))

    def _send_email(self, email, user_name, child_name, reminder):
        subject = 'Напоминание об оплате · Vladimirka'
        
        site_url = f'{settings.SITE_URL.rstrip("/")}/vhod/'

        html_message = render_to_string('studio/emails/payment_reminder.html', {
            'user_name': user_name,
            'child_name': child_name,
            'reminder': reminder,
            'site_url': site_url,
        })

        text_message = (
            f"Здравствуйте, {user_name}!\n\n"
            f"Оплатите занятия {'ребёнка ('+child_name+') ' if child_name else ''}"
            f"до {reminder.payment_due_date.strftime('%d.%m.%Y')}.\n\n"
            f"{reminder.notes if reminder.notes else ''}\n\n"
            f"Личный кабинет: {site_url}"
        )

        try:
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
                html_message=html_message,
            )
        except Exception as e:
            logger.error(f'Ошибка отправки письма на {email}: {e}')
