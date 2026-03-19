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

Hemos completado el análisis de múltiples capas del repositorio de metadatos, dotando al sistema de las siguientes capacidades:

### Base de Datos Lógica (BDL)

- **Tablas Lógicas (3,275 objetos):** Documentación detallada de cada objeto, sus campos, tipos, relaciones padre/hijo y configuración de seguridad.
- **Tipos Extendidos:** Documentación de cada tipo de dato personalizado, su formato base, precisión, escala, cifrado y funciones de validación/default asociadas.
- **Funciones Extendidas (78 funciones):** Documentación de funciones predefinidas (ABS, ADD_DAYS, CONCAT, SUM, TODAY, etc.), sus argumentos, tipos de retorno y documentación detallada con ejemplos.
- **Módulos de Datos (347 módulos):** Documentación de los módulos que agrupan objetos lógicos y relaciones en dominios funcionales.
- **Vistas SQL (112 vistas):** Código SQL completo de cada vista definida en el repositorio, con metadatos de creación y modificación.
- **Índices Lógicos (326 índices):** Documentación de índices con sus columnas, unicidad y agrupación por objeto lógico.

### Funciones LN4

- **Funciones del Motor LN4 (301 funciones):** Documentación completa de las funciones del motor de cálculo de PeopleNet, organizadas en 21 grupos funcionales (cadenas, conversión, matemáticas, fecha/hora, moneda, archivos, BDL, Meta4Objects, nómina, etc.), incluyendo argumentos con tipo, posición y opcionalidad.

### Seguridad

- **Roles RSM (50 roles):** Documentación de los roles de seguridad del repositorio, incluyendo permisos a nivel de objeto (SELECT, INSERT, UPDATE, DELETE) y permisos a nivel de campo (READ, WRITE), con jerarquía de roles padre/hijo.

### Transporte RAMDL

- **Objetos RAMDL (131 objetos):** Documentación de los objetos registrados en el sistema de transporte de metadatos, con rangos de versiones (VER_LOWEST/VER_HIGHEST) y las 24 versiones registradas del repositorio.

### M4Objects (Canales)

- **M4Objects (~6,386 canales):** Introspección completa de la capa funcional de PeopleNet. Cada canal (m4object) se documenta con su jerarquía: herencia entre canales, nodos, TIs (Technical Instances — entidad pivotal con objetos BDL propios de lectura/escritura), items (campos/métodos vinculados a la BDL), y reglas de negocio en LN4. Soporta filtros por categoría y búsqueda por texto.

### Consulta y Análisis

A través de las `skills` desarrolladas, podemos responder a preguntas complejas como:

- ¿Cuál es la estructura de un objeto y cómo se relaciona con los demás?
- ¿Qué validaciones se aplican a un campo? ¿De dónde obtiene sus valores?
- ¿Qué funciones extendidas y LN4 están disponibles y cómo se usan?
- ¿Qué objetos y relaciones agrupa un módulo de datos?
- ¿Cuál es el código SQL de una vista del repositorio?
- ¿Qué permisos tiene un rol de seguridad sobre los objetos?
- ¿Qué índices están definidos para un objeto lógico?
- ¿Qué versiones de transporte existen para un objeto RAMDL?
- ¿Cuál es la estructura jerárquica de un m4object (canal)?
- ¿Qué nodos y TIs tiene un canal y a qué objetos BDL apuntan?
- ¿Cuántas reglas de negocio tiene un canal?
- ¿Qué canales pertenecen a una categoría funcional (ej. PAYROLL)?

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
    - Para que pueda responder preguntas sin consultar constantemente la BD, genera la documentación local:
      ```bash
      # BDL: Tablas Lógicas
      python -m tools.bdl.build_bdl_dictionary

      # BDL: Tipos Extendidos
      python -m tools.bdl.build_extended_types_dictionary

      # BDL: Funciones Extendidas
      python -m tools.bdl.build_extended_functions_dictionary

      # BDL: Módulos de Datos (Case Modules)
      python -m tools.bdl.build_case_modules_dictionary

      # BDL: Vistas SQL
      python -m tools.bdl.build_views_dictionary

      # BDL: Índices Lógicos
      python -m tools.bdl.build_indexes_dictionary

      # LN4: Funciones del Motor
      python -m tools.bdl.build_ln4_dictionary

      # Seguridad: Roles RSM
      python -m tools.bdl.build_rsm_dictionary

      # Transporte: Objetos RAMDL
      python -m tools.bdl.build_ramdl_dictionary

      # M4Objects: Canales
      python -m tools.m4object.build_m4object_dictionary
      ```

5.  **Empezar a Trabajar:**
    - Ya puedes usar las `skills` individuales para hacer preguntas específicas o proponer nuevos objetivos de indagación.
    - Los agentes usarán automáticamente Engram para persistir y recuperar conocimiento entre sesiones.

## Herramientas Disponibles

### Herramientas de Consulta (`tools/bdl/`)

