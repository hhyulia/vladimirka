from __future__ import annotations

import re
from datetime import date

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone

from .models import (
    ChildRecord,
    ContactMessage,
    DanceGroup,
    ParentProfile,
    StudentProfile,
    TrialApplication,
    age_from_birth_date,
    validate_ru_phone,
)

# ── Виджет телефона с JS-маской ─────────────────
PHONE_ATTRS = {
    'type': 'tel',
    'inputmode': 'tel',
    'autocomplete': 'tel',
    'placeholder': '+7 (___) ___-__-__',
    'data-phone-mask': '1',
}


def normalize_phone(value: str) -> str:
    """Приводит телефон к +7XXXXXXXXXX."""
    digits = re.sub(r'\D', '', value)
    if digits.startswith('8') and len(digits) == 11:
        digits = '7' + digits[1:]
    if not digits.startswith('7'):
        digits = '7' + digits
    return '+' + digits


def normalize_strict_ru_phone(value: str) -> str:
    """
    Строго нормализует номер к +7XXXXXXXXXX.
    Принимает только полный российский номер (10 или 11 цифр).
    """
    raw = (value or '').strip()
    digits = re.sub(r'\D', '', raw)

    if len(digits) == 10:
        digits = '7' + digits
    elif len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]

    if len(digits) != 11 or not digits.startswith('7'):
        raise forms.ValidationError('Введите корректный номер в формате +7 (XXX) XXX-XX-XX.')

    normalized = '+' + digits
    validate_ru_phone(normalized)
    return normalized


class TrialApplicationForm(forms.ModelForm):
    class Meta:
        model = TrialApplication
        fields = (
            'name',
            'phone',
            'email',
            'age',
            'preferred_direction',
            'preferred_time_note',
            'comment',
        )
        labels = {
            'name': 'Имя',
            'phone': 'Телефон',
            'email': 'Email',
            'age': 'Возраст',
            'preferred_direction': 'Интересующее направление',
            'preferred_time_note': 'Удобное время',
            'comment': 'Комментарий',
        }
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'phone': forms.TextInput(attrs=PHONE_ATTRS),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'example@mail.ru'}),
            'age': forms.NumberInput(attrs={'min': 1, 'max': 120}),
            'preferred_time_note': forms.TextInput(attrs={'placeholder': 'Например: вечер будних дней'}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_phone(self):
        value = (self.cleaned_data.get('phone') or '').strip()
        if not value:
            return value
        return normalize_strict_ru_phone(value)


# ── Регистрация ученика ──────────────────────────

class StudentRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        label='ФИО',
        max_length=300,
        widget=forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': 'Иванов Иван Иванович'}),
    )
    birth_date = forms.DateField(
        label='Дата рождения',
        widget=forms.DateInput(attrs={'type': 'date', 'autocomplete': 'bday'}),
        help_text='Если вам уже исполнилось 18 лет, укажите свой email — он нужен для писем об оплате.',
    )
    phone = forms.CharField(
        label='Телефон (необязательно)',
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs=PHONE_ATTRS),
    )
    email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'example@mail.ru'}),
        help_text=(
            'Для занимающихся младше 18 лет необязательно, если есть привязанный родитель с почтой. '
            'С 18 лет указывать email обязательно.'
        ),
    )
    group = forms.ModelChoiceField(
        label='Группа',
        queryset=DanceGroup.objects.filter(is_active=True),
        empty_label='— выберите группу —',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'full_name', 'birth_date', 'phone', 'group', 'password1', 'password2')
        labels = {'username': 'Логин'}
        help_texts = {'username': ''}

    def clean_birth_date(self) -> date:
        birth_date = self.cleaned_data['birth_date']
        today = timezone.localtime().date()
        if birth_date > today:
            raise forms.ValidationError('Дата рождения не может быть в будущем.')
        if age_from_birth_date(birth_date) > 120:
            raise forms.ValidationError('Проверьте корректность даты рождения.')
        return birth_date

    def clean(self) -> dict[str, object]:
        cleaned_data = super().clean()
        birth_date = cleaned_data.get('birth_date')
        raw_email = (cleaned_data.get('email') or '').strip()

        # Частично заполненная форма: не дублируем ошибки полей выше по цепочке
        if birth_date is None:
            return cleaned_data

        if age_from_birth_date(birth_date) >= 18 and not raw_email:
            self.add_error(
                'email',
                'Укажите email — с 18 лет уведомления об оплате направляются на ваш адрес.',
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data.get('email') or '').strip()
        if commit:
            user.save()
            raw_phone = (self.cleaned_data.get('phone') or '').strip()
            phone_value = normalize_phone(raw_phone) if raw_phone else ''
            StudentProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                birth_date=self.cleaned_data['birth_date'],
                phone=phone_value,
                group=self.cleaned_data['group'],
            )
        return user


