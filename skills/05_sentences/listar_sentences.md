---
nombre: "listar_sentences"
version: "1.0.0"
descripcion: "Lista todas las sentences (definiciones de acceso a datos SQL-like) del repositorio de PeopleNet, con filtros opcionales por tipo o búsqueda."
parametros:
  - nombre: "type"
    tipo: "integer"
    descripcion: "Filtrar por tipo de sentence (ID_SENT_TYPE). Ej: 1, 2, 3."
    requerido: false
  - nombre: "search"
    tipo: "string"
    descripcion: "Texto libre para buscar en ID_SENTENCE."
    requerido: false
---

## Documentación de la Skill: `listar_sentences`

### Propósito
Lista todas las sentences del repositorio de metadatos. Cada sentence define cómo un TI (Table Instance) carga datos: qué objetos BDL consulta, con qué JOINs, filtros y ordenación. Son el equivalente a un visual SQL query builder almacenado como metadatos.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta con JOINs**: Ejecuta un query que une SENTENCES con SENT_OBJECTS, SENT_OBJ_REL y SENT_ADD_FLD para obtener conteos resumen.
3. **Filtrado Opcional**: Permite filtrar por `--type` (ID_SENT_TYPE) o `--search` (texto en ID_SENTENCE).
4. **Resultado JSON**: Devuelve la lista con total, tipo, conteo de objetos, joins y campos de filtro.

### Ejemplos de Uso

**Listar todas:**
```bash
python -m tools.sentences.list_sentences
```

**Filtrar por tipo:**
```bash
python -m tools.sentences.list_sentences --type 1
```

**Buscar:**
```bash
python -m tools.sentences.list_sentences --search "EMPLOYEE"
```
