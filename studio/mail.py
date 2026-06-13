import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail

from .models import ContactMessage, TrialApplication

logger = logging.getLogger(__name__)


def _studio_recipients() -> list[str]:
    email = getattr(settings, 'STUDIO_NOTIFICATION_EMAIL', '') or ''
    email = email.strip()
    return [email] if email else []


def notify_trial_application(application: TrialApplication) -> None:
    recipients = _studio_recipients()
    if not recipients:
        return
    direction = (
        application.preferred_direction.name
        if application.preferred_direction_id
        else '—'
    )
    lines = [
        f'Имя: {application.name}',
        f'Телефон: {application.phone}',
        f'Email: {application.email or "—"}',
        f'Возраст: {application.age if application.age is not None else "—"}',
        f'Направление: {direction}',
        f'Удобное время: {application.preferred_time_note or "—"}',
        f'Комментарий: {application.comment or "—"}',
    ]

    from django.template.loader import render_to_string
    html_message = render_to_string('studio/emails/trial_application.html', {'application': application})

    try:
        send_mail(
            subject=f'Новая заявка на пробное: {application.name}',
            message='\n'.join(lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
            html_message=html_message,
        )
    except Exception:
        logger.exception('Не удалось отправить письмо о заявке на пробное')


def notify_contact_message(message: ContactMessage) -> None:
    recipients = _studio_recipients()
    if not recipients:
        return
    lines = [
        f'Имя: {message.name}',
        f'Email: {message.email}',
        f'Телефон: {message.phone or "—"}',
        '',
        message.message,
    ]

    from django.template.loader import render_to_string
    html_message = render_to_string('studio/emails/contact_message.html', {'msg': message})

    try:
        send_mail(
            subject=f'Сообщение с сайта: {message.name}',
            message='\n'.join(lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
            html_message=html_message,
        )
    except Exception:
        logger.exception('Не удалось отправить письмо с формы контактов')


def send_reset_code(recipient_email: str, code: str, verify_url: str, for_user: User, requested_by_label: str = '') -> bool:
    """Отправляет письмо с 6-значным кодом и ссылкой на страницу его ввода."""
    from django.template.loader import render_to_string
    html_message = render_to_string('studio/emails/password_reset_code.html', {
        'code': code,
        'verify_url': verify_url,
        'for_user': for_user,
        'requested_by_label': requested_by_label,
    })
    try:
        send_mail(
            subject='Восстановление пароля · Vladimirka',
            message=f'Код подтверждения: {code}\nСсылка для ввода кода: {verify_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
            html_message=html_message,
        )
        return True
    except Exception:
        logger.exception('Не удалось отправить код восстановления пароля')
        return False
