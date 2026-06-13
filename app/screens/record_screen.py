"""
Экран записи видео.

Отображается во время видеосъёмки.
Пользователю доступно: видеть процесс записи и завершить её.
"""
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.logger import Logger

RECORD_KV = """
<RecordScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: 10
        padding: 30

        Label:
            text: '🔴 ЗАПИСЬ'
            font_size: '32sp'
            bold: True
            color: (1, 0.2, 0.2, 1)

        Label:
            text: f'Заказ №{root.task_id}'
            font_size: '18sp'
            color: (0.8, 0.8, 0.8, 1)

        Widget:

        # Время записи (крупно)
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.3

            Label:
                text: root.status_text
                font_size: '20sp'
                bold: True
                color: (1, 0, 0, 0.8)
                halign: 'center'

            Label:
                text: root.elapsed_display
                font_size: '52sp'
                bold: True
                color: (1, 0, 0, 1)
                halign: 'center'

            Label:
                text: 'сек'
                font_size: '16sp'
                color: (0.6, 0.6, 0.6, 1)
                halign: 'center'

        Widget:

        # Кнопка завершения (крупная, яркая)
        Button:
            text: '■ ЗАВЕРШИТЬ СЪЁМКУ'
            font_size: '22sp'
            bold: True
            size_hint_y: 0.15
            background_color: (0.8, 0.2, 0.2, 1)
            on_release: root.finish_recording()
"""


class RecordScreen(Screen):
    """Экран записи — только индикация и завершение."""

    task_id = StringProperty('')
    status_text = StringProperty('Идёт запись...')
    elapsed_display = StringProperty('0')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(RECORD_KV)
        self._seconds = 0
        self._timer = None

    def on_enter(self):
        """Начало записи."""
        app = self._get_app()
        if app:
            self.task_id = app.current_task_id
        self._seconds = 0
        self.elapsed_display = '0'
        self.status_text = 'Идёт запись...'
        self._start_timer()

    def on_leave(self):
        """Выход с экрана."""
        self._stop_timer()

    def _start_timer(self):
        self._stop_timer()
        self._timer = Clock.schedule_interval(self._tick, 1.0)

    def _tick(self, dt):
        self._seconds += 1
        self.elapsed_display = str(self._seconds)

    def _stop_timer(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def finish_recording(self):
        """Завершение записи — пользователь нажал кнопку."""
        Logger.info("RecordScreen: пользователь завершил запись")
        self._stop_timer()
        self.status_text = 'Запись завершена, обработка...'

        # NOTE: фактическая остановка камеры происходит в CameraService
        # (пользователь закрыл системную камеру)
        # Этот экран — визуальный, пока камера активна.

        app = self._get_app()
        if app:
            # Если камера ещё активна — ждём
            if app.camera.is_recording:
                Logger.info("RecordScreen: ожидание завершения камеры...")
                Clock.schedule_once(lambda dt: self.finish_recording(), 1.0)
            else:
                # Камера уже вернула результат, но пользователь
                # не нажал кнопку — переходим на done
                # (этот случай обработан в app.on_recording_finished)
                pass

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()
