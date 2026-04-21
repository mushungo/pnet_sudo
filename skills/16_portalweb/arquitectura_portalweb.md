---
id: arquitectura_portalweb
name: Arquitectura Portal Web (M4WS)
version: 1.0.0
tags: [arquitectura, portalweb, jsp, m4ws, tags, javaee]
---

# Portal Web PeopleNet (M4WS)

El Portal Web de PeopleNet (directorio `M4WS`) es una aplicación Java EE (Servlets/JSP) que actúa como el **Thin Client** de PeopleNet. Permite exponer la lógica de negocio de los M4Objects (LN4) a través de una interfaz web moderna, facilitando el Autoservicio del Empleado (ESS) y del Mánager (MSS).

## Estructura de Instancias

El sistema se organiza en instancias de sitio, mapeadas en el fichero `webcatalog.xml`.

| Directorio | Instancia | Propósito |
|---|---|---|
| `_websource_` | - | Plantillas y fuentes comunes (no instancia funcional). |
| `default` | Producción | Sitio principal de usuario final. |
| `default-inte` | Validación | Entorno de integración y pruebas de desarrollo. |

## Stack Tecnológico

- **Contenedor**: Java Servlet 3.0+ (Tomcat / JBoss).
- **Frontend**: JSP + Custom Tag Library (`M4Tags`) + AJAX (GWT/JSAPI).
- **Backend**: Servlets Java que invocan el kernel de PeopleNet (M4Operations).
- **Servicios**: SOAP (Apache Axis 1.4) y REST.

## La Tag Library "M4Tags"

Es el puente principal entre el JSP y los objetos PeopleNet. Se declara en los JSPs con:
`<%@ taglib uri="M4Tags" prefix="m4"%>`

### Tags Principales

| Tag | Función | Atributos Clave |
|---|---|---|
| `<m4:startpage>` | Inicia el contexto de página/sesión. | `m4task` (ID de tarea/BP) |
| `<m4:datadef>` | Enlaza un M4Object a un nombre de sesión. | `m4o` (ID objeto), `m4name` (alias) |
| `<m4:exec>` | Ejecuta un método en un objeto. | `m4method` (Nombre de método LN4) |
| `<m4:param>` | Pasa parámetros a métodos o defs. | `name`, `value` |
| `<m4:outputdef>` | Define el conjunto de datos de salida. | `m4alias` |
| `<m4:move>` | Posiciona el cursor en un nodo. | `value` (p.ej. `SESION:NODO[FIRST]`) |
| `<m4:loop>` | Itera sobre registros de un nodo. | `from`, `to` (p.ej. `0` a `N-1`) |
| `<m4:item>` | Muestra el valor de un campo. | `m4name`, `htmlsafe` |

### Ejemplo de Patrón de Carga (JSP)

```jsp
<%-- 1. Inicialización y carga de datos --%>
<m4:startpage m4task="SSE_VACACIONES"/>
<m4:beginjob/>
<m4:datadef m4o="SSE_VAC_REQUEST" m4name="VAC_OBJ"/>
<m4:exec m4method="CARGA:VAC_OBJ!SSE_PRINCIPAL.CARGA">
  <m4:param name="ID_EMPLOYEE" value="<%= user_id %>"/>
</m4:exec>
<m4:endjob/>

<%-- 2. Posicionamiento --%>
<m4:move><m4:param name="VAC_OBJ" value="VAC_OBJ:SSE_VAC_REQUEST[FIRST]"/></m4:move>

<%-- 3. Visualización y Loop --%>
<table>
  <m4:loop from="0" to="N-1">
    <tr>
      <td><m4:item m4name="VAC_OBJ:SSE_VAC_REQUEST!SSE_VAC_REQUEST[&VAR.m4lix].FECHA_INICIO"/></td>
      <td><m4:item m4name="VAC_OBJ:SSE_VAC_REQUEST!SSE_VAC_REQUEST[&VAR.m4lix].DIAS_SOLICITADOS"/></td>
    </tr>
  </m4:loop>
</table>
```

## Servlet Endpoints Clave

| Endpoint | Propósito |
|---|---|
| `/servlet/CheckSecurity/*` | Guardián de seguridad y acceso a JSPs. |
| `/servlet/M4JSExecutor` | Ejecutor RPC para peticiones desde GWT / JS API. |
| `/servlet/M4FileService/*` | Gestión de ficheros y adjuntos (PeopleNet File Service). |
| `/REST/*` | API REST nativa de PeopleNet. |
| `/services/*` | Servicios Web SOAP (Axis) para integración. |
| `/servlet/download_blob` | Descarga directa de campos BLOB de la base de datos. |

## Módulos Funcionales (Estructura de Carpetas)

| Prefijo/Carpeta | Descripción |
|---|---|
| `sse_g*` | **Employee Self-Service (ESS)**. Grupos de generación de pantallas. |
| `mss_g*` | **Manager Self-Service (MSS)**. Pantallas para responsables/jefes. |
| `shco_*` | Componentes compartidos (Common Components). |
| `tctools` | Herramientas del Thin Client (portal, login, cambio password). |
| `translations` | Ficheros `.properties` con los literales multi-idioma. |
| `javascripts` | Librerías JS de sistema (`m4gen.js`, `funciones_sse.js`). |

## Notas de Configuración e Integración

1. **ConfigClient**: El fichero `classes/properties/configclient.xml` define la conexión al Application Server (`localhost:4444` por defecto).
2. **Mashup**: El portal puede actuar como hub para sistemas externos usando `framework/mashup/external_system.jsp`, que gestiona el SSO enviando un `M4Credential` firmado.
3. **i18n**: Los literales no están hardcodeados; se recuperan mediante `translations/*.properties` según el idioma de la sesión.
