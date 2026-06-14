"""
ScanScreen — ultra simple.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


class ScanScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=25, spacing=12)

        layout.add_widget(Label(
            text='СКАНИРОВАНИЕ QR-КОДА',
            font_size='20sp', bold=True,
            color=(0.3, 0.6, 1.0, 1),
            size_hint_y=0.1, halign='center'
        ))

        layout.add_widget(Label(
            text='Наведите камеру на QR-код',
            font_size='14sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=0.08, halign='center'
        ))

        layout.add_widget(Label(
            text='(ZXing scanner required)',
            font_size='12sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.06, halign='center'
        ))

        btn = Button(
            text='НАЗАД',
            font_size='16sp', size_hint_y=0.12,
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1)
        )
        btn.bind(on_press=self._back)
        layout.add_widget(btn)

        self.add_widget(layout)

    def _back(self, *args):
        try:
            from kivy.app import App
            App.get_running_app().sm.current = 'confirm'
        except Exception:
            pass
