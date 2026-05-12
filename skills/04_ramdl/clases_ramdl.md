---
nombre: "clases_ramdl"
version: "1.0.0"
descripcion: "Referencia completa del modelo de clases, subclases y tablas físicas del sistema de transporte RAMDL de PeopleNet. Documenta qué tablas se mueven al transportar cada tipo de objeto."
herramienta: null
---

# Skill: `clases_ramdl` — Modelo de Clases y Transporte RAMDL

## Propósito

Esta skill es la **referencia estática** del modelo de clases de RAMDL. La información proviene del repositorio `RamDl.mdb` (herramienta cliente RAM-DL) y **no está disponible en la base de datos SQL Server** del entorno PeopleNet.

Usar esta skill para responder preguntas como:
- "¿Qué tablas físicas se transportan cuando se mueve un ITEM?"
- "¿Qué tablas componen un NODE STRUCTURE en RAMDL?"
- "¿Cuál es la diferencia entre transportar una clase y una subclase?"

---

## Arquitectura del Modelo de Clases

RAMDL organiza los objetos transportables en tres niveles:

```
CLASE (M4RDC_CLASSES)
├── Define la unidad de transporte completa de un objeto lógico
├── ID_HEAD_OBJECT → tabla principal que identifica el objeto (ej: M4RCH_TIS para NODE STRUCTURE)
├── CLASS MEMBERS (M4RDC_CLASS_MEMBER) → lista de TODAS las tablas físicas que componen la clase
│     Al transportar la clase, RAMDL mueve registros de TODAS estas tablas
└── SUBCLASES (M4RDC_SUBCLASSES) → subelementos del objeto principal
      ID_HEAD_OBJECT → tabla que identifica el subelemento (ej: M4RCH_ITEMS para ITEM)
      SUBCLASS MEMBERS (M4RDC_SUBCLASS_MBR) → tablas físicas propias de ese subelemento
```

### Relación con CCT

Cuando un **Control de Cambio (CCT)** marca un objeto para transporte:

1. RAMDL identifica la **clase o subclase** del objeto por su `ID_HEAD_OBJECT`
2. Lee `M4RDC_CLASS_MEMBER` o `M4RDC_SUBCLASS_MBR` para obtener la lista de tablas físicas
3. Mueve los registros de **todas** esas tablas que corresponden al objeto en cuestión

**Ejemplo práctico — transportar un ITEM de una TI:**

> Transportar el ITEM `SALARY` de la TI `EMPLOYEE` significa mover los registros de `M4RCH_ITEMS`, `M4RCH_ITEM_ARGS`, `M4RCH_RULES`, `M4RCH_TOTALS`, `M4RCH_TAGS`, `M4RCH_CONCEPTS`, `M4RCH_ITEM_PI`, y ~60 tablas más — todas con la clave de ese ITEM específico.

**Ejemplo práctico — transportar un NODE STRUCTURE (TI completa):**

> Transportar la TI `EMPLOYEE` significa mover `M4RCH_TIS`, todos sus ITEMs (`M4RCH_ITEMS`, `M4RCH_ITEMS1`), todas sus reglas, totales, conceptos, dependencias, alias, herencia (`M4RCH_TIS_INHERIT`), y ~52 tablas en total.

### Nota importante sobre versiones

Muchas clases tienen múltiples rangos de versión (`VER_LOWEST`–`VER_HIGHEST`). Para instalaciones modernas (v8.x / v9.x), el rango activo es `60250–99999`. Las entradas con rango `30000–60200` corresponden a estructuras legacy de versiones anteriores. Las filas con `IS_VISIBLE=False` son clases internas que RAMDL usa pero que **no aparecen en la interfaz de usuario** de la herramienta de traspasos.

---

## Clases Principales (IS_VISIBLE=True, versión actual)

Las clases más relevantes para el trabajo diario, con sus tablas físicas completas según `M4RDC_CLASS_MEMBER`:

