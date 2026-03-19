# =============================================================================
# ln4_lsp/semantic.py — Analizador semántico para LN4
# =============================================================================
# Fase 3 del LSP: diagnósticos semánticos.
# Camina el parse tree (ANTLR4 Visitor) y detecta:
#   1. Llamadas a funciones desconocidas (Error)
#   2. Número incorrecto de argumentos (Error)
#   3. Variables usadas antes de ser asignadas (Warning)
#
# Diseño:
#   - Las constantes predefinidas (M4_TRUE, EQUAL, etc.) NO se reportan
#     como variables indefinidas.
#   - Las funciones built-in se validan contra el catálogo JSON.
#   - Los items de TI (TI.ITEM, TI.METHOD(), @ITEM, #ITEM) NO se validan
#     aquí — eso requiere conocimiento del canal/nodo específico (Phase 5).
#   - La variable del For loop se registra automáticamente.
# =============================================================================

import sys
import os
import logging

from antlr4 import CommonTokenStream, InputStream, ParseTreeVisitor

# Ajustar sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ln4_lsp.generated.LN4Parser import LN4Parser
from ln4_lsp.generated.LN4Visitor import LN4Visitor
from ln4_lsp.ln4_builtins import get_catalog, is_known_constant, LN4_CONSTANTS

logger = logging.getLogger("ln4-lsp")


# =============================================================================
# Diagnóstico semántico (tuple)
# =============================================================================
# (line, column, end_column, message, severity)
# severity: "error" | "warning" | "info"

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"


