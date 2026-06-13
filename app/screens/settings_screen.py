"""
Экран настроек приложения.

Доступ только по паролю администратора.
Позволяет менять:
  - Пароль администратора
  - Параметры SMB (хост, шара, пользователь)
  - Параметры WMS (URL)
  - Настройки логирования
  - Ограничения видео
"""
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.animation import Animation

SETTINGS_KV = """
<SettingsScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: 5
        padding: 15

        # Заголовок
        Label:
            text: '⚙ Настройки'
            font_size: '24sp'
            bold: True
            color: (0.2, 0.6, 1.0, 1)
            size_hint_y: 0.08

        # ── Ввод пароля ──
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.15
            spacing: 5

            Label:
                text: root.auth_message
                font_size: '14sp'
                color: (1, root.auth_msg_color_g, root.auth_msg_color_g, 1)
                halign: 'center'
                size_hint_y: 0.3

            BoxLayout:
                size_hint_y: 0.7
                spacing: 10

                TextInput:
                    id: password_input
                    hint_text: 'Пароль администратора'
                    password: True
                    multiline: False
                    size_hint_x: 0.7
                    font_size: '18sp'

                Button:
                    text: 'Войти'
                    font_size: '16sp'
                    size_hint_x: 0.3
                    background_color: (0.2, 0.6, 1.0, 1)
                    on_release: root.check_password()

        # ── Панель настроек (доступна после пароля) ──
        ScrollView:
            size_hint_y: 0.72
            disabled: not root.authenticated

            BoxLayout:
                orientation: 'vertical'
                spacing: 10
                size_hint_y: None
                height: self.minimum_height

                # === SMB ===
                Label:
                    text: 'СЕТЕВОЙ РЕСУРС (SMB)'
                    font_size: '16sp'
                    bold: True
                    color: (0.6, 0.6, 1.0, 1)
                    size_hint_y: None
                    height: 40

                SettingsRow:
                    label: 'Хост'
                    input_id: 'smb_host_input'
                    default_text: root.smb_host_val
                    on_text: root.on_smb_host

                SettingsRow:
                    label: 'Шара'
                    input_id: 'smb_share_input'
                    default_text: root.smb_share_val
                    on_text: root.on_smb_share

                SettingsRow:
                    label: 'Пользователь'
                    input_id: 'smb_user_input'
                    default_text: root.smb_user_val
                    on_text: root.on_smb_user

                SettingsRow:
                    label: 'Пароль SMB'
                    input_id: 'smb_pass_input'
                    default_text: ''
                    password: True
                    on_text: root.on_smb_pass

                # === WMS ===
                Label:
                    text: 'WMS-СЕРВЕР'
                    font_size: '16sp'
                    bold: True
                    color: (0.6, 0.6, 1.0, 1)
                    size_hint_y: None
                    height: 40

                SettingsRow:
                    label: 'WMS URL'
                    input_id: 'wms_url_input'
                    default_text: root.wms_url_val
                    on_text: root.on_wms_url

                # === Логи ===
                Label:
                    text: 'ЛОГИРОВАНИЕ'
                    font_size: '16sp'
                    bold: True
                    color: (0.6, 0.6, 1.0, 1)
                    size_hint_y: None
                    height: 40

                SettingsRow:
                    label: 'SMB хост логов'
                    input_id: 'log_host_input'
                    default_text: root.log_host_val
                    on_text: root.on_log_host

                SettingsRow:
                    label: 'SMB шара логов'
                    input_id: 'log_share_input'
                    default_text: root.log_share_val
                    on_text: root.on_log_share

                # === Пароль админа ===
                Label:
                    text: 'СМЕНИТЬ ПАРОЛЬ'
                    font_size: '16sp'
                    bold: True
                    color: (0.6, 0.6, 1.0, 1)
                    size_hint_y: None
                    height: 40

                BoxLayout:
                    size_hint_y: None
                    height: 50
                    spacing: 10

                    TextInput:
                        id: new_password_input
                        hint_text: 'Новый пароль'
                        password: True
                        multiline: False
                        size_hint_x: 0.6

                    Button:
                        text: 'Установить'
                        size_hint_x: 0.4
                        on_release: root.set_new_password()

        # ── Кнопка выхода ──
        BoxLayout:
            size_hint_y: 0.07
            spacing: 10

            Button:
                text: '↩ Вернуться'
                font_size: '16sp'
                background_color: (0.5, 0.5, 0.5, 0.7)
                on_release: root.go_back()

            Label:
                text: root.status_text
                font_size: '13sp'
                color: (0.6, 0.6, 0.6, 1)
                halign: 'center'
"""


from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.factory import Factory


