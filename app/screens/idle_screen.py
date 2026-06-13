"""
Экран ожидания задачи от WMS.
Отображается при запуске приложения, если task_id ещё не получен.
"""
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.logger import Logger

# KV-разметка (можно вынести в screens/idle.kv)
IDLE_KV = """
<IdleScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: 20
        padding: 40

        Image:
            source: 'assets/icon.png'
            size_hint: (0.3, 0.3)
            pos_hint: {'center_x': 0.5}
            allow_stretch: True

        Label:
            text: 'WMS Video Capture'
            font_size: '28sp'
            bold: True
            color: (0.2, 0.6, 1.0, 1)

        Label:
            text: root.status_text
            font_size: '16sp'
            color: (0.5, 0.5, 0.5, 1)
            halign: 'center'

        Widget:

        Label:
            text: 'Ожидание команды от WMS...'
            font_size: '14sp'
            italic: True
            color: (0.6, 0.6, 0.6, 1)

        Widget:
"""


class IdleScreen(Screen):
    """Экран ожидания задачи."""

    status_text = StringProperty('Приложение готово к работе')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(IDLE_KV)

    def on_enter(self):
        """При переходе на экран — проверяем соединения."""
        Logger.info("IdleScreen: ожидание задачи от WMS")
        Clock.schedule_once(lambda dt: self._check_services(), 1.0)

    def _check_services(self):
        """Фоновая проверка доступности сервисов."""
        app = self.manager.parent if hasattr(self.manager, 'parent') else None
        if not app:
            return

        # Отобразим статус
        self.status_text = 'Проверка соединения с WMS...'
        Clock.schedule_once(lambda dt: self._done_checking(app), 0.5)

    def _done_checking(self, app):
        """Завершение проверки."""
        try:
            wms_ok = app.wms.health_check()
            net_ok = app.network.check_connectivity()

            if wms_ok and net_ok:
                self.status_text = 'Все сервисы доступны'
            elif wms_ok:
                self.status_text = 'WMS: OK | Сетевой ресурс: недоступен'
            elif net_ok:
                self.status_text = 'WMS: недоступен | Сетевой ресурс: OK'
            else:
                self.status_text = 'Нет соединения с серверами'
        except Exception:
            self.status_text = 'Не удалось проверить сервисы'
