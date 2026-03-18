---
# Esta sección (YAML Front Matter) contiene metadata estructurada y validable.
# Define el 'contrato' de la skill.
nombre: "ejemplo_skill"
version: "1.0.0"
descripcion: "Una explicación clara y concisa de lo que hace esta skill."
# Define los parámetros que esta skill espera recibir.
parametros:
  - nombre: "ruta_fichero"
    tipo: "string"
    descripcion: "La ruta absoluta al fichero que se debe analizar."
    requerido: true
  - nombre: "opciones_analisis"
    tipo: "object"
    descripcion: "Un objeto con opciones adicionales para el análisis."
    requerido: false
---

# (Esta sección es Markdown para documentación legible por humanos)

## Documentación de la Skill: `ejemplo_skill`

### Flujo de Trabajo
Esta skill ejecuta los siguientes pasos:
1.  **Validar Parámetros**: Asegura que la `ruta_fichero` proporcionada existe.
2.  **Leer Contenido**: Lee el contenido del fichero en memoria.
3.  **Ejecutar Análisis**: Procesa el contenido para extraer métricas clave.
4.  **Generar Informe**: Crea un informe en formato Markdown con los resultados.

### Ejemplos de Uso
Un agente invocaría esta skill de la siguiente manera, proporcionando los parámetros definidos en el Front Matter:

`usar_skill('ejemplo_skill', { "ruta_fichero": "/ruta/a/mi/codigo.py" })`
