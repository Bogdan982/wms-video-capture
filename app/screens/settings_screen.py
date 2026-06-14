"""
Экран настроек — терминальный стиль.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.app import App
from kivy.logger import Logger
from app.theme import (THEME_BG, THEME_GREEN, THEME_GREEN_DIM, THEME_GRAY,
                       THEME_BLUE, THEME_RED, THEME_ORANGE,
                       terminal_label, terminal_input, terminal_button)


class SettingsScreen(Screen):
    """Настройки."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config = None
        self._authenticated = False
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=12, spacing=6)

        root.add_widget(terminal_label('=== SETTINGS ===', '20sp', bold=True, size_hint_y=0.06))

        self.auth_msg = terminal_label('Enter password (0000):', '13sp', size_hint_y=0.04)
        root.add_widget(self.auth_msg)

        pwd_box = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=5)
        self.pwd_input = terminal_input('Password', password=True)
        self.pwd_input.size_hint_x = 0.6
        pwd_box.add_widget(self.pwd_input)
        pwd_btn = terminal_button('LOGIN', THEME_BLUE, size_hint_x=0.4)
        pwd_btn.bind(on_press=self._check_password)
        pwd_box.add_widget(pwd_btn)
        root.add_widget(pwd_box)

        self.settings_box = BoxLayout(orientation='vertical', spacing=4, size_hint_y=None)
        self.settings_box.bind(minimum_height=self.settings_box.setter('height'))

        scroll = ScrollView(size_hint_y=0.62)
        scroll.add_widget(self.settings_box)
        root.add_widget(scroll)

        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=8)
        btn_box.add_widget(terminal_button('BACK', THEME_GRAY, on_press=self._go_back))
        btn_box.add_widget(terminal_button('SAVE', THEME_GREEN_DIM, on_press=self._save))
        root.add_widget(btn_box)

        self.add_widget(root)

    def on_pre_enter(self):
        app = App.get_running_app()
        if app:
            self._config = app.config_data

    def on_leave(self):
        self._authenticated = False
        self.auth_msg.text = 'Enter password (0000):'
        self.pwd_input.text = ''
        self.settings_box.clear_widgets()

    def _check_password(self, *args):
        pwd = self.pwd_input.text
        if self._config and self._config.verify_admin_password(pwd):
            self._authenticated = True
            self.auth_msg.text = '> ACCESS GRANTED'
            self.auth_msg.color = THEME_GREEN
            self._build_settings_fields()
        else:
            self.auth_msg.text = '> ACCESS DENIED'
            self.auth_msg.color = THEME_RED
            self.pwd_input.text = ''

    def _add_field(self, label_text, value, on_change):
        box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=4)
        lbl = terminal_label(label_text, '13sp', size_hint_x=0.35, halign='right')
        box.add_widget(lbl)
        inp = terminal_input()
        inp.text = value
        inp.size_hint_x = 0.65
        inp.bind(text=on_change)
        box.add_widget(inp)
        self.settings_box.add_widget(box)
        return inp

    def _add_section(self, title):
        self.settings_box.add_widget(terminal_label(
            f'-- {title} --', '12sp', size_hint_y=None, height=22, color=THEME_GREEN_DIM
        ))

    def _build_settings_fields(self):
        self.settings_box.clear_widgets()
        if not self._config:
            return

        org_name = self._config.get('org_name', '')
        self._add_field('Organization', org_name,
                        lambda i, v: self._config.set('org_name', v))

        self._add_section('SMB')
        self._add_field('SMB Host', self._config.smb_host,
                        lambda i, v: self._config.set('smb_host', v))
        self._add_field('SMB Share', self._config.smb_share,
                        lambda i, v: self._config.set('smb_share', v))
        self._add_field('SMB User', self._config.smb_username,
                        lambda i, v: self._config.set('smb_username', v))
        self._add_field('SMB Pass', self._config.smb_password,
                        lambda i, v: self._config.set('smb_password', v))

        self._add_section('WMS')
        self._add_field('WMS URL', self._config.wms_base_url,
                        lambda i, v: self._config.set('wms_base_url', v))

        self._add_section('LOGS')
        self._add_field('Log SMB Host', self._config.log_smb_host,
                        lambda i, v: self._config.set('log_smb_host', v))
        self._add_field('Log SMB Share', self._config.log_smb_share,
                        lambda i, v: self._config.set('log_smb_share', v))

        # Смена пароля
        pwd_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=4)
        pwd_box.add_widget(terminal_label('New Pass', '13sp', size_hint_x=0.35, halign='right'))
        new_pwd = terminal_input('min 4 chars')
        new_pwd.size_hint_x = 0.4
        pwd_box.add_widget(new_pwd)
        chg_btn = terminal_button('CHANGE', THEME_ORANGE, size_hint_x=0.25, font_size='12sp')
        chg_btn.bind(on_press=lambda x: self._change_password(new_pwd.text))
        pwd_box.add_widget(chg_btn)
        self.settings_box.add_widget(pwd_box)

    def _change_password(self, new_pwd):
        if len(new_pwd) < 4:
            self.auth_msg.text = '> min 4 chars!'
            self.auth_msg.color = THEME_RED
            return
        if self._config:
            self._config.set_admin_password(new_pwd)
            self.auth_msg.text = '> Password changed!'
            self.auth_msg.color = THEME_GREEN

    def _save(self, *args):
        if self._config:
            self._config.save()
            self.auth_msg.text = '> Saved!'
            self.auth_msg.color = THEME_GREEN

    def _go_back(self, *args):
        app = App.get_running_app()
        if app:
            app.sm.current = 'confirm'