### NODE STRUCTURE
- **Head object**: `M4RCH_TIS`
- **Auditoría CCT**: Sí
- **Descripción**: La estructura completa de una Node Structure (TI) incluyendo todos sus ítems, reglas, totales, conceptos, dependencias y herencia.
- **Tablas físicas** (52 entradas):
  `M4RAU_PAR_AUDT_LOB`, `M4RCH_CHANNEL_DEP` (×2), `M4RCH_CONCEPT_NODE`, `M4RCH_CONCEPTS` (×3), `M4RCH_CONCEPTS_OWR`, `M4RCH_CONCEPTS_SLICE_MODE`, `M4RCH_EXTERNAL_DEP` (×2), `M4RCH_INTERNAL_DEP` (×2), `M4RCH_ITEM_ARGS`, `M4RCH_ITEM_PI`, `M4RCH_ITEMS`, `M4RCH_ITEMS_HAVING`, `M4RCH_ITEMS_OWR`, `M4RCH_ITEMS1`, `M4RCH_LU_EXE_GROUP`, `M4RCH_QRY_LETR_DEP`, `M4RCH_RULE_SENTENC` (×2), `M4RCH_RULES` (×2), `M4RCH_RULES1` (×2), `M4RCH_RULES2` (×2), `M4RCH_RULES3` (×2), `M4RCH_RULESCOM1` (×2), `M4RCH_TAGS` (×2), `M4RCH_TI_ALIAS`, `M4RCH_TI_CONN_ITM` (×2), `M4RCH_TI_FILTERS`, `M4RCH_TI_MASK`, `M4RCH_TI_MD_VER`, `M4RCH_TI_T3_ALIAS`, `M4RCH_TIS`, `M4RCH_TIS_INHERIT`, `M4RCH_TIS1`, `M4RCH_TOTAL_OPP`, `M4RCH_TOTAL_REF` (×2), `M4RCH_TOTAL_TAGS`, `M4RCH_TOTALS` (×2), `M4RXM_ITEM_MAP`

### META4OBJECT
- **Head object**: `M4RCH_T3S`
- **Auditoría CCT**: Sí
- **Descripción**: El Meta4Object completo (canal T3) con todos sus nodos, conectores, filtros, índices, presentaciones vinculadas, herencia y configuración payroll.
- **Tablas físicas** (88 entradas, selección):
  `M4RCH_ALIAS_RES` (×2), `M4RCH_BO_MET_ARG`, `M4RCH_BO_METHOD`, `M4RCH_BO_SERVICE`, `M4RCH_CONCEPT_NODE`, `M4RCH_CONCTOR_ARG` (×2), `M4RCH_CONCTOR_ITEM` (×2), `M4RCH_CONCTOR_PAR`, `M4RCH_CONNECTORS` (×4), `M4RCH_DISABLEDITEM`, `M4RCH_FILTER_MASK`, `M4RCH_FILTER_PRED`, `M4RCH_FILTERS` (×2), `M4RCH_INDEX` (×2), `M4RCH_INDEX_ITEM` (×2), `M4RCH_ITEM_CSDESC`, `M4RCH_ITEM_MASK`, `M4RCH_MD_VERSION`, `M4RCH_NODE_FILTER`, `M4RCH_NODE_MASK` (×2), `M4RCH_NODE_MIG`, `M4RCH_NODES`, `M4RCH_NODES1`, `M4RCH_OVERWRITE_NO`, `M4RCH_PAYROLL_ITEM`, `M4RCH_PI_OWR`, `M4RCH_PI_TAGS` (×2), `M4RCH_PICOMPONENTS` (×2), `M4RCH_QUERY_USER`, `M4RCH_T3_ALIAS_RES` (×2), `M4RCH_T3_CONN_ITEM` (×2), `M4RCH_T3_CONNTORS` (×2), `M4RCH_T3_INHERIT`, `M4RCH_T3_MIG`, `M4RCH_T3_SWITCHES`, `M4RCH_T3S` (×8), `M4RFE_NODE_PROPS`, `M4RFE_PAT_REL`, `M4RPM_PAYROLL_MENU` (×2), `M4RPM_PAYROLL_T3S` (×2), `M4RPT_ITEM_GRP_BLK`, `M4RPT_ITEM_PRESENT`, `M4RPT_ITM_CUST_EVN`, `M4RPT_NDE_CST_EVNT`, `M4RPT_NDE_GRP_BLKS`, `M4RPT_NODE_PRESENT`, `M4RPT_T3_GRP_BLKS`, `M4RPT_T3_PRESENT`, `M4RPT_VIRTUAL_ITEM`, `M4RPT_VITM_CST_EVN`, `M4RPT_VITM_GRP_BLK`, `M4RRP_NODE_GROUPS`, `M4RRP_NODES_IN_GRP`, `M4RRP_PUB_QUERY`, `M4RRP_VISIBLE_NODE`, `M4RWP_NDS_AC_READ`, `M4RWP_NODES_AC_CLC` (×2), `M4RWP_NODES_CALC` (×2), `M4RWP_NODES_CALC_O` (×2), `M4RWP_NODES_FILTER` (×2), `M4RWP_OUTPUT_REP`, `M4RXM_ITEM_MAP` (×2), `M4RXM_M4OBJECT_M1` (×2), `M4RXM_M4OBJECT_M2` (×2), `M4RXM_M4OBJECT_MAP` (×2), `M4RXM_NODE_MAP` (×2), `SPR_DIN_OBJECTS`

