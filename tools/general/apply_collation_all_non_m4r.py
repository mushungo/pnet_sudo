"""
apply_collation_all_non_m4r.py
Aplica el cambio de collation a Modern_Spanish_CI_AS en TODAS las tablas
que no sean M4R%, gestionando automáticamente el ciclo DROP / ALTER / CREATE
de índices afectados, distinguiendo entre:
  - PRIMARY KEY constraint  → ALTER TABLE DROP/ADD CONSTRAINT ... PRIMARY KEY
  - UNIQUE constraint        → ALTER TABLE DROP/ADD CONSTRAINT ... UNIQUE
  - Índice normal            → DROP INDEX / CREATE INDEX
"""
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection

# ------------------------------------------------------------------
SQL_TABLAS = """
SELECT t.name AS nombre
FROM sys.tables t
JOIN sys.columns c ON c.object_id = t.object_id
JOIN sys.types   y ON c.user_type_id = y.user_type_id
WHERE y.name IN ('varchar', 'char', 'nvarchar', 'nchar', 'text', 'ntext')
  AND c.collation_name <> 'Modern_Spanish_CI_AS'
  AND t.is_ms_shipped = 0
  AND t.name NOT LIKE 'M4R%'
GROUP BY t.name
ORDER BY t.name;
"""

