"""
Экран завершения задачи.

После записи показывает:
  1. Диалог: "Использовать ID {X} или заменить через сканер?"
  2. После выгрузки: результат ✅

Пользователю доступно: выбор ID (текущий / QR), повтор при ошибке.
"""
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.logger import Logger

DONE_KV = """
<DoneScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: 15
        padding: 30

        # Иконка
        Label:
            text: root.status_icon
            font_size: '60sp'
            size_hint_y: 0.15

        Label:
            text: root.status_title
            font_size: '24sp'
            bold: True
            color: root.title_color
            size_hint_y: 0.08

        Label:
            text: root.status_subtitle
            font_size: '16sp'
            color: (0.7, 0.7, 0.7, 1)
            halign: 'center'
            size_hint_y: 0.06

        # ── ID задачи ──
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.1
            spacing: 2

            Label:
                text: 'Идентификатор заказа:'
                font_size: '13sp'
                color: (0.5, 0.5, 0.5, 1)
                size_hint_y: 0.3

            Label:
                text: root.task_id_display
                font_size: '26sp'
                bold: True
                color: (1, 1, 1, 1)
                size_hint_y: 0.7

        Widget:

        # ── Контент (меняется в зависимости от состояния) ──
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.3
            spacing: 10

            # IDLE: скрыто
            # ID_CHANGE: кнопки выбора ID
            # COMPLETED: информация о результате
            # ERROR: сообщение об ошибке

            BoxLayout:
                orientation: 'vertical'
                spacing: 8
                disabled: not root.content_visible
                opacity: 1 if root.content_visible else 0

                Label:
                    text: root.content_text
                    font_size: '15sp'
                    color: (0.8, 0.8, 0.8, 1)
                    halign: 'center'
                    text_size: (self.width, None)
                    size_hint_y: 0.3

                # Кнопка "Использовать этот ID"
                Button:
                    text: root.btn1_text
                    font_size: '18sp'
                    bold: True
                    size_hint_y: 0.25
                    background_color: root.btn1_color
                    disabled: not root.btn1_visible
                    opacity: 1 if root.btn1_visible else 0
                    on_release: root.on_btn1()

                # Кнопка "Сканировать QR"
                Button:
                    text: root.btn2_text
                    font_size: '18sp'
                    bold: True
                    size_hint_y: 0.25
                    background_color: root.btn2_color
                    disabled: not root.btn2_visible
                    opacity: 1 if root.btn2_visible else 0
                    on_release: root.on_btn2()

                # Дополнительная кнопка
                Button:
                    text: root.btn3_text
                    font_size: '16sp'
                    size_hint_y: 0.2
                    background_color: root.btn3_color
                    disabled: not root.btn3_visible
                    opacity: 1 if root.btn3_visible else 0
                    on_release: root.on_btn3()

        Widget:
"""


