from fastapi import APIRouter, HTTPException
from .novedad_dto import NovedadCreateDTO
from db import get_connection

router = APIRouter()

def obtener_id_registro_abierto(placa: str, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id_registro FROM registro WHERE placa_vehiculo = %s AND fecha_salida IS NULL", (placa,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None

@router.post("")
def crear_novedad(dto: NovedadCreateDTO):
    conn = get_connection()
    try:
        id_registro = obtener_id_registro_abierto(dto.placa_vehiculo, conn)
        if not id_registro:
            raise HTTPException(status_code=404, detail=f"No hay registro activo para la placa {dto.placa_vehiculo}.")
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO novedad (id_registro, descripcion) VALUES (%s, %s)",
            (id_registro, dto.descripcion)
        )
        conn.commit()
        cursor.close()
        return {"message": "Novedad registrada exitosamente"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/activos")
def novedades_activas():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT n.id_registro, n.descripcion, n.fecha
            FROM novedad n
            JOIN registro r ON n.id_registro = r.id_registro
            WHERE r.fecha_salida IS NULL
            ORDER BY n.fecha DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        
        result_dict = {}
        for row in rows:
            id_reg = row[0]
            if id_reg not in result_dict:
                result_dict[id_reg] = {
                    "id_registro": id_reg,
                    "descripcion": row[1]
                }
        
        return list(result_dict.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
