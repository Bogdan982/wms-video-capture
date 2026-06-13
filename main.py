"""
WMS Video Capture — Android App.
Точка входа. Обрабатывает Intent из WMS и ActivityResult от камеры/QR.
"""
import os
import sys

# Отлавливаем task_id из CLI до инициализации Kivy
_task_id = None
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        if 'task_id=' in arg:
            _task_id = arg.split('task_id=')[-1].split('&')[0]

import kivy
kivy.require('2.2.0')

from kivy.config import Config
Config.set('kivy', 'log_level', 'info')
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '800')

from app.app import WmsVideoApp

# Android Activity Result Handler
try:
    from android import activity
    _ANDROID = True
except ImportError:
    _ANDROID = False


def main():
    """Точка входа."""
    app = WmsVideoApp(task_id=_task_id)

    if _ANDROID:
        # Регистрируем единый обработчик ActivityResult
        # который диспатчит по request_code
        def on_activity_result(request_code, result_code, data):
            if request_code == 1001:  # Camera
                app.camera.on_activity_result(request_code, result_code, data)
            elif request_code == 2001:  # QR Scanner
                app.qr.on_activity_result(request_code, result_code, data)

        activity.bind(on_activity_result=on_activity_result)

    app.run()


if __name__ == '__main__':
    main()
