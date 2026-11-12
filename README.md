# black_alpaca_expo

Demo de privacidad en redes 2G (GSM) para un evento de ciberseguridad:
**"Identidad al aire — Hacking y privacidad en redes 2G"**. Muestra, de forma
**pasiva**, cómo una red GSM expone identificadores permanentes de abonado (IMSI)
y permite perfilar roamers extranjeros y rastrear la presencia de un dispositivo
en el tiempo.

> Uso educativo / investigación de seguridad autorizada. La recepción pasiva y el
> análisis se hacen con fines de demostración del riesgo de seguir operando 2G.

## Estructura

```
gsmevil2/                 GSMEvil2 (fork ninjhacks) con parches de esta demo
  GsmEvil.py              sniffer IMSI/SMS + rutas Flask (incluye /analytics/)
  analytics.py            query por MCC/MNC, detección de roamers, presencia (RO)
  templates/analytics.html  página de análisis (tema oscuro)
  demo_scan.sh            escanea celdas vivas con el B210  (radioconda, por ruta)
  demo_livemon.sh         demodula un BCCH -> GSMTAP lo:4729 (radioconda, por ruta)
  demo_sniffer.sh         levanta GSMEvil2 (venv dedicado, sudo para capturar en lo)
  database/*.db           data capturada de la demo
identidad-al-aire-handoff.md   contexto y bitácora del proyecto
```

`gr-gsm/` **no** está versionado aquí (clon de terceros pesado). Re-clónalo.

## Docker (recomendado)

Imagen todo-en-uno (GNU Radio + gr-gsm + GSMEvil2). Evita la instalación manual.
**Solo host Linux** (necesita passthrough USB real y loopback del host).

Requisito del host (el contenedor no puede hacerlo): que el kernel no acapare el
RTL-SDR.
```bash
echo 'blacklist dvb_usb_rtl28xxu' | sudo tee /etc/modprobe.d/blacklist-rtl.conf
sudo modprobe -r dvb_usb_rtl28xxu 2>/dev/null; # o reconecta el dongle
```

Construir y correr:
```bash
docker compose -f docker/docker-compose.yml build        # ~10-15 min la 1ª vez
# ajusta SDR_FREQ/SDR_ARGS en docker/docker-compose.yml, luego:
docker compose -f docker/docker-compose.yml up
```
Abre `http://localhost/imsi/` (activa IMSI) y `http://localhost/analytics/`.

Sin compose:
```bash
docker build -t black-alpaca-expo -f docker/Dockerfile .
# escanear celdas vivas (one-off):
docker run --rm -it --privileged -v /dev/bus/usb:/dev/bus/usb \
  --entrypoint grgsm_scanner black-alpaca-expo --args=rtl=0 -b GSM850 -s 2e6
# correr la demo (RTL en 879.8M):
docker run --rm -it --net host --privileged -v /dev/bus/usb:/dev/bus/usb \
  -e SDR_FREQ=879.8M -e SDR_ARGS=rtl=0 black-alpaca-expo
```
Variables: `SDR_FREQ` (req), `SDR_GAIN` (40), `SDR_SR` (1e6), `SDR_ARGS`
(`rtl=0` RTL · `type=b200` B210 · `''` autodetecta).

> Nota CPU: el demod GSM en vivo es pesado. En equipos lentos aparecen overruns
> (`OOOO`) cuando otro proceso toma CPU. Docker no lo arregla — corre en un
> equipo con CPU decente, a ser posible con governor `performance` y en corriente.

## Instalación (bare metal)

Probado en Ubuntu 22.04, GNU Radio 3.10.12 (radioconda), UHD 4.8, USRP B210.
Dos entornos Python separados **a propósito**: radioconda (base) para la radio
(`grgsm_*`), y un venv dedicado para GSMEvil2 (pyshark/flask).

### Prerrequisitos

- **radioconda instalado** — sigue la fuente oficial de GNU Radio:
  <https://github.com/ryanvolz/radioconda> (trae GNU Radio, UHD, gr-osmosdr,
  rtl-sdr, SoapySDR; no necesitas instalarlos aparte).
- USRP **B210** (USB 3.0) y/o un **RTL-SDR**.

### Paso 0 — Paquetes de sistema

gr-gsm se compila con el compilador del sistema y enlaza contra las libs de
Osmocom (`libosmocore-dev`, que no viene en radioconda); `pyshark` usa `tshark`.

```bash
sudo apt update
sudo apt install -y build-essential cmake pkg-config git tshark libosmocore-dev python3-venv
```
Verifica: `cmake --version && tshark --version && pkg-config --modversion libosmocore`.

`python3-venv` es para el entorno de GSMEvil2 (Paso 4); en Debian/Ubuntu el
`python3` base no trae el módulo `venv` y falla con *"ensurepip is not available"*.

### Paso 1 — Clonar este repo

```bash
git clone https://github.com/ollerenac-uni/black_alpaca_expo.git
cd black_alpaca_expo
```

