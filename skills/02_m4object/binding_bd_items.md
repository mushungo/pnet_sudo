---
nombre: "binding_bd_items"
version: "1.0.0"
descripcion: "Explica el mecanismo de binding BD de los items de PeopleNet: los campos ID_READ_OBJECT, ID_WRITE_OBJECT, ID_READ_FIELD, ID_WRITE_FIELD, ID_READ_SENTENCE e ID_WRITE_SENTENCE de M4RCH_ITEMS. Aplica a cualquier dominio funcional."
---

## Documentación de la Skill: `binding_bd_items`

### Propósito

Cada item de PeopleNet (`M4RCH_ITEMS`) puede declarar un vínculo directo con la base de datos a través de seis campos de binding. Este mecanismo es **independiente del dominio funcional** del canal — aplica igual a un canal de nómina, de gestión de personas, de configuración o de cualquier otro dominio.

El binding determina:
- **De qué objeto BDL y campo lee** el motor cuando carga los datos del item
- **A qué objeto BDL y campo escribe** el motor cuando persiste el valor calculado del item

---

### Los Seis Campos de Binding

Todos residen en `M4RCH_ITEMS`:

| Campo | Dirección | Descripción |
|---|---|---|
| `ID_READ_OBJECT` | Lectura | Objeto lógico BDL del que lee el item |
| `ID_READ_FIELD` | Lectura | Campo dentro del objeto BDL de lectura |
| `ID_READ_SENTENCE` | Lectura | Sentence APISQL que refina la lectura (puede coexistir con `ID_READ_OBJECT`) |
| `ID_WRITE_OBJECT` | Escritura | Objeto lógico BDL al que escribe el item |
| `ID_WRITE_FIELD` | Escritura | Campo dentro del objeto BDL de escritura |
| `ID_WRITE_SENTENCE` | Escritura | Sentence APISQL que refina la escritura |

---

### Reglas de Precedencia e Interpretación

#### Lectura (`ID_READ_OBJECT` + `ID_READ_FIELD`)
- Si ambos son `NULL`: el item **no lee directamente de BD**. Su valor viene del cálculo LN4, de una herencia o de una asignación explícita en código.
- Si `ID_READ_OBJECT` tiene valor: el motor lee de ese objeto BDL, localizando el campo físico mediante `ID_READ_FIELD`.
- `ID_READ_SENTENCE` y `ID_READ_OBJECT` **pueden coexistir** (~107k casos en BD): `ID_READ_OBJECT` define el BDL base del item; `ID_READ_SENTENCE` refina el SQL de carga con un filtro o join adicional. No son mutuamente excluyentes.
- `ID_READ_SENTENCE` sin `ID_READ_OBJECT` (~736 casos): la lectura se hace completamente vía APISQL de la sentence, sin objeto BDL fijo.

#### Escritura (`ID_WRITE_OBJECT` + `ID_WRITE_FIELD`)
- Si ambos son `NULL`: el item **no persiste su valor en BD**. Es un valor transitorio de cálculo.
- Si `ID_WRITE_OBJECT` tiene valor: el motor, al salvar, escribe el valor del item en ese objeto BDL, en el campo identificado por `ID_WRITE_FIELD`.
- En la práctica, `ID_WRITE_FIELD` siempre acompaña a `ID_WRITE_OBJECT` (solo 8 excepciones en toda la BD).
- `ID_WRITE_SENTENCE` es muy raro (~1.471 items). Ningún concepto de nómina lo usa.

#### Relación con el binding del TI padre
El TI padre (`M4RCH_TIS`) también tiene sus propios `ID_READ_OBJECT` / `ID_WRITE_OBJECT`, que definen el objeto BDL **por defecto para todo el bloque**. Los campos de `M4RCH_ITEMS` actúan como **override individual**:

- Si `M4RCH_ITEMS.ID_READ_OBJECT` = `M4RCH_TIS.ID_READ_OBJECT`: el item lee del mismo objeto que el TI (comportamiento normal).
- Si difieren: el item tiene un **override** — lee de un objeto BDL distinto al del bloque. Hay ~17k items en esta situación.

---

### Distribución en BD (referencia)

| Tipo de item | Total | Con binding (READ o WRITE) |
|---|---|---|
| Method (`ID_ITEM_TYPE=1`) | 50.318 | **0** — los métodos nunca tienen binding directo |
| Property (`ID_ITEM_TYPE=2`) | 70.592 | 11.827 (17%) |
| Block (`ID_ITEM_TYPE=3`) | 112.970 | 112.295 (99%) — casi todos los bloques tienen binding |
| Concept (`ID_ITEM_TYPE=4`) | 3.788 | 951 (25%) |

