// =============================================================================
// LN4.g4 — Gramatica ANTLR4 para el lenguaje LN4 de PeopleNet
// =============================================================================
// LN4 es un lenguaje procedural case-insensitive, similar a VB, con dot notation
// sobre TIs (Technical Instances) y operador ! para acceso cross-channel.
//
// Referencia: Investigacion sobre 46,230 reglas reales del repositorio PeopleNet.
//
// Decisiones de diseno:
//   - Gramatica combinada (lexer + parser en un archivo).
//   - NEWLINE es token significativo: separa statements y diferencia
//     single-line If de multi-line If.
//   - El operador = es un solo token (EQ); la distincion entre asignacion
//     y comparacion se resuelve en el parser (contexto gramatical).
//   - Constantes como M4_TRUE, M4_FALSE, EQUAL, etc. se parsean como
//     IDENTIFIER y se resuelven en el analisis semantico, no en el lexer.
//   - Fechas en braces {2025/10/31} se capturan como DATE_LITERAL.
//   - Do...Until expr y Do...While expr...Loop son variantes del loop.
// =============================================================================

grammar LN4;

// ---------------------------------------------------------------------------
// Opciones: case-insensitive para keywords (If = IF = iF)
// ---------------------------------------------------------------------------
options {
    caseInsensitive = true;
}

// ============================= PARSER RULES =================================

// -- Punto de entrada ---------------------------------------------------------
program
    : NL* statementList EOF
    ;

statementList
    : (statement separator)* statement?
    ;

separator
    : NL+
    | COLON
    | COLON NL+
    ;

// -- Statements ---------------------------------------------------------------
statement
    : ifBlock
    | forBlock
    | whileBlock
    | doBlock
    | returnStatement
    | assignmentOrCall
    ;

// -- If / ElseIf / Else / EndIf ----------------------------------------------
// Dos formas:
//   1) Multi-line:  If expr Then NL ... [ElseIf...] [Else...] EndIf
//   2) Single-line: If expr Then stmt [:stmt]...    (sin EndIf, sin NL)
ifBlock
    : IF expression THEN NL+ statementList
      elseIfBlock*
      elseBlock?
      ENDIF                                         // multi-line
    | IF expression THEN inlineStatements            // single-line
    ;

elseIfBlock
    : ELSEIF expression THEN NL+ statementList
    ;

elseBlock
    : ELSE NL+ statementList
    ;

// Statements en la misma linea (separados por : si hay varios)
// Soporta: If cond Then stmt1 [: stmt2]... [Else stmtElse1 [: stmtElse2]...]
inlineStatements
    : inlineStmt (COLON inlineStmt)* (ELSE inlineStmt (COLON inlineStmt)*)?
    ;

inlineStmt
    : assignmentOrCall
    | returnStatement
    ;

// -- For / Next ---------------------------------------------------------------
forBlock
    : FOR IDENTIFIER EQ expression TO expression (STEP expression)? NL+
      statementList
      NEXT
    ;

// -- While / Wend -------------------------------------------------------------
whileBlock
    : WHILE expression NL+
      statementList
      WEND
    ;

// -- Do ... Until / Do ... While ... Loop ------------------------------------
// Dos variantes:
//   1) Do NL stmts Until expr        (sin Loop)
//   2) Do NL stmts While expr Loop   (con Loop)
doBlock
    : DO NL+
      statementList
      UNTIL expression                               // Do...Until
    | DO NL+
      statementList
      WHILE expression NL*
      LOOP                                           // Do...While...Loop
    ;

// -- Return -------------------------------------------------------------------
// Tres formas reales: Return(expr), Return expr, Return (sin valor)
returnStatement
    : RETURN LPAREN expression RPAREN               // Return(expr)
    | RETURN expression                              // Return expr
    | RETURN                                         // Return (sin valor)
    ;

// -- Assignment o llamada -----------------------------------------------------
// memberExpr = expression   -> asignacion
// expression                -> llamada (el expression puede ser un call)
assignmentOrCall
    : memberExpression EQ expression                 // asignacion
    | expression                                     // llamada o expression sola
    ;

// ============================= EXPRESSIONS ==================================
// Precedencia (menor a mayor):
//   OR -> AND -> NOT -> comparacion -> suma/resta -> mult/div -> unario -> member

expression
    : orExpr
    ;

orExpr
    : andExpr (OR andExpr)*
    ;

andExpr
    : notExpr (AND notExpr)*
    ;

notExpr
    : NOT notExpr
    | compareExpr
    ;

compareExpr
    : addExpr (compareOp addExpr)*
    ;

compareOp
    : EQ | NEQ | LT | GT | LTE | GTE
    ;

addExpr
    : mulExpr ((PLUS | MINUS) mulExpr)*
    ;

