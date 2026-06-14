"""
ConfirmScreen — русский, программный, терминальный стиль.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.app import App
from kivy.logger import Logger

# Тема
GREEN = (0.2, 1.0, 0.3, 1)
GREEN_DIM = (0.15, 0.7, 0.2, 1)
GRAY = (0.5, 0.5, 0.5, 1)
BLUE = (0.3, 0.6, 1.0, 1)
BG = (0.08, 0.08, 0.1, 1)
INPUT_BG = (0.15, 0.15, 0.15, 1)


def t_btn(text, color=BLUE, **kw):
    return Button(text=text, font_size='15sp', background_color=color,
                  color=(1, 1, 1, 1), **kw)


class ConfirmScreen(Screen):
    """Главный экран."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        self.status_label = Label(
            text='Сеть: ожидание...',
            font_size='12sp', color=GREEN_DIM,
            size_hint_y=0.05, halign='left'
        )
        layout.add_widget(self.status_label)

        layout.add_widget(Label(
            text='WMS VIDEO CAPTURE',
            font_size='20sp', bold=True, color=GREEN,
            size_hint_y=0.08, halign='center'
        ))

        self.task_label = Label(
            text='НЕТ ЗАДАНИЯ',
            font_size='26sp', bold=True, color=GREEN,
            size_hint_y=0.12, halign='center'
        )
        layout.add_widget(self.task_label)

        self.hint_label = Label(
            text='Отсканируйте QR-код для получения задания',
            font_size='14sp', color=GREEN_DIM,
            size_hint_y=0.08, halign='center'
        )
        layout.add_widget(self.hint_label)

        self.record_btn = t_btn('УДЕРЖИВАЙТЕ 2 СЕК', GREEN_DIM, size_hint_y=0.14)
        self.record_btn.bind(on_press=self._on_record)
        layout.add_widget(self.record_btn)

        qr_btn = t_btn('СКАНИРОВАТЬ QR-КОД', BLUE, size_hint_y=0.12)
        qr_btn.bind(on_press=self._on_scan)
        layout.add_widget(qr_btn)

        settings_btn = t_btn('НАСТРОЙКИ', GRAY, size_hint_y=0.1)
        settings_btn.bind(on_press=self._on_settings)
        layout.add_widget(settings_btn)

        close_btn = t_btn('ЗАКРЫТЬ', (0.5, 0.2, 0.2, 1), size_hint_y=0.08)
        close_btn.bind(on_press=self._on_close)
        layout.add_widget(close_btn)

        layout.add_widget(Label(
            text='Roman design (c) 2025',
            font_size='10sp', color=GRAY,
            size_hint_y=0.06, halign='center'
        ))

        self.add_widget(layout)

    def on_pre_enter(self):
        app = App.get_running_app()
        if app and app.current_task_id:
            self.task_label.text = f'ЗАДАЧА: {app.current_task_id}'
            self.record_btn.background_color = (0.2, 0.8, 0.2, 1)
            self.record_btn.text = 'НАЧАТЬ ЗАПИСЬ'
            self.hint_label.text = 'Удерживайте кнопку для начала съёмки'
        else:
            self.task_label.text = 'НЕТ ЗАДАНИЯ'
            self.record_btn.background_color = GREEN_DIM
            self.hint_label.text = 'Отсканируйте QR-код для получения задания'

    def on_enter(self):
        self.status_label.text = 'Сеть: готов'
        Clock.schedule_once(lambda dt: self._check_net(), 2.0)

    def _check_net(self):
        try:
            app = App.get_running_app()
            if app:
                smb = app.network.check_connectivity()
                self.status_label.text = 'Сеть: OK' if smb else 'Сеть: нет связи'
        except Exception:
            self.status_label.text = 'Сеть: —'

    def _on_record(self, *args):
        try:
            app = App.get_running_app()
            if app:
                app.start_recording()
        except Exception as e:
            Logger.error(f"Record error: {e}")

    def _on_scan(self, *args):
        try:
            app = App.get_running_app()
            if app:
                app.on_scan_requested()
        except Exception as e:
            Logger.error(f"Scan error: {e}")

    def _on_settings(self, *args):
        try:
            app = App.get_running_app()
            if app:
                app.open_settings()
        except Exception as e:
            Logger.error(f"Settings error: {e}")

    def _on_close(self, *args):
        try:
            app = App.get_running_app()
            if app:
                app.on_request_close()
        except Exception as e:
            Logger.error(f"Close error: {e}")
