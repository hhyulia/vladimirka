import random
import re
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .image_focus import IMAGE_FOCUS_X_DEFAULT, IMAGE_FOCUS_Y_DEFAULT


class ImageFocusMixin(models.Model):
    """Фокус кадрирования для object-position на сайте (0–100%)."""

    image_focus_x = models.PositiveSmallIntegerField(
        'Фокус по горизонтали (%)',
        default=IMAGE_FOCUS_X_DEFAULT,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='0 — левый край, 50 — центр, 100 — правый край видимой области.',
    )
    image_focus_y = models.PositiveSmallIntegerField(
        'Фокус по вертикали (%)',
        default=IMAGE_FOCUS_Y_DEFAULT,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='0 — верх, 50 — центр, 100 — низ. Для портретов обычно 15–30.',
    )

    class Meta:
        abstract = True

    @property
    def image_object_position(self) -> str:
        return f'{self.image_focus_x}% {self.image_focus_y}%'


def age_from_birth_date(birth_date: date) -> int:
    today = timezone.localtime().date()
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def validate_ru_phone(value):
    if not value or not str(value).strip():
        return
    digits = re.sub(r'\D', '', value)
    if len(digits) not in (10, 11):
        raise ValidationError('Введите корректный номер телефона.')
    if len(digits) == 11 and digits[0] not in ('7', '8'):
        raise ValidationError('Номер должен начинаться с +7 или 8.')


class DanceDirection(ImageFocusMixin, models.Model):

    name = models.CharField('Название', max_length=120)
    short_description = models.TextField('Краткое описание', blank=True)
    image = models.ImageField(
        'Обложка',
        upload_to='directions/',
        blank=True,
        null=True,
        help_text='Рекомендуется горизонтальное фото. Размер подгоняется автоматически.',
    )
    sort_order = models.PositiveSmallIntegerField('Порядок сортировки', default=0)

    class Meta:
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class DanceGroup(models.Model):

    name = models.CharField('Название группы', max_length=200)
    description = models.TextField('Описание', blank=True)
    sort_order = models.PositiveSmallIntegerField('Порядок сортировки', default=0)
    is_active = models.BooleanField('Показывать на сайте', default=True)

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class Trainer(ImageFocusMixin, models.Model):

    full_name = models.CharField('ФИО', max_length=200)
    role = models.CharField(
        'Специализация / направление',
        max_length=160,
        blank=True,
        help_text='Например: «Современный танец» или «Классическая хореография».',
    )
    bio = models.TextField('Краткая информация', blank=True)
    photo = models.ImageField(
        'Фото',
        upload_to='trainers/',
        blank=True,
        null=True,
        help_text='Загрузите фото и настройте кадрирование ползунками или кликом по превью в админке.',
    )
    sort_order = models.PositiveSmallIntegerField('Порядок сортировки', default=0)
    is_active = models.BooleanField('Показывать на сайте', default=True)

    class Meta:
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренеры'
        ordering = ['sort_order', 'full_name']

    def __str__(self) -> str:
        return self.full_name


class StudioHall(models.Model):
    """Площадка / зал для занятий — выбирается в слоте расписания."""

    name = models.CharField(
        'Краткое название',
        max_length=120,
        help_text='Например: «Зал №1» — для списка в админке.',
    )
    address = models.CharField('Адрес', max_length=300)
    sort_order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Зал'
        verbose_name_plural = 'Залы'
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.address


