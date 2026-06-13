"""
Экран подтверждения задачи.

При получении ID из WMS показывает:
  "Получен идентификатор заказа №XXXXXXXXXX. Начать съёмку?"

Кнопка "Начать съёмку" с защитой от случайного нажатия:
  - Долгое нажатие (3 сек) или
  - Два последовательных нажатия с подтверждением
  - Прогресс-бар удержания кнопки
"""
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import (StringProperty, NumericProperty,
                              BooleanProperty, ObjectProperty)
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.logger import Logger

CONFIRM_KV = """
<ConfirmScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: 15
        padding: 30

        # Заголовок
        Label:
            text: 'WMS Video Capture'
            font_size: '24sp'
            bold: True
            color: (0.2, 0.6, 1.0, 1)
            size_hint_y: 0.1

        Widget:
            size_hint_y: 0.05

        # Основное уведомление
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.35

            Label:
                text: '📋 Получен идентификатор заказа:'
                font_size: '16sp'
                color: (0.7, 0.7, 0.7, 1)
                halign: 'center'
                size_hint_y: 0.2

            Label:
                text: root.task_id_display
                font_size: '32sp'
                bold: True
                color: (1, 1, 1, 1)
                halign: 'center'
                text_size: (self.width, None)
                size_hint_y: 0.4

            Label:
                text: 'Начать съёмку?'
                font_size: '18sp'
                color: (0.8, 0.8, 0.8, 1)
                halign: 'center'
                size_hint_y: 0.2

        Widget:
            size_hint_y: 0.05

        # ── Защищённая кнопка "Начать съёмку" ──
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.25
            spacing: 5

            Button:
                id: start_btn
                text: root.button_text
                font_size: '22sp'
                bold: True
                size_hint_y: 0.7
                background_color: (0.2, 0.8, 0.2, root.button_alpha)
                disabled: root.button_disabled
                on_touch_down: root.on_button_touch(args[1])
                on_touch_up: root.on_button_release(args[1])
                on_release: root.on_button_click()

            # Индикатор удержания
            ProgressBar:
                id: hold_progress
                value: root.hold_progress_value
                max: 1.0
                size_hint_y: 0.2
                color: (0.2, 0.8, 0.2, 1)

            Label:
                text: root.hold_hint
                font_size: '12sp'
                color: (0.6, 0.6, 0.6, 1)
                size_hint_y: 0.1
                halign: 'center'

        Widget:
            size_hint_y: 0.05

        # Кнопка настроек (маленькая, внизу)
        BoxLayout:
            size_hint_y: 0.08
            spacing: 10

            Widget:

            Button:
                text: '⚙ Настройки'
                font_size: '14sp'
                size_hint_x: 0.4
                background_color: (0.3, 0.3, 0.5, 0.7)
                on_release: root.open_settings()

            Button:
                text: '✕ Закрыть'
                font_size: '14sp'
                size_hint_x: 0.3
                background_color: (0.5, 0.3, 0.3, 0.7)
                on_release: root.close_app()

            Widget:
"""

# Время удержания для активации (секунд)
HOLD_DURATION = 2.0