**Total items con `ID_READ_OBJECT`**: ~123.337  
**Total items con `ID_WRITE_OBJECT`**: ~96.189

---

### Casos de Uso Típicos

#### 1. ¿Este item persiste su valor en BD?
```sql
SELECT
    ID_TI, ID_ITEM,
    ID_WRITE_OBJECT,
    ID_WRITE_FIELD,
    CASE WHEN ID_WRITE_OBJECT IS NOT NULL THEN 'PERSISTE EN BD' ELSE 'TRANSITORIO' END AS persiste
FROM M4RCH_ITEMS
WHERE ID_TI = 'MI_TI' AND ID_ITEM = 'MI_ITEM'
```

#### 2. ¿De dónde lee este item?
```sql
SELECT
    i.ID_TI, i.ID_ITEM,
    i.ID_READ_OBJECT,
    i.ID_READ_FIELD,
    i.ID_READ_SENTENCE,
    o.REAL_NAME AS nombre_objeto_bdl
FROM M4RCH_ITEMS i
LEFT JOIN M4RDC_LOGIC_OBJECT o ON o.ID_TRANS_OBJESP = i.ID_READ_OBJECT
                                OR o.ID_TRANS_OBJENG = i.ID_READ_OBJECT
WHERE i.ID_TI = 'MI_TI' AND i.ID_ITEM = 'MI_ITEM'
```

#### 3. Todos los items de una TI con su binding (lectura y escritura)
```sql
SELECT
    i.ID_ITEM,
    i.ID_ITEM_TYPE,
    i.ID_READ_OBJECT,   i.ID_READ_FIELD,   i.ID_READ_SENTENCE,
    i.ID_WRITE_OBJECT,  i.ID_WRITE_FIELD,  i.ID_WRITE_SENTENCE,
    CASE
        WHEN i.ID_READ_OBJECT  IS NOT NULL THEN 'LEE BDL'
        WHEN i.ID_READ_SENTENCE IS NOT NULL THEN 'LEE SENTENCE'
        ELSE 'SIN LECTURA BD'
    END AS modo_lectura,
    CASE
        WHEN i.ID_WRITE_OBJECT IS NOT NULL THEN 'ESCRIBE BDL'
        ELSE 'NO PERSISTE'
    END AS modo_escritura
FROM M4RCH_ITEMS i
WHERE i.ID_TI = 'MI_TI'
ORDER BY i.ID_ITEM_TYPE, i.ID_ITEM
```

#### 4. Items con override (leen/escriben de un BDL distinto al del TI padre)
```sql
SELECT
    i.ID_ITEM,
    ti.ID_READ_OBJECT  AS ti_read_obj,
    i.ID_READ_OBJECT   AS item_read_obj,
    ti.ID_WRITE_OBJECT AS ti_write_obj,
    i.ID_WRITE_OBJECT  AS item_write_obj
FROM M4RCH_ITEMS i
JOIN M4RCH_TIS ti ON ti.ID_TI = i.ID_TI
WHERE i.ID_TI = 'MI_TI'
  AND (
    (i.ID_READ_OBJECT IS NOT NULL AND i.ID_READ_OBJECT <> COALESCE(ti.ID_READ_OBJECT, ''))
    OR
    (i.ID_WRITE_OBJECT IS NOT NULL AND i.ID_WRITE_OBJECT <> COALESCE(ti.ID_WRITE_OBJECT, ''))
  )
```

---

### Nota sobre `ID_WRITE_OBJECTNEW`

`M4RCH_ITEMS` también tiene un campo `ID_WRITE_OBJECTNEW` (y su par `ID_READ_OBJECT_NEW`). Estos son campos de **override de migración**: permiten redirigir la escritura a un objeto BDL distinto sin modificar `ID_WRITE_OBJECT`. Se usan en ~891 items, todos de infraestructura interna (canales de acumulado, migraciones entre versiones). **Ningún concepto de nómina los usa**. Para análisis funcionales, usar siempre `ID_WRITE_OBJECT` / `ID_READ_OBJECT`.

---

### Relaciones con otras skills

- **`describir_ti_bdl_schema`** — Traza la cadena completa TI → BDL → tablas físicas SQL, incluyendo los overrides de items.
- **`tipos_internos_items`** — El campo `ID_INTERNAL_TYPE` clasifica semánticamente el rol del item (ej. SYS_SENTENCE, DYN_FILTER). Es ortogonal al binding: un item puede tener cualquier tipo interno y también tener o no binding BD.
- **`verificar_acumulacion_concepto`** — Aplica este mecanismo al dominio de nómina: un concepto acumula si y solo si `ID_WRITE_OBJECT IS NOT NULL`.
