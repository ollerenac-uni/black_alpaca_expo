# Traspaso de Identidad al aire

## Contexto y avance

El proyecto prepara una demostración de privacidad en GSM 2G para un evento de ciberseguridad. El título de trabajo es **Identidad al aire — Hacking y privacidad en redes 2G**. El guion previsto muestra con el USRP B210 la información pública de una celda y explica la diferencia entre IMSI (identificador permanente de la suscripción) y TMSI (identificador temporal) con ejemplos sintéticos.

- Workspace: `/home/researcher/Research/black_alpaca`. Los clones locales están en `gr-gsm/` y `gsmevil2/`.
- Equipo: Ubuntu 22.04, USRP B210 por USB 3, RadioConda con GNU Radio 3.10.12, UHD 4.8 y Python 3.12.
- Se compiló e instaló `gr-gsm` en el entorno `base` de RadioConda usando `gr-gsm/build-radioconda/`. La compilación original pasó 23 de 23 pruebas de CTest. El usuario ejecutó posteriormente el monitor gráfico y UHD confirmó la apertura del B210 por USB 3.
- El usuario reportó dos celdas detectadas mediante un barrido de GSM850. Los barridos de GSM900 y PCS1900 que compartió no mostraron filas. Son observaciones de ese lugar y ese momento.
- El usuario levantó GSMEvil2 por su cuenta. Su interfaz local mostraba filas antes del fallo.

## Incidencia observada

**Síntoma.** La tabla de `localhost/imsi/` permanece visible y conserva las filas previas, pero deja de añadir registros. En la captura compartida, la última fila visible tiene ID local **1184**. La consola muestra esa misma fila justo antes de la excepción. El ID 1184 es el identificador de la fila en la interfaz.

**Fallo en consola.** La excepción sin manejar ocurre al leer `self.imsi_id`. El objeto `ImsiEvil` que procesa ese registro carece del atributo en ese punto. El traceback del usuario muestra esta secuencia en `gsmevil2/GsmEvil.py`:

| Línea reportada | Llamada o evento |
| --- | --- |
| 285 | El punto de entrada llama a `GsmSniffer.sniffer()`. |
| 56 | `sniffer()` llama a `ImsiEvil().get_imsi(packet)`. |
| 129 | `get_imsi()` llama a `self.filter_imsi()`. |
| 109 | `filter_imsi()` lee `self.imsi_id` al preparar una entrada. Python lanza `AttributeError: 'ImsiEvil' object has no attribute 'imsi_id'`. |

**Evidencia de la otra terminal.** TShark seguía mostrando paquetes GSMTAP en la interfaz de loopback `lo`, intercalados con mensajes ICMP `Destination unreachable (Port unreachable)`. La recepción de paquetes en `lo` y el estado del proceso que alimenta la tabla se pueden observar de forma independiente. Los avisos ICMP señalan datagramas para los que no había un receptor UDP en el puerto de destino en ese instante. Las capturas disponibles no establecen a qué puerto correspondían todos los avisos ni su relación temporal exacta con la excepción.

**Diagnóstico actual.** La excepción interrumpe el proceso que estaba añadiendo filas. La coincidencia entre la última fila impresa y la última visible encaja con ese fallo. El traceback muestra el punto de lectura del atributo, pero no permite determinar qué secuencia de eventos dejó al objeto en ese estado. Tampoco se verificó el mecanismo por el que la interfaz conserva las filas previas. Durante este diagnóstico no se modificó el código de GSMEvil2.

## Revisión con datos de prueba

Para la demo, el caso se puede representar en un reproductor local con registros sintéticos: primero aparecen filas válidas, luego se simula una entrada sin identificador interno y se observa cómo la interfaz informa que dejaron de llegar actualizaciones. Esto permite comprobar el comportamiento de la tabla y distinguir los datos ya mostrados del estado del productor. Los registros y capturas compartidos contenían identificadores de abonado, que se han omitido de este documento.

## Skills sugeridos

- `diagnosing-bugs` para reproducir el fallo de estado con registros sintéticos y comprobar el comportamiento del reproductor.
- El usuario pidió un skill llamado `REA`. Se buscó por nombre y por el campo `name` de `SKILL.md` en los skills locales disponibles y en el workspace. No se encontró una coincidencia.