### BUSINESS PROCESS
- **Head object**: `M4RBP_DEF`
- **Auditoría CCT**: Sí
- **Tablas físicas** (19 entradas):
  `M4RBP__PAR_DINAMIC`, `M4RBP_CODE`, `M4RBP_CODE_ALIAS`, `M4RBP_CODE1`, `M4RBP_DEF`, `M4RBP_DEF1`, `M4RBP_EXE_CODE`, `M4RBP_EXE_CODE1`, `M4RBP_GROUPS`, `M4RBP_PAR_DEF`, `M4RBP_PAR_DEF1`, `M4RBP_PARAM_DEF`, `M4RBP_PARAM_DEF1`, `M4RBP_PARAM_DEFA1`, `M4RBP_PARAM_DEFAUL`, `M4RBP_PARAM_FLOW`, `M4RBP_ROLE_EXCEPT`, `M4RBP_STRUCT`, `M4RCH_TASK_PRESENTATION`

### PRESENTATION
- **Head object**: `M4RPT_PRESENTATION`
- **Auditoría CCT**: Sí
- **Tablas físicas** (22 entradas):
  `M4RCH_MD_VERSION`, `M4RCH_PRES_MENU`, `M4RCH_TASK_PRESENTATION`, `M4ROBOT_LOG`, `M4RPT_DOCU_PRES`, `M4RPT_PRES_INHERIT`, `M4RPT_PRES_STYLE`, `M4RPT_PRESENT_PKG`, `M4RPT_PRESENT_PKG1`, `M4RPT_PRESENT_PKG2`, `M4RPT_PRESENT_PKG3`, `M4RPT_PRESENT_PKG4`, `M4RPT_PRESENT_PKG5`, `M4RPT_PRESENT_PKG6`, `M4RPT_PRESENT_PKG7`, `M4RPT_PRESENT_PKG8`, `M4RPT_PRESENT_USE`, `M4RPT_PRESENT_USE1`, `M4RPT_PRESENT_USE2`, `M4RPT_PRESENTATION`, `M4RPT_UNIT_GROUP`, `SPR_DIN_PRESENTS`

### MENU OPTION
- **Head object**: `M4RMN_OPTIONS`
- **Auditoría CCT**: Sí
- **Tablas físicas** (5 entradas):
  `M4RCH_PRES_MENU`, `M4RMN_ARGUMENTS`, `M4RMN_OPTIONS`, `M4RMN_OPTIONS1`, `M4RMN_TREE`

### SENTENCE
- **Head object**: `M4RCH_SENTENCES`
- **Auditoría CCT**: Sí
- **Tablas físicas** (19 entradas):
  `M4RCH_FILTER_PRED` (×2), `M4RCH_SENT_ADD_FLD`, `M4RCH_SENT_CALCULU`, `M4RCH_SENT_CLC_FLD`, `M4RCH_SENT_CLC_FUN`, `M4RCH_SENT_FUNCS`, `M4RCH_SENT_ITEMS`, `M4RCH_SENT_OBJ_FLD`, `M4RCH_SENT_OBJ_REL`, `M4RCH_SENT_OBJECTS`, `M4RCH_SENTENCES`, `M4RCH_SENTENCES1`, `M4RCH_SENTENCES2`, `M4RCH_SENTENCES3`, `M4RCH_SENTENCES4`, `M4RCH_SNT_CLC_PRM`, `M4RCH_TI_SENT_PAR`, `M4RDC_SCENARIO_ADD_SENTENCE`

