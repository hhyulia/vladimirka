from django.urls import path

from . import views

app_name = 'studio'

urlpatterns = [
    path('', views.home, name='home'),
    path('o-studii/', views.about, name='about'),
    path('dostizheniya/', views.achievements, name='achievements'),
    path('dostizheniya/galereya/<slug:slug>/', views.achievement_album, name='achievement_album'),
    path('napravleniya/', views.directions, name='directions'),
    path('raspisanie/', views.schedule, name='schedule'),
    path('probnoe/', views.trial_lesson, name='trial'),
    path('probnoe/zayavka/', views.trial_submit, name='trial_submit'),
    path('kontakty/', views.contact, name='contact'),
    # Правовые страницы
    path('politika-konfidencialnosti/', views.privacy_policy, name='privacy_policy'),
    path('soglasie-na-obrabotku-dannyh/', views.data_consent, name='data_consent'),
    # Авторизация
    path('vhod/', views.login_view, name='login'),
    path('vyhod/', views.logout_view, name='logout'),
    path('registratsiya/rebenok/', views.register_student, name='register_student'),
    path('registratsiya/roditel/', views.register_parent, name='register_parent'),
    # Личные кабинеты
    path('kabinet/', views.cabinet, name='cabinet'),
    path('kabinet/rebenok/', views.cabinet_student, name='cabinet_student'),
    path('kabinet/roditel/', views.cabinet_parent, name='cabinet_parent'),
    path('kabinet/nastroyki/', views.account_settings, name='account_settings'),
    path('oplata/sozdat/', views.payment_create, name='payment_create'),
    path('oplata/vozvrat/', views.payment_return, name='payment_return'),
    # Восстановление пароля
    path('vosstanovlenie/', views.password_reset_request, name='password_reset'),
    path('vosstanovlenie/otpravleno/', views.password_reset_sent, name='password_reset_sent'),
    path('vosstanovlenie/kod/<uidb64>/', views.password_reset_verify, name='password_reset_verify'),
    path('vosstanovlenie/ustanovit/<uidb64>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('vosstanovlenie/gotovo/', views.password_reset_complete, name='password_reset_complete'),
]
