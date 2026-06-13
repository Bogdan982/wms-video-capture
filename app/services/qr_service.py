"""
Сервис QR-сканирования.

Использует Intent к установленному ZXing Barcode Scanner
(com.google.zxing.client.android.SCAN).

Если ZXing не установлен — предлагает установить или использует
альтернативные методы (mlkit / встроенный сканер через камеру).

Результат возвращается через коллбэк app.on_scan_result(scanned_text).
"""
from kivy.logger import Logger

try:
    from jnius import autoclass, cast, JavaException
    from android import activity, mActivity
    from android.runnable import run_on_ui_thread

    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    Activity = autoclass('android.app.Activity')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    PackageManager = autoclass('android.content.pm.PackageManager')

    _ANDROID = True
except ImportError:
    _ANDROID = False
    Logger.warning("QRService: Android API недоступен (десктопный режим)")


# Код запроса для QR-сканирования
SCAN_REQUEST_CODE = 2001

# Пакет ZXing Barcode Scanner
ZXING_PACKAGE = 'com.google.zxing.client.android'
SCAN_ACTION = f'{ZXING_PACKAGE}.SCAN'
SCAN_MARKET_URI = 'market://details?id=com.google.zxing.client.android'


class QRService:
    """
    Сервис QR-сканирования через Intent ZXing.
    """

    def __init__(self, app):
        """
        :param app: экземпляр WmsVideoApp (для коллбэка on_scan_result)
        """
        self._app = app
        self._scanning = False

    def is_zxing_installed(self) -> bool:
        """Проверяет, установлен ли ZXing Barcode Scanner."""
        if not _ANDROID:
            return False

        try:
            pm = PythonActivity.mActivity.getPackageManager()
            pm.getPackageInfo(ZXING_PACKAGE, 0)
            return True
        except Exception:
            return False

    def start_scan(self):
        """
        Запускает QR-сканер (ZXing Intent).
        Если не установлен — показывает инструкцию.
        """
        self._scanning = True

        if not _ANDROID:
            Logger.info("QRService: [ЭМУЛЯЦИЯ] сканирование..."
                        "(возвращаю тестовый ID через 2 сек)")
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self._emulate_scan(), 2.0)
            return

        if self.is_zxing_installed():
            self._launch_zxing()
        else:
            Logger.warning("QRService: ZXing Barcode Scanner не найден")
            self._handle_no_scanner()

    def _launch_zxing(self):
        """Запускает ZXing Barcode Scanner."""
        try:
            intent = Intent(SCAN_ACTION)
            intent.setPackage(ZXING_PACKAGE)

            # Настройки сканирования
            intent.putExtra('SCAN_MODE', 'QR_CODE_MODE')  # Только QR
            intent.putExtra('SCAN_FORMATS', 'QR_CODE')
            intent.putExtra('PROMPT_MESSAGE', 'Наведите камеру на QR-код заказа')
            intent.putExtra('RESULT_DISPLAY_DURATION_MS', 0)  # Не показывать результат
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)

            PythonActivity.mActivity.startActivityForResult(
                intent, SCAN_REQUEST_CODE
            )

            Logger.info("QRService: ZXing запущен")
        except Exception as e:
            Logger.error(f"QRService: ошибка запуска ZXing: {e}")
            self._handle_no_scanner()

    def _handle_no_scanner(self):
        """Если ZXing не установлен — пробуем альтернативы."""
        Logger.info("QRService: ZXing не найден, пробуем Barcode Scanner+...")

        # Пробуем Google GMS Barcode Scanner (ML Kit)
        try:
            intent = Intent('com.google.android.gms.vision.SCAN')
            intent.putExtra('SCAN_MODE', 'QR_CODE_MODE')
            PythonActivity.mActivity.startActivityForResult(
                intent, SCAN_REQUEST_CODE
            )
            Logger.info("QRService: Google ML Kit сканер запущен")
            return
        except Exception:
            pass

        # Ничего не установлено — сообщаем пользователю
        Logger.error("QRService: ни один QR-сканер не найден")
        self._scanning = False

        # Коллбэк с None (пользователь не сканировал)
        if self._app:
            from kivy.clock import Clock
            Clock.schedule_once(
                lambda dt: self._app.on_scan_result(None), 0.3
            )

    def on_activity_result(self, request_code: int, result_code: int, data):
        """
        Обработчик результата от QR-сканера.
        Регистрируется в main.py/Android onActivityResult.
        """
        if request_code != SCAN_REQUEST_CODE:
            return

        self._scanning = False

        if result_code == Activity.RESULT_OK and data:
            # ZXing возвращает результат в extra 'SCAN_RESULT'
            scanned_text = data.getStringExtra('SCAN_RESULT')

            if scanned_text:
                scanned_text = scanned_text.strip()
                Logger.info(f"QRService: отсканировано: {scanned_text}")
                if self._app:
                    self._app.on_scan_result(scanned_text)
                return

        # Отмена или ошибка
        if result_code == Activity.RESULT_CANCELED:
            Logger.info("QRService: сканирование отменено")
        else:
            Logger.warning(f"QRService: ошибка сканирования, code={result_code}")

        # Ничего не отсканировано — возвращаем None
        if self._app:
            from kivy.clock import Clock
            Clock.schedule_once(
                lambda dt: self._app.on_scan_result(None), 0.3
            )

    def _emulate_scan(self):
        """Эмуляция QR-сканирования для десктопа."""
        Logger.info("QRService: [ЭМУЛЯЦИЯ] возвращаю тестовый ID")
        self._scanning = False
        if self._app:
            self._app.on_scan_result(f"QR-{int(__import__('time').time())}")

    @property
    def is_scanning(self) -> bool:
        return self._scanning
