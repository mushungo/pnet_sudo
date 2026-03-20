---
nombre: "listar_servicios_rest"
version: "1.0.0"
descripcion: "Lista los TIs de integración REST/WebService/SAP/SOAP de PeopleNet, con filtro opcional por categoría."
parametros:
  - nombre: "filter"
    tipo: "string"
    descripcion: "Categoría de filtro: REST, SAP, WS, SOAP, HTTP, INTERFACE, CONNECTOR, API_WS. Sin filtro lista todas."
    requerido: false
---

## Documentación de la Skill: `listar_servicios_rest`

### Propósito
Lista los TIs (Technology Items) de PeopleNet relacionados con integración: servicios REST, web services, conectores SAP, interfaces SOAP, etc.

### Contexto de Integración en PeopleNet
PeopleNet no usa funciones LN4 built-in para REST. En su lugar, los TIs exponen **ítems-método** (ITEM_TYPE=3) que los rules invocan:
- `TI.WS_GET` / `TI.WS_POST` / `TI.WS_PUT` — Llamadas HTTP
- `TI.GET_TOKEN` — OAuth token acquisition
- `TI.SQL_TO_JSON` — Serialización de datos a JSON

### Principales Categorías de TIs
| Categoría | Descripción | Ejemplo |
|---|---|---|
| **CCO_API_WS_REST** | Cliente REST principal con OAuth | CLIENT_ID, TOKEN, WS_GET |
| **CSP_REST_*** | Framework de registro de servicios REST | SERVICE, GROUP, CLIENT_ENGINE |
| **CCO_API_SAP4HANA** | Conector SAP S/4HANA | Mapeo de datos SAP ↔ PeopleNet |
| **WS_*** | Fachada de web services (137 TIs) | Documentos, personas, nómina |
| **CONNECTOR_*** | Framework genérico de conectores | CONNECTOR_ITEMS, ARGUMENTS |

### Ejemplo de Uso
```bash
# Listar todos los TIs de integración
python -m tools.rest.list_rest_services

# Filtrar solo REST
python -m tools.rest.list_rest_services --filter REST

# Filtrar SAP
python -m tools.rest.list_rest_services --filter SAP

# Filtrar web services
python -m tools.rest.list_rest_services --filter WS
```

**Resultado esperado:**
```json
{
  "status": "success",
  "count": 112,
  "services": [
    {
      "id_ti": "CCO_API_WS_REST",
      "channel": "CCO_API_WS_REST",
      "cstype": 7,
      "cstype_name": "No-BDL"
    }
  ]
}
```
