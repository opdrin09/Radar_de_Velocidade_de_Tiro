[app]

# (str) Title of your application
title = BalisticaAudio

# (str) Package name
package.name = balistica

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
# source.include_exts = py,png,jpg,kv,atlas (Duplicata removida)

# (list) List of exclusions using pattern matching
source.exclude_exts = spec

# (list) Application requirements
# Comma separated e.g. requirements = sqlite3,kivy
# Apenas o necessário. Sem ffmpeg, sem moviepy, sem scipy.
requirements = python3, kivy==2.3.0, numpy, uncertainties, plyer, pyjnius
# (str) Version of your application
version = 0.1

# (list) Permissions
# READ_EXTERNAL_STORAGE is needed to pick files
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, RECORD_AUDIO

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True
source.include_exts = py,png,jpg,kv,atlas,wav
# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) python-for-android branch to use, if not master, useful to try
# new features before they are merged
# p4a.branch = develop

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
