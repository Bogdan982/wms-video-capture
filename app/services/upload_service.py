"""
Foreground Service для фоновой выгрузки видео на сетевой ресурс.

Запускается как Android Service, чтобы выгрузка продолжалась
даже если пользователь свернул приложение.

Используется для длительных операций копирования по SMB.
"""
from kivy.logger import Logger

try:
    from jnius import autoclass, JavaException, PythonJavaClass, java_method

    # Android classes
    Service = autoclass('android.app.Service')
    Intent = autoclass('android.content.Intent')
    Notification = autoclass('android.app.Notification')
    NotificationChannel = autoclass('android.app.NotificationChannel')
    NotificationManager = autoclass('android.app.NotificationManager')
    Build = autoclass('android.os.Build')
    Context = autoclass('android.content.Context')
    PythonService = autoclass('org.kivy.android.PythonService')

    _ANDROID = True
except ImportError:
    _ANDROID = False
    Logger.info("WmsUploadService: Android Service API недоступен")


SERVICE_NAME = 'WmsUploadService'
CHANNEL_ID = 'wms_upload_channel'
NOTIFICATION_ID = 1001


def start_upload_service(task_id: str, local_path: str, config_dict: dict):
    """
    Запускает foreground service для выгрузки.

    :param task_id:     ID задачи
    :param local_path:  путь к локальному видео
    :param config_dict: словарь с настройками SMB/WMS
    """
    if not _ANDROID:
        Logger.info(f"WmsUploadService: [ЭМУЛЯЦИЯ] запуск сервиса "
                     f"task={task_id}, file={local_path}")
        return

    try:
        service_intent = Intent(PythonService.mService, PythonService)
        service_intent.putExtra('task_id', task_id)
        service_intent.putExtra('local_path', local_path)

        # Передаём конфиг как JSON
        import json
        service_intent.putExtra('config', json.dumps(config_dict))

        # Запускаем foreground service
        if Build.VERSION.SDK_INT >= 26:
            PythonService.mService.startForegroundService(service_intent)
        else:
            PythonService.mService.startService(service_intent)

        Logger.info("WmsUploadService: сервис запущен")
    except Exception as e:
        Logger.error(f"WmsUploadService: ошибка запуска: {e}")


def create_notification_channel():
    """Создаёт канал уведомлений для Android 8+."""
    if not _ANDROID or Build.VERSION.SDK_INT < 26:
        return

    try:
        notification_manager = PythonService.mService.getSystemService(
            Context.NOTIFICATION_SERVICE
        )
        channel = NotificationChannel(
            CHANNEL_ID,
            'WMS Upload',
            NotificationManager.IMPORTANCE_LOW
        )
        channel.setDescription('Канал для уведомлений о выгрузке видео')
        notification_manager.createNotificationChannel(channel)
        Logger.info("WmsUploadService: канал уведомлений создан")
    except Exception as e:
        Logger.warning(f"WmsUploadService: ошибка создания канала: {e}")


def build_notification(title: str, text: str) -> object:
    """Создаёт Notification для foreground service."""
    if not _ANDROID:
        return None

    try:
        builder = Notification.Builder(PythonService.mService, CHANNEL_ID)

        if Build.VERSION.SDK_INT >= 26:
            builder = Notification.Builder(PythonService.mService, CHANNEL_ID)
        else:
            builder = Notification.Builder(PythonService.mService)

        builder.setContentTitle(title)
        builder.setContentText(text)
        builder.setSmallIcon(
            PythonService.mService.getApplicationInfo().icon
        )
        builder.setOngoing(True)

        return builder.build()
    except Exception as e:
        Logger.error(f"WmsUploadService: ошибка создания уведомления: {e}")
        return None


def stop_service():
    """Останавливает foreground service."""
    if not _ANDROID:
        return

    try:
        PythonService.mService.stopForeground(True)
        PythonService.mService.stopSelf()
        Logger.info("WmsUploadService: сервис остановлен")
    except Exception as e:
        Logger.error(f"WmsUploadService: ошибка остановки: {e}")
