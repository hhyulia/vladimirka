from django import forms as dj_forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.html import format_html

from .admin_image_focus import ImageFocusAdminMixin, absolute_media_url, render_image_focus_preview
from .models import (
    payment_amount_limits,
    AchievementAlbum,
    AchievementPhoto,
    ChildRecord,
    ContactMessage,
    DanceDirection,
    DanceGroup,
    ParentProfile,
    PasswordResetCode,
    LessonPayment,
    PaidPaymentReminder,
    PaymentReminder,
    StudentProfile,
    StudioHall,
    Trainer,
    TrialApplication,
    WeeklyClass,
)


class AchievementPhotoInline(admin.TabularInline):
    model = AchievementPhoto
    extra = 1
    fields = ('image', 'image_focus_x', 'image_focus_y', 'caption', 'sort_order', 'is_published')


@admin.register(AchievementAlbum)
class AchievementAlbumAdmin(ImageFocusAdminMixin, admin.ModelAdmin):
    image_focus_file_field = 'cover_image'
    list_display = ('title', 'slug', 'sort_order', 'is_featured', 'is_published')
    list_editable = ('sort_order', 'is_featured', 'is_published')
    list_filter = ('is_featured', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')
    fields = (
        'title', 'slug', 'description', 'cover_image',
        'is_featured', 'featured_text', 'sort_order', 'is_published',
    )
    inlines = [AchievementPhotoInline]

    @admin.display(description='Кадрирование обложки')
    def cover_image_focus_preview(self, obj):
        return render_image_focus_preview(obj, file_attr='cover_image')


@admin.register(AchievementPhoto)
class AchievementPhotoAdmin(admin.ModelAdmin):
    list_display = ('preview', 'album', 'caption', 'sort_order', 'is_published')
    list_filter = ('album', 'is_published')
    list_editable = ('sort_order', 'is_published')
    search_fields = ('caption', 'album__title')
    fields = ('album', 'image', 'image_focus_x', 'image_focus_y', 'caption', 'sort_order', 'is_published')

    @admin.display(description='Фото')
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:52px;width:72px;object-fit:cover;border-radius:3px;">',
                absolute_media_url(obj.image.url),
            )
        return '—'


@admin.register(DanceDirection)
class DanceDirectionAdmin(ImageFocusAdminMixin, admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'sort_order')
    list_editable = ('sort_order',)
    fields = ('name', 'short_description', 'image', 'sort_order')

    @admin.display(description='Кадрирование обложки')
    def image_focus_preview(self, obj):
        return render_image_focus_preview(obj, file_attr='image')

    @admin.display(description='Фото')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:48px;width:72px;object-fit:cover;border-radius:3px;">',
                obj.image.url,
            )
        return '—'


@admin.register(Trainer)
class TrainerAdmin(ImageFocusAdminMixin, admin.ModelAdmin):
    image_focus_file_field = 'photo'
    list_display = ('photo_preview', 'full_name', 'role', 'sort_order', 'is_active')
    list_display_links = ('photo_preview', 'full_name')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('full_name', 'role')
    fields = ('full_name', 'role', 'bio', 'photo', 'sort_order', 'is_active')

    @admin.display(description='Кадрирование фото')
    def photo_focus_preview(self, obj):
        return render_image_focus_preview(obj, file_attr='photo')

    @admin.display(description='Фото')
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:52px;width:52px;object-fit:cover;border-radius:50%;">',
                obj.photo.url,
            )
        return '—'


class WeeklyClassInline(admin.TabularInline):
    """Слоты расписания прямо внутри карточки группы."""
    model = WeeklyClass
    extra = 1
    fields = ('direction', 'teacher', 'weekday', 'start_time', 'end_time', 'hall')


@admin.register(StudioHall)
class StudioHallAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('name', 'address')
    ordering = ('sort_order', 'name')


@admin.register(DanceGroup)
class DanceGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active', 'sort_order')
    inlines = [WeeklyClassInline]


@admin.register(WeeklyClass)
class WeeklyClassAdmin(admin.ModelAdmin):
    list_display = ('group', 'direction', 'teacher', 'weekday', 'start_time', 'end_time', 'hall')
    list_filter = ('weekday', 'direction', 'teacher', 'hall')
    search_fields = ('group__name', 'teacher__full_name', 'teacher_name', 'hall__address')
    fields = ('group', 'direction', 'teacher', 'teacher_name', 'weekday', 'start_time', 'end_time', 'hall')


