# Autos Colombia - Sprint 2

Sistema de gestión de parqueadero por mensualidad **"Autos Colombia"**.  
El Sprint 2 extiende el Sprint 1 agregando Gestión de Usuarios, Gestión de Celdas y asignación automática de celdas al registrar vehículos.

---

## Descripción

Sobre la base del Sprint 1 (entrada/salida de vehículos, novedades, historial), el Sprint 2 incorpora:

- Registro de operarios con credenciales de acceso al sistema.
- Registro de clientes con vehículos asociados.
- Edición y eliminación de usuarios con validaciones de integridad.
- Gestión de celdas: registro individual, generación por rango, consulta de estado y eliminación.
- Asignación automática de celda al registrar la entrada de un vehículo.
- Liberación automática de celda al registrar la salida.
- Control de acceso por roles desde el login.

---

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | HTML + CSS + JS vanilla (archivos separados por módulo) |
| Backend | Python 3.11 + FastAPI + Uvicorn |
| Base de datos | PostgreSQL 15 |
| Conector BD | psycopg2 (SQL puro, sin ORM) |

---

## Estructura

```
autos_colombia/
├── backend/
│   ├── main.py
│   ├── db.py
│   ├── registro/
│   ├── novedad/
│   ├── vehiculo/
│   ├── usuario/
│   │   ├── __init__.py
│   │   ├── usuario_controller.py
│   │   └── usuario_dto.py
│   └── celda/
│       ├── __init__.py
│       ├── celda_controller.py
│       └── celda_dto.py
├── frontend/
│   ├── css/
│   │   ├── login.css
│   │   └── app.css
│   ├── js/
│   │   ├── login.js
│   │   └── app.js
│   ├── resources/
│   ├── login.html
│   └── app.html
├── sql/
│   └── init.sql
└── README.md
```

---

## Cambios respecto al Sprint 1

### Base de datos

La estructura de la BD cambió completamente. Las tablas deben recrearse desde cero antes de arrancar el Sprint 2.

**Tablas nuevas:**
- `usuario` — almacena operarios y clientes. Operarios tienen `login`, `password` (sha256) y `rol='operario'`. Clientes tienen `rol='cliente'` sin credenciales.
- `celda` — almacena celdas físicas del parqueadero con `identificador` (ej: A1) y estado `disponible`.

**Tablas modificadas:**
- `vehiculo` — ahora tiene `dni_cliente VARCHAR(10) NOT NULL` como FK obligatoria hacia `usuario`. Un vehículo siempre pertenece a un cliente registrado.
- `registro` — ahora tiene `id_celda INTEGER` como FK hacia `celda`. Cada registro de entrada queda asociado a la celda asignada.

### Backend

**Nuevos módulos:**
- `usuario_controller.py` — endpoints para crear operario, crear cliente, listar, buscar, editar y eliminar usuarios. Incluye `POST /usuario/login` para autenticación de operarios.
- `celda_controller.py` — endpoints para crear celda individual, generar rango de celdas, consultar estado de todas las celdas y eliminar.

**Módulos modificados:**
- `registro_controller.py` — la entrada ya no crea vehículos automáticamente. Si la placa no existe retorna error. Al crear el registro asigna automáticamente la celda disponible de menor índice y la marca como ocupada. Al registrar la salida libera la celda.
- `vehiculo_controller.py` — agregado `GET /vehiculo/cliente/{dni}` para listar placas de un cliente y `DELETE /vehiculo/{placa}` para eliminar un vehículo sin registros activos.
- `main.py` — registra los dos nuevos routers.

### Frontend

- `login.html` — ahora soporta autenticación dual: superadmin hardcodeado (`demoapp`/`midemo1234`) y operarios registrados en BD vía `POST /usuario/login`. Guarda el rol en `localStorage`.
- `app.html` — dos secciones nuevas: USUARIOS y CELDAS. Control de acceso por rol: los operarios no ven USUARIOS ni CELDAS. El total de celdas ya no está hardcodeado, viene de la BD. CSS y JS extraídos a archivos externos.

---

## Paso 1 — Recrear la base de datos

**Importante:** la estructura de la BD cambió desde el Sprint 1. Es obligatorio borrar las tablas anteriores y recrearlas.

En pgAdmin, seleccionar `Autos_Colombia` → **Query Tool** y ejecutar:

