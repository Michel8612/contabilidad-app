# Compilar la app para Android (generar el APK)

La app ya funciona en PC (`python main.py`). Para el teléfono hay que
empaquetarla como APK con **buildozer**. Buildozer **no corre en Windows
directamente**: necesita Linux. En tu PC lo más fácil es usar **WSL (Ubuntu)**.

## Paso 1 — Instalar WSL (una sola vez)
En PowerShell **como administrador**:
```powershell
wsl --install -d Ubuntu
```
Reinicia si te lo pide, abre "Ubuntu" desde el menú Inicio y crea tu usuario.

## Paso 2 — Preparar Ubuntu (una sola vez)
Dentro de la terminal de Ubuntu:
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git zip unzip openjdk-17-jdk \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev cmake libffi-dev libssl-dev
pip3 install --user buildozer cython==0.29.36
```

## Paso 3 — Copiar el proyecto a Ubuntu
Desde Ubuntu puedes acceder a tu carpeta de Windows:
```bash
cp -r /mnt/c/Users/Romer/Downloads/compras_android ~/contabilidad
cd ~/contabilidad
```
> Cópialo a `~` (home de Linux); compilar dentro de `/mnt/c` es mucho más lento.

## Paso 4 — Compilar el APK
```bash
buildozer -v android debug
```
La **primera vez** descarga el SDK/NDK de Android (tarda bastante, 20–40 min).
Las siguientes veces es mucho más rápido.

Cuando termine, el APK queda en:
```
~/contabilidad/bin/contabilidad-1.0-arm64-v8a_armeabi-v7a-debug.apk
```
Cópialo de vuelta a Windows para pasarlo al teléfono:
```bash
cp bin/*.apk /mnt/c/Users/Romer/Downloads/
```

## Paso 5 — Instalar en el teléfono
- Pásalo por cable/USB, Telegram, correo, etc.
- En el teléfono, activa **"Instalar apps de origen desconocido"** y ábrelo.
- (Opcional, con el teléfono en modo desarrollador y conectado por USB):
  ```bash
  buildozer android deploy run
  ```

---

### Alternativa sin instalar nada: GitHub Actions
Si prefieres no usar WSL, se puede compilar el APK en la nube con
`ArtemSBulgakov/buildozer-action`. Dime y te dejo el archivo
`.github/workflows/build.yml` listo.
