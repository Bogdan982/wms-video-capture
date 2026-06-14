"""
SplashScreen — русский, программный.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.app import App
from kivy.logger import Logger

GREEN = (0.2, 1.0, 0.3, 1)
GREEN_DIM = (0.15, 0.7, 0.2, 1)
GRAY = (0.5, 0.5, 0.5, 1)


class SplashScreen(Screen):
    """Заставка."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=4)

        layout.add_widget(Label(size_hint_y=0.1))

        lines = [
            'ПРОГРАММА АВТОМАТИЗАЦИИ',
            'ВИДЕОФИКСАЦИИ СКЛАДСКОГО',
            'ПРОИЗВОДСТВА'
        ]
        for line in lines:
            layout.add_widget(Label(
                text=line, font_size='16sp', bold=True,
                color=GREEN, size_hint_y=0.07, halign='center'
            ))

        layout.add_widget(Label(size_hint_y=0.06))

        self.org_label = Label(
            text='НАЗВАНИЕ ОРГАНИЗАЦИИ',
            font_size='22sp', bold=True,
            color=GREEN_DIM, size_hint_y=0.14, halign='center'
        )
        layout.add_widget(self.org_label)

        layout.add_widget(Label(size_hint_y=0.1))

        layout.add_widget(Label(
            text='Roman design (c) 2025',
            font_size='11sp', color=GRAY,
            size_hint_y=0.06, halign='center'
        ))

        layout.add_widget(Label(
            text='v1.0.0',
            font_size='10sp', color=GREEN_DIM,
            size_hint_y=0.05, halign='center'
        ))

        self.add_widget(layout)

    def on_pre_enter(self):
        app = App.get_running_app()
        if app:
            org = app.config_data.get('org_name', '')
            if org:
                self.org_label.text = org
        Clock.schedule_once(self._goto_main, 2.5)

    def _goto_main(self, dt):
        Logger.info("SplashScreen: -> Confirm")
        app = App.get_running_app()
        if app:
            app.show_confirm()
