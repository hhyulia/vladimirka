from datetime import date, timedelta


def payment_reminder(request):
    if not request.user.is_authenticated:
        return {}

    today = date.today()
    threshold = today + timedelta(days=15)
    reminder = None

    try:
        student = request.user.student_profile
        reminder = student.payment_reminders.filter(
            show_reminder=True,
            paid_at__isnull=True,
            payment_due_date__gte=today,
        ).first()
        if reminder and not reminder.is_visible_today:
            reminder = None
    except Exception:
        pass

    if reminder is None:
        try:
            parent = request.user.parent_profile
            for child in parent.children.filter(student__isnull=False).select_related('student'):
                r = child.student.payment_reminders.filter(
                    show_reminder=True,
                    paid_at__isnull=True,
                    payment_due_date__gte=today,
                ).first()
                if r and r.is_visible_today:
                    reminder = r
                    break
        except Exception:
            pass

    return {'global_payment_reminder': reminder}


def trial_form(request):
    """Делает форму записи на пробное доступной в модальном окне на любой странице."""
    from .forms import TrialApplicationForm

    return {'trial_form': TrialApplicationForm()}