# =============================================================================
# Semantic Visitor — camina el parse tree
# =============================================================================
class LN4SemanticVisitor(LN4Visitor):
    """Visitor que realiza análisis semántico sobre el parse tree de LN4.

    Recolecta diagnósticos en self.diagnostics como lista de tuplas:
        (line, column, end_column, message, severity)
    donde line es 1-indexed (ANTLR4 convention).
    """

    def __init__(self):
        super().__init__()
        self.diagnostics = []
        self.catalog = get_catalog()

        # Scope de variables — set de nombres (uppercase) definidos
        # En LN4 no hay declaraciones explícitas; la primera asignación "define" la variable.
        self.defined_vars = set()

        # Variables que se usan antes de definir — para evitar reportar repetidos
        self._reported_undefined = set()

    def _add_diagnostic(self, ctx_or_token, message, severity=SEVERITY_ERROR):
        """Agrega un diagnóstico a la lista.

        Args:
            ctx_or_token: Contexto o token de ANTLR4 (tiene .start o .line/.column).
            message: Mensaje del diagnóstico.
            severity: Nivel de severidad.
        """
        if hasattr(ctx_or_token, "symbol"):
            # Es un token
            token = ctx_or_token.symbol if hasattr(ctx_or_token, "symbol") else ctx_or_token
            line = token.line
            col = token.column
            end_col = col + len(token.text) if token.text else col + 1
        elif hasattr(ctx_or_token, "start"):
            # Es un contexto con start token
            token = ctx_or_token.start
            line = token.line
            col = token.column
            # Intentar usar stop token para el rango completo
            if hasattr(ctx_or_token, "stop") and ctx_or_token.stop is not None:
                stop = ctx_or_token.stop
                if stop.line == line:
                    end_col = stop.column + len(stop.text) if stop.text else col + 1
                else:
                    end_col = col + len(token.text) if token.text else col + 1
            else:
                end_col = col + len(token.text) if token.text else col + 1
        else:
            line = 1
            col = 0
            end_col = 1

        self.diagnostics.append((line, col, end_col, message, severity))

    # -----------------------------------------------------------------
    # Statement visitors
    # -----------------------------------------------------------------

    def visitForBlock(self, ctx):
        """For i = start To end — registra 'i' como variable definida."""
        # El IDENTIFIER después de FOR es la variable del loop
        id_tokens = ctx.IDENTIFIER()
        if id_tokens:
            var_name = id_tokens.getText().upper()
            self.defined_vars.add(var_name)

        return self.visitChildren(ctx)

    # -----------------------------------------------------------------
    # Assignment — registra variables definidas
    # -----------------------------------------------------------------

    def visitAssignmentOrCall(self, ctx):
        """Detecta asignaciones para registrar variables definidas.

        assignmentOrCall:
            memberExpression EQ expression   -> asignación
            expression                       -> llamada
        """
        # Si tiene EQ, es una asignación
        if ctx.EQ():
            # El lado izquierdo es memberExpression
            member_expr = ctx.memberExpression()
            if member_expr:
                # Si es un simple IDENTIFIER (sin memberTail), es una asignación de variable
                primary = member_expr.primaryExpression()
                member_tails = member_expr.memberTail()
                if primary and (not member_tails or len(member_tails) == 0):
                    # Es primaryExpression sin tail — podría ser variable simple
                    id_node = primary.IDENTIFIER()
                    if id_node and not primary.LPAREN():
                        # Es un IDENTIFIER simple, sin paréntesis (no es func call)
                        var_name = id_node.getText().upper()
                        self.defined_vars.add(var_name)

        return self.visitChildren(ctx)

    # -----------------------------------------------------------------
    # Function calls — valida existencia y aridad
    # -----------------------------------------------------------------

    def visitPrimaryExpression(self, ctx):
        """Detecta llamadas a funciones: IDENTIFIER LPAREN argList? RPAREN.

        También detecta uso de variables/identificadores simples.
        """
        id_node = ctx.IDENTIFIER()

        if id_node and ctx.LPAREN():
            # Es una llamada a función: IDENTIFIER(args)
            func_name = id_node.getText().upper()
            self._check_function_call(ctx, func_name)
        elif id_node and not ctx.LPAREN():
            # Es un identificador simple (variable, constante, o TI)
            name = id_node.getText().upper()
            self._check_identifier(ctx, id_node, name)

        return self.visitChildren(ctx)

    def visitMemberTail(self, ctx):
        """Detecta llamadas a métodos en member access chains.

        memberTail con LPAREN indica una llamada a método:
          .METHOD(args) — método de TI (no validamos aquí)
          ..SysMethod(args) — método de sistema (no validamos aquí)
          !TI.METHOD(args) — cross-channel (no validamos aquí)

        Los métodos de TI no se validan porque requieren conocimiento
        del canal específico (Phase 5).
        """
        # No validamos métodos de TI/sistema — solo funciones standalone
        return self.visitChildren(ctx)

    def _check_function_call(self, ctx, func_name):
        """Valida una llamada a función contra el catálogo.

        Args:
            ctx: Contexto de primaryExpression.
            func_name: Nombre de la función (uppercase).
        """
        if not self.catalog.is_loaded:
            return  # Sin catálogo, no podemos validar

        # Contar argumentos
        arg_list = ctx.argList()
        if arg_list:
            # argList: expression (COMMA expression)*
            arg_count = len(arg_list.expression())
        else:
            arg_count = 0

        # Verificar si la función existe
        if not self.catalog.has_function(func_name):
            # Podría ser un método de TI que parece función standalone
            # (ej: algunas funciones se llaman sin prefijo de TI)
            # Solo reportar si el catálogo está cargado
            self._add_diagnostic(
                ctx,
                f"Función desconocida: '{func_name}'",
                SEVERITY_WARNING,
            )
            return

        # Validar número de argumentos
        error_msg = self.catalog.validate_args(func_name, arg_count)
        if error_msg:
            self._add_diagnostic(ctx, error_msg, SEVERITY_ERROR)

    def _check_identifier(self, ctx, id_node, name):
        """Verifica un identificador simple (variable, constante, TI).

        No reporta si:
          - Es una constante conocida (M4_TRUE, EQUAL, etc.)
          - Es una función conocida usada sin paréntesis (raro pero válido)
          - Es una variable ya definida
          - Ya fue reportado como indefinido
          - Empieza con M4_ (probablemente constante no catalogada)
          - Empieza con ARG_ (convención de argumentos de regla)
          - Empieza con P_ (convención de parámetros)
        """
        if is_known_constant(name):
            return

        if self.catalog.is_loaded and self.catalog.has_function(name):
            return  # Función usada como referencia

        if name in self.defined_vars:
            return

        # Heurísticas para evitar falsos positivos
        if name.startswith("M4_"):
            return  # Probablemente constante no catalogada

        if name.startswith("ARG_"):
            return  # Argumento de regla (convención PeopleNet)

        if name.startswith("P_"):
            return  # Parámetro (convención PeopleNet)

        # No reportar TIs — pueden ser identificadores de nodo
        # Los TIs no están en el scope local, pero son válidos
        # porque la resolución de TIs es contextual al canal.
        # La heurística: si se usa como base de member access (.DOT),
        # probablemente es un TI. Pero aquí en primaryExpression
        # no tenemos acceso directo al padre.
        # Por ahora, reportar como warning con bajo threshold.

        if name not in self._reported_undefined:
            self._reported_undefined.add(name)
            # No reportar — hay demasiados identificadores válidos que
            # no podemos resolver sin contexto de canal (TIs, items, etc.)
            # Se habilitará en Phase 5 cuando tengamos resolución de canal.
            # self._add_diagnostic(
            #     ctx,
            #     f"Variable posiblemente indefinida: '{name}'",
            #     SEVERITY_INFO,
            # )


# =============================================================================
# Función pública — ejecutar análisis semántico
# =============================================================================
def analyze_semantics(tree):
    """Ejecuta el análisis semántico sobre un parse tree.

    Args:
        tree: Parse tree de ANTLR4 (retornado por parser.program()).

    Returns:
        Lista de tuplas (line, column, end_column, message, severity).
    """
    visitor = LN4SemanticVisitor()
    visitor.visit(tree)
    return visitor.diagnostics
