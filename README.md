# Autos Colombia - Sprint 3

Sistema de gestión de parqueadero por mensualidad **"Autos Colombia"**.  
El Sprint 3 extiende el Sprint 2 agregando el módulo de Gestión de Pagos.

---

## Descripción

Sobre la base de los Sprints 1 y 2 (entrada/salida de vehículos, novedades, historial, usuarios y celdas), el Sprint 3 incorpora:

- Registro del pago mensual de un cliente buscando por documento o placa.
- Cálculo automático de la fecha de vencimiento (30 días después del pago).
- Consulta del estado de pago de un cliente (al día / vencido).
- Historial de pagos de un cliente ordenado del más reciente al más antiguo.
- Lista de clientes con pagos vencidos ordenada por días de mora de mayor a menor.

---

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | HTML + CSS + JS vanilla (archivos externos por módulo) |
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
│   ├── celda/
│   └── pago/
│       ├── __init__.py
│       ├── pago_controller.py
│       └── pago_dto.py
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

## Cambios respecto al Sprint 2

### Base de datos

Se agrega una tabla nueva. No se modifica ninguna tabla existente.

```sql
CREATE TABLE IF NOT EXISTS pago (
    id_pago     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    monto       NUMERIC        NOT NULL,
    dni_cliente VARCHAR(10)    NOT NULL,
    fecha_pago  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    mes         VARCHAR(10)    NOT NULL,
    CONSTRAINT fk_pago_usuario FOREIGN KEY (dni_cliente)
        REFERENCES usuario (dni)
);
```

> La fecha de vencimiento **no se almacena** en la BD. Se calcula en Python como `fecha_pago + 30 días` cada vez que se consulta. Esto es intencional.

### Backend

**Módulo nuevo:**
- `pago_controller.py` — 4 endpoints: registrar pago, consultar estado, consultar historial y listar vencidos.
- `pago_dto.py` — DTOs para registrar pago y buscar por criterio.

**main.py:**
- Agregado el router de pago con prefijo `/pago`.

**Ningún módulo anterior fue modificado.**

### Frontend

- `app.html` — agregada sección **PAGOS** al sidebar con cuatro subsecciones internas: Registrar Pago, Consultar Estado, Pagos Vencidos y Consultar Historial.
- La sección PAGOS es visible tanto para `superadmin` como para `operario`.

---

## Paso 1 — Agregar tabla pago a la BD

No es necesario recrear la BD completa. Solo ejecutar en pgAdmin con `Autos_Colombia` seleccionada:

```sql
CREATE TABLE IF NOT EXISTS pago (
    id_pago     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    monto       NUMERIC        NOT NULL,
    dni_cliente VARCHAR(10)    NOT NULL,
    fecha_pago  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    mes         VARCHAR(10)    NOT NULL,
    CONSTRAINT fk_pago_usuario FOREIGN KEY (dni_cliente)
        REFERENCES usuario (dni)
);
```

Si además los campos `login` o `password` de la tabla `usuario` tienen longitudes insuficientes, corregir con:

```sql
ALTER TABLE usuario ALTER COLUMN login TYPE VARCHAR(50);
ALTER TABLE usuario ALTER COLUMN password TYPE VARCHAR(255);
ALTER TABLE usuario ALTER COLUMN rol TYPE VARCHAR(50);
```

---

## Paso 2 — Instalar dependencias Python

Sin cambios respecto al Sprint 2:

```bash
pip install fastapi uvicorn psycopg2-binary pydantic
```

---

## Paso 3 — Arrancar el backend

```bash
cd backend
PYTHONPATH=. python3 -m uvicorn main:app --reload
```

---

## Paso 4 — Servir el frontend

```bash
cd frontend
python3 -m http.server 3000
```

Abrir en el navegador:
```
http://localhost:3000/login.html
```

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

## Lógica de pagos

**Registrar pago:**
- Se busca el cliente por DNI o por placa del vehículo.
- El backend registra `fecha_pago = NOW()` y `mes` automáticamente.
- La fecha de vencimiento se retorna en la respuesta como `fecha_pago + 30 días` pero no se guarda en la BD.

**Estado de pago:**
- Se determina comparando `fecha_pago + 30 días` del último pago con la fecha actual.
- Si `NOW() <= fecha_pago + 30 días` → **AL DÍA**.
- Si `NOW() > fecha_pago + 30 días` → **VENCIDO**.
- Si el cliente no tiene pagos → **SIN REGISTROS**.

**Pagos vencidos:**
- Lista todos los clientes cuyo pago más reciente tenga `fecha_pago + 30 días < NOW()`.
- Incluye días de mora calculados como `NOW() - (fecha_pago + 30 días)`.
- Ordenada de mayor a menor mora.
- Carga automáticamente al abrir la subsección, sin necesidad de buscar.

---
