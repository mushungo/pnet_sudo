"""
apply_collation_m4r_notnull.py
Aplica cambio de collation a Modern_Spanish_CI_AS sobre columnas de tablas M4R*
que TODAVÍA tengan collation incorrecto, incluyendo columnas NOT NULL (que el script
original apply_collation_targeted.py omitía por el filtro is_nullable = 1).

Origen del problema:
  - apply_collation_targeted.py solo migró columnas nullable de tablas M4R*.
  - Las columnas NOT NULL (como ID_OBJECT, ID_FIELD en M4RDC_FIELDS / M4RDC_REAL_FIELDS)
    quedaron con el collation antiguo.
  - Cuando PeopleNet hace JOINs entre tablas donde una columna ya fue migrada y otra no,
    SQL Server lanza: "Cannot resolve the collation conflict between
    Modern_Spanish_CI_AS and SQL_Latin1_General_CP1_CS_AS in the equal to operation."

Ciclo por tabla:
  1. DROP  — índices/constraints afectados
  2. ALTER — columnas con collation incorrecto (NULL y NOT NULL)
  3. CREATE — recreación fiel de los índices dropeados
"""
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection

BLOCK_SIZE = 10
SEP = "=" * 80
SEP2 = "-" * 80

# ------------------------------------------------------------------
# SQL 1 — Lista de tablas M4R* afectadas (columnas con collation incorrecto)
# ------------------------------------------------------------------
SQL_TABLAS = """
SELECT DISTINCT t.name AS nombre
FROM sys.columns c
JOIN sys.tables t ON c.object_id = t.object_id
JOIN sys.types  y ON c.user_type_id = y.user_type_id
WHERE y.name IN ('varchar', 'char', 'nvarchar', 'nchar', 'text', 'ntext')
  AND c.collation_name <> 'Modern_Spanish_CI_AS'
  AND t.is_ms_shipped = 0
  AND t.name LIKE 'M4R%'
ORDER BY t.name;
"""

# ------------------------------------------------------------------
# SQL 2 — Scripts DROP / ALTER / CREATE para una lista de tablas
#          SIN filtro is_nullable — incluye NOT NULL y NULL
# ------------------------------------------------------------------
SQL_MIGRATION_TEMPLATE = """
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
      AND t.name IN ({placeholders})
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
SELECT Orden, Tabla, Script, TipoIndice, EsUnico, EsPK, EsUniqueConstraint FROM (
    -- BLOQUE 1: DROP
    SELECT 1 AS Orden, ia.Tabla,
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
    SELECT 2, Tabla, AlterScript COLLATE DATABASE_DEFAULT, NULL, NULL, NULL, NULL
    FROM columnas_a_cambiar

    UNION ALL

    -- BLOQUE 3: CREATE
    SELECT 3, ia.Tabla,
        CASE
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
ORDER BY Tabla, Orden, Script;
"""


def confirmar_bloque(num_bloque, total_bloques, tablas, n_drops, n_alters, n_creates):
    """Muestra el resumen del bloque y pide confirmación. Devuelve 's', 'n' o 'a'."""
    print(f"\n{SEP}")
    print(f"  BLOQUE {num_bloque}/{total_bloques}  ({len(tablas)} tablas)")
    print(SEP2)
    for t in tablas:
        print(f"    {t}")
    print(SEP2)
    print(f"  Operaciones: {n_drops} DROPs | {n_alters} ALTERs | {n_creates} CREATEs")
    print(SEP)
    while True:
        resp = input("  Ejecutar este bloque? [s]í / [n]o (saltar) / [a]bortar todo: ").strip().lower()
        if resp in ("s", "n", "a"):
            return resp
        print("  Respuesta no válida. Escribe s, n o a.")


def procesar_tabla(cursor, tabla, drops, alters, creates):
    """
    Ejecuta DROP -> ALTER -> CREATE para una tabla.
    Si ALTER falla, intenta recrear los índices ya dropeados.
    Devuelve (ok: bool, detalle: str)
    """
    drops_ejecutados = []

    # 1. DROPs
    for sql in drops:
        try:
            cursor.execute(sql.rstrip(";"))
            drops_ejecutados.append(sql)
        except Exception as e:
            msg = str(e)
            if "3701" in msg or "Cannot drop" in msg or "does not exist" in msg.lower():
                pass  # Índice/constraint no existe — ignorar
            else:
                return False, f"DROP falló: {sql}\n    {msg}"

    # 2. ALTERs
    for sql in alters:
        try:
            cursor.execute(sql.rstrip(";"))
        except Exception as e:
            # Intentar recrear índices dropeados antes de salir
            for sql_c in creates:
                try:
                    cursor.execute(sql_c.rstrip(";"))
                except Exception:
                    pass
            return False, f"ALTER falló (índices recreados): {sql}\n    {str(e)}"

    # 3. CREATEs
    errores_create = []
    for sql in creates:
        try:
            cursor.execute(sql.rstrip(";"))
        except Exception as e:
            msg = str(e)
            if "1913" in msg or "already exists" in msg.lower():
                pass  # SKIP silencioso — el DROP no fue necesario
            else:
                errores_create.append(f"{sql}\n    {msg}")

    if errores_create:
        return False, "CREATE(s) fallaron:\n" + "\n".join(errores_create)

    return True, ""


