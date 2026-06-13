(function () {
  function clamp(value) {
    return Math.max(0, Math.min(100, value));
  }

  function getRow(widget) {
    return widget.closest('tr.form-row') || widget.closest('.form-row') || widget.parentElement;
  }

  /** Поля фокуса: inline — в той же строке, отдельная форма — по data-input-* */
  function getInputs(widget) {
    if (widget.dataset.inputX && widget.dataset.inputY) {
      return {
        x: document.getElementById(widget.dataset.inputX),
        y: document.getElementById(widget.dataset.inputY),
      };
    }
    var row = getRow(widget);
    return {
      x: row ? row.querySelector('input[id$="-image_focus_x"]') : null,
      y: row ? row.querySelector('input[id$="-image_focus_y"]') : null,
    };
  }

  function getFileInput(widget) {
    if (widget.dataset.fileInput) {
      return document.getElementById(widget.dataset.fileInput);
    }
    var row = getRow(widget);
    return row ? row.querySelector('input[type="file"][name$="-image"]') : null;
  }

  function normalizeMediaUrl(href) {
    if (!href) return '';
    if (href.indexOf('data:') === 0 || href.indexOf('http://') === 0 || href.indexOf('https://') === 0) {
      return href;
    }
    if (href.charAt(0) === '/') return href;
    if (href.indexOf('media/') === 0) return '/' + href;
    if (/^(achievements|trainers|directions)\//.test(href)) return '/media/' + href;
    return href;
  }

  function updateMarker(widget) {
    var inputs = getInputs(widget);
    if (!inputs.x || !inputs.y) return;
    var marker = widget.querySelector('[data-focus-marker]');
    if (!marker) return;
    marker.style.left = inputs.x.value + '%';
    marker.style.top = inputs.y.value + '%';
  }

  function updatePreviewImage(widget) {
    var frame = widget.querySelector('[data-focus-preview]');
    var inputs = getInputs(widget);
    if (!frame || !inputs.x || !inputs.y) return;
    var img = frame.querySelector('img');
    if (!img) return;
    img.style.objectPosition = inputs.x.value + '% ' + inputs.y.value + '%';
  }

  function syncWidget(widget) {
    updateMarker(widget);
    updatePreviewImage(widget);
  }

  function setFromPoint(widget, clientX, clientY) {
    var frame = widget.querySelector('[data-focus-preview]');
    var inputs = getInputs(widget);
    if (!frame || !inputs.x || !inputs.y) return;
    var rect = frame.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    inputs.x.value = clamp(Math.round(((clientX - rect.left) / rect.width) * 100));
    inputs.y.value = clamp(Math.round(((clientY - rect.top) / rect.height) * 100));
    syncWidget(widget);
  }

  function ensureImage(widget, url) {
    var frame = widget.querySelector('[data-focus-preview]');
    if (!frame || !url) return;
    var empty = frame.querySelector('.image-focus-widget__empty');
    var img = frame.querySelector('img');
    if (!img) {
      if (empty) empty.remove();
      img = document.createElement('img');
      img.alt = '';
      frame.insertBefore(img, frame.querySelector('[data-focus-marker]'));
    }
    img.src = url;
    syncWidget(widget);
  }

  function bindFileInput(widget) {
    var fileInput = getFileInput(widget);
    if (!fileInput || fileInput.dataset.focusBound) return;
    fileInput.dataset.focusBound = '1';
    fileInput.addEventListener('change', function () {
      var file = fileInput.files && fileInput.files[0];
      if (!file) return;
      var reader = new FileReader();
      reader.onload = function (event) {
        ensureImage(widget, event.target.result);
      };
      reader.readAsDataURL(file);
    });
  }

  function bindWidgetEvents(widget) {
    if (widget.dataset.focusReady) return;
    widget.dataset.focusReady = '1';

    var inputs = getInputs(widget);
    if (inputs.x) inputs.x.addEventListener('input', function () { syncWidget(widget); });
    if (inputs.y) inputs.y.addEventListener('input', function () { syncWidget(widget); });

    var frame = widget.querySelector('[data-focus-preview]');
    if (frame) {
      frame.addEventListener('click', function (event) {
        setFromPoint(widget, event.clientX, event.clientY);
      });
    }
  }

  function initWidget(widget) {
    bindWidgetEvents(widget);
    bindFileInput(widget);

    var img = widget.querySelector('[data-focus-preview] img');
    if (img && img.getAttribute('src')) {
      img.src = normalizeMediaUrl(img.getAttribute('src'));
    }

    var url = normalizeMediaUrl(widget.dataset.imageUrl || '');
    if (url && !img) {
      ensureImage(widget, url);
    }

    syncWidget(widget);
  }

  function initAll() {
    document.querySelectorAll('[data-focus-widget]').forEach(initWidget);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  if (typeof django !== 'undefined' && django.jQuery) {
    django.jQuery(document).on('formset:added', function () {
      setTimeout(initAll, 50);
    });
  }
})();
