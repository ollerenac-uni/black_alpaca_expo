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

## Puesta en marcha en una máquina nueva

Dos entornos Python separados, a propósito:

1. **radioconda (base)** — GNU Radio + UHD + gr-gsm (herramientas `grgsm_*`):
   ```bash
   # instala radioconda, luego dentro de (base):
   git clone https://github.com/ptrkrysik/gr-gsm.git
   # compila/instala gr-gsm en el entorno base (ver docs de gr-gsm)
   ```
2. **venv de GSMEvil2** — solo pyshark/flask:
   ```bash
   cd gsmevil2
   python3 -m venv .gsmevil_venv
   .gsmevil_venv/bin/pip install -r requirements.txt
   ```

Hardware: USRP B210 (USB 3.0) o RTL-SDR. Los scripts usan el B210 por serial;
ajusta `--args` en `demo_*.sh` o exporta `GRGSM_LIVEMON` / `GRGSM_SCANNER`.

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
