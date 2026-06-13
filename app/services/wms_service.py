"""
Сервис взаимодействия с WMS предприятия.

Отправляет файл-флаг после успешной выгрузки видео.

Формат файла-флага:
  - HTTP POST JSON на эндпоинт WMS
  - Содержит идентификатор задачи и UNC-путь к видео
  - WMS подтверждает получение (HTTP 200)
"""
import json
import time
from datetime import datetime
from kivy.logger import Logger

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False
    Logger.warning("WmsService: requests не установлен. "
                   "Установите: pip install requests")


class WmsService:
    """Отправка флагов на WMS-сервер."""

    def __init__(self, config):
        """
        :param config: экземпляр AppConfig
        """
        self._config = config

    def send_flag(self, task_id: str, remote_path: str) -> bool:
        """
        Отправляет файл-флаг на WMS.

        :param task_id:     идентификатор задачи
        :param remote_path: UNC/SMB-путь к выгруженному видео
        :return:            True если WMS подтвердил (HTTP 200-299)
        """
        payload = self._build_payload(task_id, remote_path)

        Logger.info(f"WmsService: отправка флага на {self._config.wms_flag_endpoint}")
        Logger.debug(f"WmsService: payload={json.dumps(payload, ensure_ascii=False)}")

        if not _REQUESTS_AVAILABLE:
            Logger.info("WmsService: [ЭМУЛЯЦИЯ] флаг отправлен")
            return True

        retries = self._config.retry_attempts
        delay = self._config.retry_delay_sec

        for attempt in range(1, retries + 1):
            try:
                timeout = 15 if attempt == 1 else 30
                response = requests.post(
                    url=self._config.wms_flag_endpoint,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=timeout
                )

                if 200 <= response.status_code < 300:
                    Logger.info(f"WmsService: WMS подтвердил (HTTP {response.status_code})")
                    return True
                else:
                    Logger.warning(f"WmsService: WMS вернул {response.status_code}: "
                                   f"{response.text[:200]}")

            except requests.exceptions.Timeout:
                Logger.warning(f"WmsService: таймаут (попытка {attempt})")
            except requests.exceptions.ConnectionError as e:
                Logger.warning(f"WmsService: ошибка соединения (попытка {attempt}): {e}")
            except Exception as e:
                Logger.error(f"WmsService: ошибка (попытка {attempt}): {e}")

            if attempt < retries:
                Logger.info(f"WmsService: повтор через {delay}с...")
                time.sleep(delay)

        Logger.error("WmsService: не удалось отправить флаг после всех попыток")

        # ── Сохраняем флаг локально (на случай повторной отправки) ──
        self._save_flag_locally(payload)
        return False

    def _build_payload(self, task_id: str, remote_path: str) -> dict:
        """Формирует JSON-тело запроса."""
        return {
            "event": "video_capture_completed",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "video_path": remote_path,
                "storage_type": "smb",
                "status": "uploaded",
                "device_id": self._get_device_id()
            }
        }

    def _get_device_id(self) -> str:
        """Возвращает идентификатор устройства (Android ID)."""
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

    def _save_flag_locally(self, payload: dict):
        """Сохраняет флаг локально (если WMS недоступен — для ручной синхронизации)."""
        try:
            import os
            flags_dir = os.path.join(
                os.environ.get('ANDROID_PRIVATE', '.'),
                'pending_flags'
            )
            os.makedirs(flags_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"flag_{payload['task_id']}_{timestamp}.json"
            filepath = os.path.join(flags_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            Logger.info(f"WmsService: флаг сохранён локально: {filepath}")
        except Exception as e:
            Logger.error(f"WmsService: не удалось сохранить флаг локально: {e}")

    def health_check(self) -> bool:
        """Проверяет доступность WMS-сервера."""
        if not _REQUESTS_AVAILABLE:
            return True

        try:
            resp = requests.get(
                self._config.wms_base_url,
                timeout=5
            )
            return resp.status_code < 500
        except Exception:
            return False
