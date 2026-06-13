"""
SplashScreen — заставка (программный, без KV).
Тёмно-синий фон, 3 сек, переход на ConfirmScreen.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.app import App
from kivy.logger import Logger


class SplashScreen(Screen):
    """Заставка при запуске."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(size_hint_y=0.15))
        
        layout.add_widget(Label(
            text='PROGRAMMA AVTOMATIZACII',
            font_size='18sp', bold=True,
            color=(1, 1, 1, 1), size_hint_y=0.08, halign='center'
        ))
        layout.add_widget(Label(
            text='VIDEOFIXACII SKLADSKOGO',
            font_size='18sp', bold=True,
            color=(1, 1, 1, 1), size_hint_y=0.08, halign='center'
        ))
        layout.add_widget(Label(
            text='PROIZVODSTVA',
            font_size='18sp', bold=True,
            color=(1, 1, 1, 1), size_hint_y=0.08, halign='center'
        ))
        
        layout.add_widget(Label(size_hint_y=0.05))
        
        self.org_label = Label(
            text='NAZVANIE ORGANIZACII',
            font_size='26sp', bold=True,
            color=(1, 1, 1, 0.9), size_hint_y=0.2, halign='center'
        )
        layout.add_widget(self.org_label)
        
        layout.add_widget(Label(size_hint_y=0.15))
        
        layout.add_widget(Label(
            text='Roman design (c) 2025',
            font_size='11sp', color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.08, halign='center'
        ))
        
        self.add_widget(layout)

    def on_pre_enter(self):
        app = App.get_running_app()
        if app:
            org = app.config_data.get('org_name', '')
            if org:
                self.org_label.text = org
        Clock.schedule_once(self._goto_main, 3.0)

    def _goto_main(self, dt):
        Logger.info("SplashScreen: -> ConfirmScreen")
        app = App.get_running_app()
        if app:
            app.show_confirm()