### LOGICAL TABLE
- **Head object**: `M4RDD_LOGIC_OBJECT`
- **Auditoría CCT**: Sí
- **Descripción**: Tabla lógica BDL completa con campos, índices, relaciones, filtros, vistas y auditoría.
- **Tablas físicas** (41 entradas):
  `M4RAU_LOBJ_OPE`, `M4RCH_CAR_FILTERS`, `M4RCH_CAR_FILTERS1`, `M4RCH_CAR_FILTERS2`, `M4RCH_CAR_FLTR_FLD`, `M4RCH_MD_VERSION`, `M4RCH_VALUES`, `M4RCH_YTD_OBJECTS`, `M4RDC_AUTONUM_LOCK`, `M4RDC_FIELDS`, `M4RDC_FIELDS_TRANS`, `M4RDC_FIELDS1`, `M4RDC_INDEX`, `M4RDC_INDEX_COLS`, `M4RDC_INDEX_INCLUDE_COLS`, `M4RDC_LOGIC_OBJEC1`, `M4RDC_LOGIC_OBJECT`, `M4RDC_REAL_FIELDS`, `M4RDC_REAL_INDEX`, `M4RDC_REAL_OBJECTS`, `M4RDC_REL_FM_SBREC`, `M4RDC_RELATIONS`, `M4RDC_RELATIONS1`, `M4RDC_RLTION_FLDS`, `M4RDC_SEC_FIELDS`, `M4RDC_TH_PLANA`, `M4RDC_VIEW_CODE`, `M4RDC_VIEW_CODE1`, `M4RDD_FIELDS`, `M4RDD_FIELDS_TRANS`, `M4RDD_FIELDS1`, `M4RDD_INDEX`, `M4RDD_INDEX_COLS`, `M4RDD_INDEX_INCLUDE_COLS`, `M4RDD_LOGIC_OBJEC1`, `M4RDD_LOGIC_OBJECT`, `M4RDD_REL_FM_SBREC`, `M4RDD_RELATION_FLD`, `M4RDD_RELATIONS`, `M4RDD_RELATIONS1`, `M4RDD_TH_PLANA`, `M4RDD_VIEW_CODE`, `M4RDD_VIEW_CODE1`

### APP_ROLE
- **Head object**: `M4RSC_APPROLE`
- **Auditoría CCT**: Sí
- **Tablas físicas** (5 entradas):
  `M4RSC_APPROLE`, `M4RSC_APPROLE1`, `M4RSC_APPROLE2`, `M4RSC_ROLE_ORG`, `M4RSC_SEC_PR_OPT`

### WORKFLOW PROCESS
- **Head object**: `M4RWF_BPC`
- **Auditoría CCT**: Sí
- **Tablas físicas** (33 entradas):
  `M4RWF_ASSIGNEDROLE`, `M4RWF_BPC`, `M4RWF_BPC1`, `M4RWF_BPC2`, `M4RWF_DATADEF`, `M4RWF_DATADEF1`, `M4RWF_EVENTASSOC`, `M4RWF_J_SBPC_MAP`, `M4RWF_JOINED_SBPC`, `M4RWF_RL_PARMAP`, `M4RWF_STATE`, `M4RWF_STATE_RULE`, `M4RWF_STATE1`, `M4RWF_STATE2`, `M4RWF_STATE3`, `M4RWF_STATE4`, `M4RWF_STATE5`, `M4RWF_STATE6`, `M4RWF_SUBBPC`, `M4RWF_SUBBPC_MAP`, `M4RWF_TASK`, `M4RWF_TASK_PARAM`, `M4RWF_TRANSCANCEL`, `M4RWF_TRANSITION`, `M4RWF_TRANSITION1`, `M4RWF_TRANSITION2`, `M4RWF_TRANSITION3`, `M4RWF_TRANSITION4`, `M4RWF_TRANSITION5`, `M4RWF_TRANSITION6`, `M4RWF_TRANSITION7`, `M4RWF_WF_BPC_CONF`, `M4RWF_WF_STATE_CONF`, `M4RWF_XTRAPOINT`

### REPORT
- **Head object**: `M4RRP_REPORTS`
- **Auditoría CCT**: Sí
- **Tablas físicas** (65 entradas, selección):
  `M4RRP_REPORTS`, `M4RRP_REPORTS1`, `M4RRP_REPORT_PAGS`, `M4RRP_REPORT_SECTS`, `M4RRP_REPORT_SECT1`, `M4RRP_PAGE_FIELDS`, `M4RRP_PAGE_FIELD1`–`M4RRP_PAGE_FIELD4`, `M4RRP_PAGE_PROPS`, `M4RRP_REPORT_PROP`, `M4RRP_SECT_CONTAIN`, `M4RRP_SECT_CON_FLD`, `M4RRP_SECT_CON_F1`–`M4RRP_SECT_CON_F4`, `M4RRP_GRAPH_DEF_TB`, `M4RRP_GRAPH_DETAIL`, `M4RRP_GRAPH_PARMS`, `M4RRP_GRAPH_PROPS`, `M4RRP_GRAPH_RELAT`, `M4RRP_LONG_EXPRES`, `M4RRP_LONG_EXPRE1`–`M4RRP_LONG_EXPRE7`, `M4RRP_REPORT_COLOR`, `M4RRP_REPORT_FONTS`, `M4RRP_RPT_CT`, `M4RRP_PUB_REPORTS`, `M4RRP_REPRT_FRMTS`, `M4RTC_ADB_USER_GRAPH_INF`, `SRP_GRAPH_PUBLISH`, y otras

