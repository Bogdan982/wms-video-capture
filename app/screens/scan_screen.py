"""
Экран QR-сканирования идентификатора.

Запускает системный QR-сканер (ZXing Barcode Scanner) через Intent.
Показывает инструкцию и статус.
"""
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.logger import Logger

SCAN_KV = """
<ScanScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: 15
        padding: 30

        Label:
            text: '📷 Сканирование QR-кода'
            font_size: '24sp'
            bold: True
            color: (0.2, 0.6, 1.0, 1)

        Widget:
            size_hint_y: 0.05

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.4
            spacing: 10

            Label:
                text: 'Наведите камеру на QR-код'
                font_size: '18sp'
                color: (0.8, 0.8, 0.8, 1)
                halign: 'center'
                text_size: (self.width, None)

            Label:
                text: 'с идентификатором заказа'
                font_size: '18sp'
                color: (0.7, 0.7, 0.7, 1)
                halign: 'center'
                text_size: (self.width, None)

            Label:
                text: root.status_text
                font_size: '16sp'
                color: (1, 1, 1, root.status_alpha)
                halign: 'center'

        Widget:

        # Индикатор сканирования
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.2

            Label:
                text: root.scanned_id_display
                font_size: '28sp'
                bold: True
                color: (0.2, 0.8, 0.2, 1)
                halign: 'center'

            Label:
                text: root.scanned_label
                font_size: '14sp'
                color: (0.6, 0.6, 0.6, 1)
                halign: 'center'

        Widget:

        # Кнопки
        BoxLayout:
            size_hint_y: 0.15
            spacing: 15

            Button:
                text: '↩ Назад'
                font_size: '18sp'
                background_color: (0.5, 0.5, 0.5, 0.7)
                on_release: root.go_back()

            Button:
                text: '🔄 Повторить'
                font_size: '18sp'
                background_color: (0.2, 0.6, 1, 0.7)
                disabled: root.scan_running
                on_release: root.restart_scan()
"""


class ScanScreen(Screen):
    """Экран QR-сканирования с инструкцией."""

    status_text = StringProperty('Ожидание запуска сканера...')
    status_alpha = 1.0
    scanned_id_display = StringProperty('')
    scanned_label = StringProperty('')
    scan_running = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(SCAN_KV)
        self._scanned_id = None

    def on_enter(self):
        """При переходе — запускаем сканер."""
        self.status_text = 'Запуск сканера...'
        self.scanned_id_display = ''
        self.scanned_label = ''
        self._scanned_id = None
        self.scan_running = True
        Logger.info("ScanScreen: ожидание QR-кода")

    def on_leave(self):
        """Уход с экрана."""
        self.scan_running = False

    def on_scan_result(self, scanned_text: str):
        """
        Результат сканирования.
        Вызывается из QRService при успешном сканировании.
        """
        if not scanned_text:
            self.status_text = 'QR-код не распознан. Попробуйте снова.'
            return

        self._scanned_id = scanned_text
        self.scanned_id_display = scanned_text
        self.scanned_label = '✅ Идентификатор получен'
        self.status_text = 'Сканирование выполнено успешно'
        self.scan_running = False

        Logger.info(f"ScanScreen: получен ID: {scanned_text}")

        # Автоматически передаём в App через 1 секунду
        Clock.schedule_once(lambda dt: self._apply_result(), 1.0)

    def _apply_result(self):
        """Передаёт результат в App."""
        if not self._scanned_id:
            return

        app = self._get_app()
        if app:
            app.on_scan_result(self._scanned_id)

    def restart_scan(self):
        """Повторный запуск сканера."""
        Logger.info("ScanScreen: повторное сканирование")
        self.status_text = 'Запуск сканера...'
        self.scanned_id_display = ''
        self.scanned_label = ''
        self._scanned_id = None
        self.scan_running = True

        app = self._get_app()
        if app:
            app.qr.start_scan()

    def go_back(self):
        """Назад (без сканирования — используем текущий ID)."""
        Logger.info("ScanScreen: возврат без сканирования")
        app = self._get_app()
        if app:
            app.on_use_current_id()

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()