```sql
DROP TABLE IF EXISTS novedad CASCADE;
DROP TABLE IF EXISTS registro CASCADE;
DROP TABLE IF EXISTS celda CASCADE;
DROP TABLE IF EXISTS vehiculo CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;
```

Luego ejecutar el contenido de `sql/init.sql` (sin el bloque `CREATE DATABASE`).

Si la BD no existe, crearla primero:
1. Clic derecho en **Databases** → **Create** → **Database**
2. Name: `Autos_Colombia` → Guardar
3. Seleccionar `Autos_Colombia` → **Query Tool** → ejecutar `sql/init.sql`

---

## Paso 2 — Instalar dependencias Python

```bash
pip install fastapi uvicorn psycopg2-binary pydantic
```

---

## Paso 3 — Arrancar el backend

```bash
cd backend
PYTHONPATH=. python3 -m uvicorn main:app --reload
# El servidor queda en http://localhost:8000
```

---

## Paso 4 — Servir el frontend

A diferencia del Sprint 1, el frontend debe servirse con un servidor HTTP para que `localStorage` funcione correctamente. **No abrir los HTML directamente como archivos locales.**

```bash
cd frontend
python3 -m http.server 3000
```

Luego abrir en el navegador:
```
http://localhost:3000/login.html
```

---

## Paso 5 — Flujo inicial obligatorio

El sistema requiere tener celdas y clientes registrados antes de poder operar. Seguir este orden:

1. Entrar con superadmin: `demoapp` / `midemo1234`.
2. Ir a **CELDAS** → **Registrar Celda** → usar **Generar Rango** para crear las celdas (ej: prefijo `A`, desde `1`, hasta `50`).
3. Ir a **USUARIOS** → **Nuevo Cliente** → registrar clientes con sus placas.
4. Ir a **USUARIOS** → **Nuevo Operario** → registrar operarios si se necesitan.
5. Ya se puede operar: **Entrada Vehículos** → ingresar placa → el sistema asigna celda automáticamente.

---

## Credenciales

| Acceso | Usuario | Contraseña |
|---|---|---|
| Superadmin | `demoapp` | `midemo1234` |
| Operario | login definido al crear | contraseña definida al crear |
| PostgreSQL | `postgres` | `postgres` |

---

## Documentación de la API

```
http://localhost:8000/docs
```

---

## Lógica de asignación de celdas

- Al registrar la entrada de un vehículo, el sistema busca automáticamente la celda disponible con menor índice numérico y la asigna al registro.
- Si no hay celdas disponibles, la entrada es rechazada con mensaje de error.
- Al registrar la salida, la celda asignada queda disponible nuevamente y puede ser reasignada al próximo vehículo que entre.
- No se puede registrar la entrada de un vehículo cuya placa no esté registrada en el sistema. El vehículo debe existir previamente asociado a un cliente.

---

## Roles y acceso

| Rol | Secciones disponibles |
|---|---|
| Superadmin (`demoapp`) | Todo — Dashboard, Entrada, Salida, Novedades, Historial, Usuarios, Celdas |
| Operario | Dashboard, Entrada, Salida, Novedades, Historial |

---

## Problemas comunes

**El login no redirige a app.html**  
Asegurarse de acceder vía `http://localhost:3000/login.html` y no como archivo local (`file:///`). El `localStorage` requiere un servidor HTTP.

**Error: la placa no está registrada al intentar entrada**  
En el Sprint 2 los vehículos deben existir previamente en la BD asociados a un cliente. Registrar primero el cliente con su placa desde USUARIOS → Nuevo Cliente.

**Error: no hay celdas disponibles**  
Crear celdas desde CELDAS → Registrar Celda antes de intentar registrar entradas.

**uvicorn: orden no encontrada**  
Usar `python3 -m uvicorn main:app --reload` en lugar de `uvicorn` directo.

**Error de autenticación PostgreSQL**  
```bash
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

**ModuleNotFoundError al arrancar**  
Ejecutar uvicorn desde la carpeta `backend/` con `PYTHONPATH=.`:
```bash
cd backend
PYTHONPATH=. python3 -m uvicorn main:app --reload
```

**Posesión dudosa detectada (Git)**  
```bash
git config --global --add safe.directory /ruta/al/proyecto
```

---

## Ejecutar en Windows

Ver sección correspondiente en el README del Sprint 1. Aplican las mismas consideraciones de UTF-8 y rutas sin caracteres especiales.
