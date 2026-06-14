"""
ScanScreen — защищён от краша.
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


class ScanScreen(Screen):
    """QR-сканер."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=25, spacing=12)

        layout.add_widget(Label(
            text='СКАНИРОВАНИЕ QR-КОДА', font_size='20sp',
            bold=True, color=BLUE, size_hint_y=0.08, halign='center'
        ))

        layout.add_widget(Label(
            text='Наведите камеру на QR-код', font_size='14sp',
            color=GREEN_DIM, size_hint_y=0.06, halign='center'
        ))

        layout.add_widget(Label(
            text='с идентификатором заказа', font_size='14sp',
            color=GREEN_DIM, size_hint_y=0.06, halign='center'
        ))

        self.result_label = Label(
            text='', font_size='22sp', bold=True, color=GREEN,
            size_hint_y=0.2, halign='center'
        )
        layout.add_widget(self.result_label)

        btn_back = Button(
            text='НАЗАД', font_size='14sp', size_hint_y=0.12,
            background_color=GRAY, color=(1, 1, 1, 1)
        )
        btn_back.bind(on_press=self._go_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def _go_back(self, *args):
        try:
            app = App.get_running_app()
            if app:
                app.sm.current = 'confirm'
        except Exception:
            pass
