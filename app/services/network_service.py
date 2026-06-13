"""
Сервис сетевой выгрузки на SMB/CIFS-ресурс предприятия.

Схема работы:
  1. Подключается к SMB-шаре
  2. Создаёт папку с именем идентификатора задачи
  3. Копирует видеофайл в эту папку
  4. Возвращает удалённый путь к файлу
  5. При ошибке — повторяет (согласно настройкам retry_attempts)
"""
import os
import time
from kivy.logger import Logger

try:
    from smb.SMBConnection import SMBConnection
    _SMB_AVAILABLE = True
except ImportError:
    _SMB_AVAILABLE = False
    Logger.warning("NetworkService: pysmb не установлен. "
                   "Установите: pip install pysmb")

try:
    from jnius import autoclass
    _ANDROID = True
except ImportError:
    _ANDROID = False


class NetworkService:
    """Выгрузка видео на сетевой SMB/CIFS-ресурс."""

    def __init__(self, config):
        """
        :param config: экземпляр AppConfig с настройками SMB
        """
        self._config = config
        self._conn = None

    def upload_with_folder(
        self,
        local_path: str,
        task_id: str,
        filename: str = None
    ) -> str:
        """
        Выгружает файл на SMB-шару, создаёт папку task_id.

        :param local_path: путь к локальному файлу
        :param task_id:    идентификатор задачи (= имя папки)
        :param filename:   имя файла на сервере (или basename local_path)
        :return:           удалённый путь (UNC или SMB path), или None
        """
        filename = filename or os.path.basename(local_path)
        retries = self._config.retry_attempts
        delay = self._config.retry_delay_sec

        for attempt in range(1, retries + 1):
            Logger.info(f"NetworkService: попытка {attempt}/{retries} — "
                        f"выгрузка {filename}")
            try:
                return self._do_upload(local_path, task_id, filename)
            except Exception as e:
                Logger.error(f"NetworkService: ошибка (попытка {attempt}): {e}")
                if attempt < retries:
                    Logger.info(f"NetworkService: повтор через {delay}с...")
                    time.sleep(delay)
                else:
                    Logger.error("NetworkService: все попытки исчерпаны")
                    return None

    def _do_upload(self, local_path: str, task_id: str, filename: str) -> str:
        """Реальная выгрузка по SMB."""
        if not _SMB_AVAILABLE:
            Logger.warning("NetworkService: pysmb не установлен — эмуляция")
            return self._emulate_upload(local_path, task_id, filename)

        config = self._config

        # ── 1. Подключение к SMB-серверу ──
        conn = SMBConnection(
            username=config.smb_username,
            password=config.smb_password,
            my_name='WMS_CAPTURE_APP',
            remote_name=config.smb_host,
            use_ntlm_v2=True,
            is_direct_tcp=True
        )

        try:
            if not conn.connect(config.smb_host, 445):
                raise ConnectionError(f"Не удалось подключиться к "
                                      f"{config.smb_host}:445")

            # ── 2. Создание корневой папки (если нет) ──
            root = config.smb_root_folder
            try:
                conn.listPath(config.smb_share, f'/{root}')
            except Exception:
                Logger.info(f"NetworkService: создаю корневую папку {root}")
                conn.createDirectory(config.smb_share, f'/{root}')

            # ── 3. Создание папки задачи ──
            remote_dir = f'/{root}/{task_id}'
            try:
                conn.listPath(config.smb_share, remote_dir)
                Logger.info(f"NetworkService: папка {remote_dir} уже существует")
            except Exception:
                Logger.info(f"NetworkService: создаю папку {remote_dir}")
                conn.createDirectory(config.smb_share, remote_dir)

            # ── 4. Копирование файла ──
            remote_path = f'{remote_dir}/{filename}'
            with open(local_path, 'rb') as f_local:
                conn.storeFile(config.smb_share, remote_path, f_local)

            Logger.info(f"NetworkService: файл выгружен → {remote_path}")

            # ── 5. Проверка (stat файла) ──
            try:
                files = conn.listPath(config.smb_share, remote_dir)
                uploaded = [f for f in files if f.filename == filename]
                if uploaded:
                    Logger.info(f"NetworkService: проверка пройдена, "
                                f"размер={uploaded[0].file_size} байт")
            except Exception as e:
                Logger.warning(f"NetworkService: проверка не удалась: {e}")

            conn.close()

            # Возвращаем UNC-путь
            unc_path = f"\\\\{config.smb_host}\\{config.smb_share}\\{root}\\{task_id}\\{filename}"
            return unc_path

        except Exception as e:
            try:
                conn.close()
            except Exception:
                pass
            raise

    def _emulate_upload(self, local_path: str, task_id: str, filename: str) -> str:
        """Эмуляция выгрузки для десктопной отладки."""
        Logger.info(f"NetworkService: [ЭМУЛЯЦИЯ] создаю папку {task_id}")
        Logger.info(f"NetworkService: [ЭМУЛЯЦИЯ] копирую {filename}")
        fake_remote = f"//storage-server/video_archive/captures/{task_id}/{filename}"
        Logger.info(f"NetworkService: [ЭМУЛЯЦИЯ] успешно: {fake_remote}")
        return fake_remote

    def check_connectivity(self) -> bool:
        """Проверяет доступность SMB-сервера."""
        if not _SMB_AVAILABLE:
            return True  # эмуляция

        config = self._config
        try:
            conn = SMBConnection(
                config.smb_username, config.smb_password,
                'CHECK', config.smb_host,
                use_ntlm_v2=True, is_direct_tcp=True
            )
            result = conn.connect(config.smb_host, 445, timeout=5)
            if result:
                conn.close()
            return result
        except Exception:
            return False