mulExpr
    : unaryExpr ((STAR | SLASH | MOD) unaryExpr)*
    ;

unaryExpr
    : MINUS unaryExpr
    | memberExpression
    ;

// -- Member access chain ------------------------------------------------------
// Resuelve: TI.ITEM, TI.METHOD(args), TI[i].ITEM, CHANNEL!TI.ITEM,
//           TI..SysMethod(args), CHANNEL!Method(args)
memberExpression
    : primaryExpression (memberTail)*
    ;

memberTail
    : DOT DOT IDENTIFIER (LPAREN argList? RPAREN)?   // ..SysMethod(args) — system method
    | DOT HASH_REF                                    // .#ITEM — hash-prefixed item access
    | DOT IDENTIFIER (LPAREN argList? RPAREN)?        // .ITEM o .METHOD(args)
    | LBRACKET expression RBRACKET                    // [index]
    | BANG IDENTIFIER DOT IDENTIFIER (LPAREN argList? RPAREN)?
                                                      // !TI.ITEM o !TI.METHOD(args)
    | BANG IDENTIFIER (LPAREN argList? RPAREN)?        // !Method(args) o !TI (sin dot)
    ;

// -- Primary expressions ------------------------------------------------------
primaryExpression
    : LPAREN expression RPAREN                       // (expr)
    | IDENTIFIER LPAREN argList? RPAREN              // functionCall(args)
    | STRING_LITERAL
    | NUMBER_LITERAL
    | DATE_LITERAL                                   // {2025/10/31} o {4000-01-01 00:00:00}
    | HASH_REF                                       // #FUNC_NAME — hash reference
    | AT_REF                                         // @ITEM_NAME — at reference
    | IDENTIFIER                                     // variable, item, constante
    ;

argList
    : expression (COMMA expression)*
    ;

// ============================= LEXER RULES ==================================

// -- Keywords (case-insensitive) ----------------------------------------------
// Orden importa: keywords antes que IDENTIFIER para que ANTLR las priorice.
IF          : 'if' ;
THEN        : 'then' ;
ELSEIF      : 'elseif' ;
ELSE        : 'else' ;
ENDIF       : 'endif' ;
FOR         : 'for' ;
TO          : 'to' ;
STEP        : 'step' ;
NEXT        : 'next' ;
WHILE       : 'while' ;
WEND        : 'wend' ;
DO          : 'do' ;
LOOP        : 'loop' ;
UNTIL       : 'until' ;
RETURN      : 'return' ;
AND         : 'and' ;
OR          : 'or' ;
NOT         : 'not' ;

// -- Operators ----------------------------------------------------------------
NEQ         : '<>' ;
LTE         : '<=' ;
GTE         : '>=' ;
LT          : '<' ;
GT          : '>' ;
EQ          : '=' ;
PLUS        : '+' ;
MINUS       : '-' ;
STAR        : '*' ;
SLASH       : '/' ;
MOD         : '%' ;
DOT         : '.' ;
BANG        : '!' ;
COMMA       : ',' ;
COLON       : ':' ;
LPAREN      : '(' ;
RPAREN      : ')' ;
LBRACKET    : '[' ;
RBRACKET    : ']' ;

// -- Literals -----------------------------------------------------------------
STRING_LITERAL
    : '"' (~["\r\n])* '"'
    ;

NUMBER_LITERAL
    : [0-9]+ ('.' [0-9]+)?
    ;

// Date/datetime literals in braces: {2025/10/31}, {4000-01-01 00:00:00}
DATE_LITERAL
    : '{' ~[}\r\n]* '}'
    ;

// Hash reference: #FUNC_NAME — references to functions/items
HASH_REF
    : '#' [a-z_] [a-z0-9_]*
    ;

// At reference: @ITEM_NAME — references to items (common in LN4, 7770 rules)
AT_REF
    : '@' [a-z_] [a-z0-9_]*
    ;

// -- Identifiers --------------------------------------------------------------
// Captura variables, items, constantes (M4_TRUE, M4_FALSE, EQUAL, etc.)
// Nota: con caseInsensitive=true, [a-z] ya cubre A-Z; no repetir [a-zA-Z].
IDENTIFIER
    : [a-z_] [a-z0-9_]*
    ;

// -- Newlines (significativas: separan statements) ----------------------------
NL
    : '\r'? '\n'
    ;

// -- Whitespace (espacios, tabs, y non-breaking spaces se ignoran) ------------
WS
    : [ \t\u00A0]+ -> skip
    ;

// -- Comments (se ignoran) ----------------------------------------------------
LINE_COMMENT_QUOTE
    : '\'' ~[\r\n]* -> skip
    ;

LINE_COMMENT_SLASH
    : '//' ~[\r\n]* -> skip
    ;

BLOCK_COMMENT
    : '/*' .*? '*/' -> skip
    ;