# Genera scripts para indices afectados distinguiendo PKs, UNIQUE constraints e indices normales
SQL_MIGRATION = """
WITH columnas_a_cambiar AS (
    SELECT
        SCHEMA_NAME(t.schema_id) AS Esquema,
        t.name  AS Tabla,
        c.name  AS Columna,
        t.object_id AS tabla_object_id,
        c.column_id,
        ('ALTER TABLE [' + SCHEMA_NAME(t.schema_id) + '].[' + t.name + '] ' +
        'ALTER COLUMN [' + c.name + '] ' +
        UPPER(TYPE_NAME(c.user_type_id)) +
        CASE
            WHEN TYPE_NAME(c.user_type_id) IN ('varchar', 'char', 'varbinary', 'binary')
                THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(c.max_length AS VARCHAR(5)) END + ')'
            WHEN TYPE_NAME(c.user_type_id) IN ('nvarchar', 'nchar')
                THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(c.max_length / 2 AS VARCHAR(5)) END + ')'
            ELSE ''
        END + ' COLLATE Modern_Spanish_CI_AS ' +
        CASE WHEN c.is_nullable = 1 THEN 'NULL' ELSE 'NOT NULL' END + ';') COLLATE DATABASE_DEFAULT AS AlterScript
    FROM sys.columns c
    JOIN sys.tables t ON c.object_id = t.object_id
    JOIN sys.types  y ON c.user_type_id = y.user_type_id
    WHERE y.name IN ('varchar', 'char', 'nvarchar', 'nchar', 'text', 'ntext')
      AND c.collation_name <> 'Modern_Spanish_CI_AS'
      AND t.is_ms_shipped = 0
      AND t.name NOT LIKE 'M4R%'
),
indices_afectados AS (
    SELECT DISTINCT
        i.object_id,
        i.index_id,
        i.name           AS NombreIndice,
        SCHEMA_NAME(t.schema_id) AS Esquema,
        t.name           AS Tabla,
        i.type_desc      AS TipoIndice,
        i.is_unique      AS EsUnico,
        i.is_primary_key AS EsPK,
        i.is_unique_constraint AS EsUniqueConstraint
    FROM sys.index_columns ic
    JOIN sys.indexes i  ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    JOIN sys.tables  t  ON t.object_id = i.object_id
    JOIN columnas_a_cambiar cac
         ON cac.tabla_object_id = ic.object_id AND cac.column_id = ic.column_id
    WHERE i.type > 0
)
SELECT Orden, Script, TipoIndice, EsUnico, EsPK, EsUniqueConstraint FROM (
    -- BLOQUE 1: DROP (distingue constraint vs indice normal)
    SELECT 1 AS Orden,
        CASE
            WHEN ia.EsPK = 1 OR ia.EsUniqueConstraint = 1
                THEN 'ALTER TABLE [' + ia.Esquema + '].[' + ia.Tabla + '] DROP CONSTRAINT [' + ia.NombreIndice COLLATE DATABASE_DEFAULT + '];'
            ELSE
                'DROP INDEX [' + ia.NombreIndice COLLATE DATABASE_DEFAULT + '] ON [' + ia.Esquema + '].[' + ia.Tabla + '];'
        END COLLATE DATABASE_DEFAULT AS Script,
        TipoIndice, EsUnico, EsPK, EsUniqueConstraint
    FROM indices_afectados ia

    UNION ALL

    -- BLOQUE 2: ALTER COLUMN
    SELECT 2, AlterScript COLLATE DATABASE_DEFAULT, NULL, NULL, NULL, NULL
    FROM columnas_a_cambiar

    UNION ALL

    -- BLOQUE 3: CREATE (distingue PK, UNIQUE constraint e indice normal)
    SELECT 3,
        CASE
            -- PRIMARY KEY
            WHEN ia.EsPK = 1
                THEN ('ALTER TABLE [' + ia.Esquema + '].[' + ia.Tabla + '] ADD CONSTRAINT [' + ia.NombreIndice COLLATE DATABASE_DEFAULT + '] PRIMARY KEY ' +
                    ia.TipoIndice + ' (' +
                    STUFF((
                        SELECT ', [' + c.name + ']' + CASE WHEN ic2.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END
                        FROM sys.index_columns ic2
                        JOIN sys.columns c ON ic2.object_id = c.object_id AND ic2.column_id = c.column_id
                        WHERE ic2.object_id = ia.object_id AND ic2.index_id = ia.index_id AND ic2.is_included_column = 0
                        ORDER BY ic2.key_ordinal
                        FOR XML PATH('')
                    ), 1, 2, '') + ');')
            -- UNIQUE CONSTRAINT
            WHEN ia.EsUniqueConstraint = 1
                THEN ('ALTER TABLE [' + ia.Esquema + '].[' + ia.Tabla + '] ADD CONSTRAINT [' + ia.NombreIndice COLLATE DATABASE_DEFAULT + '] UNIQUE ' +
                    ia.TipoIndice + ' (' +
                    STUFF((
                        SELECT ', [' + c.name + ']' + CASE WHEN ic2.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END
                        FROM sys.index_columns ic2
                        JOIN sys.columns c ON ic2.object_id = c.object_id AND ic2.column_id = c.column_id
                        WHERE ic2.object_id = ia.object_id AND ic2.index_id = ia.index_id AND ic2.is_included_column = 0
                        ORDER BY ic2.key_ordinal
                        FOR XML PATH('')
                    ), 1, 2, '') + ');')
            -- INDICE NORMAL
            ELSE
                ('CREATE ' + CASE WHEN ia.EsUnico = 1 THEN 'UNIQUE ' ELSE '' END +
                ia.TipoIndice + ' INDEX [' + ia.NombreIndice COLLATE DATABASE_DEFAULT + '] ON [' + ia.Esquema + '].[' + ia.Tabla + '] (' +
                STUFF((
                    SELECT ', [' + c.name + ']' + CASE WHEN ic2.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END
                    FROM sys.index_columns ic2
                    JOIN sys.columns c ON ic2.object_id = c.object_id AND ic2.column_id = c.column_id
                    WHERE ic2.object_id = ia.object_id AND ic2.index_id = ia.index_id AND ic2.is_included_column = 0
                    ORDER BY ic2.key_ordinal
                    FOR XML PATH('')
                ), 1, 2, '') + ')' +
                CASE
                    WHEN ia.TipoIndice = 'NONCLUSTERED'
                     AND EXISTS (SELECT 1 FROM sys.index_columns ic3
                                 WHERE ic3.object_id = ia.object_id AND ic3.index_id = ia.index_id AND ic3.is_included_column = 1)
                    THEN ' INCLUDE (' +
                         STUFF((SELECT ', [' + c.name + ']'
                                FROM sys.index_columns ic4
                                JOIN sys.columns c ON ic4.object_id = c.object_id AND ic4.column_id = c.column_id
                                WHERE ic4.object_id = ia.object_id AND ic4.index_id = ia.index_id AND ic4.is_included_column = 1
                                FOR XML PATH('')), 1, 2, '') + ')'
                    ELSE ''
                END + ';')
        END COLLATE DATABASE_DEFAULT AS Script,
        ia.TipoIndice, ia.EsUnico, ia.EsPK, ia.EsUniqueConstraint
    FROM indices_afectados ia
) sub
ORDER BY Orden, Script;
"""

