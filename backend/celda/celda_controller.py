from fastapi import APIRouter, HTTPException
from db import get_connection
from .celda_dto import CeldaCreateDTO, CeldaRangoDTO

router = APIRouter()

def verificar_identificador_existe(identificador: str, conn) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM celda WHERE identificador = %s", (identificador,))
        return cur.fetchone() is not None

@router.post("")
def crear_celda(dto: CeldaCreateDTO):
    conn = get_connection()
    try:
        if verificar_identificador_existe(dto.identificador, conn):
            raise HTTPException(status_code=400, detail="El identificador de celda ya existe.")
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO celda (identificador, disponible)
                VALUES (%s, TRUE)
            """, (dto.identificador,))
        conn.commit()
        return {"message": "Celda creada exitosamente."}
    finally:
        conn.close()

@router.post("/rango")
def crear_celda_rango(dto: CeldaRangoDTO):
    if dto.desde > dto.hasta:
        raise HTTPException(status_code=400, detail="El valor 'desde' debe ser menor o igual a 'hasta'.")
    if dto.hasta - dto.desde > 200:
        raise HTTPException(status_code=400, detail="No se pueden generar más de 200 celdas a la vez.")
        
    conn = get_connection()
    try:
        creadas = 0
        saltadas = 0
        with conn.cursor() as cur:
            for n in range(dto.desde, dto.hasta + 1):
                identificador = f"{dto.prefijo}{n}"
                cur.execute("""
                    INSERT INTO celda (identificador, disponible)
                    VALUES (%s, TRUE)
                    ON CONFLICT (identificador) DO NOTHING
                """, (identificador,))
                if cur.rowcount > 0:
                    creadas += 1
                else:
                    saltadas += 1
            conn.commit()
            
        total = creadas + saltadas
        msg = f"{total} celdas procesadas. {creadas} creadas, {saltadas} ya existía{'n' if saltadas != 1 else ''}."
        
        return {"creadas": creadas, "saltadas": saltadas, "mensaje": msg}
    finally:
        conn.close()

@router.get("/todas")
def listar_celdas():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.identificador, c.disponible, r.placa_vehiculo
                FROM celda c
                LEFT JOIN registro r ON c.identificador = r.id_celda AND r.fecha_salida IS NULL
                ORDER BY
                    NULLIF(regexp_replace(c.identificador, '[^0-9]', '', 'g'), '')::integer ASC,
                    c.identificador ASC
            """)
            rows = cur.fetchall()
            celdas = []
            ocupadas = 0
            disponibles = 0
            for row in rows:
                disponible = row[1]
                celda = {
                    "identificador": row[0],
                    "disponible": disponible
                }
                if row[2]:
                    celda["placa"] = row[2]
                
                celdas.append(celda)
                
                if disponible:
                    disponibles += 1
                else:
                    ocupadas += 1
            
            return {
                "celdas": celdas,
                "totales": {
                    "total": len(celdas),
                    "ocupadas": ocupadas,
                    "disponibles": disponibles
                }
            }
    finally:
        conn.close()

@router.delete("/{identificador}")
def eliminar_celda(identificador: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM celda WHERE identificador = %s", (identificador,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Celda no encontrada.")

            cur.execute("SELECT 1 FROM registro WHERE id_celda = %s AND fecha_salida IS NULL", (identificador,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="No se puede eliminar. El vehículo tiene un registro activo.")

            cur.execute("SELECT disponible FROM celda WHERE identificador = %s", (identificador,))
            row = cur.fetchone()
            if not row[0]:
                raise HTTPException(status_code=400, detail="No se puede eliminar. La celda está ocupada.")

            cur.execute("DELETE FROM celda WHERE identificador = %s", (identificador,))
        conn.commit()
        return {"message": "Celda eliminada exitosamente."}
    finally:
        conn.close()
