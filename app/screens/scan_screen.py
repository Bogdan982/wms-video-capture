"""
Экран QR-сканирования — программный (без KV).
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.app import App


class ScanScreen(Screen):
    """QR-сканер — программный."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._scanned_id = None
        
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(
            text='Сканирование QR-кода',
            font_size='22sp',
            bold=True,
            color=(0.2, 0.6, 1.0, 1),
            size_hint_y=0.1
        ))
        
        self.status_label = Label(
            text='Запуск сканера...',
            font_size='16sp',
            color=(0.8, 0.8, 0.8, 1),
            halign='center',
            size_hint_y=0.1
        )
        layout.add_widget(self.status_label)
        
        self.result_label = Label(
            text='',
            font_size='20sp',
            bold=True,
            color=(0.2, 1.0, 0.2, 1),
            halign='center',
            size_hint_y=0.3
        )
        layout.add_widget(self.result_label)
        
        btn_back = Button(
            text='Назад (без сканирования)',
            font_size='16sp',
            size_hint_y=0.15,
            background_color=(0.5, 0.5, 0.5, 0.7)
        )
        btn_back.bind(on_press=self._go_back)
        layout.add_widget(btn_back)
        
        btn_rescan = Button(
            text='Сканировать снова',
            font_size='16sp',
            size_hint_y=0.15,
            background_color=(0.2, 0.6, 1.0, 1)
        )
        btn_rescan.bind(on_press=self._restart)
        layout.add_widget(btn_rescan)
        
        self.add_widget(layout)

    def on_enter(self):
        self.status_label.text = 'Ожидание QR-кода...'
        self.result_label.text = ''
        self._scanned_id = None

    def show_scanner_unavailable(self):
        """QR-сканер не найден — показываем сообщение."""
        self.status_label.text = '❌ QR-сканер не найден'
        self.result_label.text = ('Установите ZXing Barcode Scanner\n'
                                   'из Google Play или используйте\n'
                                   'ручной ввод ID.')
        Logger.warning("ScanScreen: сканер недоступен")

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