@admin.register(TrialApplication)
class TrialApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'preferred_direction', 'created_at', 'is_processed')
    list_filter = ('is_processed', 'created_at', 'preferred_direction')
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('created_at',)
    list_editable = ('is_processed',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at', 'is_processed')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)
    list_editable = ('is_processed',)


# ── Личные кабинеты ──────────────────────────────

class ChildRecordInline(admin.TabularInline):
    model = ChildRecord
    extra = 0
    fields = ('full_name', 'student', 'group')
    autocomplete_fields = ('student',)
    verbose_name = 'Ребёнок'
    verbose_name_plural = 'Дети'


class PaymentReminderInline(admin.TabularInline):
    model = PaymentReminder
    extra = 0
    fields = ('payment_due_date', 'amount', 'show_reminder', 'notes')
    readonly_fields = ()
    verbose_name = 'Напоминание об оплате'
    verbose_name_plural = 'Активные напоминания'

    def get_queryset(self, request):
        return super().get_queryset(request).filter(paid_at__isnull=True)


# ── Вспомогательная форма для создания/редактирования аккаунта ──

class AccountAdminForm(dj_forms.ModelForm):
    """Добавляет поля создания/изменения пароля прямо в форму профиля."""
    new_username = dj_forms.CharField(
        label='Логин',
        max_length=150,
        required=False,
        help_text='Оставьте пустым, чтобы не менять. При создании — обязательно.',
        widget=dj_forms.TextInput(attrs={'style': 'width:220px'}),
    )
    new_email = dj_forms.EmailField(
        label='Email',
        max_length=254,
        required=False,
        help_text='Используется для восстановления пароля и уведомлений. Можно оставить пустым.',
        widget=dj_forms.EmailInput(attrs={'style': 'width:220px'}),
    )
    new_password = dj_forms.CharField(
        label='Пароль',
        max_length=128,
        required=False,
        help_text='Введите новый пароль. При создании — обязательно. При редактировании — оставьте пустым, чтобы не менять.',
        widget=dj_forms.PasswordInput(
            render_value=False,
            attrs={'style': 'width:220px', 'class': 'vTextField js-password-field'},
        ),
    )

    def clean_new_username(self):
        username = (self.cleaned_data.get('new_username') or '').strip()
        is_create = self.instance.pk is None
        if is_create and not username:
            raise dj_forms.ValidationError('Укажите логин для нового аккаунта.')
        if username:
            current_user_id = getattr(self.instance, 'user_id', None)
            qs = User.objects.filter(username__iexact=username)
            if current_user_id:
                qs = qs.exclude(pk=current_user_id)
            if qs.exists():
                raise dj_forms.ValidationError('Этот логин уже занят. Выберите другой.')
        return username

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password') or ''
        if self.instance.pk is None and not password.strip():
            raise dj_forms.ValidationError('Укажите пароль для нового аккаунта.')
        return password


class StudentAdminForm(AccountAdminForm):
    class Meta:
        model = StudentProfile
        fields = '__all__'


class ParentAdminForm(AccountAdminForm):
    class Meta:
        model = ParentProfile
        fields = '__all__'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ('full_name', 'login_display', 'email_display', 'phone', 'group', 'has_parent', 'password_hint_display')
    list_filter = ('group',)
    search_fields = ('full_name', 'phone', 'user__username')
    autocomplete_fields = ('group',)
    inlines = [PaymentReminderInline]
    readonly_fields = ('user',)

    fieldsets = (
        ('Данные аккаунта', {
            'fields': ('new_username', 'new_email', 'new_password', 'password_hint'),
            'description': (
                '<strong>При создании</strong> заполните логин и пароль. '
                'Поле «Пароль (подсказка)» сохраняет введённый пароль в открытом виде — '
                'только для памятки администратора. Храните осторожно.'
            ),
        }),
        ('Профиль', {
            'fields': ('full_name', 'birth_date', 'phone', 'group'),
        }),
    )

    class Media:
        js = ('studio/admin-password-toggle.js',)

    @admin.display(description='Логин')
    def login_display(self, obj):
        return obj.user.username

    @admin.display(description='Email')
    def email_display(self, obj):
        return obj.user.email or '—'

    @admin.display(description='Пароль (подсказка)')
    def password_hint_display(self, obj):
        if obj.password_hint:
            return format_html(
                '<span style="font-family:monospace;background:#f0eee8;padding:2px 6px;border-radius:3px;">{}</span>',
                obj.password_hint,
            )
        return '—'

    @admin.display(description='Привязан к родителю', boolean=True)
    def has_parent(self, obj):
        return obj.parent_links.exists()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['new_username'].initial = obj.user.username
            form.base_fields['new_email'].initial = obj.user.email
        return form

    def save_model(self, request, obj, form, change):
        new_username = form.cleaned_data.get('new_username', '').strip()
        new_email = form.cleaned_data.get('new_email', '').strip()
        new_password = form.cleaned_data.get('new_password', '').strip()

        if not change:
            # Создание нового профиля
            user = User.objects.create_user(
                username=new_username,
                email=new_email,
                password=new_password or None,
            )
            obj.user = user
        else:
            user = obj.user
            if new_username and new_username != user.username:
                user.username = new_username
                user.save(update_fields=['username'])
            if new_email != user.email:
                user.email = new_email
                user.save(update_fields=['email'])
            if new_password:
                user.set_password(new_password)
                user.save(update_fields=['password'])

        if new_password and not obj.password_hint:
            obj.password_hint = new_password
        super().save_model(request, obj, form, change)


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    form = ParentAdminForm
    list_display = ('full_name', 'login_display', 'email_display', 'phone', 'children_list', 'password_hint_display')
    search_fields = ('full_name', 'phone', 'user__username')
    inlines = [ChildRecordInline]
    readonly_fields = ('user',)

    fieldsets = (
        ('Данные аккаунта', {
            'fields': ('new_username', 'new_email', 'new_password', 'password_hint'),
            'description': (
                '<strong>При создании</strong> заполните логин и пароль. '
                'Поле «Пароль (подсказка)» сохраняет введённый пароль в открытом виде.'
            ),
        }),
        ('Профиль', {
            'fields': ('full_name', 'phone'),
        }),
    )

    class Media:
        js = ('studio/admin-password-toggle.js',)

    @admin.display(description='Логин')
    def login_display(self, obj):
        return obj.user.username

    @admin.display(description='Email')
    def email_display(self, obj):
        return obj.user.email or '—'

    @admin.display(description='Пароль (подсказка)')
    def password_hint_display(self, obj):
        if obj.password_hint:
            return format_html(
                '<span style="font-family:monospace;background:#f0eee8;padding:2px 6px;border-radius:3px;">{}</span>',
                obj.password_hint,
            )
        return '—'

    @admin.display(description='Дети')
    def children_list(self, obj):
        names = [c.full_name for c in obj.children.all()]
        return ', '.join(names) if names else '—'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['new_username'].initial = obj.user.username
            form.base_fields['new_email'].initial = obj.user.email
        return form

    def save_model(self, request, obj, form, change):
        new_username = form.cleaned_data.get('new_username', '').strip()
        new_email = form.cleaned_data.get('new_email', '').strip()
        new_password = form.cleaned_data.get('new_password', '').strip()

        if not change:
            user = User.objects.create_user(
                username=new_username,
                email=new_email,
                password=new_password or None,
            )
            obj.user = user
        else:
            user = obj.user
            if new_username and new_username != user.username:
                user.username = new_username
                user.save(update_fields=['username'])
            if new_email != user.email:
                user.email = new_email
                user.save(update_fields=['email'])
            if new_password:
                user.set_password(new_password)
                user.save(update_fields=['password'])

        if new_password and not obj.password_hint:
            obj.password_hint = new_password
        super().save_model(request, obj, form, change)


@admin.register(LessonPayment)
class LessonPaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'status', 'created_at', 'paid_at', 'yookassa_payment_id')
    list_filter = ('status',)
    search_fields = ('student__full_name', 'yookassa_payment_id')
    readonly_fields = ('created_at', 'paid_at', 'yookassa_payment_id')


