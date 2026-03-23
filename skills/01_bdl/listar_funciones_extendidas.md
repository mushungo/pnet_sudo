---
nombre: "listar_funciones_extendidas"
version: "1.0.0"
descripcion: "Lista todas las funciones extendidas disponibles en el repositorio de metadatos de PeopleNet, con tipo de retorno y conteo de argumentos."
parametros: []
herramienta: "tools.bdl.list_extended_functions"
---

## Documentación de la Skill: `listar_funciones_extendidas`

### Propósito
Lista todas las funciones extendidas (Extended Functions) del repositorio. Las funciones extendidas son funciones C++ compiladas que se registran en los metadatos de PeopleNet y se pueden invocar desde LN4 o desde items de un m4object.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta con JOINs**: Ejecuta un SELECT sobre `M4RDC_EXTENDED_FUN` con JOIN a `M4RDC_LU_M4_TYPES` para el nombre del tipo de retorno, y subconsulta de conteo sobre `M4RDC_EXT_FUNC_ARG`.
3. **Resultado JSON**: Devuelve la lista con nombre, tipo de retorno, uso frecuente y conteo de argumentos.

### Ejemplos de Uso

**Listar todas:**
```bash
python -m tools.bdl.list_extended_functions
```

**Resultado esperado:**
```json
{
  "status": "success",
  "count": 80,
  "functions": [
    {
      "id_function": "GET_EMPLOYEE_NAME",
      "name": "Obtener Nombre Empleado",
      "return_type_id": 2,
      "return_type_name": "String",
      "frequent_use": true,
      "arg_count": 1
    }
  ]
}
```
