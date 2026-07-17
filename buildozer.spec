[app]
title = QR Generator
package.name = qrgenerator
package.domain = org.kaifi
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# Kivy aur baqi libraries jo aapki app ko chahiye
requirements = python3,kivy==2.3.0,qrcode,pillow,requests,urllib3,certifi

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Android SDK / NDK settings (Stable versions)
android.api = 33
android.minapi = 24
android.ndk = 25b
android.skip_update = False
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
