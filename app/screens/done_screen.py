"""
DoneScreen — русский, программный.
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
        self._mode = 'idle'
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=25, spacing=12)

        self.status_icon = Label(
            text='', font_size='48sp', size_hint_y=0.12, halign='center'
        )
        layout.add_widget(self.status_icon)

        self.title_label = Label(
            text='', font_size='20sp', bold=True, color=GREEN,
            size_hint_y=0.08, halign='center'
        )
        layout.add_widget(self.title_label)

        self.info_label = Label(
            text='', font_size='14sp', color=GREEN_DIM,
            size_hint_y=0.12, halign='center'
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
            text='', font_size='14sp', size_hint_y=0.1,
            color=(1, 1, 1, 1)
        )
        self.btn3.bind(on_press=self._on_btn3)
        layout.add_widget(self.btn3)

        self.add_widget(layout)

    def on_enter(self):
        self.show_id_change_dialog()

    def show_id_change_dialog(self):
        self._mode = 'id_change'
        app = App.get_running_app()
        tid = app.current_task_id if app else '---'
        self.status_icon.text = ''
        self.title_label.text = 'ВИДЕО СОХРАНЕНО'
        self.info_label.text = f'Текущий ID: {tid}'
        self.btn1.text = f'ИСПОЛЬЗОВАТЬ ID: {tid}'
        self.btn1.background_color = (0.2, 0.8, 0.2, 1)
        self.btn1.disabled = False
        self.btn1.opacity = 1
        self.btn2.text = 'СКАНИРОВАТЬ QR-КОД'
        self.btn2.background_color = BLUE
        self.btn2.disabled = False
        self.btn2.opacity = 1
        self.btn3.text = ''
        self.btn3.opacity = 0

    def show_completed(self):
        self._mode = 'completed'
        self.status_icon.text = ''
        self.title_label.text = 'ГОТОВО!'
        app = App.get_running_app()
        path = app.remote_video_path if app else ''
        self.info_label.text = f'Выгружено:\n{path}' if path else 'Видео выгружено на сервер'
        self.btn1.text = 'ОЖИДАТЬ ЗАДАЧУ'
        self.btn1.background_color = BLUE
        self.btn1.disabled = False
        self.btn1.opacity = 1
        self.btn2.text = ''
        self.btn2.opacity = 0
        self.btn3.text = 'ЗАКРЫТЬ'
        self.btn3.background_color = GRAY
        self.btn3.disabled = False
        self.btn3.opacity = 1

    def show_upload_error(self):
        self._mode = 'error'
        self.status_icon.text = ''
        self.title_label.text = 'ОШИБКА ВЫГРУЗКИ'
        self.info_label.text = 'Проверьте соединение.\nСохранено локально.'
        self.btn1.text = 'ПОВТОРИТЬ'
        self.btn1.background_color = RED
        self.btn1.disabled = False
        self.btn1.opacity = 1
        self.btn2.text = 'ОЖИДАТЬ ЗАДАЧУ'
        self.btn2.background_color = GRAY
        self.btn2.disabled = False
        self.btn2.opacity = 1
        self.btn3.text = 'ЗАКРЫТЬ'
        self.btn3.background_color = GRAY
        self.btn3.disabled = False
        self.btn3.opacity = 1

    def _on_btn1(self, *args):
        app = App.get_running_app()
        if not app:
            return
        if self._mode == 'id_change':
            app.on_use_current_id()
        elif self._mode == 'completed':
            app.sm.current = 'confirm'
        elif self._mode == 'error':
            app.on_use_current_id()

    def _on_btn2(self, *args):
        app = App.get_running_app()
        if not app:
            return
        if self._mode == 'id_change':
            app.on_scan_requested()
        elif self._mode == 'error':
            app.sm.current = 'confirm'

    def _on_btn3(self, *args):
        app = App.get_running_app()
        if not app:
            return
        if self._mode in ('completed', 'error'):
            app.sm.current = 'confirm'
