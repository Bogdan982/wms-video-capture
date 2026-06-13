"""
Сервис логирования с автоматической отправкой на сетевой ресурс предприятия.

Два уровня:
  1. Локальный лог-файл (ротация по размеру)
  2. Периодическая выгрузка на SMB (log_smb_host / log_smb_share)

Логи содержат: timestamp, уровень, компонент, сообщение.
"""
import os
import sys
import time
import json
from datetime import datetime
from threading import Lock
from kivy.logger import Logger

try:
    from smb.SMBConnection import SMBConnection
    _SMB_AVAILABLE = True
except ImportError:
    _SMB_AVAILABLE = False


# Коды уровней логирования
LOG_DEBUG = 10
LOG_INFO = 20
LOG_WARNING = 30
LOG_ERROR = 40

LEVEL_NAMES = {
    LOG_DEBUG: 'DEBUG',
    LOG_INFO: 'INFO',
    LOG_WARNING: 'WARN',
    LOG_ERROR: 'ERROR',
}


class LoggerService:
    """
    Логирование с отправкой на SMB.

    Использование:
        logger = LoggerService(config)
        logger.info("CAMERA", "Запись начата")
        logger.error("UPLOAD", "Ошибка выгрузки: ...")
    """

    def __init__(self, config):
        self._config = config
        self._lock = Lock()
        self._log_dir = self._get_log_dir()
        self._log_file = self._get_log_path()
        self._upload_timer = None
        self._pending_upload = False
        self._entries_since_upload = 0

        # Создаём директорию
        os.makedirs(self._log_dir, exist_ok=True)

        # Пишем заголовок лога
        self._write_raw('# WMS Video Capture Log')
        self._write_raw(f'# Startup: {datetime.now().isoformat()}')
        self._write_raw(f'# Device: {self._get_device_id()}')
        self._write_raw(f'# Config: {json.dumps(config.to_dict(), ensure_ascii=False)}')
        self._write_raw('')

        # Флаг отправки логов при старте
        self.info("LOG", "Сервис логирования запущен")

        # Периодическая выгрузка
        self._schedule_upload()

    def _get_log_dir(self) -> str:
        """Определяет директорию для логов."""
        base = os.environ.get('ANDROID_PRIVATE', 
                             os.path.join(os.path.expanduser('~'), '.wms_capture'))
        return os.path.join(base, 'logs')

    def _get_log_path(self) -> str:
        """Путь к текущему лог-файлу."""
        date_str = datetime.now().strftime('%Y%m%d')
        device_id = self._get_device_id()[:8]
        return os.path.join(self._log_dir, f'capture_{date_str}_{device_id}.log')

    def _get_device_id(self) -> str:
        """Идентификатор устройства."""
        try:
            from jnius import autoclass
            ANDROID_ID = autoclass('android.provider.Settings$Secure')
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            return ANDROID_ID.getString(
                activity.getContentResolver(),
                ANDROID_ID.ANDROID_ID
            )
        except Exception:
            return "unknown_device"

    def debug(self, component: str, message: str):
        """Уровень DEBUG."""
        self._log(LOG_DEBUG, component, message)

    def info(self, component: str, message: str):
        """Уровень INFO."""
        self._log(LOG_INFO, component, message)

    def warning(self, component: str, message: str):
        """Уровень WARNING."""
        self._log(LOG_WARNING, component, message)

    def error(self, component: str, message: str):
        """Уровень ERROR."""
        self._log(LOG_ERROR, component, message)

    def _log(self, level: int, component: str, message: str):
        """
        Внутренний метод записи лога.
        Пишет в локальный файл и дублирует в Kivy Logger.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level_name = LEVEL_NAMES.get(level, '????')
        log_line = f'{timestamp} | {level_name} | {component:8s} | {message}'

        # Kivy Logger
        if level == LOG_DEBUG:
            Logger.debug(log_line)
        elif level == LOG_INFO:
            Logger.info(log_line)
        elif level == LOG_WARNING:
            Logger.warning(log_line)
        elif level == LOG_ERROR:
            Logger.error(log_line)

        # Локальный файл
        self._write_raw(log_line)

        # Проверка ротации
        self._check_rotation()

        # Планируем выгрузку
        self._entries_since_upload += 1
        if not self._pending_upload:
            self._pending_upload = True
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self._try_upload(), 60)

    def _write_raw(self, line: str):
        """Пишет строку в лог-файл (потокобезопасно)."""
        with self._lock:
            try:
                with open(self._log_file, 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
            except Exception as e:
                Logger.error(f"LoggerService: ошибка записи: {e}")

    # ── Ротация ──

    def _check_rotation(self):
        """Ротация при превышении размера."""
        max_size = self._config.log_max_size_kb * 1024
        try:
            size = os.path.getsize(self._log_file)
            if size > max_size:
                self._rotate()
        except Exception:
            pass

    def _rotate(self):
        """Ротация лог-файла."""
        with self._lock:
            try:
                # Выгружаем перед ротацией
                self._upload_now()

                # Переименовываем старый
                base, ext = os.path.splitext(self._log_file)
                timestamp = datetime.now().strftime('%H%M%S')
                rotated = f'{base}_{timestamp}{ext}'
                os.rename(self._log_file, rotated)

                # Новый файл
                self._log_file = self._get_log_path()
                self._write_raw('# Rotated from previous log')
                self._write_raw(f'# New file: {datetime.now().isoformat()}')

                Logger.info(f"LoggerService: ротация лога -> {rotated}")
            except Exception as e:
                Logger.error(f"LoggerService: ошибка ротации: {e}")

    # ── Выгрузка на SMB ──

    def _schedule_upload(self):
        """Периодическая выгрузка логов."""
        from kivy.clock import Clock
        interval = max(self._config.log_upload_interval_min * 60, 120)
        Clock.schedule_interval(lambda dt: self._try_upload(), interval)

    def _try_upload(self):
        """Пытается выгрузить логи на SMB."""
        self._pending_upload = False
        if not self._config.log_enabled:
            return

        if self._entries_since_upload < 5:
            return  # Слишком мало новых записей

        self._upload_now()

    def _upload_now(self) -> bool:
        """Немедленная выгрузка лог-файла на SMB."""
        if not _SMB_AVAILABLE:
            Logger.debug("LoggerService: pysmb не доступен, выгрузка логов пропущена")
            return False

        if not os.path.exists(self._log_file):
            return False

        config = self._config

        try:
            conn = SMBConnection(
                username=config.log_smb_username,
                password=config.log_smb_password,
                my_name='WMS_CAPTURE_LOG',
                remote_name=config.log_smb_host,
                use_ntlm_v2=True,
                is_direct_tcp=True
            )

            if not conn.connect(config.log_smb_host, 445, timeout=10):
                Logger.warning("LoggerService: не удалось подключиться для выгрузки логов")
                return False

            # Создаём папку по дате
            date_folder = datetime.now().strftime('%Y%m%d')
            remote_dir = f'/{config.log_smb_folder}/{date_folder}'

            try:
                conn.listPath(config.log_smb_share, remote_dir)
            except Exception:
                conn.createDirectory(config.log_smb_share, remote_dir)

            # Имя файла на сервере
            remote_filename = os.path.basename(self._log_file)
            remote_path = f'{remote_dir}/{remote_filename}'

            with open(self._log_file, 'rb') as f:
                conn.storeFile(config.log_smb_share, remote_path, f)

            conn.close()

            self._entries_since_upload = 0
            Logger.info(f"LoggerService: логи выгружены -> {remote_path}")
            return True

        except Exception as e:
            Logger.warning(f"LoggerService: ошибка выгрузки логов: {e}")
            return False

    # ── Завершение ──

    def shutdown(self):
        """Выгружает логи и завершает работу."""
        Logger.info("LoggerService: завершение работы")
        self.info("LOG", "Сервис логирования завершён")
        self._upload_now()

    def get_log_file_path(self) -> str:
        """Возвращает путь к текущему лог-файлу для ручного копирования."""
        return self._log_file
