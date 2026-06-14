"""
DoneScreen — экран завершения (программный).
Три режима: смена ID, успешно, ошибка.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.app import App
from kivy.logger import Logger


class DoneScreen(Screen):
    """Завершение задачи."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mode = 'idle'
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)

        self.status_label = Label(
            text='',
            font_size='48sp',
            size_hint_y=0.12,
            halign='center'
        )
        layout.add_widget(self.status_label)

        self.title_label = Label(
            text='',
            font_size='22sp',
            bold=True,
            size_hint_y=0.08,
            halign='center'
        )
        layout.add_widget(self.title_label)

        self.info_label = Label(
            text='',
            font_size='15sp',
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=0.12,
            halign='center'
        )
        layout.add_widget(self.info_label)

        self.btn1 = Button(
            text='', font_size='16sp', size_hint_y=0.12,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        self.btn1.bind(on_press=self._on_btn1)
        layout.add_widget(self.btn1)

        self.btn2 = Button(
            text='', font_size='16sp', size_hint_y=0.12,
            background_color=(0.2, 0.6, 1.0, 1)
        )
        self.btn2.bind(on_press=self._on_btn2)
        layout.add_widget(self.btn2)

        self.btn3 = Button(
            text='', font_size='14sp', size_hint_y=0.1,
            background_color=(0.5, 0.5, 0.5, 0.5)
        )
        self.btn3.bind(on_press=self._on_btn3)
        layout.add_widget(self.btn3)

        self.add_widget(layout)

    def on_enter(self):
        self.show_id_change_dialog()

    def show_id_change_dialog(self):
        self._mode = 'id_change'
        app = App.get_running_app()
        tid = app.current_task_id if app else '—'
        self.status_label.text = ''
        self.title_label.text = 'Видео сохранено'
        self.info_label.text = f'ID: {tid}\nИспользовать или сменить?'
        self.btn1.text = f'Использовать ID {tid}'
        self.btn1.background_color = (0.2, 0.8, 0.2, 1)
        self.btn1.opacity = 1
        self.btn2.text = 'Сканировать QR-код'
        self.btn2.background_color = (0.2, 0.6, 1.0, 1)
        self.btn2.opacity = 1
        self.btn3.text = ''
        self.btn3.opacity = 0

    def show_completed(self):
        self._mode = 'completed'
        self.status_label.text = ''
        self.title_label.text = 'Готово!'
        app = App.get_running_app()
        path = app.remote_video_path if app else ''
        self.info_label.text = f'Выгружено:\n{path}' if path else 'Видео выгружено'
        self.btn1.text = 'Ожидать новую задачу'
        self.btn1.background_color = (0.2, 0.6, 1.0, 1)
        self.btn1.opacity = 1
        self.btn2.text = ''
        self.btn2.opacity = 0
        self.btn3.text = 'Закрыть'
        self.btn3.background_color = (0.5, 0.5, 0.5, 0.5)
        self.btn3.opacity = 1

    def show_upload_error(self):
        self._mode = 'error'
        self.status_label.text = ''
        self.title_label.text = 'Ошибка выгрузки'
        self.info_label.text = 'Проверьте соединение.\nСохранено локально.'
        self.btn1.text = 'Повторить'
        self.btn1.background_color = (0.8, 0.2, 0.2, 1)
        self.btn1.opacity = 1
        self.btn2.text = 'Ожидать новую задачу'
        self.btn2.background_color = (0.5, 0.5, 0.5, 0.5)
        self.btn2.opacity = 1
        self.btn3.text = 'Закрыть'
        self.btn3.background_color = (0.5, 0.5, 0.5, 0.5)
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
        elif self._mode == 'completed':
            pass
        elif self._mode == 'error':
            app.sm.current = 'confirm'

    def _on_btn3(self, *args):
        app = App.get_running_app()
        if not app:
            return
        if self._mode == 'completed' or self._mode == 'error':
            app.sm.current = 'confirm'