class WeeklyClass(models.Model):

    class Weekday(models.IntegerChoices):
        MONDAY = 0, 'Понедельник'
        TUESDAY = 1, 'Вторник'
        WEDNESDAY = 2, 'Среда'
        THURSDAY = 3, 'Четверг'
        FRIDAY = 4, 'Пятница'
        SATURDAY = 5, 'Суббота'
        SUNDAY = 6, 'Воскресенье'

    group = models.ForeignKey(
        DanceGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='slots',
        verbose_name='Группа',
    )
    direction = models.ForeignKey(
        DanceDirection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='weekly_classes',
        verbose_name='Направление',
    )
    teacher = models.ForeignKey(
        'Trainer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='weekly_classes',
        verbose_name='Тренер',
    )
    teacher_name = models.CharField(
        'Преподаватель (текстом)',
        max_length=120,
        blank=True,
        help_text='Используется, только если тренер не выбран из списка.',
    )
    weekday = models.PositiveSmallIntegerField('День недели', choices=Weekday.choices)
    start_time = models.TimeField('Начало')
    end_time = models.TimeField('Окончание')
    hall = models.ForeignKey(
        StudioHall,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='weekly_classes',
        verbose_name='Зал',
    )

    class Meta:
        verbose_name = 'Слот расписания'
        verbose_name_plural = 'Слоты расписания'
        ordering = ['weekday', 'start_time']

    def __str__(self) -> str:
        if self.group_id and self.group:
            label = self.group.name
        elif self.direction_id and self.direction:
            label = self.direction.name
        else:
            label = 'без группы'
        return f'{self.get_weekday_display()} {self.start_time:%H:%M} — {label}'

    @property
    def teacher_display(self) -> str:
        """ФИО тренера: из выбранного тренера, иначе — текстовое поле."""
        if self.teacher_id and self.teacher:
            return self.teacher.full_name
        return self.teacher_name

    @property
    def hall_display(self) -> str:
        """Адрес зала для отображения на сайте."""
        if self.hall_id and self.hall:
            return str(self.hall)
        return ''


class TrialApplication(models.Model):

    name = models.CharField('Имя', max_length=200)
    phone = models.CharField('Телефон', max_length=32)
    email = models.EmailField('Email', blank=True)
    age = models.PositiveSmallIntegerField('Возраст', null=True, blank=True)
    preferred_direction = models.ForeignKey(
        DanceDirection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trial_applications',
        verbose_name='Интересующее направление',
    )
    preferred_time_note = models.CharField(
        'Удобное время (комментарий)',
        max_length=300,
        blank=True,
    )
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    is_processed = models.BooleanField('Обработано', default=False)

    class Meta:
        verbose_name = 'Заявка на пробное'
        verbose_name_plural = 'Заявки на пробное'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['-created_at'])]

    def __str__(self) -> str:
        return f'{self.name} — {self.phone} ({self.created_at:%d.%m.%Y %H:%M})'


class ContactMessage(models.Model):

    name = models.CharField('Имя', max_length=200)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=32, blank=True)
    message = models.TextField('Сообщение')
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    is_processed = models.BooleanField('Обработано', default=False)

    class Meta:
        verbose_name = 'Обращение с сайта'
        verbose_name_plural = 'Обращения с сайта'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['-created_at'])]

    def __str__(self) -> str:
        return f'{self.name} — {self.email} ({self.created_at:%d.%m.%Y %H:%M})'


class AchievementAlbum(ImageFocusMixin, models.Model):

    title = models.CharField('Название', max_length=120)
    slug = models.SlugField('Slug', max_length=80, unique=True)
    description = models.TextField('Описание', blank=True)
    cover_image = models.ImageField(
        'Обложка',
        upload_to='achievements/covers/',
        blank=True,
        null=True,
    )
    sort_order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_published = models.BooleanField('Опубликован', default=True)
    is_featured = models.BooleanField(
        'Показывать в карточках достижений',
        default=False,
        help_text='Отметьте, чтобы альбом попал в блок из 4 крупных карточек вверху страницы «Достижения». '
                  'Порядок карточек задаётся полем «Порядок».',
    )
    featured_text = models.TextField(
        'Текст для карточки достижения',
        blank=True,
        help_text='Короткое описание для крупной карточки вверху страницы. '
                  'Если пусто — используется обычное «Описание».',
    )

    class Meta:
        verbose_name = 'Альбом достижений'
        verbose_name_plural = 'Альбомы достижений'
        ordering = ['sort_order', 'title']

    def __str__(self) -> str:
        return self.title


