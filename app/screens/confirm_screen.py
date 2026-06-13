"""
Экран подтверждения задачи.

При получении ID из WMS показывает:
  "Получен идентификатор заказа №XXXXXXXXXX. Начать съёмку?"

Кнопка "Начать съёмку" с защитой от случайного нажатия:
  - Долгое нажатие (2 сек)
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
        spacing: 5
        padding: 10, 5, 10, 10

        # -- Status bar --
        BoxLayout:
            size_hint_y: 0.06
            spacing: 5

            Label:
                text: root.status_text
                font_size: '10sp'
                color: (0.6, 1.0, 0.6, 1)
                size_hint_x: 0.65
                halign: 'left'

            Button:
                text: '⚙'
                font_size: '14sp'
                size_hint_x: 0.15
                background_color: (0.3, 0.3, 0.5, 0.7)
                on_release: root.open_settings()

            Button:
                text: '✕'
                font_size: '14sp'
                size_hint_x: 0.15
                background_color: (0.5, 0.3, 0.3, 0.7)
                on_release: root.close_app()

        # Заголовок
        Label:
            text: 'WMS Video Capture'
            font_size: '22sp'
            bold: True
            color: (0.2, 0.6, 1.0, 1)
            size_hint_y: 0.1

        # Основное уведомление
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.3

            Label:
                text: 'Получен идентификатор заказа:'
                font_size: '14sp'
                color: (0.7, 0.7, 0.7, 1)
                halign: 'center'
                size_hint_y: 0.2

            Label:
                text: root.task_id_display
                font_size: '28sp'
                bold: True
                color: (1, 1, 1, 1)
                halign: 'center'
                size_hint_y: 0.4

            Label:
                text: 'Начать съёмку?'
                font_size: '16sp'
                color: (0.8, 0.8, 0.8, 1)
                halign: 'center'
                size_hint_y: 0.2

        # -- Защищённая кнопка --
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.25
            spacing: 3

            Button:
                id: start_btn
                text: root.button_text
                font_size: '20sp'
                bold: True
                size_hint_y: 0.7
                background_color: (0.2, 0.8, 0.2, root.button_alpha)
                disabled: root.button_disabled
                on_touch_down: root.on_button_touch(args[1])
                on_touch_up: root.on_button_release(args[1])

            ProgressBar:
                id: hold_progress
                value: root.hold_progress_value
                max: 1.0
                size_hint_y: 0.15

            Label:
                text: root.hold_hint
                font_size: '11sp'
                color: (0.6, 0.6, 0.6, 1)
                size_hint_y: 0.1
                halign: 'center'

        # -- Ручной запуск (без Intent) --
        BoxLayout:
            id: manual_box
            size_hint_y: 0.12
            spacing: 5

            Label:
                text: 'Нет задания?'
                font_size: '12sp'
                color: (0.7, 0.7, 0.7, 1)
                size_hint_x: 0.4
                halign: 'right'

            Button:
                text: 'QR-сканер'
                font_size: '14sp'
                size_hint_x: 0.4
                background_color: (0.2, 0.6, 1.0, 1)
                on_release: root.start_qr_scan()

            Widget:
                size_hint_x: 0.2

        Widget:
            size_hint_y: 0.02
"""

# Время удержания для активации (секунд)
HOLD_DURATION = 2.0


