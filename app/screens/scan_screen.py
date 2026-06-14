"""
ScanScreen — русский, программный.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.app import App
from kivy.logger import Logger

GREEN = (0.2, 1.0, 0.3, 1)
GREEN_DIM = (0.15, 0.7, 0.2, 1)
GRAY = (0.5, 0.5, 0.5, 1)
BLUE = (0.3, 0.6, 1.0, 1)
RED = (1.0, 0.3, 0.3, 1)


class ScanScreen(Screen):
    """QR-сканер."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._scanned_id = None
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=25, spacing=12)

        layout.add_widget(Label(
            text='СКАНИРОВАНИЕ QR-КОДА',
            font_size='20sp', bold=True, color=BLUE,
            size_hint_y=0.08, halign='center'
        ))

        self.status_label = Label(
            text='Запуск сканера...',
            font_size='15sp', color=GREEN_DIM,
            size_hint_y=0.08, halign='center'
        )
        layout.add_widget(self.status_label)

        self.result_label = Label(
            text='',
            font_size='22sp', bold=True, color=GREEN,
            size_hint_y=0.2, halign='center'
        )
        layout.add_widget(self.result_label)

        self.info_label = Label(
            text='Наведите камеру на QR-код\nс идентификатором заказа',
            font_size='14sp', color=GREEN_DIM,
            size_hint_y=0.12, halign='center'
        )
        layout.add_widget(self.info_label)

        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=10)
        btn_back = Button(text='НАЗАД', font_size='14sp',
                          background_color=GRAY, color=(1, 1, 1, 1))
        btn_back.bind(on_press=self._go_back)
        btn_box.add_widget(btn_back)
        btn_scan = Button(text='СКАНИРОВАТЬ', font_size='14sp',
                          background_color=BLUE, color=(1, 1, 1, 1))
        btn_scan.bind(on_press=self._restart)
        btn_box.add_widget(btn_scan)
        layout.add_widget(btn_box)

        self.add_widget(layout)

    def on_enter(self):
        self.status_label.text = 'Ожидание QR-кода...'
        self.result_label.text = ''

    def on_scan_result(self, scanned_text: str):
        if scanned_text:
            self._scanned_id = scanned_text
            self.result_label.text = f'ID: {scanned_text}'
            self.status_label.text = 'Получен!'
            Clock.schedule_once(lambda dt: self._apply_result(), 1.5)

    def _apply_result(self):
        if self._scanned_id:
            app = App.get_running_app()
            if app:
                app.on_scan_result(self._scanned_id)

    def _restart(self, *args):
        self.result_label.text = ''
        self.status_label.text = 'Перезапуск...'
        app = App.get_running_app()
        if app:
            app.qr.start_scan()

    def _go_back(self, *args):
        app = App.get_running_app()
        if app:
            app.on_use_current_id()
