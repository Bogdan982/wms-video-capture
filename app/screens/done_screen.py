"""
DoneScreen — навигация без выгрузки (тест).
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.app import App

GREEN = (0.2, 1.0, 0.3, 1)
GREEN_DIM = (0.15, 0.7, 0.2, 1)
GRAY = (0.5, 0.5, 0.5, 1)
BLUE = (0.3, 0.6, 1.0, 1)
RED = (1.0, 0.3, 0.3, 1)


class DoneScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=25, spacing=10)

        self.title_label = Label(
            text='ВИДЕО СОХРАНЕНО', font_size='20sp', bold=True,
            color=GREEN, size_hint_y=0.08, halign='center'
        )
        layout.add_widget(self.title_label)

        self.info_label = Label(
            text='', font_size='14sp', color=GREEN_DIM,
            size_hint_y=0.12, halign='center'
        )
        layout.add_widget(self.info_label)

        # Кнопка "проверить сеть"
        btn_check = Button(
            text='ПРОВЕРИТЬ СЕТЬ', font_size='15sp', size_hint_y=0.12,
            background_color=GRAY, color=(1, 1, 1, 1)
        )
        btn_check.bind(on_press=self._check_network)
        layout.add_widget(btn_check)

        # Кнопка "сканировать QR"
        btn_qr = Button(
            text='СКАНИРОВАТЬ QR-КОД', font_size='15sp', size_hint_y=0.12,
            background_color=BLUE, color=(1, 1, 1, 1)
        )
        btn_qr.bind(on_press=self._on_scan)
        layout.add_widget(btn_qr)

        # Кнопка "в главное меню"
        btn_menu = Button(
            text='В ГЛАВНОЕ МЕНЮ', font_size='15sp', size_hint_y=0.12,
            background_color=GREEN_DIM, color=(1, 1, 1, 1)
        )
        btn_menu.bind(on_press=self._on_menu)
        layout.add_widget(btn_menu)

        self.add_widget(layout)

    def on_enter(self):
        app = App.get_running_app()
        tid = app.current_task_id if app else '---'
        self.info_label.text = f'ID задачи: {tid}'

    def _check_network(self, *args):
        try:
            app = App.get_running_app()
            if app and app.network.check_connectivity():
                self.info_label.text = 'Сеть: ДОСТУПНА'
                self.info_label.color = GREEN
            else:
                self.info_label.text = 'Сеть: НЕДОСТУПНА\nПроверьте настройки подключения'
                self.info_label.color = RED
        except Exception:
            self.info_label.text = 'Сеть: НЕДОСТУПНА\nПроверьте настройки подключения'
            self.info_label.color = RED

    def _on_scan(self, *args):
        try:
            app = App.get_running_app()
            if app:
                app.on_scan_requested()
        except Exception:
            pass

    def _on_menu(self, *args):
        app = App.get_running_app()
        if app:
            app.sm.current = 'confirm'
