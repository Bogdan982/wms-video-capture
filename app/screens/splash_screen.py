"""
SplashScreen — заставка при запуске.
Градиент: голубой → синий → чёрный (сверху вниз).
Заголовок + название организации + копирайт.
"""
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger

SPLASH_KV = """
<SplashScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20

        Widget:
            size_hint_y: 0.15

        Label:
            text: 'ПРОГРАММА АВТОМАТИЗАЦИИ'
            font_size: '18sp'
            bold: True
            color: (1, 1, 1, 1)
            halign: 'center'
            size_hint_y: 0.09

        Label:
            text: 'ВИДЕОФИКСАЦИИ СКЛАДСКОГО'
            font_size: '18sp'
            bold: True
            color: (1, 1, 1, 1)
            halign: 'center'
            size_hint_y: 0.09

        Label:
            text: 'ПРОИЗВОДСТВА'
            font_size: '18sp'
            bold: True
            color: (1, 1, 1, 1)
            halign: 'center'
            size_hint_y: 0.25

        Widget:
            size_hint_y: 0.05

        Label:
            text: root.org_name
            font_size: '28sp'
            bold: True
            color: (1, 1, 1, 0.9)
            halign: 'center'
            size_hint_y: 0.2

        Widget:

        Label:
            text: 'Roman design (c) 2025'
            font_size: '11sp'
            color: (0.5, 0.5, 0.5, 1)
            halign: 'center'
            size_hint_y: 0.08

        Widget:
            size_hint_y: 0.1

        Label:
            text: root.version_text
            font_size: '12sp'
            color: (0.4, 0.7, 1.0, 1)
            halign: 'center'
            size_hint_y: 0.05
"""


class SplashScreen(Screen):
    """Заставка с градиентом."""

    org_name = StringProperty('НАЗВАНИЕ ОРГАНИЗАЦИИ')
    version_text = StringProperty('v1.0.0')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(SPLASH_KV)

    def on_pre_enter(self):
        """При появлении — загружаем название организации из конфига."""
        app = self._get_app()
        if app:
            org = app.config_data.get('org_name', 'НАЗВАНИЕ ОРГАНИЗАЦИИ')
            self.org_name = org if org else 'НАЗВАНИЕ ОРГАНИЗАЦИИ'
            self.version_text = f'v{app.config_data.get("version", "1.0.0")}'
        # Градиентный фон
        self._apply_gradient()
        # Через 3 сек переходим к основному экрану
        Clock.schedule_once(self._goto_main, 3.0)

    def _apply_gradient(self):
        """Рисует фон."""
        with self.canvas.before:
            Color(0.05, 0.1, 0.3, 1)  # тёмно-синий
            self._rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_gradient, pos=self._update_gradient)

    def _update_gradient(self, *args):
        if hasattr(self, '_rect'):
            self._rect.size = self.size
            self._rect.pos = self.pos

    def _goto_main(self, dt):
        """Переход к ConfirmScreen."""
        Logger.info("SplashScreen: переход к ConfirmScreen")
        app = App.get_running_app()
        if app:
            app.show_confirm()

    def _get_app(self):
        return App.get_running_app()