class PaymentReminderAdminBase(admin.ModelAdmin):
    search_fields = ('student__full_name', 'notes')
    date_hierarchy = 'payment_due_date'

    @admin.display(description='Родитель привязан')
    def parent_link_status(self, obj):
        linked = obj.student.parent_links.select_related('parent').first()
        if linked:
            return f'✓ {linked.parent.full_name}'
        return '— не привязан'


@admin.register(PaymentReminder)
class PaymentReminderAdmin(PaymentReminderAdminBase):
    list_display = (
        'student', 'payment_due_date', 'amount', 'show_reminder', 'visible_today', 'parent_link_status',
    )
    list_filter = ('show_reminder',)
    list_editable = ('show_reminder', 'amount')
    fields = ('student', 'payment_due_date', 'amount', 'show_reminder', 'notes')
    readonly_fields = ('paid_at', 'lesson_payment')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(paid_at__isnull=True)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        minimum, maximum = payment_amount_limits()
        form.base_fields['amount'].help_text = (
            f'От {minimum} до {maximum} ₽. Отображается в личном кабинете и уходит в ЮKassa.'
        )
        form.base_fields['show_reminder'].help_text = (
            'Снимите галочку после оплаты — запись перейдёт в раздел «Оплаченные занятия», '
            'а система создаст следующее напоминание на ту же дату следующего месяца '
            '(с той же суммой, её можно изменить).'
        )
        return form

    @admin.display(description='Видно сегодня', boolean=True)
    def visible_today(self, obj):
        return obj.is_visible_today


@admin.register(PaidPaymentReminder)
class PaidPaymentReminderAdmin(PaymentReminderAdminBase):
    list_display = (
        'student',
        'payment_due_date',
        'amount',
        'paid_at',
        'payment_source',
        'parent_link_status',
    )
    list_filter = ('paid_at',)
    readonly_fields = (
        'student', 'payment_due_date', 'amount', 'show_reminder', 'paid_at',
        'lesson_payment', 'notes', 'created_at', 'updated_at',
    )
    fields = readonly_fields

    def get_queryset(self, request):
        return super().get_queryset(request).filter(paid_at__isnull=False)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.display(description='Способ оплаты')
    def payment_source(self, obj):
        if obj.lesson_payment_id:
            lp = obj.lesson_payment
            return f'Онлайн (ЮKassa), {lp.amount} ₽'
        return 'Отмечено администратором'


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'expires_at', 'is_used', 'is_valid_display')
    list_filter = ('is_used',)
    search_fields = ('user__username',)
    readonly_fields = ('user', 'code', 'created_at', 'expires_at')

    @admin.display(description='Активен', boolean=True)
    def is_valid_display(self, obj):
        return obj.is_valid
