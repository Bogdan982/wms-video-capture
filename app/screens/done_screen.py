"""
Экран завершения задачи.

После записи показывает диалог выбора идентификатора:
  - Использовать полученный ID
  - Сканировать QR-код
  - Ввести вручную

После выгрузки: результат ✅ / ❌
"""
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import (StringProperty, BooleanProperty,
                              NumericProperty, ObjectProperty)
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
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
            size_hint_y: 0.12

        Label:
            text: root.status_title
            font_size: '24sp'
            bold: True
            color: root.title_color
            size_hint_y: 0.07

        Label:
            text: root.status_subtitle
            font_size: '16sp'
            color: (0.7, 0.7, 0.7, 1)
            halign: 'center'
            size_hint_y: 0.05

        # ── ID задачи ──
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.08
            spacing: 2

            Label:
                text: 'Идентификатор заказа:'
                font_size: '13sp'
                color: (0.5, 0.5, 0.5, 1)
                size_hint_y: 0.3

            Label:
                text: root.task_id_display
                font_size: '24sp'
                bold: True
                color: (1, 1, 1, 1)
                size_hint_y: 0.7

        Widget:

        # ── Контент (меняется в зависимости от состояния) ──
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.38
            spacing: 8

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
                    size_hint_y: 0.2

                # Кнопка 1
                Button:
                    text: root.btn1_text
                    font_size: '18sp'
                    bold: True
                    size_hint_y: 0.22
                    background_color: root.btn1_color
                    disabled: not root.btn1_visible
                    opacity: 1 if root.btn1_visible else 0
                    on_release: root.on_btn1()

                # Кнопка 2
                Button:
                    text: root.btn2_text
                    font_size: '18sp'
                    bold: True
                    size_hint_y: 0.22
                    background_color: root.btn2_color
                    disabled: not root.btn2_visible
                    opacity: 1 if root.btn2_visible else 0
                    on_release: root.on_btn2()

                # Кнопка 3
                Button:
                    text: root.btn3_text
                    font_size: '16sp'
                    size_hint_y: 0.18
                    background_color: root.btn3_color
                    disabled: not root.btn3_visible
                    opacity: 1 if root.btn3_visible else 0
                    on_release: root.on_btn3()

        Widget:
"""


class ManualIdPopup(Popup):
    """
    Popup для ручного ввода идентификатора заказа.

    Содержит:
      - Поясняющий текст
      - TextInput для ввода ID
      - Кнопки: OK / Отмена
    """

    def __init__(self, done_screen, **kwargs):
        super().__init__(**kwargs)
        self._done_screen = done_screen

        self.title = '✏ Ввод идентификатора'
        self.size_hint = (0.85, 0.45)
        self.auto_dismiss = False  # Не закрывать по клику вне окна

        # Основной контент
        layout = BoxLayout(
            orientation='vertical',
            spacing=15,
            padding=20
        )

        # Пояснение
        lbl = Label(
            text='Введите идентификатор заказа вручную:',
            font_size='16sp',
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=0.25
        )
        layout.add_widget(lbl)

        # Поле ввода
        self._input = TextInput(
            hint_text='Например: ABC-123 или 45678',
            font_size='22sp',
            multiline=False,
            size_hint_y=0.35,
            foreground_color=(1, 1, 1, 1),
            background_color=(0.2, 0.2, 0.2, 1)
        )
        # Авто-фокус на поле
        self._input.bind(on_text_validate=self._on_ok)
        layout.add_widget(self._input)

        # Кнопки
        btn_layout = BoxLayout(
            orientation='horizontal',
            spacing=15,
            size_hint_y=0.3
        )

        cancel_btn = Button(
            text='Отмена',
            font_size='18sp',
            background_color=(0.5, 0.5, 0.5, 0.7),
            on_release=self.dismiss
        )
        btn_layout.add_widget(cancel_btn)

        ok_btn = Button(
            text='✅ Подтвердить',
            font_size='18sp',
            bold=True,
            background_color=(0.2, 0.8, 0.2, 1),
            on_release=self._on_ok
        )
        btn_layout.add_widget(ok_btn)

        layout.add_widget(btn_layout)
        self.content = layout

        # Авто-открытие клавиатуры
        Clock.schedule_once(lambda dt: self._focus_input(), 0.3)

    def _focus_input(self):
        """Фокус на поле ввода после открытия popup."""
        if self._input:
            self._input.focus = True

    def _on_ok(self, *args):
        """Пользователь подтвердил ввод."""
        text = self._input.text.strip()
        if not text:
            # Показываем подсказку
            self._input.hint_text = '⚠ Введите идентификатор!'
            self._input.text = ''
            return

        Logger.info(f"ManualIdPopup: пользователь ввёл ID: {text}")
        self.dismiss()

        # Передаём в DoneScreen
        if self._done_screen:
            self._done_screen.on_manual_id_submit(text)


class DoneScreen(Screen):
    """
    Экран завершения задачи с переключением режимов:
      - idle: ничего не отображается
      - id_change: диалог выбора ID (текущий / QR / ручной ввод)
      - completed: успех с информацией
      - error: ошибка с кнопкой повтора
    """

    _mode = StringProperty('idle')

    # Свойства UI
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
        """При входе — восстанавливаем состояние из app_status."""
        app = self._get_app()
        if app:
            self.task_id_display = app.current_task_id
            # Восстанавливаем режим из app_status
            if app.app_status == 'done':
                self.show_id_change_dialog()
            else:
                self._set_idle()

    # ── Режимы ──

    def _set_idle(self):
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
        "Видео записано. Выберите идентификатор для выгрузки:"
          [✅ Использовать ABC-123]  — оставить текущий
          [📷 Сканировать QR]        — отсканировать QR-код
          [✏ Ввести вручную]         — ввести ID с клавиатуры
        """
        self._mode = 'id_change'
        self.status_icon = '🎥'
        self.status_title = 'Видео записано'
        self.status_subtitle = 'Выберите идентификатор для выгрузки'

        self.content_text = f'Текущий ID: {self.task_id_display}'
        self.content_visible = True

        self.btn1_text = f'✅ Использовать {self.task_id_display}'
        self.btn1_color = (0.2, 0.8, 0.2, 1)
        self.btn1_visible = True

        self.btn2_text = '📷 Сканировать QR-код'
        self.btn2_color = (0.2, 0.6, 1.0, 1)
        self.btn2_visible = True

        self.btn3_text = '✏ Ввести вручную'
        self.btn3_color = (0.6, 0.6, 0.6, 0.9)
        self.btn3_visible = True

        Logger.info("DoneScreen: показан диалог выбора ID (текущий / QR / ручной)")

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

        self.content_text = ('Проверьте соединение с сервером.\n'
                             'Видео сохранено локально.')
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
        """Кнопка 3."""
        if self._mode == 'id_change':
            # "Ввести вручную" — показываем Popup
            self._show_manual_input()

        elif self._mode == 'completed':
            # "Закрыть"
            self._close_app()

        elif self._mode == 'error':
            # "Закрыть"
            self._close_app()

    # ── Ручной ввод ID ──

    def _show_manual_input(self):
        """Открывает Popup для ручного ввода идентификатора."""
        Logger.info("DoneScreen: открыт popup ручного ввода ID")
        popup = ManualIdPopup(done_screen=self)
        popup.open()

    def on_manual_id_submit(self, manual_id: str):
        """
        Вызывается из ManualIdPopup после ввода ID.
        Передаёт ID в App для выгрузки.
        """
        if not manual_id:
            return

        Logger.info(f"DoneScreen: ручной ввод ID: {manual_id}")
        app = self._get_app()
        if app:
            app.on_manual_id_entered(manual_id)

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