### EXTENDED FUNCTION
- **Head object**: `M4RDC_EXTENDED_FUN`
- **Auditoría CCT**: Sí
- **Tablas físicas** (5 entradas):
  `M4RDC_EXT_FUNC_ARG`, `M4RDC_EXTENDED_FU1`, `M4RDC_EXTENDED_FUN`, `M4RDC_FUN_ARGS_REL`, `M4RDC_FUNCTION_REL`

### EXTENDED TYPE
- **Head object**: `M4RDC_EXTENDED_TPS`
- **Auditoría CCT**: Sí
- **Tablas físicas** (3 entradas):
  `M4RDC_EXT_TPS_TRAN`, `M4RDC_EXTENDED_TP1`, `M4RDC_EXTENDED_TPS`

### FILTER
- **Head object**: `M4RDC_FILTERS`
- **Auditoría CCT**: Sí
- **Tablas físicas**: `M4RDC_FILTERS`, `M4RDC_FILTERS1`, `M4RDC_FILTERS2`

### FORMULA
- **Head object**: `M4RDC_FORMULA`
- **Tablas físicas**: `M4RDC_FORMULA`, `M4RDC_FORMULA1`

### SECURITY M4O
- **Head object**: `M4RCH_T3_RSM`
- **Auditoría CCT**: Sí
- **Descripción**: Seguridad (RSM/máscaras) de un Meta4Object.
- **Tablas físicas** (9 entradas):
  `M4RCH_FILTER_MASK`, `M4RCH_ITEM_MASK`, `M4RCH_MD_VERSION`, `M4RCH_NODE_MASK`, `M4RCH_NODE_MASK1`, `M4RCH_T3_CON_MASK`, `M4RCH_T3_MASK`, `M4RCH_T3_RSM`, `M4RCH_TI_MASK`

### SECURITY LT
- **Head object**: `M4RDC_SEC_LOBJ`
- **Auditoría CCT**: Sí
- **Tablas físicas** (6 entradas):
  `M4RCH_MD_VERSION`, `M4RDC_SEC_FIELDS`, `M4RDC_SEC_LOBJ`, `M4RDC_SEC_LOBJ_F1`, `M4RDC_SEC_LOBJ_FIL`, `M4RDC_SEC_RELATION`

### SECURITY BP
- **Head object**: `M4RBP_APPROLE`
- **Auditoría CCT**: Sí
- **Tablas físicas**: `M4RBP_APPROLE`

### SECURITY BPC
- **Head object**: `M4RWF_ROLE_BPC`
- **Auditoría CCT**: Sí
- **Tablas físicas**: `M4RWF_ROLE_BPC`

### EVENT
- **Head object**: `M4REV_EVENT`
- **Auditoría CCT**: Sí
- **Tablas físicas** (6 entradas):
  `M4REV_DEST`, `M4REV_EVENT`, `M4REV_ORIG`, `M4REV_PARAM`, `M4REV_PARAM_DEST`, `M4REV_PARAM_ORIG`

### IMPORT
- **Head object**: `M4RIM_IMPORTS`
- **Auditoría CCT**: Sí
- **Tablas físicas**: `M4RIM_FIELDSIM`, `M4RIM_IMPORTS`

### RSM
- **Head object**: `M4RSC_RSM`
- **Auditoría CCT**: Sí
- **Tablas físicas**: `M4RSC_RSM`, `M4RSC_RSM1`

### APPLICATION PARAMS
- **Head object**: `M4RAV_APPLICATION`
- **Auditoría CCT**: Sí
- **Tablas físicas** (7 entradas):
  `M4RAV_APP_VAL_LG`, `M4RAV_APP_VAL_LG1`, `M4RAV_APP_VALUE`, `M4RAV_APPLICATION`, `M4RAV_KEY`, `M4RAV_KEY1`, `M4RAV_SECTION`

