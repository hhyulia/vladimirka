from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .forms import (
    AccountResetRequestForm,
    ChangeUsernameForm,
    ContactMessageForm,
    ParentRegistrationForm,
    SetNewPasswordForm,
    StudioLoginForm,
    StudioPasswordChangeForm,
    StudentRegistrationForm,
    TrialApplicationForm,
    VerifyCodeForm,
)
from .mail import notify_contact_message, notify_trial_application, send_reset_code
from django.core.exceptions import ValidationError

from .models import (
    AchievementAlbum,
    AchievementPhoto,
    ChildRecord,
    DanceDirection,
    DanceGroup,
    LessonPayment,
    ParentProfile,
    get_active_payment_reminder,
    get_upcoming_payment_reminder,
    payment_amount_limits,
    validate_payment_amount,
    PasswordResetCode,
    StudentProfile,
    Trainer,
)
from .payments import create_remote_payment, is_yookassa_configured, sync_lesson_payment


def home(request):
    directions = list(DanceDirection.objects.all()[:3])
    albums = list(
        AchievementAlbum.objects.filter(is_published=True).order_by('sort_order', 'title')[:2]
    )
    trainers = list(Trainer.objects.filter(is_active=True))
    context = {
        'directions': directions,
        'albums': albums,
        'trainers': trainers,
        'stats': {
            'since_year': 2018,
            'directions_count': DanceDirection.objects.count(),
            'groups_count': DanceGroup.objects.filter(is_active=True).count(),
        },
    }
    return render(request, 'studio/home.html', context)


def about(request):
    trainers = list(Trainer.objects.filter(is_active=True))
    return render(request, 'studio/about.html', {'trainers': trainers})


def privacy_policy(request):
    return render(request, 'studio/privacy_policy.html')


def data_consent(request):
    return render(request, 'studio/data_consent.html')


def achievements(request):
    albums = AchievementAlbum.objects.filter(is_published=True).order_by('sort_order', 'title')
    featured = list(albums.filter(is_featured=True)[:4])
    albums_count = albums.count()
    photos_count = AchievementPhoto.objects.filter(
        is_published=True, album__is_published=True
    ).count()
    return render(request, 'studio/achievements.html', {
        'albums': albums,
        'featured': featured,
        'albums_count': albums_count,
        'photos_count': photos_count,
    })


def achievement_album(request, slug):
    album = get_object_or_404(AchievementAlbum, slug=slug, is_published=True)
    photos = album.photos.filter(is_published=True).order_by('sort_order', 'id')
    return render(request, 'studio/achievements_gallery.html', {'album': album, 'photos': photos})


def directions(request):
    items = DanceDirection.objects.all()
    return render(request, 'studio/directions.html', {'directions': items})


def schedule(request):
    groups = (
        DanceGroup.objects.filter(is_active=True)
        .prefetch_related('slots__direction', 'slots__hall')
        .order_by('sort_order', 'name')
    )
    return render(request, 'studio/schedule.html', {'groups': groups})


def trial_lesson(request):
    direction_pk = None
    raw_dir = request.GET.get('direction')
    if raw_dir is not None:
        try:
            cand = int(raw_dir)
        except (TypeError, ValueError):
            cand = None
        if cand is not None and DanceDirection.objects.filter(pk=cand).exists():
            direction_pk = cand

    if request.method == 'POST':
        form = TrialApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            notify_trial_application(application)
            messages.success(
                request,
                'Заявка принята. Мы свяжемся с вами в ближайшее время.',
            )
            return redirect('studio:trial')
    else:
        initial = {}
        if direction_pk is not None:
            initial['preferred_direction'] = direction_pk
        form = TrialApplicationForm(initial=initial)
    return render(request, 'studio/trial.html', {'form': form})


@require_POST
def trial_submit(request):
    form = TrialApplicationForm(request.POST)
    if form.is_valid():
        application = form.save()
        notify_trial_application(application)
        return JsonResponse({
            'ok': True,
            'message': 'Заявка принята. Мы свяжемся с вами в ближайшее время.',
        })
    return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