def run(solo_bloque=None, dry_run=False, auto_yes=False):
    """
    solo_bloque: si se indica un número (1-based), solo ejecuta ese bloque.
    dry_run: si True, muestra las operaciones pero NO las ejecuta.
    auto_yes: si True, confirma todos los bloques automáticamente sin preguntar.
    """
    ok_tablas = []
    err_tablas = []
    skip_tablas = []

    with db_connection() as conn:
        conn.autocommit = True
        cursor = conn.cursor()

        # Paso 1 — tablas afectadas
        cursor.execute(SQL_TABLAS)
        tablas = [row.nombre for row in cursor.fetchall()]

        if not tablas:
            print("No hay columnas M4R* que necesiten migración de collation. Nada que hacer.")
            return

        print(SEP)
        print(f"  Tablas M4R* con columnas pendientes de migrar: {len(tablas)}")
        print(SEP)
        for t in tablas:
            print(f"    {t}")

        if dry_run:
            print(f"\n  [DRY RUN] Las tablas anteriores tienen columnas con collation incorrecto.")
            print(f"  Ejecuta sin --dry-run para aplicar los cambios.")
            return

        # Dividir en bloques
        bloques = [tablas[i:i + BLOCK_SIZE] for i in range(0, len(tablas), BLOCK_SIZE)]
        total_bloques = len(bloques)

        if solo_bloque is not None:
            if solo_bloque < 1 or solo_bloque > total_bloques:
                print(f"\n  ERROR: --bloque {solo_bloque} fuera de rango (1-{total_bloques}).")
                return
            print(f"\n  Modo prueba: solo se ejecutará el bloque {solo_bloque}/{total_bloques}.")

        for num_bloque, bloque_tablas in enumerate(bloques, start=1):

            # Paso 2 — obtener scripts para este bloque
            placeholders = ", ".join(["?" for _ in bloque_tablas])
            sql = SQL_MIGRATION_TEMPLATE.replace("{placeholders}", placeholders)
            cursor.execute(sql, bloque_tablas)
            rows = cursor.fetchall()

            # Agrupar por tabla y orden
            por_tabla = {}
            for row in rows:
                t = row.Tabla
                if t not in por_tabla:
                    por_tabla[t] = {1: [], 2: [], 3: []}
                if row.Script not in por_tabla[t][row.Orden]:
                    por_tabla[t][row.Orden].append(row.Script)

            n_drops   = sum(len(v[1]) for v in por_tabla.values())
            n_alters  = sum(len(v[2]) for v in por_tabla.values())
            n_creates = sum(len(v[3]) for v in por_tabla.values())

            # Paso 3 — confirmación
            if solo_bloque is not None and num_bloque != solo_bloque:
                skip_tablas.extend(bloque_tablas)
                continue

            resp = "s" if (solo_bloque == num_bloque or auto_yes) else None
            if resp is None:
                resp = confirmar_bloque(num_bloque, total_bloques, bloque_tablas, n_drops, n_alters, n_creates)
            else:
                print(f"\n{SEP}")
                print(f"  BLOQUE {num_bloque}/{total_bloques}  ({len(bloque_tablas)} tablas)  [AUTO-CONFIRM]")
                print(SEP2)
                for t in bloque_tablas:
                    print(f"    {t}")
                print(SEP2)
                print(f"  Operaciones: {n_drops} DROPs | {n_alters} ALTERs | {n_creates} CREATEs")
                print(SEP)

            if resp == "a":
                print("\n  Ejecución abortada por el usuario.")
                break
            if resp == "n":
                skip_tablas.extend(bloque_tablas)
                print(f"  Bloque {num_bloque} saltado.")
                continue

            # Paso 4 — ejecutar tabla a tabla
            print()
            for tabla in bloque_tablas:
                if tabla not in por_tabla:
                    print(f"  SKIP  {tabla}  (sin operaciones generadas)")
                    skip_tablas.append(tabla)
                    continue

                drops   = por_tabla[tabla][1]
                alters  = por_tabla[tabla][2]
                creates = por_tabla[tabla][3]

                ok, detalle = procesar_tabla(cursor, tabla, drops, alters, creates)
                if ok:
                    ok_tablas.append(tabla)
                    print(f"  OK    {tabla}  ({len(drops)} drops | {len(alters)} alters | {len(creates)} creates)")
                else:
                    err_tablas.append((tabla, detalle))
                    print(f"  ERR   {tabla}")
                    print(f"        {detalle}")

    # Resumen global
    print(f"\n{SEP}")
    print("  RESUMEN GLOBAL")
    print(SEP)
    print(f"  OK     : {len(ok_tablas)} tablas")
    print(f"  ERROR  : {len(err_tablas)} tablas")
    print(f"  SALTAR : {len(skip_tablas)} tablas")

    if err_tablas:
        print(f"\n{SEP2}")
        print("  TABLAS CON ERROR:")
        for tabla, motivo in err_tablas:
            print(f"\n  [{tabla}]")
            for linea in motivo.splitlines():
                print(f"    {linea}")

    if skip_tablas:
        print(f"\n{SEP2}")
        print("  TABLAS SALTADAS:")
        for t in skip_tablas:
            print(f"    {t}")

    print(SEP)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Migración de collation a Modern_Spanish_CI_AS en tablas M4R* — columnas NOT NULL incluidas."
    )
    parser.add_argument("--bloque", type=int, default=None,
                        help="Ejecutar solo el bloque N (1-based). Útil para pruebas.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo mostrar qué tablas tienen el problema, sin ejecutar cambios.")
    parser.add_argument("--yes", action="store_true",
                        help="Confirmar todos los bloques automáticamente sin preguntar.")
    args = parser.parse_args()
    run(solo_bloque=args.bloque, dry_run=args.dry_run, auto_yes=args.yes)
