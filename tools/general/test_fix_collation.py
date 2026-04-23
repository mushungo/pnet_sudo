"""
test_fix_collation.py
Prueba el script fix_collation_with_indexes.sql contra la base de datos.
Muestra las tablas seleccionadas y los scripts generados (DROP / ALTER / CREATE).
No ejecuta ningún cambio — solo genera y muestra el output.
"""
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection

# ------------------------------------------------------------------
# SQL que selecciona 3 tablas no-M4R con columnas a migrar
# ------------------------------------------------------------------
SQL_TABLAS = """
SELECT TOP 3 t.name AS nombre
FROM sys.tables t
JOIN sys.columns c ON c.object_id = t.object_id
JOIN sys.types   y ON c.user_type_id = y.user_type_id
WHERE y.name IN ('varchar', 'char', 'nvarchar', 'nchar', 'text', 'ntext')
  AND c.collation_name <> 'Modern_Spanish_CI_AS'
  AND t.is_ms_shipped = 0
  AND t.name NOT LIKE 'M4R%'
GROUP BY t.name;
"""

SQL_MIGRATION = """
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
      AND t.name IN ({placeholders})
),
indices_afectados AS (
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
    WHERE i.type > 0
)
SELECT Orden, Script, TipoIndice, EsUnico FROM (
    SELECT 1 AS Orden,
        'DROP INDEX [' + NombreIndice + '] ON [' + Esquema + '].[' + Tabla + '];' COLLATE DATABASE_DEFAULT AS Script,
        TipoIndice, CAST(EsUnico AS VARCHAR(5)) AS EsUnico
    FROM indices_afectados

    UNION ALL

    SELECT 2, AlterScript COLLATE DATABASE_DEFAULT, NULL, NULL
    FROM columnas_a_cambiar

    UNION ALL

    SELECT 3,
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
        END + ';') COLLATE DATABASE_DEFAULT,
        ia.TipoIndice, CAST(ia.EsUnico AS VARCHAR(5))
    FROM indices_afectados ia
) sub
ORDER BY Orden, Script;
"""

LABELS = {1: "DROP  ", 2: "ALTER ", 3: "CREATE"}
SEP = "-" * 80


def main():
    with db_connection() as conn:
        cursor = conn.cursor()

        # 1. Obtener las 3 tablas
        cursor.execute(SQL_TABLAS)
        tablas = [row.nombre for row in cursor.fetchall()]

        if not tablas:
            print("No se encontraron tablas con columnas a migrar (no-M4R).")
            return

        print(SEP)
        print(f"Tablas seleccionadas ({len(tablas)}):")
        for t in tablas:
            print(f"  - {t}")
        print(SEP)

        # 2. Generar scripts de migración para esas tablas
        placeholders = ", ".join(f"'{t}'" for t in tablas)
        sql = SQL_MIGRATION.format(placeholders=placeholders)
        cursor.execute(sql)
        rows = cursor.fetchall()

        if not rows:
            print("No se generaron scripts (puede que las tablas no tengan índices ni columnas pendientes).")
            return

        bloque_actual = None
        for row in rows:
            orden, script, tipo, unico = row.Orden, row.Script, row.TipoIndice, row.EsUnico
            if orden != bloque_actual:
                bloque_actual = orden
                titulos = {1: "BLOQUE 1 — DROP INDEX", 2: "BLOQUE 2 — ALTER COLUMN", 3: "BLOQUE 3 — CREATE INDEX"}
                print(f"\n{'=' * 80}")
                print(f"  {titulos[orden]}")
                print("=" * 80)
            extra = f"  [{tipo}{'  UNIQUE' if unico == '1' else ''}]" if tipo else ""
            print(f"{LABELS[orden]}  {script}{extra}")

        print(f"\n{SEP}")
        drops  = sum(1 for r in rows if r.Orden == 1)
        alters = sum(1 for r in rows if r.Orden == 2)
        creates = sum(1 for r in rows if r.Orden == 3)
        print(f"Resumen: {drops} DROP  |  {alters} ALTER COLUMN  |  {creates} CREATE INDEX")
        print(SEP)


if __name__ == "__main__":
    main()
