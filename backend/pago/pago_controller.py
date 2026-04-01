from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
import calendar
from db import get_connection
from .pago_dto import PagoCreateDTO, PagoBuscarDTO

router = APIRouter()

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

def calcular_vencimiento(fecha_pago):
    return fecha_pago + timedelta(days=30)

def buscar_cliente_por_criterio(criterio: str, conn):
    with conn.cursor() as cur:
        # Buscar en usuario por DNI
        cur.execute("SELECT dni, nombres FROM usuario WHERE dni = %s OR login = %s", (criterio, criterio))
        row = cur.fetchone()
        if row:
            # Traer placa si tiene
            cur.execute("SELECT placa FROM vehiculo WHERE dni_cliente = %s LIMIT 1", (row[0],))
            placa_row = cur.fetchone()
            placa = placa_row[0] if placa_row else ""
            return {"dni": row[0], "nombres": row[1], "placa": placa}
        
        # Buscar en vehiculo por Placa
        cur.execute("""
            SELECT u.dni, u.nombres, v.placa 
            FROM vehiculo v
            JOIN usuario u ON v.dni_cliente = u.dni
            WHERE v.placa = %s
        """, (criterio,))
        row = cur.fetchone()
        if row:
            return {"dni": row[0], "nombres": row[1], "placa": row[2]}
            
    return None

@router.post("")
def registrar_pago(dto: PagoCreateDTO):
    conn = get_connection()
    try:
        cliente = buscar_cliente_por_criterio(dto.criterio, conn)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado.")
        
        with conn.cursor() as cur:
            now = datetime.now()
            mes_actual = MESES_ES[now.month]
            
            cur.execute("""
                INSERT INTO pago (monto, dni_cliente, fecha_pago, mes) 
                VALUES (%s, %s, %s, %s)
                RETURNING fecha_pago
            """, (dto.monto, cliente["dni"], now, mes_actual))
            fecha_pago = cur.fetchone()[0]
            
        conn.commit()
        return {
            "mensaje": "Pago registrado correctamente",
            "fecha_pago": fecha_pago,
            "fecha_vencimiento": calcular_vencimiento(fecha_pago)
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@router.get("/estado/{criterio}")
def consultar_estado(criterio: str):
    conn = get_connection()
    try:
        cliente = buscar_cliente_por_criterio(criterio, conn)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado.")
            
        with conn.cursor() as cur:
            cur.execute("""
                SELECT fecha_pago 
                FROM pago 
                WHERE dni_cliente = %s 
                ORDER BY fecha_pago DESC 
                LIMIT 1
            """, (cliente["dni"],))
            row = cur.fetchone()
            
            if not row:
                return {
                    "cliente": cliente,
                    "estado": "sin_pagos"
                }
                
            ultimo_pago = row[0]
            # Convert to naive if it's offset-aware for comparison, or use timezone active
            # Postgres NOW() is timestamptz. We assume Python datetime handles it.
            now = datetime.now(ultimo_pago.tzinfo) if ultimo_pago.tzinfo else datetime.now()
            vencimiento = calcular_vencimiento(ultimo_pago)
            
            estado = "al_dia" if now <= vencimiento else "vencido"
            
            return {
                "nombre": cliente["nombres"],
                "dni": cliente["dni"],
                "placa": cliente["placa"],
                "ultimo_pago": ultimo_pago,
                "vencimiento": vencimiento,
                "estado": estado
            }
    finally:
        conn.close()

@router.get("/historial/{criterio}")
def consultar_historial(criterio: str):
    conn = get_connection()
    try:
        cliente = buscar_cliente_por_criterio(criterio, conn)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado.")
            
        with conn.cursor() as cur:
            cur.execute("""
                SELECT fecha_pago, monto 
                FROM pago 
                WHERE dni_cliente = %s 
                ORDER BY fecha_pago DESC
            """, (cliente["dni"],))
            rows = cur.fetchall()
            
            historial = []
            for row in rows:
                historial.append({
                    "fecha_pago": row[0],
                    "monto": float(row[1]),
                    "vencimiento": calcular_vencimiento(row[0])
                })
                
            return historial
    finally:
        conn.close()

@router.get("/vencidos")
def consultar_vencidos():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # LEFT JOIN: incluye clientes con pagos vencidos Y clientes sin ningún pago
            cur.execute("""
                WITH UltimosPagos AS (
                    SELECT dni_cliente, MAX(fecha_pago) as max_fecha_pago
                    FROM pago
                    GROUP BY dni_cliente
                )
                SELECT u.nombres, u.dni, up.max_fecha_pago,
                       (SELECT placa FROM vehiculo v WHERE v.dni_cliente = u.dni LIMIT 1) as placa
                FROM usuario u
                LEFT JOIN UltimosPagos up ON u.dni = up.dni_cliente
                WHERE u.rol = 'cliente'
            """)
            rows = cur.fetchall()

            resultado = []
            for row in rows:
                nombres = row[0]
                dni = row[1]
                ultimo_pago = row[2]
                placa = row[3] if row[3] else ""

                if ultimo_pago is None:
                    # Sin pagos registrados → mora empieza en 0
                    resultado.append({
                        "nombre": nombres,
                        "dni": dni,
                        "placa": placa,
                        "ultimo_pago": None,
                        "mora_dias": 0,
                        "estado": "sin_pagos"
                    })
                else:
                    now = datetime.now(ultimo_pago.tzinfo) if ultimo_pago.tzinfo else datetime.now()
                    vencimiento = calcular_vencimiento(ultimo_pago)
                    if now > vencimiento:
                        mora_dias = (now - vencimiento).days
                        resultado.append({
                            "nombre": nombres,
                            "dni": dni,
                            "placa": placa,
                            "ultimo_pago": ultimo_pago,
                            "mora_dias": mora_dias,
                            "estado": "vencido"
                        })
                    # Si está al día, no se incluye en la lista

            # Primero sin_pagos, luego vencidos ordenados por mora desc
            resultado.sort(key=lambda x: (x["estado"] != "sin_pagos", -(x["mora_dias"] or 0)))
            return resultado
    finally:
        conn.close()