---

## Subclases Principales

Las subclases son subelementos de una clase. Al transportar una subclase, RAMDL mueve **solo las tablas de ese subelemento**, no la clase completa.

### ITEM (subclase de NODE STRUCTURE)
- **Head object**: `M4RCH_ITEMS`
- **Descripción**: Un ítem concreto de una Node Structure (TI). Transportar un ITEM no transporta la TI completa.
- **Tablas físicas** (65 entradas, selección):
  `M4RCH_CHANNEL_DEP` (×2), `M4RCH_CONCEPT_NODE`, `M4RCH_CONCEPTS` (×3), `M4RCH_CONCEPTS_OWR`, `M4RCH_CONCEPTS_SLICE_MODE`, `M4RCH_CONCTOR_ARG` (×2), `M4RCH_CONCTOR_ITEM` (×2), `M4RCH_CONCTOR_PAR`, `M4RCH_EXTERNAL_DEP` (×2), `M4RCH_INDEX_ITEM`, `M4RCH_INTERNAL_DEP` (×2), `M4RCH_ITEM_ARGS`, `M4RCH_ITEM_CSDESC`, `M4RCH_ITEM_MASK`, `M4RCH_ITEM_PI` (×2), `M4RCH_ITEMS`, `M4RCH_ITEMS_HAVING`, `M4RCH_ITEMS_OWR`, `M4RCH_ITEMS1`, `M4RCH_NODE_FILTER`, `M4RCH_QRY_LETR_DEP`, `M4RCH_RULE_SENTENC` (×2), `M4RCH_RULES` (×2), `M4RCH_RULES1` (×2), `M4RCH_RULES2` (×2), `M4RCH_RULES3` (×2), `M4RCH_RULESCOM1` (×2), `M4RCH_SENT_ITEMS`, `M4RCH_T3_CONN_ITEM` (×2), `M4RCH_TAGS` (×3), `M4RCH_TI_CONN_ITM` (×4), `M4RCH_TI_FILTERS`, `M4RCH_TI_SENT_PAR`, `M4RCH_TOTAL_OPP`, `M4RCH_TOTAL_REF` (×7), `M4RCH_TOTAL_TAGS` (×5), `M4RCH_TOTALS` (×2), `M4RXM_ITEM_MAP`, `M4RAU_PAR_AUDT_LOB`

### NODE (subclase de META4OBJECT)
- **Head object**: `M4RCH_NODES`
- **Descripción**: Un nodo concreto de un Meta4Object (T3). Transportar un NODE no transporta el T3 completo.
- **Tablas físicas** (56 entradas, selección):
  `M4RCH_ALIAS_RES` (×2), `M4RCH_BO_MET_ARG`, `M4RCH_CONCTOR_ARG` (×2), `M4RCH_CONCTOR_ITEM` (×2), `M4RCH_CONCTOR_PAR`, `M4RCH_CONNECTORS` (×4), `M4RCH_DISABLEDITEM` (×2), `M4RCH_FILTER_MASK`, `M4RCH_FILTER_PRED`, `M4RCH_FILTERS` (×2), `M4RCH_INDEX` (×2), `M4RCH_INDEX_ITEM` (×2), `M4RCH_ITEM_CSDESC`, `M4RCH_ITEM_MASK`, `M4RCH_NODE_FILTER` (×2), `M4RCH_NODE_MASK` (×2), `M4RCH_NODE_MIG`, `M4RCH_NODES`, `M4RCH_NODES1`, `M4RCH_OVERWRITE_NO`, `M4RCH_T3_ALIAS_RES` (×2), `M4RCH_T3_CONN_ITEM` (×2), `M4RCH_T3_CONNTORS` (×3), `M4RFE_NODE_PROPS`, `M4RFE_PAT_REL`, `M4RRP_NODE_GROUPS`, `M4RRP_NODES_IN_GRP` (×2), `M4RRP_VISIBLE_NODE`, `M4RWP_NDS_AC_READ`, `M4RWP_NODES_AC_CLC` (×2), `M4RWP_NODES_CALC` (×4), `M4RWP_NODES_CALC_O`, `M4RWP_NODES_FILTER`, `M4RXM_NODE_MAP`