def contact(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            msg = form.save()
            notify_contact_message(msg)
            messages.success(
                request,
                'Сообщение отправлено. Мы ответим вам в ближайшее время.',
            )
            return redirect('studio:contact')
    else:
        form = ContactMessageForm()
    return render(request, 'studio/contact.html', {'form': form})


def register_student(request):
    if request.user.is_authenticated:
        return redirect('studio:cabinet')
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                _autolink_student_to_parent_records(user.student_profile)
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно. Добро пожаловать!')
            return redirect('studio:cabinet')
    else:
        form = StudentRegistrationForm()
    return render(request, 'studio/register_student.html', {'form': form})


def register_parent(request):
    if request.user.is_authenticated:
        return redirect('studio:cabinet')
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        children_data = _extract_children(request.POST)

        missing_children = []
        found_students = {}
        for item in children_data:
            try:
                student = StudentProfile.objects.get(user__username=item['username'])
                found_students[item['username']] = student
            except StudentProfile.DoesNotExist:
                missing_children.append(item['username'])

        if missing_children:
            logins_str = ', '.join(missing_children)
            form.add_error(None, f'Ученики с логином «{logins_str}» не найдены. Проверьте правильность логина.')
        elif form.is_valid():
            with transaction.atomic():
                user = form.save()
                parent = user.parent_profile
                for item in children_data:
                    student = found_students[item['username']]
                    ChildRecord.objects.create(
                        parent=parent,
                        full_name=student.full_name,
                        student=student,
                    )
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно. Добро пожаловать!')
            return redirect('studio:cabinet')
    else:
        form = ParentRegistrationForm()
        children_data = []
    return render(request, 'studio/register_parent.html', {
        'form': form,
        'children_data': children_data,
    })


def _extract_children(post):
    result = []
    i = 0
    while True:
        username = post.get(f'child_username_{i}', '').strip()
        if username == '' and i > 0:
            break
        if i > 20:
            break
        result.append({'username': username})
        i += 1
    return [r for r in result if r['username']]


def login_view(request):
    if request.user.is_authenticated:
        return redirect('studio:cabinet')
    if request.method == 'POST':
        form = StudioLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(request.GET.get('next') or 'studio:cabinet')
    else:
        form = StudioLoginForm(request)
    return render(request, 'studio/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('studio:home')


@login_required
def cabinet(request):
    user = request.user
    if hasattr(user, 'student_profile'):
        return redirect('studio:cabinet_student')
    if hasattr(user, 'parent_profile'):
        return redirect('studio:cabinet_parent')
    if user.is_staff or user.is_superuser:
        return redirect('/admin/')
    return redirect('studio:home')


@login_required
def cabinet_student(request):
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return redirect('studio:home')

    group = profile.group
    slots_by_day = []
    if group:
        from itertools import groupby
        slots = list(
            group.slots.select_related('direction', 'hall')
            .order_by('weekday', 'start_time')
        )
        for day_num, day_slots in groupby(slots, key=lambda s: s.weekday):
            slots_by_day.append({
                'day_label': dict(
                    [(0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'),
                     (3, 'Четверг'), (4, 'Пятница'), (5, 'Суббота'), (6, 'Воскресенье')]
                )[day_num],
                'slots': list(day_slots),
            })

    reminder = get_active_payment_reminder(profile)
    upcoming_reminder = None if reminder else get_upcoming_payment_reminder(profile)
    return render(request, 'studio/cabinet_student.html', {
        'profile': profile,
        'group': group,
        'slots_by_day': slots_by_day,
        'reminder': reminder,
        'upcoming_reminder': upcoming_reminder,
        'yookassa_enabled': is_yookassa_configured(),
    })


@login_required
@require_POST
def payment_create(request):
    child_record = None
    child_id = request.POST.get('child_id', '').strip()

    if child_id:
        try:
            parent = request.user.parent_profile
        except ParentProfile.DoesNotExist:
            raise Http404 from None
        child_record = get_object_or_404(parent.children, pk=child_id)
        if not child_record.student_id:
            messages.error(
                request,
                'Ребёнок не привязан к аккаунту на сайте — оплату может провести только '
                'зарегистрированный ученик 18+ или администратор.',
            )
            return redirect('studio:cabinet_parent')
        profile = child_record.student
        cancel_url = 'studio:cabinet_parent'
    else:
        try:
            profile = request.user.student_profile
        except StudentProfile.DoesNotExist:
            raise Http404 from None
        if not profile.is_adult:
            raise Http404 from None
        cancel_url = 'studio:cabinet_student'

    reminder = get_active_payment_reminder(profile)
    if not reminder:
        messages.info(
            request,
            'Онлайн-оплата доступна только при активном напоминании об оплате в личном кабинете.',
        )
        return redirect(cancel_url)

    try:
        validate_payment_amount(reminder.amount)
    except ValidationError as exc:
        minimum, maximum = payment_amount_limits()
        messages.error(
            request,
            f'Некорректная сумма к оплате ({reminder.amount} ₽). '
            f'Администратор должен указать от {minimum} до {maximum} ₽ в напоминании.',
        )
        return redirect(cancel_url)

    if not is_yookassa_configured():
        messages.error(
            request,
            'Онлайн-оплата не настроена. Добавьте YOOKASSA_SECRET_KEY в файл .env.',
        )
        return redirect(cancel_url)

    payment_description = (
        f'Оплата занятий до {reminder.payment_due_date:%d.%m.%Y} — {profile.full_name}'
    )
    local_payment = LessonPayment.objects.create(
        student=profile,
        amount=reminder.amount,
        description=payment_description[:255],
    )
    try:
        remote = create_remote_payment(local_payment)
    except Exception:
        local_payment.delete()
        messages.error(
            request,
            'Не удалось создать платёж. Проверьте ключи ЮKassa и что установлен пакет yookassa.',
        )
        return redirect(cancel_url)

    local_payment.yookassa_payment_id = remote.id
    local_payment.save(update_fields=['yookassa_payment_id'])
    request.session['pending_lesson_payment_id'] = local_payment.pk
    if child_record:
        request.session['pending_lesson_payment_child_id'] = child_record.pk

    confirmation_url = remote.confirmation.confirmation_url
    return redirect(confirmation_url)


def _lesson_payment_for_user(user, payment_id):
    payment = LessonPayment.objects.select_related('student').get(pk=payment_id)
    try:
        if payment.student_id == user.student_profile.pk:
            return payment
    except StudentProfile.DoesNotExist:
        pass
    try:
        parent = user.parent_profile
        if parent.children.filter(student_id=payment.student_id).exists():
            return payment
    except ParentProfile.DoesNotExist:
        pass
    raise LessonPayment.DoesNotExist


@login_required
def payment_return(request):
    payment = None
    payment_id = request.session.pop('pending_lesson_payment_id', None)
    child_record_id = request.session.pop('pending_lesson_payment_child_id', None)
    if payment_id:
        try:
            payment = _lesson_payment_for_user(request.user, payment_id)
            payment = sync_lesson_payment(payment)
        except LessonPayment.DoesNotExist:
            payment = None

    if payment and payment.status == LessonPayment.Status.SUCCEEDED:
        messages.success(request, 'Оплата прошла успешно. Спасибо!')
    elif payment and payment.status == LessonPayment.Status.CANCELED:
        messages.warning(request, 'Оплата не была завершена.')
    else:
        messages.info(request, 'Платёж обрабатывается. Обновите страницу через минуту.')

    if child_record_id:
        cabinet_url = f"{reverse('studio:cabinet_parent')}?child={child_record_id}"
    else:
        cabinet_url = reverse('studio:cabinet_student')

    return redirect(cabinet_url)


@login_required
def cabinet_parent(request):
    try:
        profile = request.user.parent_profile
    except ParentProfile.DoesNotExist:
        return redirect('studio:home')

    if request.method == 'POST' and request.POST.get('action') == 'remove_child':
        child_id = request.POST.get('child_id', '').strip()
        try:
            record = profile.children.get(pk=child_id)
            name = record.full_name
            record.delete()
            messages.success(request, f'Ребёнок «{name}» удалён из кабинета.')
        except ChildRecord.DoesNotExist:
            pass
        return redirect('studio:cabinet_parent')

    add_child_error = None
    if request.method == 'POST' and request.POST.get('action') == 'add_child':
        child_username = request.POST.get('new_child_username', '').strip()
        if not child_username:
            add_child_error = 'Укажите логин ребёнка.'
        else:
            try:
                student = StudentProfile.objects.get(user__username=child_username)
                if profile.children.filter(student=student).exists():
                    add_child_error = f'Ребёнок «{student.full_name}» уже добавлен в ваш кабинет.'
                else:
                    ChildRecord.objects.create(
                        parent=profile,
                        full_name=student.full_name,
                        student=student,
                    )
                    messages.success(request, f'Ребёнок «{student.full_name}» добавлен.')
                    return redirect('studio:cabinet_parent')
            except StudentProfile.DoesNotExist:
                add_child_error = f'Ученик с логином «{child_username}» не зарегистрирован на сайте.'

    children = list(
        profile.children
        .select_related('student__group', 'group')
        .order_by('full_name')
    )
    active_child_id = None
    if children:
        try:
            active_child_id = int(request.GET.get('child', children[0].pk))
        except (TypeError, ValueError):
            active_child_id = children[0].pk

    active_child = None
    slots_by_day = []
    reminder = None
    upcoming_reminder = None
    for ch in children:
        if ch.pk == active_child_id:
            active_child = ch
            break

    if active_child:
        group = active_child.effective_group
        if group:
            from itertools import groupby
            slots = list(
                group.slots.select_related('direction', 'hall')
                .order_by('weekday', 'start_time')
            )
            for day_num, day_slots in groupby(slots, key=lambda s: s.weekday):
                slots_by_day.append({
                    'day_label': dict(
                        [(0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'),
                         (3, 'Четверг'), (4, 'Пятница'), (5, 'Суббота'), (6, 'Воскресенье')]
                    )[day_num],
                    'slots': list(day_slots),
                })
        if active_child.student:
            reminder = get_active_payment_reminder(active_child.student)
            if not reminder:
                upcoming_reminder = get_upcoming_payment_reminder(active_child.student)

    return render(request, 'studio/cabinet_parent.html', {
        'profile': profile,
        'children': children,
        'active_child': active_child,
        'slots_by_day': slots_by_day,
        'reminder': reminder,
        'upcoming_reminder': upcoming_reminder,
        'add_child_error': add_child_error,
        'yookassa_enabled': is_yookassa_configured(),
    })


def _autolink_student_to_parent_records(student_profile):
    ChildRecord.objects.filter(
        full_name__iexact=student_profile.full_name,
        student__isnull=True,
    ).update(student=student_profile)


def _autolink_child_record_to_student(child_record):
    try:
        student = StudentProfile.objects.get(full_name__iexact=child_record.full_name)
        child_record.student = student
        child_record.save(update_fields=['student'])
    except (StudentProfile.DoesNotExist, StudentProfile.MultipleObjectsReturned):
        pass


@login_required
def account_settings(request):
    user = request.user
    username_form = ChangeUsernameForm(user)
    password_form = StudioPasswordChangeForm(user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_username':
            username_form = ChangeUsernameForm(user, request.POST)
            if username_form.is_valid():
                user.username = username_form.cleaned_data['new_username']
                user.save(update_fields=['username'])
                messages.success(request, 'Логин успешно изменён.')
                return redirect('studio:account_settings')
        elif action == 'change_password':
            password_form = StudioPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                changed_user = password_form.save()
                update_session_auth_hash(request, changed_user)
                messages.success(request, 'Пароль успешно изменён.')
                return redirect('studio:account_settings')

    return render(request, 'studio/account_settings.html', {
        'username_form': username_form,
        'password_form': password_form,
    })




def _send_code_for_user(request, target_user, recipient_email, recipient_label=''):
    reset_code = PasswordResetCode.generate_for(target_user)
    uid = urlsafe_base64_encode(force_bytes(target_user.pk))
    verify_url = request.build_absolute_uri(f'/vosstanovlenie/kod/{uid}/')
    return send_reset_code(recipient_email, reset_code.code, verify_url, target_user, recipient_label)


def password_reset_request(request):
    if request.user.is_authenticated:
        return redirect('studio:cabinet')

    form = AccountResetRequestForm()

    if request.method == 'POST':
        form = AccountResetRequestForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                target_user = User.objects.get(username=username)
            except User.DoesNotExist:
                form.add_error(None, 'Пользователь с таким логином не найден.')
            else:
                if hasattr(target_user, 'parent_profile'):
                    if not target_user.email:
                        form.add_error(None, 'У аккаунта родителя не указан email. Обратитесь к администратору.')
                    else:
                        sent_ok = _send_code_for_user(request, target_user, target_user.email)
                        if sent_ok:
                            return redirect('studio:password_reset_sent')
                        form.add_error(None, 'Не удалось отправить письмо. Проверьте настройки SMTP или попробуйте позже.')
                elif hasattr(target_user, 'student_profile'):
                    if target_user.email:
                        sent_ok = _send_code_for_user(request, target_user, target_user.email)
                        if sent_ok:
                            return redirect('studio:password_reset_sent')
                        form.add_error(None, 'Не удалось отправить письмо. Проверьте настройки SMTP или попробуйте позже.')
                    else:
                        student_profile = target_user.student_profile
                        parent_records = (
                            ChildRecord.objects
                            .filter(student=student_profile)
                            .select_related('parent__user')
                        )
                        sent = False
                        for record in parent_records:
                            parent_user = record.parent.user
                            if parent_user.email:
                                sent_ok = _send_code_for_user(
                                    request,
                                    target_user,
                                    parent_user.email,
                                    recipient_label=f'родителя {parent_user.username}',
                                )
                                if sent_ok:
                                    sent = True
                                    break
                        if sent:
                            return redirect('studio:password_reset_sent')
                        form.add_error(
                            None,
                            'У аккаунта ученика нет email и нет привязанного родителя с почтой. '
                            'Обратитесь к администратору студии.'
                        )
                else:
                    form.add_error(None, 'Этот логин не привязан к кабинету ученика или родителя.')

    return render(request, 'studio/password_reset.html', {
        'form': form,
    })


def password_reset_sent(request):
    return render(request, 'studio/password_reset_sent.html')


def password_reset_verify(request, uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        target_user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        target_user = None

    if target_user is None:
        return render(request, 'studio/password_reset_verify.html', {'invalid_link': True})

    form = VerifyCodeForm(request.POST or None)
    error = None

    if request.method == 'POST' and form.is_valid():
        entered = form.cleaned_data['code']
        try:
            reset_code = PasswordResetCode.objects.filter(
                user=target_user, is_used=False
            ).latest('created_at')
        except PasswordResetCode.DoesNotExist:
            error = 'Код не найден. Запросите новый.'
        else:
            if not reset_code.is_valid:
                error = 'Код истёк. Запросите новый.'
            elif reset_code.code != entered:
                error = 'Неверный код. Попробуйте ещё раз.'
            else:
                reset_code.is_used = True
                reset_code.save(update_fields=['is_used'])
                request.session[f'pwd_reset_ok_{uid}'] = True
                return redirect('studio:password_reset_confirm', uidb64=uidb64)

    return render(request, 'studio/password_reset_verify.html', {
        'form': form,
        'uidb64': uidb64,
        'error': error,
        'target_username': target_user.username,
    })


def password_reset_confirm(request, uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        target_user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        target_user = None

    session_key = f'pwd_reset_ok_{uid}' if target_user else None
    if target_user is None or not request.session.get(session_key):
        return render(request, 'studio/password_reset_confirm.html', {'invalid_link': True})

    form = SetNewPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        target_user.set_password(form.cleaned_data['new_password1'])
        target_user.save()
        request.session.pop(session_key, None)
        if hasattr(target_user, 'student_profile'):
            target_user.student_profile.password_hint = ''
            target_user.student_profile.save(update_fields=['password_hint'])
        elif hasattr(target_user, 'parent_profile'):
            target_user.parent_profile.password_hint = ''
            target_user.parent_profile.save(update_fields=['password_hint'])
        login(request, target_user)
        return redirect('studio:password_reset_complete')

    return render(request, 'studio/password_reset_confirm.html', {
        'form': form,
        'uidb64': uidb64,
    })


def password_reset_complete(request):
    return render(request, 'studio/password_reset_complete.html')
