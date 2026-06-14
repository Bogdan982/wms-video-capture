"""
Экран настроек — русский, без theme.py.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.app import App

GREEN = (0.2, 1.0, 0.3, 1)
GREEN_DIM = (0.15, 0.7, 0.2, 1)
GRAY = (0.5, 0.5, 0.5, 1)
BLUE = (0.3, 0.6, 1.0, 1)
RED = (1.0, 0.3, 0.3, 1)
ORANGE = (0.9, 0.6, 0.1, 1)
INPUT_BG = (0.15, 0.15, 0.15, 1)


class SettingsScreen(Screen):
    """Настройки."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config = None
        self._authenticated = False
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=12, spacing=6)

        root.add_widget(Label(
            text='=== НАСТРОЙКИ ===',
            font_size='20sp', bold=True, color=GREEN,
            size_hint_y=0.06, halign='center'
        ))

        self.auth_msg = Label(
            text='Введите пароль (0000):',
            font_size='13sp', color=GREEN_DIM,
            size_hint_y=0.04, halign='center'
        )
        root.add_widget(self.auth_msg)

        pwd_box = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=5)
        self.pwd_input = TextInput(
            hint_text='Пароль', multiline=False, password=True,
            font_size='14sp', foreground_color=GREEN,
            background_color=INPUT_BG, cursor_color=GREEN,
            size_hint_x=0.6
        )
        pwd_box.add_widget(self.pwd_input)
        pwd_btn = Button(text='ВХОД', font_size='14sp', size_hint_x=0.4,
                         background_color=BLUE, color=(1, 1, 1, 1))
        pwd_btn.bind(on_press=self._check_password)
        pwd_box.add_widget(pwd_btn)
        root.add_widget(pwd_box)

        self.settings_box = BoxLayout(orientation='vertical', spacing=4, size_hint_y=None)
        self.settings_box.bind(minimum_height=self.settings_box.setter('height'))

        scroll = ScrollView(size_hint_y=0.62)
        scroll.add_widget(self.settings_box)
        root.add_widget(scroll)

        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=8)
        btn_box.add_widget(Button(text='НАЗАД', font_size='14sp',
                                  background_color=GRAY, color=(1, 1, 1, 1),
                                  on_press=self._go_back))
        btn_box.add_widget(Button(text='СОХРАНИТЬ', font_size='14sp',
                                  background_color=GREEN_DIM, color=(1, 1, 1, 1),
                                  on_press=self._save))
        root.add_widget(btn_box)

        self.add_widget(root)

    def on_pre_enter(self):
        app = App.get_running_app()
        if app:
            self._config = app.config_data

    def on_leave(self):
        self._authenticated = False
        self.auth_msg.text = 'Введите пароль (0000):'
        self.auth_msg.color = GREEN_DIM
        self.pwd_input.text = ''
        self.settings_box.clear_widgets()

    def _check_password(self, *args):
        pwd = self.pwd_input.text
        if self._config and self._config.verify_admin_password(pwd):
            self._authenticated = True
            self.auth_msg.text = '> ДОСТУП РАЗРЕШЁН'
            self.auth_msg.color = GREEN
            self._build_settings_fields()
        else:
            self.auth_msg.text = '> ДОСТУП ЗАПРЕЩЁН'
            self.auth_msg.color = RED
            self.pwd_input.text = ''

    def _add_field(self, label_text, value, on_change):
        box = BoxLayout(orientation='horizontal', size_hint_y=None, height=48, spacing=4)
        box.add_widget(Label(text=label_text, font_size='13sp', color=GREEN_DIM,
                             size_hint_x=0.35, halign='right'))
        inp = TextInput(
            text=value, multiline=False, font_size='13sp',
            foreground_color=GREEN, background_color=INPUT_BG,
            cursor_color=GREEN, size_hint_x=0.65
        )
        box.add_widget(inp)
        if on_change:
            inp.bind(text=on_change)
        self.settings_box.add_widget(box)
        return inp

    def _add_section(self, title):
        self.settings_box.add_widget(Label(
            text=f'-- {title} --', font_size='12sp', color=GREEN_DIM,
            size_hint_y=None, height=22, halign='center'
        ))

    def _build_settings_fields(self):
        self.settings_box.clear_widgets()
        if not self._config:
            return

        self._add_field('Организация', self._config.get('org_name', ''),
                        lambda i, v: self._config.set('org_name', v))

        self._add_section('SMB')
        self._add_field('SMB Сервер', self._config.smb_host,
                        lambda i, v: self._config.set('smb_host', v))
        self._add_field('SMB Шара', self._config.smb_share,
                        lambda i, v: self._config.set('smb_share', v))
        self._add_field('SMB Пользователь', self._config.smb_username,
                        lambda i, v: self._config.set('smb_username', v))
        self._add_field('SMB Пароль', self._config.smb_password,
                        lambda i, v: self._config.set('smb_password', v))

        self._add_section('WMS')
        self._add_field('WMS URL', self._config.wms_base_url,
                        lambda i, v: self._config.set('wms_base_url', v))

        self._add_section('ЛОГИ')
        self._add_field('Логи SMB Сервер', self._config.log_smb_host,
                        lambda i, v: self._config.set('log_smb_host', v))
        self._add_field('Логи SMB Шара', self._config.log_smb_share,
                        lambda i, v: self._config.set('log_smb_share', v))

        # Смена пароля
        pwd_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=48, spacing=4)
        pwd_box.add_widget(Label(text='Новый пароль', font_size='13sp', color=GREEN_DIM,
                                 size_hint_x=0.35, halign='right'))
        new_pwd = TextInput(
            hint_text='мин. 4 символа', multiline=False, font_size='13sp',
            foreground_color=GREEN, background_color=INPUT_BG,
            cursor_color=GREEN, size_hint_x=0.4
        )
        pwd_box.add_widget(new_pwd)
        chg_btn = Button(text='СМЕНИТЬ', font_size='12sp', size_hint_x=0.25,
                         background_color=ORANGE, color=(1, 1, 1, 1))
        chg_btn.bind(on_press=lambda x: self._change_password(new_pwd.text))
        pwd_box.add_widget(chg_btn)
        self.settings_box.add_widget(pwd_box)

    def _change_password(self, new_pwd):
        if len(new_pwd) < 4:
            self.auth_msg.text = '> Минимум 4 символа!'
            self.auth_msg.color = RED
            return
        if self._config:
            self._config.set_admin_password(new_pwd)
            self.auth_msg.text = '> Пароль изменён!'
            self.auth_msg.color = GREEN

    def _save(self, *args):
        if self._config:
            self._config.save()
            self.auth_msg.text = '> Сохранено!'
            self.auth_msg.color = GREEN

    def _go_back(self, *args):
        app = App.get_running_app()
        if app:
            app.sm.current = 'confirm'
