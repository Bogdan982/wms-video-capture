"""
DoneScreen — ultra simple, no external calls.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


class DoneScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=25, spacing=12)

        layout.add_widget(Label(
            text='ВИДЕО СОХРАНЕНО',
            font_size='20sp', bold=True,
            color=(0.2, 1.0, 0.3, 1),
            size_hint_y=0.1, halign='center'
        ))

        layout.add_widget(Label(
            text='Выберите действие:',
            font_size='14sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.08, halign='center'
        ))

        btn1 = Button(
            text='В ГЛАВНОЕ МЕНЮ',
            font_size='16sp', size_hint_y=0.12,
            background_color=(0.2, 0.8, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        btn1.bind(on_press=self._back)
        layout.add_widget(btn1)

        btn2 = Button(
            text='ПРОВЕРИТЬ СЕТЬ',
            font_size='16sp', size_hint_y=0.12,
            background_color=(0.3, 0.6, 1.0, 1),
            color=(1, 1, 1, 1)
        )
        btn2.bind(on_press=self._check)
        layout.add_widget(btn2)

        self.status_label = Label(
            text='',
            font_size='14sp',
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=0.2, halign='center'
        )
        layout.add_widget(self.status_label)

        self.add_widget(layout)

    def _back(self, *args):
        try:
            from kivy.app import App
            App.get_running_app().sm.current = 'confirm'
        except Exception:
            pass

    def _check(self, *args):
        self.status_label.text = 'Сеть: проверка...'
        try:
            from kivy.app import App
            app = App.get_running_app()
            if app and app.network:
                ok = app.network.check_connectivity()
                self.status_label.text = 'Сеть: ДОСТУПНА' if ok else 'Сеть: НЕДОСТУПНА'
                self.status_label.color = (0.2, 1.0, 0.3, 1) if ok else (1.0, 0.3, 0.3, 1)
            else:
                self.status_label.text = 'Сервис сети не готов'
                self.status_label.color = (1.0, 0.3, 0.3, 1)
        except Exception as e:
            self.status_label.text = f'Ошибка: {e}'
            self.status_label.color = (1.0, 0.3, 0.3, 1)
