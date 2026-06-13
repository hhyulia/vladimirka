from django.conf import settings
from django.utils.html import format_html


def absolute_media_url(url: str) -> str:
    """Абсолютный URL файла — иначе в админке превью ломается."""
    if not url:
        return ''
    if url.startswith(('http://', 'https://', '/')):
        return url
    media_url = settings.MEDIA_URL
    if not media_url.startswith('/'):
        media_url = '/' + media_url
    if not media_url.endswith('/'):
        media_url += '/'
    return media_url + url.lstrip('/')


def _focus_frame_html(
    *,
    url: str,
    x: int,
    y: int,
    file_input_id: str = '',
    x_id: str = '',
    y_id: str = '',
) -> str:
    """HTML блока превью с кадрированием."""
    if url:
        frame_inner = format_html(
            '<img src="{}" alt="" style="object-position:{x}% {y}%;">',
            url, x=x, y=y,
        )
    else:
        frame_inner = format_html(
            '<div class="image-focus-widget__empty">Загрузите фото, затем настройте фокус.</div>'
        )

    return format_html(
        '<div class="image-focus-widget" data-focus-widget data-focus-inline="0" data-image-url="{url}" '
        'data-file-input="{file_input_id}" data-input-x="{x_id}" data-input-y="{y_id}">'
        '<div class="image-focus-widget__frame" data-focus-preview>{frame_inner}'
        '<span class="image-focus-widget__marker" data-focus-marker aria-hidden="true" '
        'style="left:{x}%;top:{y}%;"></span></div>'
        '<p class="image-focus-widget__hint">Клик по превью или ползунки ниже.</p></div>',
        url=url, file_input_id=file_input_id, x_id=x_id, y_id=y_id,
        frame_inner=frame_inner, x=x, y=y,
    )


def render_image_focus_preview(obj, *, file_attr: str, x_field: str = 'image_focus_x', y_field: str = 'image_focus_y'):
    """Превью для формы админки (обложка, тренер, направление)."""
    file_field = getattr(obj, file_attr, None)
    url = absolute_media_url(file_field.url) if file_field else ''
    return _focus_frame_html(
        url=url,
        x=getattr(obj, x_field, 50),
        y=getattr(obj, y_field, 20),
        file_input_id=f'id_{file_attr}',
        x_id=f'id_{x_field}',
        y_id=f'id_{y_field}',
    )


class ImageFocusAdminMixin:
    """Подключает превью кадрирования к ModelAdmin с загрузкой фото."""

    image_focus_file_field = 'image'

    class Media:
        css = {'all': ('studio/admin-image-focus.css',)}
        js = ('studio/admin-image-focus.js',)

    @property
    def image_focus_readonly_field(self):
        return f'{self.image_focus_file_field}_focus_preview'

    def get_image_focus_preview(self, obj):
        return render_image_focus_preview(obj, file_attr=self.image_focus_file_field)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        preview = self.image_focus_readonly_field
        if preview not in readonly:
            readonly.append(preview)
        return readonly

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        preview = self.image_focus_readonly_field
        file_field = self.image_focus_file_field
        focus_fields = ['image_focus_x', 'image_focus_y']

        if preview not in fields and file_field in fields:
            idx = fields.index(file_field) + 1
            insert = [preview, *focus_fields]
            for name in insert:
                if name not in fields:
                    fields.insert(idx, name)
                    idx += 1
        return fields
