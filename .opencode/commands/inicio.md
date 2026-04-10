---
description: Iniciar sesion en pnet_sudo recuperando contexto de Engram
---

Ejecuta el protocolo de inicio de sesion del proyecto pnet_sudo:

1. Llama a `engram_mem_context` con `project="pnet_sudo"` para recuperar el estado de sesiones anteriores.
2. Llama a `engram_mem_session_start` con un ID descriptivo en formato `session-<FECHA>-<TEMA>` y `project="pnet_sudo"`. Para la fecha usa el formato YYYY-MM-DD.
3. Presenta al usuario un resumen breve con: que se hizo en sesiones anteriores, que quedo pendiente, y en que punto esta el proyecto actualmente.
