"""
Сервис управления локальными файлами.

- Копирование видео из URI системной камеры в постоянное хранилище
- Переименование в формат {идентификатор}_{timestamp}.mp4
- Удаление локальной копии после выгрузки
"""
import os
import shutil
from datetime import datetime
from kivy.logger import Logger

try:
    from jnius import autoclass, JavaException
    _ANDROID = True
except ImportError:
    _ANDROID = False

# Android ContentResolver
if _ANDROID:
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Uri = autoclass('android.net.Uri')
    InputStream = autoclass('java.io.InputStream')
    FileOutputStream = autoclass('java.io.FileOutputStream')
    File = autoclass('java.io.File')
    BitmapFactory = autoclass('android.graphics.BitmapFactory')


class FileService:
    """Операции с видеофайлами на устройстве."""

    def __init__(self, base_dir: str = None):
        """
        :param base_dir: директория для хранения видео.
                         На Android — внешнее хранилище / movies.
        """
        if base_dir:
            self._base_dir = base_dir
        else:
            self._base_dir = self._get_default_storage()

        os.makedirs(self._base_dir, exist_ok=True)
        Logger.info(f"FileService: хранилище: {self._base_dir}")

    def _get_default_storage(self) -> str:
        """Определяет директорию по умолчанию."""
        if _ANDROID:
            try:
                env = autoclass('android.os.Environment')
                pictures_dir = env.getExternalStoragePublicDirectory(
                    env.DIRECTORY_MOVIES
                )
                video_dir = File(pictures_dir, 'WMSCapture')
                video_dir.mkdirs()
                return str(video_dir.getAbsolutePath())
            except Exception:
                pass
        # Десктоп / запасной
        return os.path.join(os.path.expanduser('~'), 'WMSCapture')

    def generate_filename(self, task_id: str) -> str:
        """
        Генерирует имя файла: {task_id}_{YYYYMMDD_HHMMSS}.mp4
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Очищаем task_id от недопустимых символов в имени файла
        safe_id = ''.join(c for c in task_id if c.isalnum() or c in '-_.')
        return f"{safe_id}_{timestamp}.mp4"

    def save_video(self, video_uri: str, task_id: str) -> str:
        """
        Сохраняет видео из URI системной камеры в постоянное хранилище.

        :param video_uri: URI видео (content:// schema на Android, или путь)
        :param task_id:   идентификатор задачи
        :return:          локальный путь к сохранённому файлу, или None
        """
        filename = self.generate_filename(task_id)
        dest_path = os.path.join(self._base_dir, filename)

        if _ANDROID and video_uri.startswith('content://'):
            return self._copy_from_content_uri(video_uri, dest_path)
        elif os.path.exists(video_uri):
            return self._copy_local_file(video_uri, dest_path)
        else:
            Logger.error(f"FileService: URI не найден: {video_uri}")
            return None

    def _copy_from_content_uri(self, content_uri: str, dest_path: str) -> str:
        """Копирует файл из content:// URI в локальную файловую систему."""
        try:
            activity = PythonActivity.mActivity
            uri = Uri.parse(content_uri)
            content_resolver = activity.getContentResolver()
            input_stream = content_resolver.openInputStream(uri)

            if not input_stream:
                Logger.error("FileService: не удалось открыть InputStream")
                return None

            # Определяем размер файла из ContentResolver
            cursor = content_resolver.query(uri, None, None, None, None)
            file_size = 0
            if cursor:
                try:
                    if cursor.moveToFirst():
                        size_idx = cursor.getColumnIndex('_size')
                        if size_idx >= 0:
                            file_size = cursor.getLong(size_idx)
                finally:
                    cursor.close()

            # Копируем
            with open(dest_path, 'wb') as f_out:
                buffer = bytearray(8192)
                total = 0
                while True:
                    bytes_read = input_stream.read(buffer, 0, 8192)
                    if bytes_read <= 0:
                        break
                    f_out.write(bytes(buffer[:bytes_read]))
                    total += bytes_read

            input_stream.close()
            Logger.info(f"FileService: скопировано {total} байт -> {dest_path}")
            return dest_path

        except Exception as e:
            Logger.error(f"FileService: ошибка копирования из content URI: {e}")
            return None

    def _copy_local_file(self, source_path: str, dest_path: str) -> str:
        """Копирует локальный файл."""
        try:
            shutil.copy2(source_path, dest_path)
            src_size = os.path.getsize(source_path)
            Logger.info(f"FileService: скопировано {src_size} байт "
                        f"{source_path} -> {dest_path}")
            return dest_path
        except Exception as e:
            Logger.error(f"FileService: ошибка копирования файла: {e}")
            return None

    def delete_local(self, file_path: str) -> bool:
        """
        Безвозвратно удаляет локальный видеофайл.
        Вызывается после подтверждения успешной выгрузки.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                Logger.info(f"FileService: файл удалён: {file_path}")
                return True
            else:
                Logger.warning(f"FileService: файл не найден: {file_path}")
                return False
        except Exception as e:
            Logger.error(f"FileService: ошибка удаления {file_path}: {e}")
            return False

    def rename_with_id(self, file_path: str, new_task_id: str) -> str:
        """
        Переименовывает видеофайл с новым идентификатором.
        Старый формат: {old_id}_{timestamp}.mp4
        Новый формат: {new_id}_{timestamp}.mp4

        :param file_path:  текущий путь к файлу
        :param new_task_id: новый идентификатор задачи
        :return:           новый путь, или None при ошибке
        """
        try:
            dirname = os.path.dirname(file_path)
            basename = os.path.basename(file_path)

            # Извлекаем timestamp из старого имени (после первого _)
            # old format: OLDID_20250101_143022.mp4
            if '_' in basename:
                timestamp_part = basename.split('_', 1)[1]  # "20250101_143022.mp4"
                safe_id = ''.join(c for c in new_task_id if c.isalnum() or c in '-_.')
                new_name = f"{safe_id}_{timestamp_part}"
            else:
                # Если timestamp не найден — просто заменяем имя
                safe_id = ''.join(c for c in new_task_id if c.isalnum() or c in '-_.')
                new_name = f"{safe_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

            new_path = os.path.join(dirname, new_name)

            if os.path.exists(file_path):
                os.rename(file_path, new_path)
                Logger.info(f"FileService: файл переименован {file_path} -> {new_path}")
                return new_path
            else:
                Logger.warning(f"FileService: файл не найден для переименования: {file_path}")
                return None

        except Exception as e:
            Logger.error(f"FileService: ошибка переименования: {e}")
            return None

    def get_free_space(self) -> int:
        """Возвращает свободное место на устройстве (байт)."""
        try:
            stat = os.statvfs(self._base_dir)
            return stat.f_frsize * stat.f_bavail
        except Exception:
            return -1

    def ensure_dir(self, path: str) -> bool:
        """Создаёт директорию, если её нет."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            Logger.error(f"FileService: не удалось создать {path}: {e}")
            return False
