"""
Главный класс приложения WmsVideoApp.

Поток:
  1. Intent от WMS → экран подтверждения (confirm)
  2. Пользователь нажимает "Начать съёмку" (с защитой от случайного нажатия)
  3. RecordScreen → системная камера
  4. После записи → диалог: "Использовать ID {X} или заменить через сканер?"
  5. Если сканер → QR → новый ID → повторная выгрузка с новым ID
  6. Выгрузка на SMB
  7. Удаление локальной копии
  8. Флаг на WMS
  9. DoneScreen

Пользователю доступно: начало съёмки, завершение, QR-сканирование ID.
Настройки — только по паролю администратора.
"""
import os
import sys
import json
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty

from app.config import AppConfig
from app.services.camera_service import CameraService
from app.services.network_service import NetworkService
from app.services.wms_service import WmsService
from app.services.file_service import FileService
from app.services.logger_service import LoggerService
from app.services.qr_service import QRService

from app.screens.confirm_screen import ConfirmScreen
from app.screens.record_screen import RecordScreen
from app.screens.upload_screen import UploadScreen
from app.screens.done_screen import DoneScreen
from app.screens.scan_screen import ScanScreen
from app.screens.settings_screen import SettingsScreen
from app.screens.splash_screen import SplashScreen


class WmsVideoApp(App):
    """Приложение для видеосъёмки по заданию из WMS."""

    # ── Свойства состояния ──
    current_task_id = StringProperty('')
    original_task_id = StringProperty('')
    current_video_path = StringProperty('')
    remote_video_path = StringProperty('')
    app_status = StringProperty('idle')  # idle | confirm | recording | uploading | done | scan | settings

    def __init__(self, task_id=None, **kwargs):
        super().__init__(**kwargs)
        self._task_id = task_id or ''

        # Конфиг
        self.config_data = AppConfig()

        # Сервисы
        self.camera = CameraService(self)
        self.network = NetworkService(self.config_data)
        self.wms = WmsService(self.config_data)
        self.file_mgr = FileService()
        self.logger = LoggerService(self.config_data)
        self.qr = QRService(self)

        # Screen manager
        self.sm = ScreenManager()
        self.sm.add_widget(SplashScreen(name='splash'))
        self.sm.add_widget(ConfirmScreen(name='confirm'))
        self.sm.add_widget(RecordScreen(name='record'))
        self.sm.add_widget(UploadScreen(name='upload'))
        self.sm.add_widget(DoneScreen(name='done'))
        self.sm.add_widget(ScanScreen(name='scan'))
        self.sm.add_widget(SettingsScreen(name='settings'))

    def build(self):
        """Kivy: построение UI."""
        self.title = 'WMS Video Capture'

        # Логируем запуск
        self.logger.info("APP", "Приложение запущено")

        # Проверяем Intent при старте
        self._setup_android_intent_handler()

        # Всегда показываем сплэш-экран
        self.sm.current = 'splash'

        if self._task_id:
            Logger.info(f"WmsApp: получен task_id из CLI: {self._task_id}")
            self.logger.info("APP", f"Получен task_id из CLI: {self._task_id}")
            Clock.schedule_once(lambda dt: self.show_task_confirmation(self._task_id), 0.5)

        return self.sm

    def show_confirm(self):
        """Переход на ConfirmScreen (после сплэша)."""
        self.sm.current = 'confirm'

    # ═════════════════════════════════════════════
    # ОБРАБОТКА INTENT ОТ WMS
    # ═════════════════════════════════════════════

    def _setup_android_intent_handler(self):
        """На Android: регистрируем обработчик Intent'ов."""
        try:
            from jnius import autoclass
            from android import activity, mActivity
            _ANDROID = True
        except ImportError:
            _ANDROID = False

        if not _ANDROID:
            return

        def handle_new_intent(intent):
            try:
                self._process_intent(intent)
            except Exception as e:
                Logger.error(f"WmsApp: ошибка Intent: {e}")

        activity.bind(on_new_intent=handle_new_intent)
        current_intent = mActivity.getIntent()
        if current_intent:
            self._process_intent(current_intent)

    def _process_intent(self, intent):
        """Извлекает task_id из Intent."""
        task_id = None
        try:
            extras = intent.getExtras()
            if extras:
                task_id = extras.getString('task_id')

            if not task_id:
                data_uri = intent.getData()
                if data_uri:
                    uri_str = str(data_uri.toString())
                    if 'task_id=' in uri_str:
                        task_id = uri_str.split('task_id=')[-1].split('&')[0]
                    elif '/task/' in uri_str:
                        task_id = uri_str.split('/task/')[-1].split('/')[0]
        except Exception as e:
            Logger.error(f"WmsApp: ошибка разбора Intent: {e}")

        if task_id:
            Logger.info(f"WmsApp: получен task_id из Intent: {task_id}")
            self.logger.info("APP", f"Получен task_id из Intent: {task_id}")
            Clock.schedule_once(lambda dt: self.show_task_confirmation(task_id), 0.3)

    # ═════════════════════════════════════════════
    # ЭКРАН ПОДТВЕРЖДЕНИЯ
    # ═════════════════════════════════════════════

    def show_task_confirmation(self, task_id: str):
        """
        Показывает экран подтверждения: "Получен ID заказа №ХХХ. Начать съёмку?"
        """
        self.current_task_id = task_id
        self.original_task_id = task_id
        self.app_status = 'confirm'
        self.sm.current = 'confirm'

        record_screen = self.sm.get_screen('record')
        if record_screen:
            record_screen.task_id = task_id

        self.logger.info("TASK", f"Показано подтверждение задачи {task_id}")

    # ═════════════════════════════════════════════
    # ЗАПУСК ЗАПИСИ
    # ═════════════════════════════════════════════

    def start_recording(self):
        """Пользователь подтвердил — запускаем камеру."""
        Logger.info(f"WmsApp: старт записи для {self.current_task_id}")
        self.logger.info("TASK", f"Старт записи {self.current_task_id}")

        self.app_status = 'recording'
        self.sm.current = 'record'

        # Запускаем камеру после отрисовки экрана
        Clock.schedule_once(lambda dt: self._begin_recording(), 0.5)

    def _begin_recording(self):
        """Запуск системной камеры."""
        try:
            self.camera.start_recording(self.current_task_id)
        except Exception as e:
            Logger.error(f"WmsApp: ошибка камеры: {e}")
            self.logger.error("CAMERA", f"Ошибка запуска: {e}")

    # ═════════════════════════════════════════════
    # ЗАВЕРШЕНИЕ ЗАПИСИ → ДИАЛОГ СМЕНЫ ID
    # ═════════════════════════════════════════════

    def on_recording_finished(self, video_uri: str, task_id: str = None):
        """
        Запись завершена. Сохраняем видео и показываем диалог:
        "Использовать ID {X} или заменить через сканер?"
        """
        task_id = task_id or self.current_task_id
        if not video_uri:
            Logger.error("WmsApp: URI видео пуст")
            self.logger.error("CAMERA", "Видео не получено от камеры")
            self.app_status = 'error'
            return

        Logger.info(f"WmsApp: запись завершена, URI={video_uri}")
        self.logger.info("TASK", f"Запись завершена, URI={video_uri}")

        # Сохраняем локально
        local_path = self.file_mgr.save_video(video_uri, task_id)
        if not local_path:
            Logger.error("WmsApp: не удалось сохранить видео")
            self.logger.error("FILE", "Не удалось сохранить видео локально")
            self.app_status = 'error'
            return

        self.current_video_path = local_path
        Logger.info(f"WmsApp: видео сохранено: {local_path}")

        # ── DoneScreen сам восстановит режим из app_status ──
        self.app_status = 'done'
        self.sm.current = 'done'
        self.logger.info("TASK", "Ожидание решения пользователя по ID")

    # ═════════════════════════════════════════════
    # QR-СКАНИРОВАНИЕ ИДЕНТИФИКАТОРА
    # ═════════════════════════════════════════════

    def on_scan_requested(self):
        """Пользователь выбрал 'Заменить ID через сканер'."""
        Logger.info("WmsApp: запрос QR-сканирования")
        self.logger.info("QR", "Запуск QR-сканера")
        self.app_status = 'scan'
        self.sm.current = 'scan'

        # Запускаем сканер
        Clock.schedule_once(lambda dt: self.qr.start_scan(), 0.5)

    def on_scanner_unavailable(self):
        """QR-сканер не найден на устройстве — показываем сообщение на ScanScreen."""
        Logger.warning("WmsApp: QR-сканер недоступен")
        self.logger.warning("QR", "QR-сканер не найден на устройстве")
        scan_screen = self.sm.get_screen('scan')
        if scan_screen:
            scan_screen.show_scanner_unavailable()

    def on_scan_result(self, scanned_id: str):
        """
        Результат QR-сканирования. Если ID получен — запускаем выгрузку с новым ID.
        """
        if not scanned_id:
            Logger.warning("WmsApp: QR-сканер не вернул ID")
            self.logger.warning("QR", "Сканирование не дало результата")
            # Возвращаем на done с исходным ID
            self.sm.current = 'done'
            return

        Logger.info(f"WmsApp: получен ID из QR: {scanned_id}")
        self.logger.info("QR", f"Получен ID из QR: {scanned_id}")

        # Меняем ID задачи
        self.current_task_id = scanned_id

        # Переименовываем локальный файл с новым ID
        original_path = self.current_video_path
        new_path = self.file_mgr.rename_with_id(original_path, scanned_id)
        if new_path:
            self.current_video_path = new_path
            Logger.info(f"WmsApp: файл переименован: {new_path}")

        # Запускаем выгрузку
        self.app_status = 'uploading'
        self.sm.current = 'upload'
        Clock.schedule_once(lambda dt: self._upload_video(self.current_video_path, scanned_id), 0.3)

    # ═════════════════════════════════════════════
    # РУЧНОЙ ВВОД ИДЕНТИФИКАТОРА
    # ═════════════════════════════════════════════

    def on_manual_id_entered(self, manual_id: str):
        """
        Пользователь ввёл ID вручную вместо сканирования.
        Переименовываем файл и запускаем выгрузку с новым ID.
        """
        if not manual_id or not manual_id.strip():
            Logger.warning("WmsApp: ручной ввод ID — пустая строка")
            return

        manual_id = manual_id.strip()
        Logger.info(f"WmsApp: ручной ввод ID: {manual_id}")
        self.logger.info("TASK", f"Ручной ввод ID: {manual_id}")

        # Меняем ID задачи
        self.current_task_id = manual_id

        # Переименовываем локальный файл с новым ID
        original_path = self.current_video_path
        new_path = self.file_mgr.rename_with_id(original_path, manual_id)
        if new_path:
            self.current_video_path = new_path
            Logger.info(f"WmsApp: файл переименован: {new_path}")

        # Запускаем выгрузку
        self.app_status = 'uploading'
        self.sm.current = 'upload'
        Clock.schedule_once(
            lambda dt: self._upload_video(self.current_video_path, manual_id), 0.3
        )

    # ═════════════════════════════════════════════
    # ВЫГРУЗКА
    # ═════════════════════════════════════════════

    def on_use_current_id(self):
        """Пользователь решил использовать текущий ID — сразу выгружаем."""
        self.logger.info("TASK", f"Использован ID: {self.current_task_id}")
        self.app_status = 'uploading'
        self.sm.current = 'upload'
        Clock.schedule_once(
            lambda dt: self._upload_video(self.current_video_path, self.current_task_id),
            0.3
        )

    def _upload_video(self, local_path: str, task_id: str):
        """
        Выгружает видео на SMB. Создаёт папку task_id.
        """
        Logger.info(f"WmsApp: начало выгрузки {local_path}")
        self.logger.info("UPLOAD", f"Начало выгрузки {local_path}")

        try:
            remote_path = self.network.upload_with_folder(
                local_path=local_path,
                task_id=task_id,
                filename=os.path.basename(local_path)
            )

            if remote_path:
                self.remote_video_path = remote_path
                Logger.info(f"WmsApp: выгружено: {remote_path}")
                self.logger.info("UPLOAD", f"Видео выгружено: {remote_path}")

                # Удаляем локальную копию
                if self.config_data.delete_local_after_upload:
                    self.file_mgr.delete_local(local_path)

                # Отправляем флаг на WMS
                self._send_wms_flag(task_id, remote_path)

                # Переключаем DoneScreen в режим "готово"
                done_screen = self.sm.get_screen('done')
                if done_screen:
                    done_screen.show_completed()
                self.app_status = 'done'
                self.sm.current = 'done'
                self.logger.info("TASK", f"Задача {task_id} завершена")

            else:
                Logger.error("WmsApp: ошибка выгрузки")
                self.logger.error("UPLOAD", "Ошибка выгрузки видео")
                self.app_status = 'error'
                done_screen = self.sm.get_screen('done')
                if done_screen:
                    done_screen.show_upload_error()

        except Exception as e:
            Logger.error(f"WmsApp: исключение выгрузки: {e}")
            self.logger.error("UPLOAD", f"Исключение: {e}")
            self.app_status = 'error'

    def _send_wms_flag(self, task_id: str, remote_path: str):
        """Флаг на WMS."""
        Logger.info(f"WmsApp: отправка флага на WMS {task_id}")
        try:
            success = self.wms.send_flag(task_id, remote_path)
            if success:
                self.logger.info("WMS", f"Флаг отправлен для {task_id}")
            else:
                self.logger.warning("WMS", f"Не удалось отправить флаг {task_id}")
        except Exception as e:
            self.logger.error("WMS", f"Ошибка флага: {e}")

    # ═════════════════════════════════════════════
    # НАСТРОЙКИ (ПО ПАРОЛЮ)
    # ═════════════════════════════════════════════

    def open_settings(self):
        """Открыть экран настроек (с паролем)."""
        self.sm.current = 'settings'

    # ═════════════════════════════════════════════
    # ЗАВЕРШЕНИЕ
    # ═════════════════════════════════════════════

    def on_request_close(self):
        """Закрытие приложения."""
        self.logger.info("APP", "Приложение закрыто")
        try:
            from jnius import autoclass
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            mActivity.finish()
        except Exception:
            self.stop()
