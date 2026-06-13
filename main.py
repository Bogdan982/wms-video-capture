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

from app.app import WmsVideoApp

# Android Activity Result Handler
try:
    from android import activity
    _ANDROID = True
except ImportError:
    _ANDROID = False


def _request_permissions():
    """Запрашивает разрешения: камера, микрофон, хранилище."""
    try:
        from android.permissions import request_permissions, Permission, check_permission
        needed = []
        if not check_permission(Permission.CAMERA):
            needed.append(Permission.CAMERA)
        if not check_permission(Permission.RECORD_AUDIO):
            needed.append(Permission.RECORD_AUDIO)
        if not check_permission(Permission.WRITE_EXTERNAL_STORAGE):
            needed.append(Permission.WRITE_EXTERNAL_STORAGE)
        if needed:
            request_permissions(needed)
    except Exception as e:
        from kivy.logger import Logger
        Logger.warning(f"Permissions: {e}")


def main():
    """Точка входа."""
    # Запрос разрешений на Android
    if _ANDROID:
        _request_permissions()

    app = WmsVideoApp(task_id=_task_id)

    if _ANDROID:
        def on_activity_result(request_code, result_code, data):
            if request_code == 1001:  # Camera
                app.camera.on_activity_result(request_code, result_code, data)
            elif request_code == 2001:  # QR Scanner
                app.qr.on_activity_result(request_code, result_code, data)

        activity.bind(on_activity_result=on_activity_result)

    app.run()


if __name__ == '__main__':
    main()
