"""
ConfirmScreen — терминальный стиль, программный.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.app import App
from kivy.logger import Logger
from app.theme import THEME_BG, THEME_GREEN, THEME_GREEN_DIM, THEME_GRAY, THEME_BLUE, THEME_RED, terminal_button


class ConfirmScreen(Screen):
    """Главный экран."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Статус
        self.status_label = Label(
            text='SYS: waiting...',
            font_size='12sp',
            color=THEME_GREEN_DIM,
            size_hint_y=0.05,
            halign='left'
        )
        layout.add_widget(self.status_label)

        # Заголовок
        layout.add_widget(Label(
            text='WMS VIDEO CAPTURE',
            font_size='22sp', bold=True,
            color=THEME_GREEN,
            size_hint_y=0.1, halign='center'
        ))

        # Task ID
        self.task_label = Label(
            text='NO TASK',
            font_size='28sp', bold=True,
            color=THEME_GREEN,
            size_hint_y=0.12, halign='center'
        )
        layout.add_widget(self.task_label)

        # Подсказка
        self.hint_label = Label(
            text='Hold 2 sec to start recording',
            font_size='14sp',
            color=THEME_GREEN_DIM,
            size_hint_y=0.08, halign='center'
        )
        layout.add_widget(self.hint_label)

        # Кнопка записи
        self.record_btn = terminal_button(
            'HOLD 2 SEC TO RECORD',
            color=THEME_GREEN_DIM,
            size_hint_y=0.15
        )
        self.record_btn.bind(on_press=self._on_record)
        layout.add_widget(self.record_btn)

        # QR кнопка
        qr_btn = terminal_button(
            'SCAN QR CODE',
            color=THEME_BLUE,
            size_hint_y=0.12
        )
        qr_btn.bind(on_press=self._on_scan)
        layout.add_widget(qr_btn)

        # Настройки
        settings_btn = terminal_button(
            'SETTINGS',
            color=THEME_GRAY,
            size_hint_y=0.1
        )
        settings_btn.bind(on_press=self._on_settings)
        layout.add_widget(settings_btn)

        # Копирайт
        layout.add_widget(Label(
            text='Roman design (c) 2025',
            font_size='10sp',
            color=THEME_GRAY,
            size_hint_y=0.06, halign='center'
        ))

        self.add_widget(layout)

    def on_pre_enter(self):
        app = App.get_running_app()
        if app and app.current_task_id:
            self.task_label.text = f'TASK: {app.current_task_id}'
            self.record_btn.background_color = (0.2, 0.8, 0.2, 1)
            self.record_btn.text = 'HOLD 2 SEC TO RECORD'
            self.hint_label.text = 'Hold 2 sec to start'
        else:
            self.task_label.text = 'NO TASK'
            self.record_btn.background_color = THEME_GREEN_DIM
            self.hint_label.text = 'Scan QR to get task ID'

    def on_enter(self):
        self.status_label.text = 'SYS: ready'
        Clock.schedule_once(lambda dt: self._check_net(), 2.0)

    def _check_net(self):
        try:
            app = App.get_running_app()
            if app:
                smb = app.network.check_connectivity()
                self.status_label.text = 'SYS: SMB OK | WMS OK' if smb else 'SYS: no connection'
        except Exception:
            self.status_label.text = 'SYS: —'

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
