"""
DoneScreen — русский, без выгрузки (тестовый режим).
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.app import App
from kivy.logger import Logger

GREEN = (0.2, 1.0, 0.3, 1)
GREEN_DIM = (0.15, 0.7, 0.2, 1)
GRAY = (0.5, 0.5, 0.5, 1)
BLUE = (0.3, 0.6, 1.0, 1)
RED = (1.0, 0.3, 0.3, 1)


class DoneScreen(Screen):
    """Завершение задачи."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=25, spacing=12)

        self.title_label = Label(
            text='', font_size='20sp', bold=True, color=GREEN,
            size_hint_y=0.08, halign='center'
        )
        layout.add_widget(self.title_label)

        self.info_label = Label(
            text='', font_size='14sp', color=GREEN_DIM,
            size_hint_y=0.15, halign='center'
        )
        layout.add_widget(self.info_label)

        self.btn1 = Button(
            text='', font_size='15sp', size_hint_y=0.12,
            color=(1, 1, 1, 1)
        )
        self.btn1.bind(on_press=self._on_btn1)
        layout.add_widget(self.btn1)

        self.btn2 = Button(
            text='', font_size='15sp', size_hint_y=0.12,
            color=(1, 1, 1, 1)
        )
        self.btn2.bind(on_press=self._on_btn2)
        layout.add_widget(self.btn2)

        self.btn3 = Button(
            text='ЗАКРЫТЬ', font_size='14sp', size_hint_y=0.1,
            background_color=GRAY, color=(1, 1, 1, 1)
        )
        self.btn3.bind(on_press=self._on_btn3)
        layout.add_widget(self.btn3)

        self.add_widget(layout)

    def on_enter(self):
        self.show_id_change_dialog()

    def show_id_change_dialog(self):
        app = App.get_running_app()
        tid = app.current_task_id if app else '---'
        self.title_label.text = 'ВИДЕО СОХРАНЕНО'
        self.info_label.text = f'ID задачи: {tid}'
        self.btn1.text = f'ИСПОЛЬЗОВАТЬ ID: {tid}'
        self.btn1.background_color = (0.2, 0.8, 0.2, 1)
        self.btn1.disabled = False
        self.btn1.opacity = 1
        self.btn2.text = 'СКАНИРОВАТЬ QR-КОД'
        self.btn2.background_color = BLUE
        self.btn2.disabled = False
        self.btn2.opacity = 1
        self.btn3.text = 'В ГЛАВНОЕ МЕНЮ'
        self.btn3.background_color = GRAY
        self.btn3.disabled = False
        self.btn3.opacity = 1

    def _on_btn1(self, *args):
        """Использовать текущий ID — в главное меню."""
        Logger.info("DoneScreen: use current ID")
        app = App.get_running_app()
        if app:
            app.sm.current = 'confirm'

    def _on_btn2(self, *args):
        """QR-сканер."""
        Logger.info("DoneScreen: open QR scanner")
        app = App.get_running_app()
        if app:
            app.on_scan_requested()

    def _on_btn3(self, *args):
        """Закрыть — в главное меню."""
        Logger.info("DoneScreen: back to confirm")
        app = App.get_running_app()
        if app:
            app.sm.current = 'confirm'