class SettingsRow(BoxLayout):
    """Вспомогательный компонент: строка настроек с label + input."""

    def __init__(self, label='', input_id='', default_text='',
                 password=False, on_text=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 10
        self.size_hint_y = None
        self.height = 50

        lbl = Label(
            text=label,
            font_size='14sp',
            size_hint_x=0.3,
            color=(0.8, 0.8, 0.8, 1)
        )
        self.add_widget(lbl)

        self._input = TextInput(
            text=default_text,
            hint_text=label,
            multiline=False,
            password=password,
            font_size='15sp',
            size_hint_x=0.7
        )
        if on_text:
            self._input.bind(text=on_text)
        self.add_widget(self._input)

    @property
    def value(self) -> str:
        return self._input.text


Factory.register('SettingsRow', cls=SettingsRow)


class SettingsScreen(Screen):
    """Экран настроек с аутентификацией."""

    authenticated = BooleanProperty(False)
    auth_message = StringProperty('Введите пароль для доступа к настройкам')
    auth_msg_color_g = NumericProperty(0.6)
    status_text = StringProperty('')

    # Значения полей (для KV)
    smb_host_val = StringProperty('')
    smb_share_val = StringProperty('')
    smb_user_val = StringProperty('')
    wms_url_val = StringProperty('')
    log_host_val = StringProperty('')
    log_share_val = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(SETTINGS_KV)
        self._config = None

    def on_pre_enter(self):
        """Загружаем текущие настройки."""
        app = self._get_app()
        if app:
            self._config = app.config_data
            self._load_values()

        # Если пароль не установлен — открываем сразу
        if self._config and not self._config.get('admin_password_hash'):
            self.authenticated = True
            self.auth_message = '✅ Пароль не установлен — доступ открыт'

    def _load_values(self):
        """Загружает текущие значения из конфига в поля."""
        if not self._config:
            return

        self.smb_host_val = self._config.smb_host
        self.smb_share_val = self._config.smb_share
        self.smb_user_val = self._config.smb_username
        self.wms_url_val = self._config.wms_base_url
        self.log_host_val = self._config.log_smb_host
        self.log_share_val = self._config.log_smb_share

    # ── Аутентификация ──

    def check_password(self):
        """Проверка пароля администратора."""
        password_input = self.ids.get('password_input')
        if not password_input or not self._config:
            return

        pwd = password_input.text
        if not pwd:
            self._flash_auth_msg('Введите пароль', (1, 0.3, 0.3))
            return

        if self._config.verify_admin_password(pwd):
            self.authenticated = True
            self.auth_message = '✅ Доступ разрешён'
            self._flash_auth_msg('✅ Доступ разрешён', (0.3, 1, 0.3))
            Logger.info("SettingsScreen: аутентификация успешна")
        else:
            self._flash_auth_msg('❌ Неверный пароль', (1, 0.3, 0.3))
            Logger.warning("SettingsScreen: неверный пароль")
            password_input.text = ''

    def _flash_auth_msg(self, text, color):
        """Вспышка сообщения аутентификации."""
        self.auth_message = text
        self.auth_msg_color_g = color[1]
        # Анимация цвета
        anim = Animation(auth_msg_color_g=0.6, duration=2.0)
        anim.start(self)

    # ── Изменение настроек ──

    def on_smb_host(self, instance, value):
        if self._config and value:
            self._config.set('smb_host', value)

    def on_smb_share(self, instance, value):
        if self._config and value:
            self._config.set('smb_share', value)

    def on_smb_user(self, instance, value):
        if self._config and value:
            self._config.set('smb_username', value)

    def on_smb_pass(self, instance, value):
        if self._config and value:
            self._config.set('smb_password', value)

    def on_wms_url(self, instance, value):
        if self._config and value:
            self._config.set('wms_base_url', value)

    def on_log_host(self, instance, value):
        if self._config and value:
            self._config.set('log_smb_host', value)

    def on_log_share(self, instance, value):
        if self._config and value:
            self._config.set('log_smb_share', value)

    def set_new_password(self):
        """Установка нового пароля администратора."""
        input_field = self.ids.get('new_password_input')
        if not input_field or not self._config:
            return

        new_pwd = input_field.text
        if len(new_pwd) < 4:
            self.status_text = '❌ Пароль должен быть минимум 4 символа'
            return

        self._config.set_admin_password(new_pwd)
        self.status_text = '✅ Пароль изменён'
        input_field.text = ''
        Logger.info("SettingsScreen: пароль администратора изменён")

    # ── Навигация ──

    def go_back(self):
        """Возврат на главный экран."""
        self.authenticated = False
        self.auth_message = 'Введите пароль для доступа к настройкам'
        self.status_text = ''

        app = self._get_app()
        if app:
            app.sm.current = 'confirm' if app.current_task_id else 'confirm'

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()
