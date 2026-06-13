"""
WMS Video Capture — минимальная версия для отладки краша.
"""
import kivy
kivy.require('2.2.0')

from kivy.config import Config
Config.set('kivy', 'log_level', 'info')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.lang import Builder

KV = """
<MinimalScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 20

        Label:
            text: 'WMS Video Capture'
            font_size: '24sp'
            bold: True
            color: (0.2, 0.6, 1.0, 1)
            size_hint_y: 0.15

        Label:
            text: 'App started!\\n(minimal test)'
            font_size: '18sp'
            halign: 'center'
            size_hint_y: 0.3

        Button:
            text: 'Закрыть'
            font_size: '16sp'
            size_hint_y: 0.15
            on_release: app.stop()

        Label:
            text: 'Roman design (c) 2025'
            font_size: '10sp'
            color: (0.5, 0.5, 0.5, 1)
            size_hint_y: 0.1
"""


class MinimalScreen(Screen):
    pass


class MinimalApp(App):
    def build(self):
        Builder.load_string(KV)
        sm = ScreenManager()
        sm.add_widget(MinimalScreen(name='main'))
        return sm


if __name__ == '__main__':
    MinimalApp().run()