class ConfirmScreen(Screen):
    """Экран подтверждения с защитой от случайного нажатия."""

    task_id = StringProperty('')
    task_id_display = StringProperty('-')
    button_text = StringProperty('УДЕРЖИВАЙТЕ 2 СЕК')
    button_disabled = BooleanProperty(True)
    button_alpha = NumericProperty(0.5)
    hold_progress_value = NumericProperty(0.0)
    hold_hint = StringProperty('Удерживайте кнопку 2 секунды')
    status_text = StringProperty('Сеть: проверка...')
    manual_mode = BooleanProperty(True)
    manual_mode_opacity = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(CONFIRM_KV)
        self._hold_active = False
        self._hold_timer = None
        self._hold_anim = None

    def on_enter(self):
        """При переходе на экран — проверяем статус сети."""
        self._check_network()

    def on_pre_enter(self):
        """Берём task_id из App."""
        app = self._get_app()
        if app and app.current_task_id:
            self.task_id = app.current_task_id
            self.task_id_display = app.current_task_id
            self._reset_button()
            self.manual_mode = False
            self.manual_mode_opacity = 0.0
        else:
            self.task_id_display = '-'
            self.manual_mode = True
            self.manual_mode_opacity = 1.0
            self.hold_hint = 'Используйте QR-сканер для ввода ID'

    def on_leave(self):
        self._cancel_hold()

    def _check_network(self):
        """Проверка доступности SMB/WMS."""
        try:
            app = self._get_app()
            if not app:
                return
            smb_ok = app.network.check_connectivity()
            wms_ok = app.wms.health_check()
            if smb_ok and wms_ok:
                self.status_text = 'Сеть: OK'
            elif smb_ok:
                self.status_text = 'Сеть: SMB OK'
            elif wms_ok:
                self.status_text = 'Сеть: WMS OK'
            else:
                self.status_text = 'Сеть: нет'
        except Exception as e:
            self.status_text = 'Сеть: —'

    # -- Защита от случайного нажатия --

    def on_button_touch(self, touch):
        if self.button_disabled:
            return
        if not self.ids.start_btn.collide_point(*touch.pos):
            return
        if touch.is_mouse_scrolling:
            return
        self._hold_active = True
        self.hold_progress_value = 0.0
        self.button_text = 'УДЕРЖИВАЙТЕ...'
        self._hold_anim = Animation(hold_progress_value=1.0, duration=HOLD_DURATION)
        self._hold_anim.bind(on_complete=self._on_hold_complete)
        self._hold_anim.start(self)
        self._hold_timer = Clock.schedule_once(self._on_hold_complete, HOLD_DURATION)

    def on_button_release(self, touch):
        if not self._hold_active:
            return
        if self.hold_progress_value < 1.0:
            self._cancel_hold()
            self.hold_hint = 'Отпущено рано. Повторите.'
            Clock.schedule_once(lambda dt: self._reset_button(), 1.5)

    def on_button_click(self):
        if self.hold_progress_value < 1.0:
            self._cancel_hold()
            self.hold_hint = 'Удерживайте, не отпуская!'
            Clock.schedule_once(lambda dt: self._reset_button(), 1.5)

    def _on_hold_complete(self, *args):
        if not self._hold_active:
            return
        self._hold_active = False
        self._cancel_timer()
        self.hold_progress_value = 1.0
        self.button_text = 'СТАРТ'
        self.button_disabled = False
        self.button_alpha = 1.0
        self.hold_hint = 'Запуск камеры...'
        self._start_recording()

    def _start_recording(self):
        app = self._get_app()
        if app:
            app.start_recording()

    def _cancel_hold(self):
        self._hold_active = False
        self._cancel_timer()
        if self._hold_anim:
            self._hold_anim.cancel(self)
            self._hold_anim = None
        self.hold_progress_value = 0.0

    def _cancel_timer(self):
        if self._hold_timer:
            self._hold_timer.cancel()
            self._hold_timer = None

    def _reset_button(self):
        self._cancel_hold()
        self.button_text = 'УДЕРЖИВАЙТЕ 2 СЕК'
        self.button_disabled = True
        self.button_alpha = 0.5
        self.hold_progress_value = 0.0
        self.hold_hint = 'Удерживайте кнопку 2 секунды'

    def open_settings(self):
        app = self._get_app()
        if app:
            app.open_settings()

    def start_qr_scan(self):
        app = self._get_app()
        if app:
            app.on_scan_requested()

    def close_app(self):
        app = self._get_app()
        if app:
            app.on_request_close()

    def _get_app(self):
        try:
            return self.manager.parent
        except Exception:
            return None
