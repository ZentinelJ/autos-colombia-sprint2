from fastapi import APIRouter, HTTPException, status
import hashlib
from db import get_connection
from .usuario_dto import UsuarioOperarioCreateDTO, ClienteCreateDTO, UsuarioUpdateDTO, UsuarioLoginDTO

router = APIRouter()

def hashear_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_dni_existe(dni: str, conn) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM usuario WHERE dni = %s", (dni,))
        return cur.fetchone() is not None

def verificar_login_en_uso(login: str, conn) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM usuario WHERE login = %s", (login,))
        return cur.fetchone() is not None

def verificar_placa_asociada(placa: str, conn) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM vehiculo WHERE placa = %s", (placa,))
        return cur.fetchone() is not None

def verificar_registros_activos_usuario(dni: str, conn) -> bool:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM vehiculo v
            JOIN registro r ON v.placa = r.placa_vehiculo
            WHERE v.dni_cliente = %s AND r.fecha_salida IS NULL
        """, (dni,))
        return cur.fetchone() is not None

@router.post("/login")
def login(dto: UsuarioLoginDTO):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT dni, nombres, login, password, rol FROM usuario WHERE login = %s AND rol = 'operario'", (dto.login,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Credenciales incorrectas.")
            
            hashed_input = hashear_password(dto.password)
            if hashed_input != row[3]:
                raise HTTPException(status_code=401, detail="Credenciales incorrectas.")
            
            return {
                "dni": row[0],
                "nombres": row[1],
                "login": row[2],
                "rol": row[4]
            }
    finally:
        conn.close()

@router.post("/operario")
def crear_operario(dto: UsuarioOperarioCreateDTO):
    conn = get_connection()
    try:
        if verificar_dni_existe(dto.dni, conn):
            raise HTTPException(status_code=400, detail="El documento ya está registrado.")
        if verificar_login_en_uso(dto.login, conn):
            raise HTTPException(status_code=400, detail="El usuario ya está en uso.")
        
        hashed_password = hashear_password(dto.password)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO usuario (dni, nombres, movil, correo, login, password, rol)
                VALUES (%s, %s, %s, %s, %s, %s, 'operario')
            """, (dto.dni, dto.nombres, dto.movil, dto.correo, dto.login, hashed_password))
        conn.commit()
        return {"message": "Operario creado exitosamente."}
    finally:
        conn.close()

@router.post("/cliente")
def crear_cliente(dto: ClienteCreateDTO):
    conn = get_connection()
    try:
        if verificar_dni_existe(dto.dni, conn):
            raise HTTPException(status_code=400, detail="El documento ya está registrado.")
        if verificar_placa_asociada(dto.placa, conn):
            raise HTTPException(status_code=400, detail="La placa ya está asociada a otro cliente.")
        
        with conn.cursor() as cur:
            # Transaction starts implicitly
            cur.execute("""
                INSERT INTO usuario (dni, nombres, movil, correo, rol)
                VALUES (%s, %s, %s, %s, 'cliente')
            """, (dto.dni, dto.nombres, dto.movil, dto.correo))
            
            cur.execute("""
                INSERT INTO vehiculo (placa, marca, modelo, dni_cliente)
                VALUES (%s, %s, %s, %s)
            """, (dto.placa, dto.marca, dto.modelo, dto.dni))
        conn.commit()
        return {"message": "Cliente creado exitosamente."}
    except HTTPException as he:
        # HTTPException is already raised when validating, we shouldn't rollback the db transaction that hasn't started
        raise he
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@router.get("/todos")
def listar_usuarios():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.dni, u.nombres, u.movil, u.correo, u.rol, u.login,
                       ARRAY_AGG(v.placa) FILTER (WHERE v.placa IS NOT NULL) as placas
                FROM usuario u
                LEFT JOIN vehiculo v ON u.dni = v.dni_cliente
                GROUP BY u.dni, u.nombres, u.movil, u.correo, u.rol, u.login
                ORDER BY u.nombres
            """)
            rows = cur.fetchall()
            usuarios = []
            for row in rows:
                usuario = {
                    "dni": row[0],
                    "nombres": row[1],
                    "movil": row[2],
                    "correo": row[3],
                    "rol": row[4]
                }
                if row[4] == 'operario':
                    usuario['login'] = row[5]
                elif row[4] == 'cliente' and row[6]:
                    usuario['placas'] = row[6]
                usuarios.append(usuario)
            return usuarios
    finally:
        conn.close()

@router.get("/buscar")
def buscar_usuarios(q: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            search_param = f"%{q}%"
            cur.execute("""
                SELECT u.dni, u.nombres, u.movil, u.correo, u.rol, u.login,
                       ARRAY_AGG(v.placa) FILTER (WHERE v.placa IS NOT NULL) as placas
                FROM usuario u
                LEFT JOIN vehiculo v ON u.dni = v.dni_cliente
                WHERE u.dni ILIKE %s OR u.nombres ILIKE %s
                GROUP BY u.dni, u.nombres, u.movil, u.correo, u.rol, u.login
                ORDER BY u.nombres
            """, (search_param, search_param))
            rows = cur.fetchall()
            usuarios = []
            for row in rows:
                usuario = {
                    "dni": row[0],
                    "nombres": row[1],
                    "movil": row[2],
                    "correo": row[3],
                    "rol": row[4]
                }
                if row[4] == 'operario':
                    usuario['login'] = row[5]
                elif row[4] == 'cliente' and row[6]:
                    usuario['placas'] = row[6]
                usuarios.append(usuario)
            return usuarios
    finally:
        conn.close()

@router.get("/{dni}")
def obtener_usuario(dni: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT dni, nombres, movil, correo, rol, login FROM usuario WHERE dni = %s", (dni,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
            
            usuario = {
                "dni": row[0],
                "nombres": row[1],
                "movil": row[2],
                "correo": row[3],
                "rol": row[4]
            }
            if row[4] == 'operario':
                usuario['login'] = row[5]
            return usuario
    finally:
        conn.close()

@router.put("/{dni}")
def editar_usuario(dni: str, dto: UsuarioUpdateDTO):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT rol FROM usuario WHERE dni = %s", (dni,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
            
            rol = row[0]
            if rol == 'operario':
                if dto.password:
                    hashed_password = hashear_password(dto.password)
                    cur.execute("""
                        UPDATE usuario
                        SET nombres = %s, movil = %s, correo = %s, login = %s, password = %s
                        WHERE dni = %s
                    """, (dto.nombres, dto.movil, dto.correo, dto.login, hashed_password, dni))
                else:
                    cur.execute("""
                        UPDATE usuario
                        SET nombres = %s, movil = %s, correo = %s, login = %s
                        WHERE dni = %s
                    """, (dto.nombres, dto.movil, dto.correo, dto.login, dni))
            else:
                cur.execute("""
                    UPDATE usuario
                    SET nombres = %s, movil = %s, correo = %s
                    WHERE dni = %s
                """, (dto.nombres, dto.movil, dto.correo, dni))
        conn.commit()
        return {"message": "Usuario actualizado exitosamente."}
    finally:
        conn.close()

@router.delete("/{dni}")
def eliminar_usuario(dni: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM usuario WHERE dni = %s", (dni,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
        if verificar_registros_activos_usuario(dni, conn):
            raise HTTPException(status_code=400, detail="No se puede eliminar. El usuario tiene registros activos.")
        
        with conn.cursor() as cur:
            cur.execute("DELETE FROM usuario WHERE dni = %s", (dni,))
        conn.commit()
        return {"message": "Usuario eliminado exitosamente."}
    finally:
        conn.close()
