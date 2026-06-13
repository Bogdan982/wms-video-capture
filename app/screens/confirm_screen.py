"""
ConfirmScreen — ultra simple for debugging.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger


class ConfirmScreen(Screen):
    """Минимальная версия для отладки."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        layout.add_widget(Label(
            text='WMS Video Capture',
            font_size='24sp',
            bold=True,
            color=(0.2, 0.6, 1.0, 1),
            size_hint_y=0.15
        ))
        
        layout.add_widget(Label(
            text='Приложение запущено!',
            font_size='18sp',
            halign='center',
            size_hint_y=0.2
        ))
        
        btn = Button(
            text='Начать съёмку',
            font_size='20sp',
            size_hint_y=0.2,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        btn.bind(on_press=self._start)
        layout.add_widget(btn)
        
        btn_qr = Button(
            text='QR-сканер',
            font_size='16sp',
            size_hint_y=0.15,
            background_color=(0.2, 0.6, 1.0, 1)
        )
        btn_qr.bind(on_press=self._start_qr)
        layout.add_widget(btn_qr)
        
        btn_settings = Button(
            text='Настройки',
            font_size='14sp',
            size_hint_y=0.1,
            background_color=(0.3, 0.3, 0.5, 0.7)
        )
        btn_settings.bind(on_press=self._open_settings)
        layout.add_widget(btn_settings)

        layout.add_widget(Label(
            text='Roman design (c) 2025',
            font_size='10sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.1
        ))
        
        self.add_widget(layout)

    def _start(self, *args):
        Logger.info("ConfirmScreen: start recording")
        try:
            app = self._get_app()
            if app:
                app.start_recording()
        except Exception as e:
            Logger.error(f"ConfirmScreen: _start error: {e}")

    def _start_qr(self, *args):
        Logger.info("ConfirmScreen: QR scan")
        try:
            app = self._get_app()
            if app:
                app.on_scan_requested()
        except Exception as e:
            Logger.error(f"ConfirmScreen: QR scan error: {e}")

    def _open_settings(self, *args):
        Logger.info("ConfirmScreen: open settings")
        try:
            app = self._get_app()
            if app:
                app.open_settings()
        except Exception as e:
            Logger.error(f"ConfirmScreen: settings error: {e}")

    def _get_app(self):
        try:
            return self.manager.parent
        except Exception:
            return None
