-- MIGRACIÓN 001
-- Corrige constraints incorrectos en tablas rf_* y agrega foto_url
--
-- Problema: el id_unico en rf_* es el identificador propio de cada foto,
-- no una FK al formulario padre. La relación fotos↔formulario es por folio.
--
-- Ejecutar UNA SOLA VEZ en el SQL Editor de Supabase al configurar el proyecto.

-- 1. Eliminar FK incorrectos en tablas de registros fotográficos
ALTER TABLE rf_cantidades     DROP CONSTRAINT IF EXISTS rf_cantidades_id_unico_fkey;
ALTER TABLE rf_reporte_diario DROP CONSTRAINT IF EXISTS rf_reporte_diario_id_unico_fkey;
ALTER TABLE rf_componentes    DROP CONSTRAINT IF EXISTS rf_componentes_id_unico_fkey;

-- 2. Permitir múltiples ítems con el mismo folio en registros_cantidades
--    (el formulario QField genera un id_unico por ítem, no uno por folio)
ALTER TABLE registros_cantidades
    DROP CONSTRAINT IF EXISTS registros_cantidades_folio_key;

-- 3. Agregar columna para URL pública de fotos en Supabase Storage
ALTER TABLE rf_cantidades     ADD COLUMN IF NOT EXISTS foto_url text;
ALTER TABLE rf_componentes    ADD COLUMN IF NOT EXISTS foto_url text;
ALTER TABLE rf_reporte_diario ADD COLUMN IF NOT EXISTS foto_url text;
