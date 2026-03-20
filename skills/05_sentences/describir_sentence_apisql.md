---
nombre: "describir_sentence_apisql"
version: "1.0.0"
descripcion: "Obtiene el SQL compilado (APISQL) de una sentence de PeopleNet, junto con el filtro abstracto y los objetos BDL referenciados."
parametros:
  - nombre: "id_sentence"
    tipo: "string"
    descripcion: "El identificador de la sentence. Ej: 'SENT_EMPLOYEES'."
    requerido: true
---

## Documentación de la Skill: `describir_sentence_apisql`

### Propósito
Obtiene el SQL compilado (APISQL) de una sentence de PeopleNet. Complementa la skill `describir_sentence` mostrando el SQL generado internamente por el motor, que usa un dialecto propietario.

### Dialecto APISQL
El APISQL no es SQL estándar. Usa una sintaxis propietaria de PeopleNet:
- `@FIELD = A.COLUMN` — Bindings de SELECT (mapeo campo → columna)
- `&OBJECT` — Referencia a un objeto BDL
- `#FUNC()` — Funciones built-in (#TODAY(), #SUM(), #TRIM())
- `?(type,size,prec)` — Parámetros tipados (1=num, 2=str, 4=date, 5=datetime, 6=long)
- `(+)` — Oracle-style outer join

### Las 4 Capas de SQL en PeopleNet
1. **APISQL (design-time)**: SQL compilado en SENTENCES3 (99.5% de las 15,350 sentences)
2. **SYS_SENTENCE + SYS_PARAM (declarative)**: Loading declarativo — `Load_Blk()` / `Load_Prg()`
3. **DYN_FILTER (runtime)**: Filtros de usuario en tiempo de ejecución
4. **ExecuteSQL() (imperative)**: SQL raw vía TIs contenedor EXE_APISQL

### Tablas Consultadas
- `M4RCH_SENTENCES` — Metadatos de la sentence
- `M4RCH_SENTENCES1` — FILTER (template abstracto)
- `M4RCH_SENTENCES2` — APISQL parcial (FROM clause)
- `M4RCH_SENTENCES3` — APISQL completo (SQL compilado final)
- `M4RCH_SENTENCES4` — APISQL extra (ORDER BY, GROUP BY)
- `M4RCH_SENT_OBJECTS` — Objetos BDL referenciados

### Ejemplo de Uso
```bash
python -m tools.sentences.get_sentence_apisql "SENT_EMPLOYEES"
```

**Resultado esperado:**
```json
{
  "id_sentence": "SENT_EMPLOYEES",
  "is_distinct": false,
  "sent_type": 0,
  "filter_template": "@FIELD1 = A.COL1 AND @FIELD2 = B.COL2",
  "apisql_from": "FROM &EMPLOYEE A LEFT JOIN &DEPARTMENT B ON ...",
  "apisql": "SELECT @EMP_ID = A.ID_EMPLOYEE, @EMP_NAME = A.NAME FROM &EMPLOYEE A WHERE A.STATUS = ?(2,1,0)",
  "apisql_extra": "ORDER BY A.NAME",
  "objects": [
    {"id_object": "EMPLOYEE", "alias": "A", "is_basis": true}
  ]
}
```