### PAYROLL ITEM (subclase de META4OBJECT)
- **Head object**: `M4RCH_PAYROLL_ITEM`
- **Descripción**: Ítem de nómina (PI) de un Meta4Object.
- **Tablas físicas** (9 entradas):
  `M4RCH_PAYROLL_ITEM` (×2), `M4RCH_PI_OWR`, `M4RCH_PI_TAGS` (×3), `M4RCH_PICOMPONENTS` (×3)

### FIELD (subclase de LOGICAL TABLE)
- **Head object**: `M4RDD_FIELDS`
- **Descripción**: Un campo de una tabla lógica BDL.
- **Tablas físicas** (28 entradas, selección):
  `M4RCH_AST_FLD_REL`, `M4RCH_AST_VAL_REL`, `M4RCH_CAR_FLTR_FLD`, `M4RCH_DIMENSIONS`, `M4RCH_ITEMS` (×2), `M4RCH_SENT_ADD_FLD`, `M4RCH_SENT_CLC_FLD`, `M4RCH_SENT_OBJ_FLD` (×2), `M4RDC_AUTONUM_LOCK`, `M4RDC_FIELDS` (×2), `M4RDC_FIELDS_TRANS`, `M4RDC_FIELDS1`, `M4RDC_INDEX_COLS`, `M4RDC_INDEX_INCLUDE_COLS`, `M4RDC_REAL_FIELDS`, `M4RDC_RLTION_FLDS` (×2), `M4RDC_SEC_FIELDS`, `M4RDD_FIELDS`, `M4RDD_FIELDS_TRANS`, `M4RDD_FIELDS1`, `M4RDD_INDEX_COLS`, `M4RDD_INDEX_INCLUDE_COLS`, `M4RDD_RELATION_FLD` (×2)

### SECURITY BP ROLE (subclase de BUSINESS PROCESS)
- **Head object**: `M4RBP_APPROLE`
- **Tablas físicas**: `M4RBP_APPROLE`

### SECURITY M4O RSM (subclase de META4OBJECT)
- **Head object**: `M4RCH_T3_RSM`
- **Tablas físicas**: `M4RCH_T3_RSM`

### SECURITY LT RSM (subclase de LOGICAL TABLE)
- **Head object**: `M4RDC_SEC_LOBJ`
- **Tablas físicas** (5 entradas):
  `M4RDC_SEC_FIELDS`, `M4RDC_SEC_LOBJ`, `M4RDC_SEC_LOBJ_F1`, `M4RDC_SEC_LOBJ_FIL`, `M4RDC_SEC_RELATION`

### WORKFLOW PROCESS CONF (subclase de WORKFLOW PROCESS)
- **Head object**: `M4RWF_BPC_CON`
- **Tablas físicas** (6 entradas):
  `M4RWF_BPC_CON`, `M4RWF_EXEC_CONDITION_CON`, `M4RWF_RL_PAR_CON`, `M4RWF_SROLE_CON`, `M4RWF_SRULE_CON`, `M4RWF_STATE_CON`

### BP GROUP (subclase de BUSINESS PROCESS)
- **Head object**: `M4RBP_GROUPS`
- **Tablas físicas**: `M4RBP_GROUPS`

### DMD COMPONENT (subclase de DMD)
- **Head object**: `M4RCH_DMD_COMPNTS`
- **Tablas físicas**: `M4RCH_DMD_COMPNTS`, `M4RCH_DMD_GRP_CMP`

### LOGICAL INDEX (subclase de LOGICAL TABLE)
- **Head object**: `M4RDD_INDEX`
- **Tablas físicas** (8 entradas):
  `M4RDC_INDEX`, `M4RDC_INDEX_COLS`, `M4RDC_INDEX_INCLUDE_COLS`, `M4RDC_REAL_INDEX` (×2), `M4RDD_INDEX`, `M4RDD_INDEX_COLS`, `M4RDD_INDEX_INCLUDE_COLS`

### RELATION (subclase de LOGICAL TABLE)
- **Head object**: `M4RDD_RELATIONS`
- **Tablas físicas** (6 entradas):
  `M4RDC_RELATIONS`, `M4RDC_RELATIONS1`, `M4RDC_RLTION_FLDS`, `M4RDD_RELATION_FLD`, `M4RDD_RELATIONS`, `M4RDD_RELATIONS1`

---

## Tabla de Referencia Rápida: Clase/Subclase por Head Object

Usar esta tabla para identificar a qué clase pertenece un objeto dado su `ID_HEAD_OBJECT`:

| ID_HEAD_OBJECT | Clase | Subclase |
|---|---|---|
| `M4RCH_TIS` | NODE STRUCTURE | — |
| `M4RCH_ITEMS` | — | ITEM (de NODE STRUCTURE) |
| `M4RCH_T3S` | META4OBJECT | — |
| `M4RCH_NODES` | — | NODE (de META4OBJECT) |
| `M4RCH_PAYROLL_ITEM` | — | PAYROLL ITEM (de META4OBJECT) |
| `M4RBP_DEF` | BUSINESS PROCESS | — |
| `M4RBP_GROUPS` | — | BP GROUP (de BUSINESS PROCESS) |
| `M4RBP_APPROLE` | SECURITY BP | SECURITY BP ROLE (de BP) |
| `M4RPT_PRESENTATION` | PRESENTATION | — |
| `M4RMN_OPTIONS` | MENU OPTION | — |
| `M4RCH_SENTENCES` | SENTENCE | — |
| `M4RDD_LOGIC_OBJECT` | LOGICAL TABLE | — |
| `M4RDD_FIELDS` | — | FIELD (de LOGICAL TABLE) |
| `M4RDD_INDEX` | — | LOGICAL INDEX (de LOGICAL TABLE) |
| `M4RDD_RELATIONS` | — | RELATION (de LOGICAL TABLE) |
| `M4RDC_SEC_LOBJ` | SECURITY LT | SECURITY LT RSM (de LOGICAL TABLE) |
| `M4RSC_APPROLE` | APP_ROLE | — |
| `M4RSC_RSM` | RSM | — |
| `M4RWF_BPC` | WORKFLOW PROCESS | — |
| `M4RWF_BPC_CON` | — | WORKFLOW PROCESS CONF (de WF PROCESS) |
| `M4RWF_ROLE_BPC` | SECURITY BPC | SECURITY BPC ROLE (de WF PROCESS) |
| `M4RRP_REPORTS` | REPORT | — |
| `M4REV_EVENT` | EVENT | — |
| `M4RDC_EXTENDED_FUN` | EXTENDED FUNCTION | — |
| `M4RDC_EXTENDED_TPS` | EXTENDED TYPE | — |
| `M4RDC_FILTERS` | FILTER | — |
| `M4RDC_FORMULA` | FORMULA | — |
| `M4RCH_T3_RSM` | SECURITY M4O | SECURITY M4O RSM (de META4OBJECT) |
| `M4RIM_IMPORTS` | IMPORT | — |
| `M4RAV_APPLICATION` | APPLICATION PARAMS | — |
| `M4RCH_DMD_COMPNTS` | — | DMD COMPONENT (de DMD) |

---

## Diferencia entre Clase y Subclase en la práctica

| Acción | Resultado |
|---|---|
| Transportar clase **NODE STRUCTURE** (una TI) | Se mueven ~52 tablas: la TI, todos sus ítems, reglas, totales, conceptos, alias, herencia, dependencias |
| Transportar subclase **ITEM** (un ítem de una TI) | Se mueven ~65 entradas de tablas: solo el ítem, sus reglas, totales, tags, conceptos vinculados a ese ítem |
| Transportar clase **META4OBJECT** (un T3) | Se mueven ~88 entradas de tablas: el T3, todos sus nodos, connectores, filtros, herencia, presentaciones |
| Transportar subclase **NODE** (un nodo de un T3) | Se mueven ~56 entradas de tablas: solo el nodo, sus conectores, filtros, índices |
| Transportar clase **BUSINESS PROCESS** | Se mueven 19 tablas: definición, código, parámetros, estructura, roles de excepción, presentaciones vinculadas |

> **Regla general**: La clase transporta el objeto completo con todo su contenido. La subclase transporta solo ese subelemento con sus dependencias directas, dejando el resto de la clase intacto en destino.

---

## Fuente de los Datos

Esta documentación fue extraída del repositorio `z_input/RamDl.mdb` (herramienta cliente RAM-DL, formato Access Jet3) mediante parsing directo. Las tablas fuente son:
- `M4RDC_CLASSES` — 138 entradas (múltiples versiones por clase)
- `M4RDC_CLASS_MEMBER` — 809 entradas
- `M4RDC_SUBCLASSES` — 49 entradas
- `M4RDC_SUBCLASS_MBR` — 255 entradas
- `M4RDC_SUPERCLASSES` — 36 entradas

Estas tablas **no existen en SQL Server**. El equivalente parcial en SQL Server es `M4RDC_CLASSES_PAR` (41 filas, solo metadatos básicos de clase sin membresía de tablas físicas).
