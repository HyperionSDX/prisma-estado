"""Actualiza estado.json para la página pública de Prisma (prisma.is-a.dev).

Corre en GitHub Actions (fuera del servidor), así la página sigue funcionando aunque el servidor esté caído:
- Si el panel responde, copia su /estado.json (solo nombre, descripción y estado de cada servicio; nada personal).
- Si no responde, marca todo como caído y recuerda desde cuándo.
Escribe sitio/estado.json y deja en `cambio.txt` "si" cuando el estado cambió (para guardar el historial solo entonces).
"""
import datetime
import json
import os
import urllib.request
from zoneinfo import ZoneInfo

# Prisma puede estar en Oracle o en Azure: se pregunta a cada uno y se usa el primero que responde.
FUENTES = [("Oracle", "https://prisma.tail53ad1c.ts.net/estado.json"),
           ("Azure", "https://prisma-azure.tail87f042.ts.net/estado.json")]
if os.environ.get("FUENTE"):
    FUENTES = [("Servidor", os.environ["FUENTE"])]
ZONA = ZoneInfo("America/Santiago")
ARCHIVO = "estado.json"            # historial (en el repo): solo cambia cuando cambia algún estado
BASE = [{"nombre": "Prisma", "descripcion": "Asistente personal"},
        {"nombre": "Botzy", "descripcion": "Bot de música"},
        {"nombre": "CeratiBot", "descripcion": "Homenaje a Gustavo Cerati"}]


def ahora():
    return datetime.datetime.now(ZONA).isoformat(timespec="minutes")


def leer_fuentes():
    """(nombre del servidor, servicios) del primer servidor que responde; si ninguno responde, lanza el último error."""
    error = None
    for nombre, url in FUENTES:
        try:
            return nombre, leer_fuente(url)
        except Exception as e:
            print(f"{nombre} no respondió: {type(e).__name__}")
            error = e
    raise error or ValueError("sin fuentes")


def leer_fuente(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "prisma-estado"})
    with urllib.request.urlopen(pedido, timeout=20) as r:
        datos = json.load(r)
    servicios = [{k: s[k] for k in ("nombre", "descripcion", "estado", "porcentaje_7d") if k in s}
                 for s in datos.get("servicios", []) if s.get("nombre")]
    if not servicios:
        raise ValueError("respuesta sin servicios")
    return servicios


def main():
    anterior = {}
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, encoding="utf-8") as f:
            anterior = json.load(f)
    try:
        donde, servicios = leer_fuentes()
        servidor = {"estado": "operativo", "nombre": donde}
    except Exception as e:
        print(f"Ningún servidor respondió: {type(e).__name__}")
        previos = anterior.get("servicios") or BASE
        servicios = [{"nombre": s["nombre"], "descripcion": s.get("descripcion", ""), "estado": "caido"} for s in previos]
        caido_desde = (anterior.get("servidor") or {}).get("caido_desde") if (anterior.get("servidor") or {}).get("estado") == "caido" else None
        servidor = {"estado": "caido", "caido_desde": caido_desde or ahora()}

    nuevo = {"servidor": servidor, "servicios": servicios}
    cambio = {k: anterior.get(k) for k in ("servidor", "servicios")} != nuevo
    if cambio:
        nuevo["cambio"] = ahora()
        with open(ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(nuevo, f, ensure_ascii=False, indent=2)
            f.write("\n")
    else:
        nuevo["cambio"] = anterior.get("cambio")
    os.makedirs("sitio", exist_ok=True)
    with open("sitio/estado.json", "w", encoding="utf-8") as f:
        json.dump({**nuevo, "actualizado": ahora()}, f, ensure_ascii=False)
    with open("cambio.txt", "w") as f:
        f.write("si" if cambio else "no")
    print(("Cambió: " if cambio else "Sin cambios: ") + servidor["estado"])


if __name__ == "__main__":
    main()
