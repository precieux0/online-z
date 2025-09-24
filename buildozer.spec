[app]
title = Online X Chat AI
package.name = onlinexchat
package.domain = org.yashasmon

source.dir = .
source.include_exts = py,png,jpg,kv,json,gif

version = 1.0.0
requirements = python3,kivy,requests,pillow

orientation = portrait

[buildozer]
log_level = 2

android.api = 33
android.minapi = 21
android.permissions = INTERNET,ACCESS_NETWORK_STATE

presplash.filename = %(source.dir)s/assets/logo.png
icon.filename = %(source.dir)s/assets/logo.png