"""
Конфигурация приложения.

Настройки WMS-сервера, сетевого хранилища (SMB/CIFS),
параметры логирования, пароль администратора, QR-сканера.

Читается из config.json в папке приложения.
При первом запуске создаётся с умолчаниями.
"""
import os
import json
import hashlib
from kivy.logger import Logger


CONFIG_FILE = os.path.join(
    os.environ.get('ANDROID_PRIVATE', '.'),
    'config.json'
)

# Пароль по умолчанию (hex-хэш sha256 от "admin")
_DEFAULT_PASSWORD_HASH = hashlib.sha256(b'0000').hexdigest()


class AppConfig:
    """
    Конфигурация приложения.

    Хранит:
      - SMB/CIFS-подключение к сетевому ресурсу
      - REST-эндпоинты WMS
      - Настройки логирования (путь на SMB для логов)
      - Пароль администратора (SHA-256 хэш)
      - Параметры видео и ретраев
    """

    def __init__(self, config_path: str = CONFIG_FILE):
        self._path = config_path
        self._data = {}
        self._loaded = False
        self.load()

    # ── WMS ──────────────────────────────────────

    @property
    def wms_base_url(self) -> str:
        return self._data.get('wms_base_url',
                              'http://192.168.1.100:8080/wms')

    @property
    def wms_flag_endpoint(self) -> str:
        return self._data.get(
            'wms_flag_endpoint',
            f'{self.wms_base_url}/api/v1/tasks/flag'
        )

    # ── SMB (сетевой ресурс) ──────────────────────

    @property
    def smb_host(self) -> str:
        return self._data.get('smb_host', '192.168.1.200')

    @property
    def smb_share(self) -> str:
        return self._data.get('smb_share', 'video_archive')

    @property
    def smb_username(self) -> str:
        return self._data.get('smb_username', 'WORKGROUP\\wms_user')

    @property
    def smb_password(self) -> str:
        return self._data.get('smb_password', '')

    @property
    def smb_root_folder(self) -> str:
        return self._data.get('smb_root_folder', 'captures')

    # ── Логирование ──────────────────────────────

    @property
    def log_enabled(self) -> bool:
        """Включено ли удалённое логирование."""
        return self._data.get('log_enabled', True)

    @property
    def log_smb_host(self) -> str:
        """SMB-сервер для логов (может быть тем же или отдельным)."""
        return self._data.get('log_smb_host', self.smb_host)

    @property
    def log_smb_share(self) -> str:
        """SMB-шара для логов."""
        return self._data.get('log_smb_share', 'logs')

    @property
    def log_smb_folder(self) -> str:
        """Папка внутри шары для логов (по устройству или дате)."""
        return self._data.get('log_smb_folder', 'wms_capture')

    @property
    def log_smb_username(self) -> str:
        return self._data.get('log_smb_username', self.smb_username)

    @property
    def log_smb_password(self) -> str:
        return self._data.get('log_smb_password', self.smb_password)

    @property
    def log_max_size_kb(self) -> int:
        """Максимальный размер локального лог-файла до ротации (КБ)."""
        return self._data.get('log_max_size_kb', 512)

    @property
    def log_upload_interval_min(self) -> int:
        """Интервал автоматической выгрузки логов (минуты)."""
        return self._data.get('log_upload_interval_min', 30)

    # ── Безопасность ────────────────────────────

    @property
    def admin_password_hash(self) -> str:
        """SHA-256 хэш пароля для входа в настройки."""
        return self._data.get('admin_password_hash', _DEFAULT_PASSWORD_HASH)

    def verify_admin_password(self, plain_password: str) -> bool:
        """Проверяет пароль администратора."""
        pwd_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        return pwd_hash == self.admin_password_hash

    def set_admin_password(self, new_plain_password: str):
        """Устанавливает новый пароль (сохраняет хэш)."""
        self._data['admin_password_hash'] = \
            hashlib.sha256(new_plain_password.encode()).hexdigest()
        self.save()

    # ── Видео ────────────────────────────────────

    @property
    def video_max_duration_sec(self) -> int:
        return self._data.get('video_max_duration_sec', 300)

    @property
    def video_quality(self) -> int:
        return self._data.get('video_quality', 1)

    # ── Retry ─────────────────────────────────────

    @property
    def delete_local_after_upload(self) -> bool:
        return self._data.get('delete_local_after_upload', True)

    @property
    def retry_attempts(self) -> int:
        return self._data.get('retry_attempts', 3)

    @property
    def retry_delay_sec(self) -> int:
        return self._data.get('retry_delay_sec', 5)

    # ── QR / Сканер ──────────────────────────────

    @property
    def qr_timeout_sec(self) -> int:
        """Таймаут ожидания QR-сканирования."""
        return self._data.get('qr_timeout_sec', 60)

    # ── Загрузка / сохранение ────────────────────

    def load(self):
        try:
            if os.path.exists(self._path):
                with open(self._path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                self._loaded = True
                Logger.info(f"AppConfig: загружена из {self._path}")
            else:
                Logger.info("AppConfig: файл не найден, создаю умолчания")
                self.save()
        except Exception as e:
            Logger.warning(f"AppConfig: ошибка загрузки: {e}")

    def save(self):
        try:
            with open(self._path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            Logger.info(f"AppConfig: сохранена в {self._path}")
            return True
        except Exception as e:
            Logger.error(f"AppConfig: ошибка сохранения: {e}")
            return False

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def to_dict(self) -> dict:
        return dict(self._data)

    def __repr__(self) -> str:
        return f"<AppConfig loaded={self._loaded} keys={list(self._data.keys())}>"