| Herramienta | Descripción |
|---|---|
| `get_bdl_object.py` | Obtiene la estructura completa de un objeto lógico (campos, tipos, relaciones) |
| `list_bdl_objects.py` | Lista todos los objetos lógicos del repositorio |
| `find_bdl_usages.py` | Encuentra dónde se usa un objeto/campo en m4objects y nodos |
| `find_bdl_lookup.py` | Encuentra tablas maestras (lookups) asociadas a un campo |
| `get_bdl_relations.py` | Obtiene las relaciones padre/hijo de un objeto |
| `get_bdl_extended_type_details.py` | Obtiene detalles de un tipo extendido |
| `get_extended_function.py` | Obtiene detalles de una función extendida |
| `list_extended_functions.py` | Lista todas las funciones extendidas |
| `get_case_module.py` | Obtiene detalles de un módulo de datos |
| `list_case_modules.py` | Lista todos los módulos de datos |
| `get_view.py` | Obtiene una vista SQL con su código y metadatos |
| `list_views.py` | Lista todas las vistas SQL del repositorio |
| `get_ln4_function.py` | Obtiene una función LN4 con argumentos, grupo y documentación |
| `list_ln4_functions.py` | Lista todas las funciones LN4 (soporta filtro por grupo) |
| `get_rsm_role.py` | Obtiene un rol RSM con permisos de objeto y campo |
| `list_rsm_roles.py` | Lista todos los roles RSM con conteo de permisos |
| `get_index.py` | Obtiene un índice lógico con sus columnas |
| `list_indexes.py` | Lista todos los índices lógicos (soporta filtro por objeto) |
| `get_ramdl_object.py` | Obtiene un objeto RAMDL con sus entradas de versión |
| `list_ramdl_objects.py` | Lista todos los objetos RAMDL (soporta flag `--versions`) |

### Herramientas de Consulta (`tools/m4object/`)

| Herramienta | Descripción |
|---|---|
| `get_m4object.py` | Obtiene la estructura jerárquica completa de un canal (T3→Nodos→TI→Items, reglas) |
| `list_m4objects.py` | Lista todos los m4objects con categoría, stream type y conteo de nodos |

### Generadores de Diccionario (`tools/bdl/`)

| Generador | Destino | Contenido |
|---|---|---|
| `build_bdl_dictionary.py` | `docs/01_bdl/logical_tables/` | 3,275 tablas lógicas |
| `build_extended_types_dictionary.py` | `docs/01_bdl/extended_types/` | Tipos extendidos |
| `build_extended_functions_dictionary.py` | `docs/01_bdl/extended_functions/` | 78 funciones extendidas |
| `build_case_modules_dictionary.py` | `docs/01_bdl/case_modules/` | 347 módulos de datos |
| `build_views_dictionary.py` | `docs/01_bdl/views/` | 112 vistas SQL |
| `build_indexes_dictionary.py` | `docs/01_bdl/indexes/` | 326 índices lógicos |
| `build_ln4_dictionary.py` | `docs/02_ln4/functions/` | 301 funciones LN4 |
| `build_rsm_dictionary.py` | `docs/03_security/rsm_roles/` | 50 roles de seguridad |
| `build_ramdl_dictionary.py` | `docs/04_ramdl/objects/` | 131 objetos RAMDL |

### Generadores de Diccionario (`tools/m4object/`)

| Generador | Destino | Contenido |
|---|---|---|
| `build_m4object_dictionary.py` | `docs/02_m4object/channels/` | ~6,386 canales (m4objects) |

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
│   │   ├── case_modules/       # 347 módulos de datos
│   │   ├── extended_functions/ # 78 funciones extendidas
│   │   ├── extended_types/     # Tipos extendidos
│   │   ├── indexes/            # 326 índices lógicos
│   │   ├── logical_tables/     # 3,275 tablas lógicas
│   │   └── views/              # 112 vistas SQL
│   ├── 02_ln4/
│   │   └── functions/          # 301 funciones LN4
│   ├── 02_m4object/
│   │   └── channels/           # ~6,386 canales (m4objects)
│   ├── 03_security/
│   │   └── rsm_roles/          # 50 roles de seguridad
│   └── 04_ramdl/
│       └── objects/            # 131 objetos RAMDL
├── modificadores/      # Configuraciones para modificar el comportamiento de los agentes.
├── schemas/            # JSON Schemas para validar la configuración de agentes y modificadores.
├── skills/             # Documentación de las capacidades de las herramientas (SDD).
│   ├── 00_general/
│   ├── 01_bdl/         # Skills para BDL, vistas e índices
│   ├── 02_m4object/    # Skills para m4objects y funciones LN4
│   ├── 03_security/    # Skills para roles RSM
│   └── 04_ramdl/       # Skills para objetos RAMDL
└── tools/              # Scripts de Python que implementan la lógica.
    ├── general/        # Utilidades compartidas (conexión a BD, carga de contexto).
    ├── bdl/            # Herramientas para introspección de la BDL, LN4, seguridad y RAMDL.
    └── m4object/       # Herramientas para introspección de m4objects (canales).
```
