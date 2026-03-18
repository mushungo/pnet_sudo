# Proyecto de Introspección de PeopleNet

Este proyecto contiene un conjunto de agentes, herramientas y `skills` de `opencode` diseñados para analizar, documentar y comprender la arquitectura de **Cegid PeopleNet**, una solución de software para la gestión de nóminas en grandes empresas y administraciones públicas. El sistema está capacitado para interactuar directamente con la base de datos de la aplicación, interpretar sus metadatos (RDL) y construir una base de conocimiento sobre su funcionamiento.
Advertir al avezado consultor que ose utilizar esta herramienta que su uso pretende abrirle nuevas metas y ver nuevos horizontes más allá de los límites aun desconocidos.

## Arquitectura de PeopleNet (Descubrimientos Clave)

Nuestra investigación ha revelado que PeopleNet opera bajo un paradigma de **Desarrollo Dirigido por Metadatos (Metadata-Driven Development)**:

- **El Repositorio es la Fuente de Verdad:** No existen scripts `CREATE TABLE` separados. La estructura, lógica, relaciones y tipos de datos se definen como datos en tablas de metadatos especiales.
- **RDL (Repository Definition Language):** Las definiciones en estas tablas de metadatos constituyen un lenguaje propio, el RDL.
- **ram-dl (Herramienta de Traspasos):** Es la herramienta que interpreta el RDL para transportar los objetos y definiciones (metadatos) de la aplicación entre distintos entornos (por ejemplo, desde desarrollo a integración).
- **Lógica de Fallback de Idioma:** La aplicación es multi-idioma. Nuestras herramientas simulan su comportamiento solicitando siempre los campos en español e inglés y usando el inglés como alternativa si el español es nulo.

## Estado Actual del Proyecto y Capacidades

Hemos completado la fase de análisis de la **Base de Datos Lógica (BDL)**, dotando al sistema de las siguientes capacidades:

- **Generación de una Base de Conocimiento:** El sistema puede generar una enciclopedia completa en formato Markdown de todos los componentes de la BDL, incluyendo:
    - **Tablas Lógicas:** Documentación detallada de cada objeto, sus campos y sus relaciones.
    - **Tipos Extendidos:** Documentación de cada tipo de dato, su formato y su lógica de validación.
    - **Funciones Extendidas:** Documentación de las 78 funciones predefinidas (ABS, ADD_DAYS, CONCAT, SUM, TODAY, etc.), sus argumentos, tipos de retorno y documentación detallada con ejemplos.
    - **Módulos de Datos (Case Modules):** Documentación de los 347 módulos que agrupan objetos lógicos y relaciones en dominios funcionales.
- **Consulta y Análisis:** A través de las `skills` desarrolladas, podemos responder a preguntas complejas sobre la BDL, como:
    - ¿Cuál es la estructura de un objeto?
    - ¿Cómo se relaciona un objeto con los demás?
    - ¿Qué validaciones se aplican a un campo?
    - ¿De dónde obtiene un campo sus valores (tablas maestras)?
    - ¿Qué funciones extendidas están disponibles y cómo se usan?
    - ¿Qué objetos y relaciones agrupa un módulo de datos?

## Flujo de Trabajo en una Nueva Sesión

Para retomar el trabajo, sigue estos pasos:

1.  **Instalar Dependencias:**
    - Asegúrate de tener un fichero `.env` con las credenciales de la base de datos (puedes copiarlo desde `.env.example`).
    - Instala todas las dependencias de Python:
      ```bash
      pip install -r requirements.txt
      ```
    - Instala **Engram** (memoria persistente para agentes):
      - Descarga el binario para Windows desde [Engram Releases](https://github.com/Gentleman-Programming/engram/releases).
      - Coloca `engram.exe` en una carpeta incluida en el `PATH` del sistema.
      - Verifica la instalación: `engram --version`

2.  **Iniciar el Entorno (Recomendado):**
    - Usa el script de lanzamiento que inicia automáticamente el servidor Engram y opencode:
      ```bash
      iniciar_contexto_pnet.cmd
      ```
    - Alternativamente, inicia los servicios manualmente:
      ```bash
      # Iniciar el servidor Engram en segundo plano
      start /B engram serve

      # Iniciar opencode
      opencode
      ```

3.  **Cargar Contexto del Proyecto (Recomendado):**
    - Para que el agente `opencode` tenga conocimiento de todos los agentes y `skills` disponibles desde el inicio, ejecuta el siguiente comando:
      ```bash
      python -m tools.general.load_context
      ```

4.  **Construir la Base de Conocimiento (Opcional):**
    - Para que pueda responder preguntas sin consultar constantemente la BD, primero genera la documentación local.
      ```bash
      # Generar documentación de los Tipos Extendidos (pendiente de implementación)
      python -m tools.bdl.build_extended_types_dictionary
      
      # Generar documentación de las Tablas Lógicas (enriquecida)
      python -m tools.bdl.build_bdl_dictionary

      # Generar documentación de las Funciones Extendidas
      python -m tools.bdl.build_extended_functions_dictionary

      # Generar documentación de los Módulos de Datos
      python -m tools.bdl.build_case_modules_dictionary
      ```

5.  **Empezar a Trabajar:**
    - Ya puedes usar las `skills` individuales para hacer preguntas específicas o proponer nuevos objetivos de indagación (como el análisis de `m4objects`).
    - Los agentes usarán automáticamente Engram para persistir y recuperar conocimiento entre sesiones.

## Memoria Persistente (Engram)

El proyecto utiliza [Engram](https://github.com/Gentleman-Programming/engram) como sistema de memoria persistente para los agentes de IA. Engram es un binario de Go que expone herramientas MCP (Model Context Protocol) para guardar, buscar y recuperar observaciones entre sesiones de trabajo.

### Características principales

- **Persistencia entre sesiones:** Los descubrimientos sobre PeopleNet, decisiones de diseño y hallazgos de depuración sobreviven entre sesiones de opencode.
- **Búsqueda full-text (FTS5):** Permite buscar conocimiento previo antes de investigar de cero.
- **Recuperación tras compactación:** Todos los agentes llaman a `mem_context` automáticamente tras un reinicio de contexto.
- **Integración transparente:** Configurado como servidor MCP en `opencode.json`, los agentes acceden a las herramientas de memoria sin configuración adicional.

Para más detalles sobre el protocolo de memoria y las herramientas disponibles, consultar `AGENTS.md`.

## Estructura del Proyecto

La estructura está organizada por módulos funcionales:

```
/
├── agentes/            # Definiciones de los agentes especializados (JSON).
├── docs/               # Documentación generada automáticamente (ignorada por git).
│   ├── 01_bdl/
│   │   ├── case_modules/
│   │   ├── extended_functions/
│   │   ├── extended_types/
│   │   └── logical_tables/
│   └── 02_m4object/
├── modificadores/      # Configuraciones para modificar el comportamiento de los agentes.
├── schemas/            # JSON Schemas para validar la configuración de agentes y modificadores.
├── skills/             # Documentación de las capacidades de las herramientas.
│   ├── 00_general/
│   ├── 01_bdl/
│   └── 02_m4object/
└── tools/              # Scripts de Python que implementan la lógica.
    ├── general/        # Utilidades compartidas (conexión a BD, carga de contexto).
    ├── bdl/            # Herramientas para introspección de la BDL.
    └── m4object/       # Herramientas para introspección de m4objects (en desarrollo).
```