SEP = "=" * 80
TITULOS = {1: "BLOQUE 1 — DROP CONSTRAINT/INDEX", 2: "BLOQUE 2 — ALTER COLUMN", 3: "BLOQUE 3 — ADD CONSTRAINT/CREATE INDEX"}
LABELS  = {1: "DROP  ", 2: "ALTER ", 3: "CREATE"}


def run():
    ok  = {1: 0, 2: 0, 3: 0}
    err = {1: [], 2: [], 3: []}
    # Rastrear qué drops tuvieron éxito para solo recrear esos
    drops_ok = set()   # (tabla, nombre_indice)

    with db_connection() as conn:
        conn.autocommit = True
        cursor = conn.cursor()

        # 1. Tablas afectadas
        cursor.execute(SQL_TABLAS)
        tablas = [row.nombre for row in cursor.fetchall()]

        if not tablas:
            print("No hay tablas no-M4R con columnas a migrar. Nada que hacer.")
            return

        print(SEP)
        print(f"Tablas a procesar: {len(tablas)}")
        print(SEP)

        # 2. Generar scripts
        cursor.execute(SQL_MIGRATION)
        rows = cursor.fetchall()

        if not rows:
            print("No se generaron scripts.")
            return

        bloques = {1: [], 2: [], 3: []}
        for row in rows:
            bloques[row.Orden].append(row)

        total = sum(len(v) for v in bloques.values())
        print(f"Scripts generados: {len(bloques[1])} DROP  |  {len(bloques[2])} ALTER  |  {len(bloques[3])} CREATE  (total: {total})\n")

        # 3. BLOQUE 1 — DROP
        print(SEP)
        print(f"  {TITULOS[1]}  ({len(bloques[1])} statements)")
        print(SEP)
        for row in bloques[1]:
            sql = row.Script.rstrip(";").strip()
            # Extraer nombre tabla e indice del script para tracking
            key = row.Script
            try:
                cursor.execute(sql)
                ok[1] += 1
                drops_ok.add(key)
                print(f"  OK   {row.Script}")
            except Exception as e:
                err[1].append((row.Script, str(e)))
                print(f"  ERR  {row.Script}")
                print(f"       {e}")

        # 4. BLOQUE 2 — ALTER
        print(f"\n{SEP}")
        print(f"  {TITULOS[2]}  ({len(bloques[2])} statements)")
        print(SEP)
        for row in bloques[2]:
            sql = row.Script.rstrip(";").strip()
            try:
                cursor.execute(sql)
                ok[2] += 1
                print(f"  OK   {row.Script}")
            except Exception as e:
                err[2].append((row.Script, str(e)))
                print(f"  ERR  {row.Script}")
                print(f"       {e}")

        # 5. BLOQUE 3 — CREATE (solo si el DROP correspondiente tuvo exito)
        print(f"\n{SEP}")
        print(f"  {TITULOS[3]}  ({len(bloques[3])} statements)")
        print(SEP)
        for row in bloques[3]:
            sql = row.Script.rstrip(";").strip()
            try:
                cursor.execute(sql)
                ok[3] += 1
                print(f"  OK   {row.Script}")
            except Exception as e:
                # Ignorar "already exists" — significa que el DROP nunca ocurrio (FK, etc.)
                if "1913" in str(e) or "already exists" in str(e).lower():
                    print(f"  SKIP {row.Script}")
                    print(f"       (indice ya existe — DROP no fue necesario o fallo)")
                else:
                    err[3].append((row.Script, str(e)))
                    print(f"  ERR  {row.Script}")
                    print(f"       {e}")

    # 6. Resumen
    print(f"\n{SEP}")
    print("RESUMEN FINAL")
    print(SEP)
    for orden in [1, 2, 3]:
        print(f"  {TITULOS[orden]}: {ok[orden]} OK  |  {len(err[orden])} errores reales")
    if any(err[o] for o in [1, 2, 3]):
        print("\nERRORES REALES (no 'already exists'):")
        for orden in [1, 2, 3]:
            for stmt, msg in err[orden]:
                print(f"  [{TITULOS[orden]}]")
                print(f"    SQL : {stmt}")
                print(f"    ERR : {msg}")
    print(SEP)


if __name__ == "__main__":
    run()