class AchievementPhoto(ImageFocusMixin, models.Model):

    album = models.ForeignKey(
        AchievementAlbum,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Альбом',
    )
    image = models.ImageField('Фото', upload_to='achievements/photos/')
    caption = models.CharField('Подпись', max_length=220, blank=True)
    sort_order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_published = models.BooleanField('Опубликовано', default=True)

    class Meta:
        verbose_name = 'Фото достижения'
        verbose_name_plural = 'Фото достижений'
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.caption or f'Фото #{self.pk}'


class StudentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='Пользователь',
    )
    full_name = models.CharField('ФИО', max_length=300)
    birth_date = models.DateField(
        'Дата рождения',
        null=True,
        blank=True,
        help_text='Указывается при регистрации; для лиц 18+ на аккаунте должен быть email для уведомлений об оплате.',
    )
    phone = models.CharField('Телефон', max_length=25, blank=True, validators=[validate_ru_phone])
    group = models.ForeignKey(
        DanceGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Группа',
    )
    password_hint = models.CharField(
        'Пароль (подсказка)',
        max_length=128,
        blank=True,
        help_text='Заполняется администратором при создании аккаунта. Виден только в панели администратора.',
    )

    class Meta:
        verbose_name = 'Профиль ученика'
        verbose_name_plural = 'Профили учеников'

    def __str__(self) -> str:
        return self.full_name

    @property
    def is_adult(self) -> bool:
        if not self.birth_date:
            return False
        return age_from_birth_date(self.birth_date) >= 18


class ParentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        verbose_name='Пользователь',
    )
    full_name = models.CharField('ФИО', max_length=300)
    phone = models.CharField('Телефон', max_length=25, validators=[validate_ru_phone])
    password_hint = models.CharField(
        'Пароль (подсказка)',
        max_length=128,
        blank=True,
        help_text='Заполняется администратором при создании аккаунта. Виден только в панели администратора.',
    )

    class Meta:
        verbose_name = 'Профиль родителя'
        verbose_name_plural = 'Профили родителей'

    def __str__(self) -> str:
        return self.full_name


class ChildRecord(models.Model):

    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name='Родитель',
    )
    full_name = models.CharField('ФИО ребёнка', max_length=300)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parent_links',
        verbose_name='Аккаунт ученика',
        help_text='Заполняется администратором, если ребёнок зарегистрирован на сайте.',
    )
    group = models.ForeignKey(
        DanceGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_records',
        verbose_name='Группа',
        help_text='Если аккаунт ученика указан — группа берётся оттуда.',
    )

    class Meta:
        verbose_name = 'Ребёнок родителя'
        verbose_name_plural = 'Дети родителей'
        ordering = ['full_name']

    def __str__(self) -> str:
        return f'{self.full_name} (родитель: {self.parent})'

    @property
    def effective_group(self):
        if self.student_id and self.student:
            return self.student.group
        return self.group


class LessonPayment(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает оплаты'
        SUCCEEDED = 'succeeded', 'Оплачено'
        CANCELED = 'canceled', 'Отменено'

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='lesson_payments',
        verbose_name='Ученик',
    )
    amount = models.DecimalField('Сумма, ₽', max_digits=10, decimal_places=2)
    description = models.CharField('Описание', max_length=255)
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    yookassa_payment_id = models.CharField(
        'ID платежа ЮKassa',
        max_length=64,
        blank=True,
        unique=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Онлайн-оплата'
        verbose_name_plural = 'Онлайн-оплаты'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.student} — {self.amount} ₽ ({self.get_status_display()})'


def default_reminder_amount() -> Decimal:
    return Decimal(str(getattr(settings, 'YOOKASSA_PAYMENT_AMOUNT', '500.00')))


def payment_amount_limits() -> tuple[Decimal, Decimal]:
    minimum = Decimal(str(getattr(settings, 'PAYMENT_AMOUNT_MIN', '1.00')))
    maximum = Decimal(str(getattr(settings, 'PAYMENT_AMOUNT_MAX', '100000.00')))
    return minimum, maximum