### Paso 2 — Compilar gr-gsm dentro de radioconda (base)

Mainline `ptrkrysik/gr-gsm` ya compila con GNU Radio 3.10 vía pybind11. Fijamos
el commit probado (`2ebf07d`, 23/23 tests) y lo instalamos **en el prefix de
radioconda** para que `grgsm_*` queden en el PATH de base.

```bash
conda activate base                 # entorno radioconda

# radioconda trae las LIBS de Boost/pybind11 (runtime de GNU Radio) pero no
# siempre los HEADERS de desarrollo que necesita compilar un módulo OOT.
# Sin esto cmake falla con "Could NOT find Boost (missing: Boost_INCLUDE_DIR...)".
mamba install -c conda-forge -y libboost-devel pybind11

git clone https://github.com/ptrkrysik/gr-gsm.git
cd gr-gsm
git checkout 2ebf07d
cmake -S . -B build \
  -DCMAKE_INSTALL_PREFIX="$CONDA_PREFIX" \
  -DCMAKE_PREFIX_PATH="$CONDA_PREFIX"
cmake --build build -j"$(nproc)"
ctest --test-dir build              # esperado: 23/23 passed
cmake --install build
cd ..
```
Verifica: `grgsm_scanner --help` responde sin error.
Si reconfiguras tras un fallo, borra el cache antes: `rm -rf build`.

### Paso 3 — Hardware

**USRP B210** (UHD, ya en radioconda):
```bash
uhd_images_downloader        # baja imágenes FPGA del B210 si faltan
uhd_find_devices             # debe listar type: b200
```
**RTL-SDR:** radioconda instala el blacklist de `dvb_usb_rtl28xxu`. Además hace
falta una regla udev para acceder al USB sin root (si no, `rtl_test` da
`usb_open error -3`):
```bash
sudo tee /etc/udev/rules.d/rtl-sdr.rules >/dev/null <<'EOF'
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2832", GROUP="plugdev", MODE="0666", SYMLINK+="rtl_sdr"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", GROUP="plugdev", MODE="0666", SYMLINK+="rtl_sdr"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
# desconecta y reconecta el dongle, luego:
rtl_test -t                  # debe detectar el tuner (R820T/R820T2)
```
Si `lsusb | grep -i realtek` muestra otro `idProduct`, ajústalo en la regla.

### Paso 4 — venv de GSMEvil2

Créalo con el **python del sistema** (desactiva conda) para no mezclar entornos:

```bash
conda deactivate
cd gsmevil2
python3 -m venv .gsmevil_venv
.gsmevil_venv/bin/pip install -r requirements.txt
cd ..
```
Verifica: `gsmevil2/.gsmevil_venv/bin/python -c "import pyshark, flask; print('ok')"`.

### Paso 5 — Permisos de captura

El sniffer lee la interfaz `lo`, lo que requiere privilegios. `demo_sniffer.sh`
ya usa `sudo`. Para evitar sudo cada vez, puedes dar capacidades a `dumpcap`:
```bash
sudo setcap cap_net_raw,cap_net_admin=eip "$(which dumpcap)"
```

### Hardware en los scripts

Los `demo_*.sh` llaman a radioconda por **ruta absoluta** (funcionan con cualquier
env activo) y por defecto usan **cualquier B210** (`--args="type=b200"`).

- RTL-SDR: `GRGSM_ARGS='' ./demo_scan.sh`  (args vacíos = autodetecta el RTL)
- Un B210 concreto: `GRGSM_ARGS='type=b200,serial=XXXX' ./demo_livemon.sh 879.8M`
- Binarios en otra ruta: exporta `GRGSM_LIVEMON` / `GRGSM_SCANNER`.

## Correr la demo

```bash
# 1) encontrar una celda viva
cd gsmevil2 && ./demo_scan.sh GSM850

# 2) demodular (terminal aparte) — usa la frecuencia más fuerte
./demo_livemon.sh 879.8M

# 3) sniffer + web (terminal aparte)
./demo_sniffer.sh
#   http://localhost/imsi/        tabla IMSI en vivo
#   http://localhost/analytics/   redes MCC/MNC, roamers, presencia
```

Captura sana en (2) = hex que **no** sea todo `2b`.

## Qué demuestra `/analytics/`

- **Roamers**: combos MCC+MNC únicos; SIM extranjera (MCC ≠ local) marcada en rojo.
- **Presencia**: por IMSI, nº de pagings y primera/última vez visto = rastreo pasivo.
- **Escala**: suscriptores únicos y % expuesto.

## Notas técnicas

- Fix aplicado: `self.imsi_id` ahora se define en todas las ramas de `filter_imsi()`
  (antes crasheaba con `AttributeError` al re-ver una IMSI ya en DB tras reiniciar).
- `analytics.py` trae self-check: `python gsmevil2/analytics.py`.
- El MNC del parser e212 a veces sale raro (p.ej. `60` en vez de `06`); el país por
  MCC sí es fiable. Afinar el parseo e212 en `get_imsi()` es trabajo pendiente.
