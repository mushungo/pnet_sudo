-- =============================================================================
-- fix_collation_with_indexes.sql
-- Migra collation de columnas de texto a Modern_Spanish_CI_AS,
-- dropeando y recreando los índices afectados.
--
-- Uso:
--   1. Ajusta el TOP y los filtros en @tablas según el scope deseado.
--   2. Ejecuta el script → obtienes filas con columna Script (ordenadas 1→2→3).
--   3. Copia el contenido de Script y ejecútalo como migración.
-- =============================================================================

-- ----------------------------------------------------------------
-- Selecciona 3 tablas de prueba que NO sean M4R y tengan columnas
-- con collation distinto a Modern_Spanish_CI_AS
-- (quita el TOP 3 y el NOT LIKE para ejecutar en todo el esquema)
-- ----------------------------------------------------------------
DECLARE @tablas TABLE (nombre SYSNAME);

INSERT INTO @tablas
SELECT TOP 3 t.name
FROM sys.tables t
JOIN sys.columns c ON c.object_id = t.object_id
JOIN sys.types   y ON c.user_type_id = y.user_type_id
WHERE y.name IN ('varchar', 'char', 'nvarchar', 'nchar', 'text', 'ntext')
  AND c.collation_name <> 'Modern_Spanish_CI_AS'
  AND t.is_ms_shipped = 0
  AND t.name NOT LIKE 'M4R%'
GROUP BY t.name;

-- Ver qué tablas se seleccionaron
SELECT * FROM @tablas;

-- ================================================================
WITH columnas_a_cambiar AS (
    SELECT
        SCHEMA_NAME(t.schema_id) AS Esquema,
        t.name  AS Tabla,
        c.name  AS Columna,
        t.object_id AS tabla_object_id,
        c.column_id,
        'ALTER TABLE [' + SCHEMA_NAME(t.schema_id) + '].[' + t.name + '] ' +
        'ALTER COLUMN [' + c.name + '] ' +
        UPPER(TYPE_NAME(c.user_type_id)) +
        CASE
            WHEN TYPE_NAME(c.user_type_id) IN ('varchar', 'char', 'varbinary', 'binary')
                THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(c.max_length AS VARCHAR(5)) END + ')'
            WHEN TYPE_NAME(c.user_type_id) IN ('nvarchar', 'nchar')
                THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(c.max_length / 2 AS VARCHAR(5)) END + ')'
            ELSE ''
        END + ' COLLATE Modern_Spanish_CI_AS ' +
        CASE WHEN c.is_nullable = 1 THEN 'NULL' ELSE 'NOT NULL' END + ';' AS AlterScript
    FROM sys.columns c
    JOIN sys.tables t ON c.object_id = t.object_id
    JOIN sys.types  y ON c.user_type_id = y.user_type_id
    WHERE y.name IN ('varchar', 'char', 'nvarchar', 'nchar', 'text', 'ntext')
      AND c.collation_name <> 'Modern_Spanish_CI_AS'
      AND t.is_ms_shipped = 0
      AND t.name IN (SELECT nombre FROM @tablas)
),
indices_afectados AS (
    -- Índices que contienen (como key column o INCLUDE) alguna columna a cambiar
    SELECT DISTINCT
        i.object_id,
        i.index_id,
        i.name       AS NombreIndice,
        SCHEMA_NAME(t.schema_id) AS Esquema,
        t.name       AS Tabla,
        i.type_desc  AS TipoIndice,
        i.is_unique  AS EsUnico
    FROM sys.index_columns ic
    JOIN sys.indexes i  ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    JOIN sys.tables  t  ON t.object_id = i.object_id
    JOIN columnas_a_cambiar cac
         ON cac.tabla_object_id = ic.object_id AND cac.column_id = ic.column_id
    WHERE i.type > 0   -- Excluir heap
)

SELECT Orden, Script, TipoIndice, EsUnico FROM (
    -- ----------------------------------------------------------------
    -- BLOQUE 1 — DROP INDEX
    -- ----------------------------------------------------------------
    SELECT
        1 AS Orden,
        'DROP INDEX [' + NombreIndice + '] ON [' + Esquema + '].[' + Tabla + '];' COLLATE DATABASE_DEFAULT AS Script,
        TipoIndice,
        EsUnico
    FROM indices_afectados

    UNION ALL

    -- ----------------------------------------------------------------
    -- BLOQUE 2 — ALTER COLUMN (cambio de collation)
    -- ----------------------------------------------------------------
    SELECT
        2 AS Orden,
        AlterScript COLLATE DATABASE_DEFAULT AS Script,
        NULL AS TipoIndice,
        NULL AS EsUnico
    FROM columnas_a_cambiar

    UNION ALL

    -- ----------------------------------------------------------------
    -- BLOQUE 3 — CREATE INDEX (recrear índices dropeados)
    -- ----------------------------------------------------------------
    SELECT
        3 AS Orden,
        ('CREATE ' +
        CASE WHEN ia.EsUnico = 1 THEN 'UNIQUE ' ELSE '' END +
        ia.TipoIndice + ' INDEX [' + ia.NombreIndice COLLATE DATABASE_DEFAULT + '] ON ['
            + ia.Esquema + '].[' + ia.Tabla + '] (' +
        STUFF((
            SELECT ', [' + c.name + ']' +
                   CASE WHEN ic2.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END
            FROM sys.index_columns ic2
            JOIN sys.columns c ON ic2.object_id = c.object_id AND ic2.column_id = c.column_id
            WHERE ic2.object_id = ia.object_id
              AND ic2.index_id  = ia.index_id
              AND ic2.is_included_column = 0
            ORDER BY ic2.key_ordinal
            FOR XML PATH('')
        ), 1, 2, '') + ')' +
        CASE
            WHEN ia.TipoIndice = 'NONCLUSTERED'
             AND EXISTS (
                 SELECT 1 FROM sys.index_columns ic3
                 WHERE ic3.object_id = ia.object_id
                   AND ic3.index_id  = ia.index_id
                   AND ic3.is_included_column = 1
             )
            THEN ' INCLUDE (' +
                 STUFF((
                     SELECT ', [' + c.name + ']'
                     FROM sys.index_columns ic4
                     JOIN sys.columns c ON ic4.object_id = c.object_id AND ic4.column_id = c.column_id
                     WHERE ic4.object_id = ia.object_id
                       AND ic4.index_id  = ia.index_id
                       AND ic4.is_included_column = 1
                     FOR XML PATH('')
                 ), 1, 2, '') + ')'
            ELSE ''
        END + ';') COLLATE DATABASE_DEFAULT AS Script,
        ia.TipoIndice,
        ia.EsUnico
    FROM indices_afectados ia
) sub
ORDER BY Orden, Script;
