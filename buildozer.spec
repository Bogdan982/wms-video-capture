[app]

# (str) Title of your application
title = WMS Video Capture

# (str) Package name
package.name = wmsvideocapture

# (str) Package domain (needs java-like package name)
package.domain = org.enterprise.wms

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (relative to source.dir)
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml

# (list) List of inclusions using pattern matching
# source.include_patterns = assets/*,app/**/*,res/**/*

# (list) Source files to exclude (relative to source.dir)
# source.exclude_exts = spec,md

# (list) List of directory to exclude from the conversion
# source.exclude_dirs = tests, bin

# (list) List of git branches to ignore
source.ignore_git_branches = develop,staging

# (str) Application versioning (method 1)
version = 1.0.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (str) Application versioning (method 2)
# version.regex = __version__ = ['\"](.*)['\"]
# Python-for-Android обязательные: python3, hostpython3, kivy
requirements = python3,kivy==2.3.1

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of: landscape, sensorLandscape, portrait, sensorPortrait, all)
orientation = portrait

# (list) List of service to declare
# services = WmsUploadService:app/services/upload_service.py:foreground

# (bool) Full screen
fullscreen = 1

# (list) Android permissions
android.permissions = CAMERA, RECORD_AUDIO, INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, FOREGROUND_SERVICE

# (list) Android extra API calls (для вызова системной камеры через Intent)
android.api = 34
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 34

# (str) Android NDK version to use
android.ndk = 27c

# (str) Android build tools version to use
android.build_tools = 34.0.0

# (list) Android archs to build for
android.archs = arm64-v8a

# (str) Android private storage path
android.private_storage_path = wms_video_capture

# (str) Java package name for the activity
android.activity_class = org.kivy.android.PythonActivity

# (str) Which Java package to use for the Java activity
android.java_package_name = org.enterprise.wms.videocapture

# (str) Android intent filter to handle custom scheme
android.add_activity_meta_data = intent-filter:action=android.intent.action.VIEW;scheme=wmscapture;host=*

# (list) Additional Java files/libraries to include
# android.add_src =

# (str) Path to a custom AndroidManifest.xml
# android.manifest = assets/AndroidManifest.xml

# (bool) If True, then skip trying to update the Android SDK
android.accept_sdk_license = True

# (str) Log level (debug, info, warning, error)
log_level = 2

# (str) Log filename
log_filename = wms_capture.log

# (str) Log max size
log_max_size = 1000000

# (str) WHICH Python for Android distribution to use
# p4a.branch = develop

# (str) What to build: debug or release
# android.release_artifact = aab
