"""
SplashScreen — терминальный стиль, программный.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.app import App
from kivy.logger import Logger
from app.theme import THEME_GREEN, THEME_GREEN_DIM, THEME_GRAY


class SplashScreen(Screen):
    """Заставка."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=6)

        layout.add_widget(Label(size_hint_y=0.1))

        for line in ['PROGRAMMA', 'AVTOMATIZACII', 'VIDEOFIXACII SKLADSKOGO', 'PROIZVODSTVA']:
            layout.add_widget(Label(
                text=line, font_size='18sp', bold=True,
                color=THEME_GREEN, size_hint_y=0.07, halign='center'
            ))

        layout.add_widget(Label(size_hint_y=0.08))

        self.org_label = Label(
            text='NAZVANIE ORGANIZACII',
            font_size='24sp', bold=True,
            color=THEME_GREEN_DIM, size_hint_y=0.15, halign='center'
        )
        layout.add_widget(self.org_label)

        layout.add_widget(Label(size_hint_y=0.12))

        layout.add_widget(Label(
            text='Roman design (c) 2025',
            font_size='11sp', color=THEME_GRAY,
            size_hint_y=0.06, halign='center'
        ))

        layout.add_widget(Label(
            text='v1.0.0',
            font_size='10sp', color=THEME_GREEN_DIM,
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
