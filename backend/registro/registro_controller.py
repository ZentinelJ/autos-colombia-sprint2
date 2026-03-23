from fastapi import APIRouter, HTTPException
from .registro_dto import RegistroCreateDTO, RegistroSalidaDTO
from db import get_connection

router = APIRouter()

def validar_longitud_placa(placa: str):
    if len(placa) != 6:
        raise HTTPException(status_code=400, detail="La placa debe tener exactamente 6 caracteres.")

def verificar_registro_abierto(placa: str, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id_registro, id_celda FROM registro WHERE placa_vehiculo = %s AND fecha_salida IS NULL", (placa,))
    row = cursor.fetchone()
    cursor.close()
    return row

@router.post("/entrada")
def registrar_entrada(dto: RegistroCreateDTO):
    validar_longitud_placa(dto.placa_vehiculo)
    conn = get_connection()
    try:
        if verificar_registro_abierto(dto.placa_vehiculo, conn):
            raise HTTPException(status_code=400, detail=f"El vehículo {dto.placa_vehiculo} ya tiene una entrada activa.")
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM vehiculo WHERE placa = %s", (dto.placa_vehiculo,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="La placa no está registrada. Registre primero el cliente desde la sección Usuarios.")
        
        # Buscar celda disponible ordenando por identificador (PK), de menor a mayor
        cursor.execute("""
            SELECT identificador FROM celda
            WHERE disponible = TRUE
            ORDER BY
                NULLIF(regexp_replace(identificador, '[^0-9]', '', 'g'), '')::integer ASC,
                identificador ASC
            LIMIT 1
        """)
        celda_row = cursor.fetchone()
        if not celda_row:
            raise HTTPException(status_code=400, detail="No hay celdas disponibles en el parqueadero.")
        id_celda = celda_row[0]
        
        cursor.execute("INSERT INTO registro (placa_vehiculo, id_celda) VALUES (%s, %s) RETURNING id_registro, fecha_entrada", (dto.placa_vehiculo, id_celda))
        row = cursor.fetchone()
        nuevo_id = row[0]
        fecha_entrada = row[1].isoformat()
        
        cursor.execute("UPDATE celda SET disponible = FALSE WHERE identificador = %s", (id_celda,))
        
        conn.commit()
        cursor.close()
        return {"message": "Entrada registrada exitosamente", "id_registro": nuevo_id, "fecha_entrada": fecha_entrada}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/salida")
def registrar_salida(dto: RegistroSalidaDTO):
    conn = get_connection()
    try:
        row = verificar_registro_abierto(dto.placa_vehiculo, conn)
        if not row:
            raise HTTPException(status_code=404, detail=f"No se encontró registro activo para la placa {dto.placa_vehiculo}.")
        
        id_registro = row[0]
        id_celda = row[1]  # ahora es el identificador VARCHAR
        
        cursor = conn.cursor()
        cursor.execute("UPDATE registro SET fecha_salida = NOW() WHERE id_registro = %s", (id_registro,))
        
        if id_celda:
            cursor.execute("UPDATE celda SET disponible = TRUE WHERE identificador = %s", (id_celda,))
            
        conn.commit()
        cursor.close()
        return {"message": "Salida registrada exitosamente"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/activos")
def registros_activos():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id_registro, r.placa_vehiculo, r.fecha_entrada, v.marca, v.modelo, r.id_celda as celda
            FROM registro r
            JOIN vehiculo v ON r.placa_vehiculo = v.placa
            WHERE r.fecha_salida IS NULL
            ORDER BY r.fecha_entrada DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        
        result = []
        for row in rows:
            result.append({
                "id_registro": row[0],
                "placa_vehiculo": row[1],
                "fecha_entrada": row[2].isoformat() if row[2] else None,
                "marca": row[3],
                "modelo": row[4],
                "celda": row[5]
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/historial/{placa}")
def historial_registro(placa: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_registro, fecha_entrada, fecha_salida
            FROM registro
            WHERE placa_vehiculo = %s AND fecha_salida IS NOT NULL
            ORDER BY fecha_salida DESC
        """, (placa,))
        rows = cursor.fetchall()
        cursor.close()
        
        result = []
        for row in rows:
            result.append({
                "id_registro": row[0],
                "fecha_entrada": row[1].isoformat() if row[1] else None,
                "fecha_salida": row[2].isoformat() if row[2] else None
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
