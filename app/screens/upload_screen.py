"""
Экран выгрузки видео на сетевой ресурс.
Показывает прогресс загрузки, статус и кнопку повтора при ошибке.
"""
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.logger import Logger

UPLOAD_KV = """
<UploadScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: 15
        padding: 30

        Label:
            text: 'Выгрузка видео'
            font_size: '26sp'
            bold: True
            color: (1, 0.6, 0, 1)

        Label:
            text: f'Задача: {root.task_id}'
            font_size: '18sp'
            color: (0.8, 0.8, 0.8, 1)

        Widget:

        # Статус
        Label:
            text: root.status_text
            font_size: '20sp'
            color: (1, 1, 1, root.status_alpha)
            halign: 'center'
            text_size: (self.width, None)

        # Прогресс (анимация)
        BoxLayout:
            size_hint_y: 0.1
            spacing: 10
            padding: (0, 20, 0, 0)

            ProgressBar:
                id: upload_progress
                value: root.progress_value
                max: 100
                size_hint_x: 0.8

            Label:
                text: f'{int(root.progress_value)}%'
                font_size: '16sp'
                size_hint_x: 0.2

        Widget:

        # Кнопка повтора (показана при ошибке)
        Button:
            text: 'Повторить'
            size_hint_y: 0.12
            pos_hint: {'center_x': 0.5}
            background_color: (0.2, 0.6, 1, 1) if root.show_retry else (0.5, 0.5, 0.5, 0.3)
            disabled: not root.show_retry
            on_release: root.retry_upload()

        Button:
            text: 'Отмена'
            size_hint_y: 0.1
            background_color: (0.5, 0.5, 0.5, 0.5)
            on_release: root.cancel_upload()
"""


class UploadScreen(Screen):
    """Экран выгрузки с индикацией прогресса."""

    task_id = StringProperty('')
    status_text = StringProperty('Подключение к серверу...')
    status_alpha = NumericProperty(1.0)
    progress_value = NumericProperty(0)
    show_retry = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(UPLOAD_KV)
        self._progress_timer = None
        self._upload_started = False

    def on_enter(self):
        """Начало экрана выгрузки."""
        app = self._get_app()
        if app:
            self.task_id = app.current_task_id
            self.status_text = 'Идёт выгрузка на сервер...'
            self.show_retry = False
            self.progress_value = 0
            self._upload_started = False

            # Запускаем симуляцию прогресса (10-90%)
            self._progress_timer = Clock.schedule_interval(
                self._simulate_progress, 0.5
            )

    def on_leave(self):
        """Останавливаем таймер прогресса."""
        self._stop_progress()

    def _simulate_progress(self, dt):
        """Имитация прогресса до 90% (реальный прогресс от SMB не получить тривиально)."""
        if self._upload_started:
            return

        if self.progress_value < 70:
            self.progress_value += 2
        elif self.progress_value < 90:
            self.progress_value += 1

        # Когда загрузка реально завершена — app сам переключит экран
        # Этот таймер просто даёт визуальный фидбек

    def _stop_progress(self):
        """Останавливает симуляцию прогресса."""
        if self._progress_timer:
            self._progress_timer.cancel()
            self._progress_timer = None

    def retry_upload(self):
        """Повторная попытка выгрузки."""
        Logger.info("UploadScreen: повторная попытка выгрузки")
        self.show_retry = False
        self.status_text = 'Повторная попытка...'
        self.progress_value = 0
        self._progress_timer = Clock.schedule_interval(
            self._simulate_progress, 0.5
        )

        app = self._get_app()
        if app and app.current_video_path and app.current_task_id:
            Clock.schedule_once(
                lambda dt: app._upload_video(
                    app.current_video_path,
                    app.current_task_id
                ),
                0.3
            )

    def cancel_upload(self):
        """Отмена выгрузки (возврат на idle)."""
        Logger.info("UploadScreen: выгрузка отменена")
        self._stop_progress()
        self.manager.current = 'idle'

    def set_error(self, message: str = 'Ошибка выгрузки'):
        """Отображает состояние ошибки."""
        self._stop_progress()
        self.status_text = f'❌ {message}'
        self.show_retry = True
        self.progress_value = 0

    def set_complete(self):
        """Загрузка завершена — переключаемся на DoneScreen."""
        self._stop_progress()
        self.progress_value = 100
        self.status_text = '✅ Выгрузка завершена'

    def _get_app(self):
        try:
            return self.manager.parent
        except Exception:
            return None
