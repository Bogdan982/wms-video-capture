"""
Тема приложения — зелёный терминал на тёмном фоне.
"""
# Цвета
THEME_BG = (0.1, 0.1, 0.1, 1)          # фон — почти чёрный
THEME_INPUT_BG = (0.15, 0.15, 0.15, 1)  # фон полей ввода — тёмно-серый
THEME_GREEN = (0.2, 1.0, 0.3, 1)        # зелёный текст
THEME_GREEN_DIM = (0.15, 0.7, 0.2, 1)   # приглушённый зелёный
THEME_GRAY = (0.5, 0.5, 0.5, 1)         # серый текст
THEME_BLUE = (0.3, 0.6, 1.0, 1)         # синий акцент
THEME_RED = (1.0, 0.3, 0.3, 1)          # красный
THEME_ORANGE = (0.9, 0.6, 0.1, 1)       # оранжевый

def terminal_label(text='', font_size='16sp', bold=False, **kw):
    """Создаёт Label в стиле терминала."""
    from kivy.uix.label import Label
    return Label(
        text=text,
        font_size=font_size,
        bold=bold,
        color=THEME_GREEN,
        halign='center',
        **kw
    )

def terminal_input(hint='', multiline=False, password=False, **kw):
    """Создаёт TextInput в стиле терминала."""
    from kivy.uix.textinput import TextInput
    return TextInput(
        hint_text=hint,
        multiline=multiline,
        password=password,
        font_size='14sp',
        foreground_color=THEME_GREEN,
        background_color=THEME_INPUT_BG,
        cursor_color=THEME_GREEN,
        **kw
    )

def terminal_button(text='', color=THEME_BLUE, **kw):
    """Создаёт Button в стиле терминала."""
    from kivy.uix.button import Button
    return Button(
        text=text,
        font_size='15sp',
        background_color=color,
        color=(1, 1, 1, 1),
        **kw
    )
