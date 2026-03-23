from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from db import get_connection

router = APIRouter()

class VehiculoCreateDTO(BaseModel):
    placa: str
    marca: str
    modelo: str
    dni_cliente: Optional[str] = None

@router.post("")
def create_vehiculo(vehiculo: VehiculoCreateDTO):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if vehiculo.dni_cliente:
            cursor.execute(
                """
                INSERT INTO vehiculo (placa, marca, modelo, dni_cliente)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (placa) DO NOTHING
                """,
                (vehiculo.placa, vehiculo.marca, vehiculo.modelo, vehiculo.dni_cliente)
            )
        else:
            cursor.execute(
                """
                INSERT INTO vehiculo (placa, marca, modelo)
                VALUES (%s, %s, %s)
                ON CONFLICT (placa) DO NOTHING
                """,
                (vehiculo.placa, vehiculo.marca, vehiculo.modelo)
            )
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Vehículo procesado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cliente/{dni}")
def get_vehiculos_cliente(dni: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT placa FROM vehiculo WHERE dni_cliente = %s", (dni,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{placa}")
def get_vehiculo(placa: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT placa, marca, modelo FROM vehiculo WHERE placa = %s", (placa,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="La placa ingresada no existe en el sistema.")
        return {"placa": row[0], "marca": row[1], "modelo": row[2]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{placa}")
def delete_vehiculo(placa: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_registro FROM registro WHERE placa_vehiculo = %s AND fecha_salida IS NULL", (placa,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="No se puede eliminar. El vehículo tiene un registro activo.")
            
        cursor.execute("DELETE FROM registro WHERE placa_vehiculo = %s", (placa,))    
        cursor.execute("DELETE FROM vehiculo WHERE placa = %s", (placa,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Vehículo eliminado correctamente."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
