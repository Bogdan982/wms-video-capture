"""
Сервис управления камерой.

На Android: использует стандартный Intent MediaStore.ACTION_VIDEO_CAPTURE
для записи видео штатной камерой. После завершения возвращает URI видео.

На десктопе (отладка): имитирует запись.
"""
import os
import uuid
from datetime import datetime
from kivy.logger import Logger

# Android-импорты (доступны только на устройстве)
try:
    from jnius import autoclass, cast, JavaException
    from android import mActivity
    from android.runnable import run_on_ui_thread

    # Android classes
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    Environment = autoclass('android.os.Environment')
    MediaStore = autoclass('android.provider.MediaStore')
    FileProvider = autoclass('androidx.core.content.FileProvider')
    File = autoclass('java.io.File')
    Activity = autoclass('android.app.Activity')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')

    _ANDROID = True
except ImportError:
    _ANDROID = False
    Logger.warning("CameraService: Android API недоступен (работает в режиме эмуляции)")


# Код запроса для Activity Result (запись видео)
CAPTURE_VIDEO_REQUEST_CODE = 1001


class CameraService:
    """Сервис записи видео через системную камеру Android."""

    def __init__(self, app):
        """
        :param app: экземпляр WmsVideoApp (для коллбэков)
        """
        self._app = app
        self._task_id = None
        self._output_uri = None
        self._recording = False

    def start_recording(self, task_id: str):
        """
        Запускает системную камеру для записи видео.

        На Android:
          1. Создаёт временный URI через FileProvider
          2. Запускает Intent ACTION_VIDEO_CAPTURE
          3. Регистрирует коллбэк на результат

        На десктопе:
          Имитирует запись (3 сек) и возвращает тестовый путь.
        """
        self._task_id = task_id
        self._recording = True

        if not _ANDROID:
            # ── Десктопная эмуляция ──
            Logger.info("CameraService: [ЭМУЛЯЦИЯ] запись видео...")
            from kivy.clock import Clock
            Clock.schedule_once(self._emulate_recording, 3.0)
            return

        # ── Android: запуск системной камеры ──
        try:
            self._start_android_camera(task_id)
        except Exception as e:
            Logger.error(f"CameraService: ошибка запуска камеры: {e}")
            self._recording = False
            if self._app:
                self._app.on_recording_finished(None, task_id)

    def _start_android_camera(self, task_id: str):
        """Android: запускает Intent для записи видео."""
        Logger.info(f"CameraService: запуск системной камеры для {task_id}")

        # Создаём Intent
        intent = Intent(MediaStore.ACTION_VIDEO_CAPTURE)

        # Ограничения записи (из конфига)
        config = self._app.config_data if self._app else None
        if config:
            duration_limit = config.video_max_duration_sec
            quality = config.video_quality
        else:
            duration_limit = 300
            quality = 1

        intent.putExtra(MediaStore.EXTRA_DURATION_LIMIT, duration_limit)
        intent.putExtra(MediaStore.EXTRA_VIDEO_QUALITY, quality)
        intent.putExtra('android.intent.extra.USE_FRONT_CAMERA', False)

        # Внешняя временная директория
        # (на Android 10+ используется MediaStore, но для обратной совместимости — FileProvider)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{task_id}_{timestamp}.mp4"

        try:
            # Создаём файл в кэш-директории приложения
            cache_dir = mActivity.getCacheDir()
            video_dir = File(cache_dir, 'videos')
            video_dir.mkdirs()

            video_file = File(video_dir, filename)

            # Получаем URI через FileProvider
            authority = f"{mActivity.getPackageName()}.fileprovider"
            output_uri = FileProvider.getUriForFile(mActivity, authority, video_file)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, output_uri)
            self._output_uri = output_uri

            # Предоставляем временные права на запись
            intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

        except Exception as e:
            Logger.warning(f"CameraService: FileProvider не сработал, "
                           f"используем стандартный Output: {e}")
            # Запасной вариант — без EXTRA_OUTPUT, камера сама сохранит

        # Запускаем Intent с обработкой результата
        # Используем onActivityResult
        PythonActivity.mActivity.startActivityForResult(intent, CAPTURE_VIDEO_REQUEST_CODE)

    def on_activity_result(self, request_code: int, result_code: int, data):
        """
        Обработчик результата от системной камеры.
        Регистрируется в main.py/Android onActivityResult.
        """
        if request_code != CAPTURE_VIDEO_REQUEST_CODE:
            return

        self._recording = False

        if result_code == Activity.RESULT_OK and data:
            # Получаем URI записанного видео
            video_uri = data.getData()
            if video_uri:
                uri_str = str(video_uri.toString())
                Logger.info(f"CameraService: видео записано: {uri_str}")
                if self._app:
                    self._app.on_recording_finished(uri_str, self._task_id)
                return
            elif self._output_uri:
                # Если мы указали EXTRA_OUTPUT — видео там
                uri_str = str(self._output_uri.toString())
                Logger.info(f"CameraService: видео записано (выходной URI): {uri_str}")
                if self._app:
                    self._app.on_recording_finished(uri_str, self._task_id)
                return

        # Ошибка или отмена
        if result_code == Activity.RESULT_CANCELED:
            Logger.warning("CameraService: съёмка отменена пользователем")
        else:
            Logger.error(f"CameraService: ошибка записи, code={result_code}")

        if self._app:
            self._app.on_recording_finished(None, self._task_id)

    def _emulate_recording(self, dt):
        """Эмуляция записи для десктопной отладки."""
        Logger.info("CameraService: [ЭМУЛЯЦИЯ] запись завершена")
        self._recording = False
        fake_path = f"/tmp/{self._task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        if self._app:
            self._app.on_recording_finished(fake_path, self._task_id)

    @property
    def is_recording(self) -> bool:
        return self._recording