def validate_payment_amount(value: Decimal) -> None:
    minimum, maximum = payment_amount_limits()
    if value < minimum or value > maximum:
        raise ValidationError(
            f'Сумма должна быть от {minimum} до {maximum} ₽. '
            f'Слишком большие значения ЮKassa не принимает.'
        )


def payment_amount_validators():
    minimum, maximum = payment_amount_limits()
    return [
        MinValueValidator(minimum),
        MaxValueValidator(maximum),
    ]


def get_active_payment_reminder(student_profile: StudentProfile):
    """Напоминание, видимое в кабинете и доступное для онлайн-оплаты."""
    for reminder in student_profile.payment_reminders.filter(
        show_reminder=True,
        paid_at__isnull=True,
    ).order_by('payment_due_date'):
        if reminder.is_visible_today:
            return reminder
    return None


def get_upcoming_payment_reminder(student_profile: StudentProfile):
    """Ближайшее напоминание, которое ещё не наступило (раньше чем за 15 дней до оплаты)."""
    for reminder in student_profile.payment_reminders.filter(
        show_reminder=True,
        paid_at__isnull=True,
    ).order_by('payment_due_date'):
        if not reminder.is_visible_today:
            return reminder
    return None


class PaymentReminder(models.Model):
    # За сколько дней до срока открывается оплата и напоминание в кабинете
    PAYMENT_VISIBLE_DAYS_BEFORE = 15

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='payment_reminders',
        verbose_name='Ученик',
    )
    payment_due_date = models.DateField('Дата оплаты')
    amount = models.DecimalField(
        'Сумма к оплате, ₽',
        max_digits=10,
        decimal_places=2,
        default=default_reminder_amount,
        validators=payment_amount_validators(),
        help_text='От 1 до 100 000 ₽. Уходит в ЮKassa при онлайн-оплате.',
    )
    show_reminder = models.BooleanField(
        'Показывать напоминание',
        default=True,
    )
    paid_at = models.DateTimeField(
        'Оплачено',
        null=True,
        blank=True,
        help_text='Заполняется при онлайн-оплате или когда администратор снимает напоминание.',
    )
    lesson_payment = models.ForeignKey(
        'LessonPayment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_reminders',
        verbose_name='Платёж ЮKassa',
    )
    notes = models.TextField('Примечание', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Напоминание об оплате'
        verbose_name_plural = 'Напоминания об оплате'
        ordering = ['payment_due_date']

    def __str__(self) -> str:
        return f'{self.student} — оплата до {self.payment_due_date:%d.%m.%Y}'

    def clean(self):
        super().clean()
        validate_payment_amount(self.amount)

    @property
    def is_paid(self) -> bool:
        return self.paid_at is not None

    @property
    def is_amount_valid(self) -> bool:
        try:
            validate_payment_amount(self.amount)
        except ValidationError:
            return False
        return True

    @property
    def payment_available_from(self) -> date:
        """Дата, с которой в кабинете доступна кнопка оплаты."""
        return self.payment_due_date - timedelta(days=self.PAYMENT_VISIBLE_DAYS_BEFORE)

    @property
    def is_visible_today(self) -> bool:
        if not self.show_reminder or self.is_paid:
            return False
        return date.today() >= self.payment_available_from


class PaidPaymentReminder(PaymentReminder):
    """Прокси для раздела админки с историей оплаченных периодов."""

    class Meta:
        proxy = True
        verbose_name = 'Оплаченное занятие'
        verbose_name_plural = 'Оплаченные занятия'


class PasswordResetCode(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reset_codes',
        verbose_name='Пользователь',
    )
    code = models.CharField('Код', max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField('Истекает')
    is_used = models.BooleanField('Использован', default=False)

    class Meta:
        verbose_name = 'Код восстановления пароля'
        verbose_name_plural = 'Коды восстановления пароля'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user.username} — {self.code} ({"использован" if self.is_used else "активен"})'

    @classmethod
    def generate_for(cls, user) -> 'PasswordResetCode':
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        code = f'{random.randint(0, 999999):06d}'
        return cls.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=15),
        )

    @property
    def is_valid(self) -> bool:
        return not self.is_used and timezone.now() <= self.expires_at
