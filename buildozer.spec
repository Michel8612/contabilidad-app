[app]

# Nombre visible de la app
title = Area de Contabilidad

# Nombre del paquete (sin espacios ni mayusculas)
package.name = contabilidad
package.domain = org.siliconbay

# Codigo fuente
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0

# Dependencias que se empaquetan dentro del APK
requirements = python3,kivy==2.3.1

# Orientacion vertical (telefono)
orientation = portrait
fullscreen = 0

# --- Android ---
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a

# La base de datos SQLite se guarda en el almacenamiento privado de la app,
# no hace falta ningun permiso especial.
# android.permissions =

# Aceptar automaticamente las licencias del SDK durante el build
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