# ── Регистрация родителя ─────────────────────────

class ParentRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        label='ФИО',
        max_length=300,
        widget=forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': 'Иванова Мария Петровна'}),
    )
    phone = forms.CharField(
        label='Телефон',
        max_length=25,
        widget=forms.TextInput(attrs=PHONE_ATTRS),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'example@mail.ru'}),
        help_text='На этот адрес будут приходить напоминания об оплате',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'full_name', 'phone', 'password1', 'password2')
        labels = {'username': 'Логин'}
        help_texts = {'username': ''}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            ParentProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                phone=normalize_phone(self.cleaned_data['phone']),
            )
        return user


# ── Форма входа ──────────────────────────────────

class StudioLoginForm(AuthenticationForm):
    """Тонкая обёртка над стандартной формой с русскими лейблами."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'
        self.fields['username'].widget.attrs['placeholder'] = 'Введите логин'
        self.fields['password'].widget.attrs['placeholder'] = 'Введите пароль'


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'phone', 'message')
        labels = {
            'name': 'Имя',
            'email': 'Email',
            'phone': 'Телефон',
            'message': 'Сообщение',
        }
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'example@mail.ru'}),
            'phone': forms.TextInput(attrs=PHONE_ATTRS),
            'message': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_phone(self):
        value = (self.cleaned_data.get('phone') or '').strip()
        if not value:
            return value
        return normalize_strict_ru_phone(value)


# ── Восстановление пароля ────────────────────────

class AccountResetRequestForm(forms.Form):
    """Запрос восстановления для любого аккаунта: только логин."""
    username = forms.CharField(
        label='Логин',
        max_length=150,
        widget=forms.TextInput(attrs={'autocomplete': 'username', 'placeholder': 'Введите логин'}),
    )


class VerifyCodeForm(forms.Form):
    """Ввод 6-значного кода из письма."""
    code = forms.CharField(
        label='Код из письма',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'placeholder': '••••••',
            'maxlength': '6',
            'style': 'letter-spacing: 0.5em; font-size: 1.8rem; text-align: center; width: 100%; padding: 0.85rem 1rem; font-weight: 600;',
        }),
    )

    def clean_code(self):
        value = self.cleaned_data.get('code', '').strip()
        if not value.isdigit():
            raise forms.ValidationError('Код должен состоять из 6 цифр.')
        return value


class SetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Минимум 8 символов'}),
        min_length=8,
    )
    new_password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Повторите пароль'}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Пароли не совпадают.')
        return cleaned


# ── Настройки аккаунта (смена логина и пароля) ───

class ChangeUsernameForm(forms.Form):
    """Смена логина. Для подтверждения требуется текущий пароль."""
    new_username = forms.CharField(
        label='Новый логин',
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={'autocomplete': 'username', 'placeholder': 'Новый логин'}),
        help_text='Не более 150 символов: буквы, цифры и @/./+/-/_.',
    )
    current_password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': 'Подтвердите текущим паролем',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_username(self):
        username = (self.cleaned_data.get('new_username') or '').strip()
        if username == self.user.username:
            raise forms.ValidationError('Это ваш текущий логин. Введите новый.')
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('Этот логин уже занят. Выберите другой.')
        return username

    def clean_current_password(self):
        password = self.cleaned_data.get('current_password') or ''
        if not self.user.check_password(password):
            raise forms.ValidationError('Неверный текущий пароль.')
        return password


class StudioPasswordChangeForm(PasswordChangeForm):
    """Стандартная смена пароля Django с русскими подписями."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Текущий пароль'
        self.fields['old_password'].widget.attrs.update({
            'autocomplete': 'current-password',
            'placeholder': 'Введите текущий пароль',
        })
        self.fields['new_password1'].label = 'Новый пароль'
        self.fields['new_password1'].widget.attrs.update({
            'autocomplete': 'new-password',
            'placeholder': 'Минимум 8 символов',
        })
        self.fields['new_password2'].label = 'Повторите новый пароль'
        self.fields['new_password2'].widget.attrs.update({
            'autocomplete': 'new-password',
            'placeholder': 'Повторите новый пароль',
        })
