-- Script para crear tablas en PostgreSQL
-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    correo_electronico VARCHAR(255) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL
);

-- Tabla de tareas
CREATE TABLE IF NOT EXISTS tareas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(100) NOT NULL,
    descripcion TEXT,
    fecha_vencimiento DATE,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('Pendiente', 'En progreso', 'Completada')),
    id_usuario INTEGER NOT NULL,
    id_personaje INTEGER,  -- ID del personaje de Rick and Morty
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Datos de prueba
INSERT INTO usuarios (correo_electronico, contrasena) VALUES 
('demo@ejemplo.com', '$2b$12$EjemploHashParaContrasena');  -- Hash de 'password123', genera uno real con werkzeug

INSERT INTO tareas (titulo, descripcion, fecha_vencimiento, estado, id_usuario, id_personaje) VALUES 
('Tarea Demo', 'Descripción de prueba', '2025-09-01', 'Pendiente', 1, 1);  -- Asume usuario id 1 y Rick id 1