class ConfirmScreen(Screen):
    """
    Экран подтверждения с защитой от случайного нажатия.
    Кнопка активируется после удержания в течение HOLD_DURATION.
    """

    task_id = StringProperty('')
    task_id_display = StringProperty('—')
    button_text = StringProperty('УДЕРЖИВАЙТЕ 2 СЕК')
    button_disabled = BooleanProperty(True)
    button_alpha = NumericProperty(0.5)
    hold_progress_value = NumericProperty(0.0)
    hold_hint = StringProperty('Удерживайте кнопку 2 секунды для начала съёмки')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(CONFIRM_KV)
        self._hold_active = False
        self._hold_timer = None
        self._hold_anim = None

    def on_pre_enter(self):
        """При подготовке экрана — берём task_id из App."""
        app = self._get_app()
        if app and app.current_task_id:
            self.task_id = app.current_task_id
            self.task_id_display = app.current_task_id
            self._reset_button()

            Logger.info(f"ConfirmScreen: показан ID {self.task_id}")

    def on_leave(self):
        """При уходе — сбрасываем состояние кнопки."""
        self._cancel_hold()

    # ── Защита от случайного нажатия: удержание ──

    def on_button_touch(self, touch):
        """Начало касания кнопки."""
        if self.button_disabled:
            return
        if not self.ids.start_btn.collide_point(*touch.pos):
            return
        if touch.is_mouse_scrolling:
            return

        self._hold_active = True
        self.hold_progress_value = 0.0
        self.button_text = 'УДЕРЖИВАЙТЕ...'
        self.hold_hint = f'Удерживайте {HOLD_DURATION} сек...'

        # Анимация прогресс-бара
        self._hold_anim = Animation(
            hold_progress_value=1.0,
            duration=HOLD_DURATION
        )
        self._hold_anim.bind(on_complete=self._on_hold_complete)
        self._hold_anim.start(self)

        # Таймер на случай сбоя анимации
        self._hold_timer = Clock.schedule_once(
            self._on_hold_complete, HOLD_DURATION
        )

    def on_button_release(self, touch):
        """Отпускание кнопки — сброс, если удержание не завершено."""
        if not self._hold_active:
            return
        if self.hold_progress_value < 1.0:
            self._cancel_hold()
            self.hold_hint = 'Отпущено слишком рано. Повторите удержание.'
            # Сброс через 1.5 сек
            Clock.schedule_once(lambda dt: self._reset_button(), 1.5)

    def on_button_click(self):
        """Обычный клик (без удержания) — игнорируем."""
        if self.hold_progress_value < 1.0:
            self._cancel_hold()
            self.hold_hint = 'Удерживайте кнопку, не отпуская!'
            Clock.schedule_once(lambda dt: self._reset_button(), 1.5)

    def _on_hold_complete(self, *args):
        """Удержание завершено — кнопка активирована."""
        if not self._hold_active:
            return

        self._hold_active = False
        self._cancel_timer()

        self.hold_progress_value = 1.0
        self.button_text = '▶ СТАРТ'
        self.button_disabled = False
        self.button_alpha = 1.0
        self.hold_hint = 'Нажмите для начала съёмки'

        # Ещё один клик для запуска
        # (или можно запустить автоматически после удержания)
        self._start_recording()

    def _start_recording(self):
        """Запуск видеосъёмки через App."""
        Logger.info(f"ConfirmScreen: запуск съёмки для {self.task_id}")
        self.hold_hint = 'Запуск камеры...'

        app = self._get_app()
        if app:
            app.start_recording()

    def _cancel_hold(self):
        """Отмена удержания."""
        self._hold_active = False
        self._cancel_timer()
        if self._hold_anim:
            self._hold_anim.cancel(self)
            self._hold_anim = None
        self.hold_progress_value = 0.0

    def _cancel_timer(self):
        """Отмена таймера."""
        if self._hold_timer:
            self._hold_timer.cancel()
            self._hold_timer = None

    def _reset_button(self):
        """Сброс кнопки в исходное состояние."""
        self._cancel_hold()
        self.button_text = 'УДЕРЖИВАЙТЕ 2 СЕК'
        self.button_disabled = True
        self.button_alpha = 0.5
        self.hold_progress_value = 0.0
        self.hold_hint = 'Удерживайте кнопку 2 секунды для начала съёмки'

    # ── Действия ──

    def open_settings(self):
        """Открыть настройки."""
        app = self._get_app()
        if app:
            app.open_settings()

    def close_app(self):
        """Закрыть приложение."""
        app = self._get_app()
        if app:
            app.on_request_close()

    def _get_app(self):
        try:
            return self.manager.parent
        except Exception:
            return None
