---
title: "Gramática y Referencia del Lenguaje OBL"
version: "1.0.0"
tags: ["obl", "presentaciones", "uidesign", "peoplenet"]
description: "Referencia completa del lenguaje declarativo OBL (Object Based Language) para presentaciones de PeopleNet."
---

# Lenguaje OBL (Object Based Language)

El OBL es el lenguaje declarativo utilizado por el motor de presentaciones de PeopleNet para definir la interfaz de usuario, la navegación y la lógica básica de eventos. Se almacena compilado en la tabla `M4RPT_PRESENT_PKG1` (blob `XPACKAGE`).

## Estructura General

El lenguaje sigue una estructura jerárquica de bloques delimitados por `BEGIN` y `END`.

```obl
BEGIN <TipoControl> <Alias>
    <Propiedad> = <Valor>
    BEGIN <SubControl> <AliasSub>
        ...
    END
END
```

- **Case-Insensitivity**: Las palabras clave y tipos de control no distinguen entre mayúsculas y minúsculas.
- **Identación**: Por convención, se utilizan 4 espacios.

## Contenedores de Layout

| Control | Descripción | Propiedades Clave |
| :--- | :--- | :--- |
| `Form` | Ventana principal o formulario. | `Width`, `Height`, `Text`, `Sizable`, `Left`, `Top` |
| `Splitthorizontal` | Divisor de pantalla horizontal. | `Align` (Topfixed, Bottomfixed, All), `Width`, `Height` |
| `Splittvertical` | Divisor de pantalla vertical. | `Align`, `Width`, `Height` |
| `Splittblock` | Bloque dentro de un divisor. | `Length`, `Borderstyle`, `Roundborder`, `Borderlinecolor` |
| `Scrollpanel` | Contenedor con barras de desplazamiento. | `Align`, `Backcolor` |
| `Panel` | Contenedor genérico de controles. | `Idnode` (vínculo a nodo de datos), `Borderstyle` |
| `Tabstrip` | Contenedor de pestañas. | `Align`, `Keepalive` (1 = persistente en memoria) |
| `Tab` | Pestaña individual. | `Idnode`, `Text` |
| `Changer` | Switcher dinámico de vistas. | `Object` (ID del panel/tab activo por defecto) |
| `Groupbox` | Agrupador visual con borde. | `Text`, `Align` |

## Controles de Datos

| Control | Descripción | Propiedades Clave |
| :--- | :--- | :--- |
| `Label` | Etiqueta de texto estático o dinámico. | `Text`, `Fontbold`, `Fontunderline`, `Forecolor`, `Alignment`, `Mousecursor` |
| `Itemlabel` | Control vinculado a un item de datos. | `Iditem`, `Grants` (permisos), `Dependson`, `Format`, `Vbcompulsory` (obligatorio) |
| `Mimic` | Renderizado automático de un nodo. | `Class` (Table, Scrollpanel), `Idnode` |
| `Table` | Rejilla de datos. | `Singleselect`, `Colorheader`, `Tablemaxalign` |
| `Treeview` | Árbol de navegación. | `Align`, `Borderstyle` |
| `Treenode` | Nodo individual del árbol. | `Text`, `Tag` (metadatos para acciones) |

## Tokens Especiales y Direccionamiento

### Tokens de Metadatos
- `##CHNNL[ID]` -> Nombre del Canal (ID_CHANNEL).
- `##ND[ID]` -> Nombre del Nodo (ID_NODE).
- `##TM[ID]` -> Traducción del Item (ID_ITEM).

### Rutas de Objetos (`*O*`)
Se utiliza para referenciar propiedades o métodos de otros controles en el árbol.
- **Absoluta**: `*O*/Pres2/FormMain/splForm/Control.Metodo()`
- **Relativa**: `*O*../../Control.Propiedad := Valor`

## Lógica, Eventos y Acciones

### Eventos
- `Evclick`: Se dispara al hacer clic en un control o nodo.
- `Evload`: Se dispara al cargar un contenedor.
- `Evshow`: Se dispara cuando la presentación se hace visible.

### Acciones
- `Action_call`: Ejecuta un método o bloque.
  - `Sentence = "*O*...Exeblk.Call(Nombre)"`
- `Action_set`: Cambia una propiedad en tiempo de ejecución.
  - `Set = "*O*...Control.Visible := False"`
- `Action_preload`: Controla la carga inicial de datos.
  - `Autoload`, `Cancelif`, `Buttonnew`

### Bloques de Ejecución (`Exeblocks`)
Permiten definir lógica reutilizable dentro de la presentación, a menudo conteniendo otros bloques `Presentation` que se activan condicionalmente.

## Sistema de Lookups (`Listgroup`)

Define la ayuda de búsqueda (F9/Zoom) de un campo.

- `Function List`: Define el buscador (List).
- `Function Zoom`: Define la ventana de mantenimiento (Zoom).
- `Function Validate`: Lógica de validación post-edición.
- `Function Clear`: Limpieza de campos dependientes.

Propiedades de `Function`:
- `Idfuncchannel`, `Idfuncnode`, `Idfuncmethod`
- `Mainargs`, `Mainobjs`
- `Targetitems`, `Targetobjs` (mapeo de retorno de valores)

## Herencia e Includes

- `Includecall`: Inserta una presentación predefinida (ej: `SRTC_INCL_MENU`).
- `Argument`: Pasa parámetros al include (`Value`).
- `Extends`: Herencia de instancia para m4objects.
