CREATE TABLE IF NOT EXISTS usuario (
    dni      VARCHAR(10)  PRIMARY KEY,
    movil    VARCHAR(10)  NOT NULL,
    nombres  VARCHAR(50)  NOT NULL,
    correo   VARCHAR(50)  NOT NULL,
    login    VARCHAR(12)  UNIQUE,
    password VARCHAR(25),
    rol      VARCHAR(20)  NOT NULL DEFAULT 'cliente'
);

CREATE TABLE IF NOT EXISTS vehiculo (
    placa       VARCHAR(6)  PRIMARY KEY,
    marca       VARCHAR(12) NOT NULL,
    modelo      VARCHAR(20) NOT NULL,
    dni_cliente VARCHAR(10) NOT NULL,
    CONSTRAINT fk_vehiculo_usuario FOREIGN KEY (dni_cliente)
        REFERENCES usuario (dni)
);

CREATE TABLE IF NOT EXISTS celda (
    identificador VARCHAR(10) PRIMARY KEY,
    disponible    BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS registro (
    id_registro    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    placa_vehiculo VARCHAR(6)  NOT NULL,
    fecha_entrada  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_salida   TIMESTAMPTZ,
    id_celda       VARCHAR(10),
    CONSTRAINT fk_id_celda FOREIGN KEY (id_celda)
        REFERENCES celda (identificador),
    CONSTRAINT fk_placa_vehiculo FOREIGN KEY (placa_vehiculo)
        REFERENCES vehiculo (placa)
);

CREATE TABLE IF NOT EXISTS novedad (
    id_novedad  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_registro INTEGER      NOT NULL,
    fecha       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    descripcion VARCHAR(512) NOT NULL,
    CONSTRAINT fk_id_registro FOREIGN KEY (id_registro)
        REFERENCES registro (id_registro)
        ON DELETE CASCADE
);