class DoneScreen(Screen):
    """
    Экран завершения задачи с переключением режимов:
      - idle: ничего не отображается
      - id_change: диалог смены ID
      - completed: успех с информацией
      - error: ошибка с кнопкой повтора
    """

    # ── Состояние ──
    _mode = StringProperty('idle')  # idle | id_change | completing | completed | error

    # Свойства для обновления UI
    status_icon = StringProperty('')
    status_title = StringProperty('')
    status_subtitle = StringProperty('')
    title_color = (1, 1, 1, 1)

    task_id_display = StringProperty('')

    content_text = StringProperty('')
    content_visible = BooleanProperty(False)

    btn1_text = StringProperty('')
    btn1_color = (0.2, 0.8, 0.2, 1)
    btn1_visible = BooleanProperty(False)

    btn2_text = StringProperty('')
    btn2_color = (0.2, 0.6, 1.0, 1)
    btn2_visible = BooleanProperty(False)

    btn3_text = StringProperty('')
    btn3_color = (0.5, 0.5, 0.5, 0.7)
    btn3_visible = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(DONE_KV)

    def on_enter(self):
        """При входе — определяем режим."""
        app = self._get_app()
        if app:
            self.task_id_display = app.current_task_id

        # По умолчанию ничего не показываем (ждём команды от App)
        self._set_idle()

    # ── Режимы ──

    def _set_idle(self):
        """Сброс."""
        self._mode = 'idle'
        self.status_icon = ''
        self.status_title = 'Обработка...'
        self.status_subtitle = ''
        self.content_visible = False
        self.btn1_visible = False
        self.btn2_visible = False
        self.btn3_visible = False

    def show_id_change_dialog(self):
        """
        Режим: диалог выбора ID.
        "Видео записано. Использовать ID {X} или заменить через сканер?"
        """
        self._mode = 'id_change'
        self.status_icon = '🎥'
        self.status_title = 'Видео записано'
        self.status_subtitle = 'Выберите идентификатор для выгрузки'

        self.content_text = f'Текущий ID: {self.task_id_display}\nИспользовать его или отсканировать другой?'
        self.content_visible = True

        self.btn1_text = f'✅ Использовать {self.task_id_display}'
        self.btn1_color = (0.2, 0.8, 0.2, 1)
        self.btn1_visible = True

        self.btn2_text = '📷 Сканировать QR-код'
        self.btn2_color = (0.2, 0.6, 1.0, 1)
        self.btn2_visible = True

        self.btn3_text = ''
        self.btn3_visible = False

        Logger.info("DoneScreen: показан диалог смены ID")

    def show_completed(self):
        """
        Режим: задача выполнена успешно.
        """
        self._mode = 'completed'
        self.status_icon = '✅'
        self.status_title = 'Задача выполнена'
        self.status_subtitle = 'Видео выгружено, флаг отправлен'
        self.title_color = (0.2, 0.8, 0.2, 1)

        app = self._get_app()
        if app:
            self.content_text = f'Видео сохранено:\n{app.remote_video_path}'
        else:
            self.content_text = 'Видео успешно выгружено'

        self.content_visible = True

        self.btn1_text = '📋 Ожидать новую задачу'
        self.btn1_color = (0.2, 0.6, 1.0, 1)
        self.btn1_visible = True

        self.btn2_text = ''
        self.btn2_visible = False

        self.btn3_text = '✕ Закрыть'
        self.btn3_color = (0.5, 0.5, 0.5, 0.5)
        self.btn3_visible = True

        Logger.info("DoneScreen: задача выполнена")

    def show_upload_error(self):
        """
        Режим: ошибка выгрузки.
        """
        self._mode = 'error'
        self.status_icon = '❌'
        self.status_title = 'Ошибка выгрузки'
        self.status_subtitle = 'Не удалось загрузить видео на сервер'
        self.title_color = (1, 0.3, 0.3, 1)

        self.content_text = 'Проверьте соединение с сервером.\nВидео сохранено локально и будет отправлено при повторной попытке.'
        self.content_visible = True

        self.btn1_text = '🔄 Повторить'
        self.btn1_color = (0.2, 0.8, 0.2, 1)
        self.btn1_visible = True

        self.btn2_text = '📋 Ожидать новую задачу'
        self.btn2_color = (0.5, 0.5, 0.5, 0.7)
        self.btn2_visible = True

        self.btn3_text = '✕ Закрыть'
        self.btn3_color = (0.5, 0.3, 0.3, 0.7)
        self.btn3_visible = True

    # ── Обработчики кнопок ──

    def on_btn1(self):
        """Кнопка 1."""
        if self._mode == 'id_change':
            # "Использовать текущий ID"
            app = self._get_app()
            if app:
                app.on_use_current_id()

        elif self._mode == 'completed':
            # "Ожидать новую задачу"
            self._return_to_confirm()

        elif self._mode == 'error':
            # "Повторить"
            app = self._get_app()
            if app and app.current_video_path:
                app._upload_video(app.current_video_path, app.current_task_id)

    def on_btn2(self):
        """Кнопка 2."""
        if self._mode == 'id_change':
            # "Сканировать QR-код"
            app = self._get_app()
            if app:
                app.on_scan_requested()

        elif self._mode == 'error':
            # "Ожидать новую задачу"
            self._return_to_confirm()

    def on_btn3(self):
        """Кнопка 3 — закрыть / отмена."""
        if self._mode in ('completed', 'error'):
            self._close_app()

    # ── Вспомогательное ──

    def _return_to_confirm(self):
        """Возврат в режим ожидания следующей задачи."""
        app = self._get_app()
        if app:
            app.current_task_id = ''
            app.current_video_path = ''
            app.remote_video_path = ''
            app.sm.current = 'confirm'

    def _close_app(self):
        """Закрыть приложение."""
        app = self._get_app()
        if app:
            app.on_request_close()

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()
