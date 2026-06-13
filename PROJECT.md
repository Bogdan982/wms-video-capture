# WMS Video Capture — Android Application

## Полное описание проекта

**Версия:** 1.0.0  
**Платформа:** Android (minSdk 21, targetSdk 34)  
**Язык:** Python + Kivy  
**Сборка:** Buildozer (через Docker Desktop или WSL 2)  
**Репозиторий:** `C:\Users\Roman\kivy-video-capture\`

---

## 1. Назначение

Мобильное приложение для видеосъёмки объектов по команде из WMS-системы предприятия. Основная задача — оператор получает идентификатор заказа, снимает видео штатной камерой устройства, и файл автоматически попадает в сетевое хранилище предприятия (SMB/CIFS) с уведомлением WMS.

---

## 2. Поток работы (User Flow)

```
┌─────────────────────────────────────────────────────────┐
│  1. WMS отправляет Intent с task_id                    │
│     (wmscapture://task/ABC-123)                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  2. ConfirmScreen                                       │
│     "Получен идентификатор заказа №ABC-123"            │
│     "Начать съёмку?"                                    │
│     [████████░░] УДЕРЖИВАЙТЕ 2 СЕК                      │
└─────────────────────────────────────────────────────────┘
                          │ (удержание 2 сек)
                          ▼
┌─────────────────────────────────────────────────────────┐
│  3. RecordScreen                                        │
│     🔴 ЗАПИСЬ                                           │
│     Заказ №ABC-123                                      │
│     047 сек                                              │
│     [■ ЗАВЕРШИТЬ СЪЁМКУ]                                 │
└─────────────────────────────────────────────────────────┘
                          │ (пользователь завершает съёмку)
                          ▼
┌─────────────────────────────────────────────────────────┐
│  4. DoneScreen (диалог выбора ID)                       │
│     🎥 Видео записано                                   │
│     "Использовать ABC-123, сканировать QR или ввести вручную?"   │
│     [✅ Использовать]  [📷 QR]  [✏ Ввести]                    │
└─────────────────────────────────────────────────────────┘
         │                   │                    │
         ▼                   ▼                    ▼
┌──────────────────┐  ┌──────────────┐  ┌───────────────┐
│  5a. UploadScreen│  │ 5b. ScanScrn │  │ 5c. ManualId  │
│  Выгрузка... 67% │  │ 📷 QR-код   │  │ ✏ Ввод ID    │
│  [████████░░░]   │  │ → XYZ-789   │  │ → вручную    │
└──────────────────┘  └──────┬───────┘  └───────┬───────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│  6. SMB-выгрузка                                        │
│     \\server\video_archive\captures\{ID}\{ID}_timestamp.mp4 │
│     ✔ создана папка /captures/{ID}/                     │
│     ✔ файл скопирован                                   │
│     ✔ проверка размела                                  │
└──────────────────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│  7. 🗑 Удаление локальной копии                         │
│     ✔ /storage/.../WMSCapture/{ID}_*.mp4 удалён         │
└──────────────────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│  8. HTTP POST → WMS (файл-флаг)                         │
│     {"event":"video_capture_completed",                 │
│      "task_id":"ABC-123",                               │
│      "data":{"video_path":"\\\\server\\...\\video.mp4", │
│              "status":"uploaded"}}                      │
└──────────────────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│  9. DoneScreen (результат)                              │
│     ✅ Задача выполнена                                  │
│     [📋 Ожидать новую задачу]  [✕ Закрыть]             │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Архитектура приложения

### 3.1. Структура файлов

```
kivy-video-capture/
│
├── main.py                          # Точка входа
│   └── Парсинг task_id из CLI/Intent
│   └── Регистрация ActivityResult диспетчера (камера + QR)
│
├── buildozer.spec                   # Конфигурация сборки APK
│   └── Зависимости: python3,kivy==2.3.1,pyjnius,pysmb,requests,android
│   └── Разрешения: CAMERA,RECORD_AUDIO,INTERNET,FOREGROUND_SERVICE
│   └── Кастомный AndroidManifest
│
├── app/
│   ├── app.py                       # Главный класс приложения
│   │   └── WmsVideoApp
│   │   └── Управление состоянием и экранами
│   │   └── Обработка Intent'ов от WMS
│   │   └── Оркестрация сервисов
│   │
│   ├── config.py                    # Конфигурация приложения
│   │   └── AppConfig
│   │   └── Чтение/запись JSON в ANDROID_PRIVATE
│   │   └── SMB/WMS/лог/видео-параметры
│   │   └── SHA-256 хэш пароля администратора
│   │   └── verify_admin_password()
│   │
│   ├── screens/
│   │   ├── confirm_screen.py        # Экран подтверждения задачи
│   │   │   └── Уведомление об ID
│   │   │   └── Кнопка с защитой от случайного нажатия
│   │   │   └── Удержание 2 сек → активация
│   │   │   └── Доступ к настройкам
│   │   │
│   │   ├── record_screen.py         # Экран записи видео
│   │   │   └── Счётчик времени записи
│   │   │   └── Кнопка "Завершить съёмку"
│   │   │
│   │   ├── upload_screen.py         # Экран выгрузки
│   │   │   └── Прогресс-бар
│   │   │   └── Кнопка "Повторить" при ошибке
│   │   │
│   │   ├── done_screen.py           # Экран завершения
│   │   │   └── Режимы: id_change / completed / error
│   │   │   └── Диалог выбора ID или QR-сканирования
│   │   │   └── Информация о результате
│   │   │
│   │   ├── scan_screen.py           # Экран QR-сканирования
│   │   │   └── Инструкция для пользователя
│   │   │   └── Отображение отсканированного ID
│   │   │   └── Кнопки "Повторить" / "Назад"
│   │   │
│   │   └── settings_screen.py       # Экран настроек
│   │       └── Ввод пароля администратора
│   │       └── Редактирование SMB/WMS/лог-параметров
│   │       └── Смена пароля
│   │
│   └── services/
│       ├── camera_service.py        # Сервис камеры
│       │   └── Запуск MediaStore.ACTION_VIDEO_CAPTURE
│       │   └── FileProvider для URI
│       │   └── on_activity_result → коллбэк
│       │   └── Десктопная эмуляция записи
│       │
│       ├── file_service.py          # Сервис файлов
│       │   └── Копирование content:// URI → локальный файл
│       │   └── Генерация имени: {ID}_{timestamp}.mp4
│       │   └── rename_with_id() для QR-замены
│       │   └── delete_local()
│       │
│       ├── network_service.py       # Сервис сети (SMB)
│       │   └── pysmb SMBConnection
│       │   └── Создание папки /captures/{ID}/
│       │   └── Копирование файла
│       │   └── Проверка размера после копирования
│       │   └── Retry-логика (3 попытки)
│       │
│       ├── wms_service.py           # Сервис WMS
│       │   └── HTTP POST JSON-флага
│       │   └── Retry-логика
│       │   └── Локальное сохранение при недоступности WMS
│       │
│       ├── logger_service.py        # Сервис логирования
│       │   └── Запись в локальный файл
│       │   └── Ротация при 512 КБ
│       │   └── Автовыгрузка на SMB каждые 30 мин
│       │   └── Формат: timestamp | LEVEL | COMPONENT | message
│       │
│       ├── qr_service.py            # Сервис QR-сканирования
│       │   └── Intent к ZXing Barcode Scanner
│       │   └── Fallback на Google ML Kit
│       │   └── on_activity_result → коллбэк
│       │
│       └── upload_service.py        # Foreground Service
│           └── Android foreground service
│           └── Уведомление о процессе выгрузки
│           └── Канал уведомлений (Android 8+)
│
├── assets/
│   ├── AndroidManifest.xml          # Кастомный манифест
│   │   └── Intent-filter: wmscapture://task/*
│   │   └── FileProvider (androidx)
│   │   └── Foreground Service
│   │   └── Разрешения: камера, аудио, интернет, storage
│   │
│   ├── config.default.json          # Пример конфигурации
│   │
│   └── file_paths.xml               # FileProvider пути
│
└── res/xml/
    └── file_paths.xml               # Ресурсы APK
```

### 3.2. Диаграмма классов

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WmsVideoApp                                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Properties: current_task_id, current_video_path,              │  │
│  │             remote_video_path, app_status                     │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ Services:                                                     │  │
│  │   config_data: AppConfig                                      │  │
│  │   camera:     CameraService                                   │  │
│  │   network:    NetworkService                                  │  │
│  │   wms:        WmsService                                      │  │
│  │   file_mgr:   FileService                                     │  │
│  │   logger:     LoggerService                                   │  │
│  │   qr:         QRService                                       │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ Screens (ScreenManager):                                      │  │
│  │   confirm, record, upload, done, scan, settings               │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ Methods:                                                      │  │
│  │   show_task_confirmation(id) → confirm_screen                 │  │
│  │   start_recording() → camera.start_recording()                │  │
│  │   on_recording_finished(uri) → done_screen (dialog)           │  │
│  │   on_use_current_id() → upload                                │  │
│  │   on_scan_requested() → scan_screen                           │  │
│  │   on_scan_result(id) → upload with new ID                     │  │
│  │   _upload_video(path, id) → SMB + flag                       │  │
│  │   open_settings() → settings_screen (with password)           │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

  Сервисы:
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ CameraService │  │NetworkService│  │  WmsService  │  │  FileService  │
  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤
  │start_recording│  │upload_with_   │  │ send_flag()  │  │ save_video()  │
  │on_activity_   │  │  folder()    │  │ health_check()│  │ delete_local()│
  │  result()    │  │check_         │  │ _save_flag_  │  │ rename_with_  │
  │is_recording  │  │ connectivity()│  │  locally()   │  │  id()        │
  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘

  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ LoggerService │  │  QRService   │  │ AppConfig    │
  ├──────────────┤  ├──────────────┤  ├──────────────┤
  │ info/error()  │  │ start_scan() │  │ smb_*        │
  │ _upload_now() │  │ is_zxing_    │  │ wms_*        │
  │ _rotate()    │  │  installed()│  │ log_*        │
  │ shutdown()   │  │ on_activity_ │  │ admin_       │
  │              │  │  result()   │  │  password_*  │
  └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 4. Компоненты подробно

### 4.1. main.py — точка входа

**Назначение:** Парсинг аргументов, запуск Kivy-приложения, регистрация диспетчера Android ActivityResult.

```python
# Извлечение task_id из sys.argv
# Регистрация on_activity_result для камеры (code=1001) и QR (code=2001)
# Запуск WmsVideoApp(task_id)
```

ActivityResult диспетчер маршрутизирует:
- `request_code == 1001` → `camera_service.on_activity_result()`
- `request_code == 2001` → `qr_service.on_activity_result()`

### 4.2. app.py — WmsVideoApp

**Главный класс приложения.** Содержит:

| Свойство | Тип | Назначение |
|----------|-----|------------|
| `current_task_id` | StringProperty | Текущий ID заказа |
| `original_task_id` | StringProperty | Исходный ID (до QR-замены) |
| `current_video_path` | StringProperty | Путь к локальному видео |
| `remote_video_path` | StringProperty | UNC-путь на сервере |
| `app_status` | StringProperty | idle/confirm/recording/uploading/done/scan |

**Методы:**

| Метод | Вызывается | Действие |
|-------|-----------|----------|
| `show_task_confirmation(id)` | Intent handler | Показать ConfirmScreen |
| `start_recording()` | ConfirmScreen (удержание) | Запуск камеры |
| `on_recording_finished(uri)` | CameraService | Сохранить, показать DoneScreen диалог |
| `on_use_current_id()` | DoneScreen (кнопка) | Запустить выгрузку |
| `on_scan_requested()` | DoneScreen (QR) | Открыть ScanScreen |
| `on_scan_result(id)` | QRService | Переименовать, выгрузить с новым ID |
| `_upload_video(path, id)` | Внутренний | SMB + флаг + удаление |
| `open_settings()` | ConfirmScreen | SettingsScreen (с паролем) |

### 4.3. config.py — AppConfig

**Настройки приложения.** Хранятся в JSON-файле (`ANDROID_PRIVATE/config.json`).

**Группы настроек:**

```
WMS:
  wms_base_url        - http://192.168.1.100:8080/wms
  wms_flag_endpoint   - .../api/v1/tasks/flag

SMB (видео):
  smb_host              - 192.168.1.200
  smb_share             - video_archive
  smb_username          - WORKGROUP\wms_user
  smb_password          - (пустой)
  smb_root_folder       - captures

Логирование:
  log_enabled           - true
  log_smb_host          - (тот же хост)
  log_smb_share         - logs
  log_smb_folder        - wms_capture
  log_max_size_kb       - 512
  log_upload_interval_min - 30

Безопасность:
  admin_password_hash   - SHA-256 хэш (по умолчанию "admin")

Видео:
  video_max_duration_sec - 300 (5 минут)
  video_quality          - 1 (high)

Retry:
  retry_attempts         - 3
  retry_delay_sec        - 5
```

**Методы:**
- `verify_admin_password(plain)` — проверка хэша
- `set_admin_password(plain)` — обновление хэша + save()
- `get(key, default)` / `set(key, value)` — произвольные параметры

### 4.4. confirm_screen.py — экран подтверждения

**Защита от случайного нажатия:**
- Кнопка заблокирована (`disabled=True`, alpha=0.5)
- Пользователь удерживает кнопку **2 секунды**
- ProgressBar заполняется анимацией `Animation(duration=2.0)`
- При отпускании до завершения — сброс, сообщение «Отпущено слишком рано»
- После полного удержания: `button_text = '▶ СТАРТ'`, `disabled=False`
- Автоматический запуск записи после удержания

### 4.5. done_screen.py — экран завершения

Полиморфный экран с **3 режимами**:

| Режим | Иконка | Описание | Кнопки |
|-------|--------|----------|--------|
| `id_change` | 🎥 | «Видео записано. Выберите ID» | [Текущий ID] [QR] [✏ Ввести] |
| `completed` | ✅ | «Задача выполнена» | [Ожидать] [Закрыть] |
| `error` | ❌ | «Ошибка выгрузки» | [Повторить] [Ожидать] |

**Дополнительно:** `ManualIdPopup` — модальное окно с TextInput для ввода ID вручную. Вызывается из `id_change` при нажатии кнопки «✏ Ввести вручную».

| Элемент Popup | Описание |
|---------------|----------|
| TextInput | Поле ввода ID (авто-фокус, поддержка Enter) |
| [Отмена] | Закрывает popup без изменений |
| [✅ Подтвердить] | Проверяет ввод → передаёт ID в `app.on_manual_id_entered()` |

### 4.6. camera_service.py — сервис камеры

**Android:**
1. Создаёт `Intent(MediaStore.ACTION_VIDEO_CAPTURE)`
2. Передаёт `EXTRA_DURATION_LIMIT` (из config)
3. Передаёт `EXTRA_VIDEO_QUALITY`
4. Для Android 7+ создаёт URI через FileProvider
5. Запускает `startActivityForResult(code=1001)`
6. Результат: `on_activity_result()` → `app.on_recording_finished(uri)`

**Десктоп (эмуляция):**
- Ждёт 3 секунды, возвращает `/tmp/{ID}_{timestamp}.mp4`

### 4.7. file_service.py — сервис файлов

| Метод | Описание |
|-------|----------|
| `save_video(uri, task_id)` | Копирует content:// URI в локальное хранилище |
| `generate_filename(task_id)` | `{safe_id}_{YYYYMMDD_HHMMSS}.mp4` |
| `delete_local(path)` | Удаление после выгрузки |
| `rename_with_id(path, new_id)` | Переименование при смене ID через QR |

**Хранилище:** На Android — `Environment.DIRECTORY_MOVIES/WMSCapture/`.
На десктопе — `~/WMSCapture/`.

**Копирование content:// URI:**
1. `ContentResolver.openInputStream(uri)`
2. Чтение буферами по 8 КБ
3. Запись в локальный файл

### 4.8. network_service.py — SMB-выгрузка

**Протокол:** SMB/CIFS через `pysmb.SMBConnection`

**Алгоритм:**
1. Подключение к `smb_host:445`
2. Создание папки `/{smb_root_folder}/{task_id}/` (если нет)
3. Копирование файла
4. Проверка: `listPath` → поиск имени файла → проверка размера
5. Возврат UNC-пути: `\\\\{host}\\{share}\\{root}\\{id}\\{file}`

**Retry:** до 3 попыток с задержкой 5 секунд.

### 4.9. wms_service.py — сервис WMS

**Формат флага (JSON):**
```json
{
  "event": "video_capture_completed",
  "task_id": "ABC-123",
  "timestamp": "2026-06-12T14:30:22",
  "data": {
    "video_path": "\\\\server\\video_archive\\captures\\ABC-123\\ABC-123_20260612_143022.mp4",
    "storage_type": "smb",
    "status": "uploaded",
    "device_id": "..."
  }
}
```

**Поведение при недоступности WMS:**
- Локальное сохранение в `pending_flags/flag_{task_id}_{timestamp}.json`
- Повторная отправка при следующем запуске

### 4.10. logger_service.py — сервис логирования

**Формат записи:**
```
2026-06-12 14:30:22.123 | INFO | CAMERA   | Запись начата
2026-06-12 14:30:22.456 | INFO | UPLOAD   | Выгрузка /captures/ABC-123/video.mp4
2026-06-12 14:30:25.789 | ERROR | UPLOAD   | Ошибка: Connection refused
```

**Компоненты:** `APP`, `TASK`, `CAMERA`, `FILE`, `UPLOAD`, `WMS`, `QR`, `LOG`

**Уровни:** DEBUG, INFO, WARN, ERROR

**Автовыгрузка:**
- Локальный файл: `{log_dir}/capture_{YYYYMMDD}_{device_id[:8]}.log`
- SMB: `//{log_smb_share}/{log_smb_folder}/{YYYYMMDD}/capture_{...}.log`
- Интервал: `log_upload_interval_min` (по умолчанию 30 мин)
- Ротация при `log_max_size_kb` (512 КБ) → переименование + выгрузка

### 4.11. qr_service.py — сервис QR-сканирования

**Приоритет:**
1. **ZXing Barcode Scanner** — Intent `com.google.zxing.client.android.SCAN`
2. **Google ML Kit** — Intent `com.google.android.gms.vision.SCAN`
3. **Ничего не найдено** → коллбэк с `None`

**Результат:** `data.getStringExtra('SCAN_RESULT')` → `app.on_scan_result(text)`

### 4.12. settings_screen.py — настройки

**Аутентификация:**
- TextInput (password mode) + кнопка «Войти»
- Проверка: `AppConfig.verify_admin_password()`
- Визуальная обратная связь (зелёный/красный)

**Панель настроек** (после входа):
- SMB: хост, шара, пользователь, пароль
- WMS: базовый URL
- Логи: SMB хост, SMB шара
- Смена пароля администратора

Изменения применяются мгновенно (каждое поле → `config.set()`)

---

## 5. Android-интеграция

### 5.1. Intent Filter (AndroidManifest.xml)

```xml
<!-- Запуск по схеме wmscapture://task/{ID} -->
<intent-filter>
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="wmscapture"
          android:host="*"
          android:pathPrefix="/task/" />
</intent-filter>
```

**Вызов из WMS:**
```java
// Android (Java/Kotlin):
Intent intent = new Intent(Intent.ACTION_VIEW);
intent.setData(Uri.parse("wmscapture://task/ABC-123"));
startActivity(intent);

// С extra:
Intent intent = new Intent();
intent.setClassName("org.enterprise.wms.videocapture",
                     "org.kivy.android.PythonActivity");
intent.putExtra("task_id", "ABC-123");
startActivity(intent);
```

### 5.2. FileProvider

Для передачи URI системной камере на Android 7+:

```xml
<provider
    android:name="androidx.core.content.FileProvider"
    android:authorities="${applicationId}.fileprovider"
    android:exported="false"
    android:grantUriPermissions="true">
    <meta-data android:name="android.support.FILE_PROVIDER_PATHS"
               android:resource="@xml/file_paths" />
</provider>
```

Пути:
- `cache-path videos/` — временные видео
- `external-files-path WMSCapture/` — постоянное хранилище
- `external-path Movies/WMSCapture/` — публичные видео

### 5.3. Разрешения (AndroidManifest.xml)

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"
    android:maxSdkVersion="28" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"
    android:maxSdkVersion="32" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

---

## 6. Конфигурация

### 6.1. Файл config.json

Автоматически создаётся при первом запуске в `ANDROID_PRIVATE/config.json`.

Полный пример: `assets/config.default.json`

```json
{
    "wms_base_url": "http://192.168.1.100:8080/wms",
    "wms_flag_endpoint": "http://192.168.1.100:8080/wms/api/v1/tasks/flag",

    "smb_host": "192.168.1.200",
    "smb_share": "video_archive",
    "smb_username": "WORKGROUP\\wms_user",
    "smb_password": "",
    "smb_root_folder": "captures",

    "log_enabled": true,
    "log_smb_host": "192.168.1.200",
    "log_smb_share": "logs",
    "log_smb_folder": "wms_capture",
    "log_smb_username": "WORKGROUP\\wms_user",
    "log_smb_password": "",
    "log_max_size_kb": 512,
    "log_upload_interval_min": 30,

    "admin_password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",

    "video_max_duration_sec": 300,
    "video_quality": 1,
    "delete_local_after_upload": true,
    "retry_attempts": 3,
    "retry_delay_sec": 5,
    "qr_timeout_sec": 60
}
```

### 6.2. Пароль администратора

По умолчанию: **admin**

Хэш SHA-256: `240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9`

Для генерации нового хэша:
```python
import hashlib
print(hashlib.sha256(b'новый_пароль').hexdigest())
```

---

## 7. Сборка и развёртывание

### 7.1. Требования к среде

| Компонент | Версия | Примечание |
|-----------|--------|------------|
| Python | 3.11.x | Установлен |
| Kivy | ≥ 2.2.0 | pip install kivy |
| Buildozer | latest | pip install buildozer |
| Docker Desktop | 4.77 + | Для сборки APK |
| WSL 2 | Ubuntu | Для Docker backend |

### 7.2. Сборка APK

```bash
# 1. Перейти в проект
cd C:\Users\Roman\kivy-video-capture

# 2. Собрать APK (Docker)
docker run -v "%cd%":/app kivy/buildozer:latest buildozer android debug

# Или (WSL 2):
cd /mnt/c/Users/Roman/kivy-video-capture
buildozer android debug

# 3. Результат
ls bin/*.apk
```

### 7.3. Установка на устройство

1. Скопировать APK на устройство (USB, email, облако)
2. Включить «Установка из неизвестных источников»
3. Открыть APK → Установить

### 7.4. Первый запуск

1. Приложение создаст `config.json` с настройками по умолчанию
2. Через экран настроек (пароль: `admin`) ввести реальные параметры:
   - IP SMB-сервера и учётные данные
   - URL WMS-сервера
   - Параметры логирования
3. При необходимости сменить пароль администратора

### 7.5. Установка QR-сканера (ZXing)

Для работы QR-сканирования требуется установить **ZXing Barcode Scanner**:
- Google Play: https://play.google.com/store/apps/details?id=com.google.zxing.client.android
- F-Droid: https://f-droid.org/packages/com.google.zxing.client.android/

Без него кнопка «Сканировать QR» будет неактивна (покажет сообщение об установке).

---

## 8. Сетевые требования

### 8.1. SMB/CIFS (сетевой ресурс)

- **Протокол:** SMB 2.0+ (NT LAN Manager v2)
- **Порт:** TCP 445
- **Требования к серверу:**
  - Расшаренная папка (share) с доступом на запись
  - Пользователь с правами: create directory, write file, list directory
- **Именование папок на сервере:**
  ```
  \\SERVER\video_archive\captures\
  \\SERVER\video_archive\captures\ABC-123\
  \\SERVER\video_archive\captures\ABC-123\ABC-123_20260612_143022.mp4
  ```
- **Структура папок:**
  ```
  captures/
  ├── ABC-123/
  │   └── ABC-123_20260612_143022.mp4
  ├── DEF-456/
  │   └── DEF-456_20260612_150010.mp4
  └── ...
  ```

### 8.2. Логи (отдельная SMB-шара)

```
\\SERVER\logs\
└── wms_capture\
    ├── 20260612\
    │   ├── capture_20260612_deviceid1.log
    │   └── capture_20260612_deviceid2.log
    └── 20260613\
        └── capture_20260613_deviceid1.log
```

### 8.3. WMS (HTTP)

- **Протокол:** HTTP 1.1 (REST)
- **Таймаут:** 15 сек (первая попытка), 30 сек (повторы)
- **Эндпоинт:** `POST {wms_base_url}/api/v1/tasks/flag`
- **Content-Type:** `application/json`
- **Успех:** HTTP 200–299
- **Повторы:** 3 попытки с задержкой 5 сек

---

## 9. Обработка ошибок и исключительные ситуации

| Ситуация | Поведение |
|----------|-----------|
| WMS отправил пустой ID | ConfirmScreen не показывается, приложение ждёт |
| Камера отменена пользователем | Коллбэк с `None`, возврат на ConfirmScreen |
| Не удалось сохранить видео локально | Ошибка, переход на ConfirmScreen |
| Нет места на устройстве | `FileService.get_free_space()` → проверка перед записью |
| SMB-сервер недоступен | 3 попытки → DoneScreen (режим error) |
| WMS-сервер не отвечает | 3 попытки → локальное сохранение флага |
| QR-сканер не установлен | Fallback на Google ML Kit → сообщение пользователю |
| Лог-файл слишком большой | Автоматическая ротация + выгрузка |

---

## 10. Тестирование

### 10.1. Десктопная эмуляция

На десктопе (Windows/git-bash):
```bash
python main.py --task_id=TEST-001
```

Эмулируются:
- Запись видео (3 сек задержки)
- SMB-выгрузка (логирование, без реальной передачи)
- QR-сканирование (возврат тестового ID)

### 10.2. Тестовые сценарии

1. **Получение задачи:** WMS → Intent `wmscapture://task/TEST-001` → ConfirmScreen
2. **Подтверждение:** Удержание 2 сек → RecordScreen
3. **Запись:** Системная камера → запись → завершение
4. **Диалог ID:** DoneScreen → [Использовать TEST-001] или [QR]
5. **Выгрузка:** ProgressBar → SMB → удаление → флаг
6. **QR-замена:** [QR] → ZXing → новый ID → выгрузка с новым ID
7. **Ошибка SMB:** Отключить сервер → DoneScreen → [Повторить]
8. **Настройки:** ConfirmScreen → [⚙] → пароль → изменение параметров

---

## 11. Разработка и расширение

### 11.1. Добавление нового экрана

1. Создать `app/screens/new_screen.py`
2. Добавить в `app/app.py`: `from app.screens.new_screen import NewScreen`
3. Зарегистрировать: `self.sm.add_widget(NewScreen(name='new'))`
4. Переключение: `self.sm.current = 'new'`

### 11.2. Добавление нового сервиса

1. Создать `app/services/new_service.py`
2. Добавить в `app/app.py` как свойство класса
3. Использовать в экранах через `app = self._get_app()`

### 11.3. Добавление параметра в конфиг

1. Добавить `@property` в `app/config.py`
2. Добавить значение по умолчанию в `_data.get('key', default)`
3. Добавить поле в `settings_screen.py`
4. Обновить `assets/config.default.json`

---

## 12. Структура логов

### 12.1. Локальный лог-файл

**Путь:** `ANDROID_PRIVATE/logs/capture_{YYYYMMDD}_{device_id[:8]}.log`

**Пример:**
```
2026-06-12 14:30:22.123 | INFO  | APP      | Приложение запущено
2026-06-12 14:30:22.456 | INFO  | APP      | Получен task_id из Intent: ABC-123
2026-06-12 14:30:22.789 | INFO  | TASK     | Показано подтверждение задачи ABC-123
2026-06-12 14:30:25.012 | INFO  | TASK     | Старт записи ABC-123
2026-06-12 14:31:30.456 | INFO  | CAMERA   | Запись завершена, URI=content://media/...
2026-06-12 14:31:31.000 | INFO  | FILE     | Скопировано 52428800 байт -> /WMSCapture/ABC-123_20260612_143130.mp4
2026-06-12 14:31:32.111 | INFO  | TASK     | Ожидание решения пользователя по ID
2026-06-12 14:31:35.222 | INFO  | TASK     | Использован ID: ABC-123
2026-06-12 14:31:35.333 | INFO  | UPLOAD   | Начало выгрузки /WMSCapture/ABC-123_20260612_143130.mp4
2026-06-12 14:31:36.444 | INFO  | UPLOAD   | Видео выгружено: \\\\server\\video_archive\\captures\\ABC-123\\ABC-123_20260612_143130.mp4
2026-06-12 14:31:37.555 | INFO  | WMS      | Флаг отправлен для ABC-123
2026-06-12 14:31:37.666 | INFO  | TASK     | Задача ABC-123 завершена
2026-06-12 14:31:38.000 | INFO  | LOG      | Сервис логирования запущен
```

### 12.2. Лог на SMB-сервере

**Путь:** `//{log_smb_share}/{log_smb_folder}/{YYYYMMDD}/capture_{YYYYMMDD}_{device_id[:8]}.log`

Автоматическая выгрузка каждые 30 минут или по достижении 512 КБ.

---

## 13. Диаграмма состояний (State Machine)

```
                    ┌──────────────┐
                    │    IDLE      │
                    │ (при запуске)│
                    └──────┬───────┘
                           │ Intent from WMS
                           ▼
                    ┌──────────────┐
              ┌─────│  CONFIRM     │◄──────────────┐
              │     │ (удержание)  │                │
              │     └──────┬───────┘                │
              │            │ удержание 2 сек        │
              │            ▼                        │
              │     ┌──────────────┐                │
              │     │  RECORDING   │                │
              │     │ (системная   │                │
              │     │  камера)     │                │
              │     └──────┬───────┘                │
              │            │ запись завершена       │
              │            ▼                        │
              │     ┌──────────────┐                │
              │     │  DONE        │───── QR ───────┤
              │     │ (диалог ID)  │                │
              │     └──────┬───────┘                │
              │            │ использовать ID        │
              │            ▼                        │
              │     ┌──────────────┐                │
              │     │  UPLOADING   │                │
              │     │ (SMB + флаг) │                │
              │     └──────┬───────┘                │
              │            │ завершено / ошибка     │
              │            ▼                        │
              │     ┌──────────────┐                │
              │     │  RESULT      │────────────────┘
              │     │ (✅ / ❌)    │
              │     └──────────────┘
              │
              └────── Settings (по паролю)
```

---

## 14. Зависимости (requirements)

```
# Обязательные:
kivy==2.3.1            # UI-фреймворк
pyjnius                # Доступ к Android API через JNI
pysmb                  # SMB/CIFS-клиент (чистый Python)
requests               # HTTP-клиент
android                # Python-for-Android библиотека (pyjnius + activity)

# Опциональные:
# Для QR-сканера: ZXing Barcode Scanner (отдельное приложение из Play Market)
# https://play.google.com/store/apps/details?id=com.google.zxing.client.android
```

buildozer.spec:
```
requirements = python3,kivy==2.3.1,pyjnius,pysmb,requests,android
```

---

## 15. Ресурсы

- **Kivy:** https://kivy.org/doc/stable/
- **Buildozer:** https://buildozer.readthedocs.io/
- **pysmb:** https://pysmb.readthedocs.io/
- **PyJnius:** https://pyjnius.readthedocs.io/
- **ZXing Barcode Scanner:** https://github.com/zxing/zxing
- **Python for Android:** https://python-for-android.readthedocs.io/

---

*Документ создан: июнь 2026*
*Последнее обновление: 12.06.2026*
