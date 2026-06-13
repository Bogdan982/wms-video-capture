"""
Экран настроек — программный.
Доступ по паролю (по умолчанию 0000).
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.app import App
from kivy.logger import Logger


class SettingsScreen(Screen):
    """Настройки приложения."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # Заголовок
        root.add_widget(Label(
            text='Настройки',
            font_size='24sp',
            bold=True,
            color=(0.2, 0.6, 1.0, 1),
            size_hint_y=0.08
        ))

        # Пароль
        self.auth_msg = Label(
            text='Введите пароль (0000)',
            font_size='14sp',
            color=(1, 1, 1, 1),
            size_hint_y=0.05,
            halign='center'
        )
        root.add_widget(self.auth_msg)

        pwd_box = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=5)
        self.pwd_input = TextInput(
            hint_text='Пароль',
            multiline=False,
            password=True,
            font_size='16sp',
            size_hint_x=0.6
        )
        pwd_box.add_widget(self.pwd_input)
        pwd_btn = Button(text='Войти', font_size='14sp', size_hint_x=0.4,
                         background_color=(0.2, 0.6, 1.0, 1))
        pwd_btn.bind(on_press=self._check_password)
        pwd_box.add_widget(pwd_btn)
        root.add_widget(pwd_box)

        # Скролл с настройками (изначально скрыт)
        self.settings_box = BoxLayout(orientation='vertical', spacing=8, size_hint_y=0.6)
        self.settings_box.opacity = 1

        scroll = ScrollView(size_hint_y=0.55)
        scroll.add_widget(self.settings_box)
        root.add_widget(scroll)

        # Кнопки внизу
        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=10)
        back_btn = Button(text='Назад', font_size='14sp',
                          background_color=(0.5, 0.5, 0.5, 0.7))
        back_btn.bind(on_press=self._go_back)
        btn_box.add_widget(back_btn)
        save_btn = Button(text='Сохранить', font_size='14sp',
                          background_color=(0.2, 0.8, 0.2, 1))
        save_btn.bind(on_press=self._save)
        btn_box.add_widget(save_btn)
        root.add_widget(btn_box)

        self.add_widget(root)

    def on_pre_enter(self):
        app = App.get_running_app()
        if app:
            self._config = app.config_data

    def _check_password(self, *args):
        pwd = self.pwd_input.text
        if self._config and self._config.verify_admin_password(pwd):
            self.auth_msg.text = 'Доступ разрешён!'
            self.auth_msg.color = (0.2, 1.0, 0.2, 1)
            self._build_settings_fields()
        else:
            self.auth_msg.text = 'Неверный пароль!'
            self.auth_msg.color = (1.0, 0.3, 0.3, 1)
            self.pwd_input.text = ''

    def _add_field(self, label_text, value, on_change):
        box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
        box.add_widget(Label(text=label_text, font_size='13sp', size_hint_x=0.35, halign='right'))
        inp = TextInput(text=value, multiline=False, font_size='13sp', size_hint_x=0.65)
        inp.bind(text=on_change)
        box.add_widget(inp)
        self.settings_box.add_widget(box)
        return inp

    def _build_settings_fields(self):
        self.settings_box.clear_widgets()
        if not self._config:
            return

        self._add_field('SMB сервер', self._config.smb_host,
                        lambda i, v: self._config.set('smb_host', v))
        self._add_field('SMB шара', self._config.smb_share,
                        lambda i, v: self._config.set('smb_share', v))
        self._add_field('SMB пользователь', self._config.smb_username,
                        lambda i, v: self._config.set('smb_username', v))
        self._add_field('SMB пароль', self._config.smb_password,
                        lambda i, v: self._config.set('smb_password', v))
        self._add_field('WMS URL', self._config.wms_base_url,
                        lambda i, v: self._config.set('wms_base_url', v))
        self._add_field('Логи SMB сервер', self._config.log_smb_host,
                        lambda i, v: self._config.set('log_smb_host', v))
        self._add_field('Логи SMB шара', self._config.log_smb_share,
                        lambda i, v: self._config.set('log_smb_share', v))

        # Смена пароля
        pwd_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
        pwd_box.add_widget(Label(text='Новый пароль', font_size='13sp', size_hint_x=0.35, halign='right'))
        new_pwd = TextInput(hint_text='мин. 4 символа', multiline=False, font_size='13sp', size_hint_x=0.4)
        pwd_box.add_widget(new_pwd)
        chg_btn = Button(text='Сменить', font_size='12sp', size_hint_x=0.25,
                         background_color=(0.8, 0.6, 0.2, 1))
        chg_btn.bind(on_press=lambda x: self._change_password(new_pwd.text))
        pwd_box.add_widget(chg_btn)
        self.settings_box.add_widget(pwd_box)

    def _change_password(self, new_pwd):
        if len(new_pwd) < 4:
            self.auth_msg.text = 'Пароль должен быть минимум 4 символа!'
            return
        if self._config:
            self._config.set_admin_password(new_pwd)
            self.auth_msg.text = 'Пароль изменён!'
            self.auth_msg.color = (0.2, 1.0, 0.2, 1)

    def _save(self, *args):
        if self._config:
            self._config.save()
            self.auth_msg.text = 'Сохранено!'

    def _go_back(self, *args):
        app = App.get_running_app()
        if app:
            app.sm.current = 'confirm'
