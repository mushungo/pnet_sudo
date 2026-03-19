# Generated from ln4_lsp/grammar/LN4.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .LN4Parser import LN4Parser
else:
    from LN4Parser import LN4Parser

# This class defines a complete listener for a parse tree produced by LN4Parser.
class LN4Listener(ParseTreeListener):

    # Enter a parse tree produced by LN4Parser#program.
    def enterProgram(self, ctx:LN4Parser.ProgramContext):
        pass

    # Exit a parse tree produced by LN4Parser#program.
    def exitProgram(self, ctx:LN4Parser.ProgramContext):
        pass


    # Enter a parse tree produced by LN4Parser#statementList.
    def enterStatementList(self, ctx:LN4Parser.StatementListContext):
        pass

    # Exit a parse tree produced by LN4Parser#statementList.
    def exitStatementList(self, ctx:LN4Parser.StatementListContext):
        pass


    # Enter a parse tree produced by LN4Parser#separator.
    def enterSeparator(self, ctx:LN4Parser.SeparatorContext):
        pass

    # Exit a parse tree produced by LN4Parser#separator.
    def exitSeparator(self, ctx:LN4Parser.SeparatorContext):
        pass


    # Enter a parse tree produced by LN4Parser#statement.
    def enterStatement(self, ctx:LN4Parser.StatementContext):
        pass

    # Exit a parse tree produced by LN4Parser#statement.
    def exitStatement(self, ctx:LN4Parser.StatementContext):
        pass


    # Enter a parse tree produced by LN4Parser#ifBlock.
    def enterIfBlock(self, ctx:LN4Parser.IfBlockContext):
        pass

    # Exit a parse tree produced by LN4Parser#ifBlock.
    def exitIfBlock(self, ctx:LN4Parser.IfBlockContext):
        pass


    # Enter a parse tree produced by LN4Parser#elseIfBlock.
    def enterElseIfBlock(self, ctx:LN4Parser.ElseIfBlockContext):
        pass

    # Exit a parse tree produced by LN4Parser#elseIfBlock.
    def exitElseIfBlock(self, ctx:LN4Parser.ElseIfBlockContext):
        pass


    # Enter a parse tree produced by LN4Parser#elseBlock.
    def enterElseBlock(self, ctx:LN4Parser.ElseBlockContext):
        pass

    # Exit a parse tree produced by LN4Parser#elseBlock.
    def exitElseBlock(self, ctx:LN4Parser.ElseBlockContext):
        pass


    # Enter a parse tree produced by LN4Parser#inlineStatements.
    def enterInlineStatements(self, ctx:LN4Parser.InlineStatementsContext):
        pass

    # Exit a parse tree produced by LN4Parser#inlineStatements.
    def exitInlineStatements(self, ctx:LN4Parser.InlineStatementsContext):
        pass


    # Enter a parse tree produced by LN4Parser#inlineStmt.
    def enterInlineStmt(self, ctx:LN4Parser.InlineStmtContext):
        pass

    # Exit a parse tree produced by LN4Parser#inlineStmt.
    def exitInlineStmt(self, ctx:LN4Parser.InlineStmtContext):
        pass


    # Enter a parse tree produced by LN4Parser#forBlock.
    def enterForBlock(self, ctx:LN4Parser.ForBlockContext):
        pass

    # Exit a parse tree produced by LN4Parser#forBlock.
    def exitForBlock(self, ctx:LN4Parser.ForBlockContext):
        pass


    # Enter a parse tree produced by LN4Parser#whileBlock.
    def enterWhileBlock(self, ctx:LN4Parser.WhileBlockContext):
        pass

    # Exit a parse tree produced by LN4Parser#whileBlock.
    def exitWhileBlock(self, ctx:LN4Parser.WhileBlockContext):
        pass


    # Enter a parse tree produced by LN4Parser#doBlock.
    def enterDoBlock(self, ctx:LN4Parser.DoBlockContext):
        pass

    # Exit a parse tree produced by LN4Parser#doBlock.
    def exitDoBlock(self, ctx:LN4Parser.DoBlockContext):
        pass


    # Enter a parse tree produced by LN4Parser#returnStatement.
    def enterReturnStatement(self, ctx:LN4Parser.ReturnStatementContext):
        pass

    # Exit a parse tree produced by LN4Parser#returnStatement.
    def exitReturnStatement(self, ctx:LN4Parser.ReturnStatementContext):
        pass


    # Enter a parse tree produced by LN4Parser#assignmentOrCall.
    def enterAssignmentOrCall(self, ctx:LN4Parser.AssignmentOrCallContext):
        pass

    # Exit a parse tree produced by LN4Parser#assignmentOrCall.
    def exitAssignmentOrCall(self, ctx:LN4Parser.AssignmentOrCallContext):
        pass


    # Enter a parse tree produced by LN4Parser#expression.
    def enterExpression(self, ctx:LN4Parser.ExpressionContext):
        pass

    # Exit a parse tree produced by LN4Parser#expression.
    def exitExpression(self, ctx:LN4Parser.ExpressionContext):
        pass


    # Enter a parse tree produced by LN4Parser#orExpr.
    def enterOrExpr(self, ctx:LN4Parser.OrExprContext):
        pass

    # Exit a parse tree produced by LN4Parser#orExpr.
    def exitOrExpr(self, ctx:LN4Parser.OrExprContext):
        pass


    # Enter a parse tree produced by LN4Parser#andExpr.
    def enterAndExpr(self, ctx:LN4Parser.AndExprContext):
        pass

    # Exit a parse tree produced by LN4Parser#andExpr.
    def exitAndExpr(self, ctx:LN4Parser.AndExprContext):
        pass


    # Enter a parse tree produced by LN4Parser#notExpr.
    def enterNotExpr(self, ctx:LN4Parser.NotExprContext):
        pass

    # Exit a parse tree produced by LN4Parser#notExpr.
    def exitNotExpr(self, ctx:LN4Parser.NotExprContext):
        pass


    # Enter a parse tree produced by LN4Parser#compareExpr.
    def enterCompareExpr(self, ctx:LN4Parser.CompareExprContext):
        pass

    # Exit a parse tree produced by LN4Parser#compareExpr.
    def exitCompareExpr(self, ctx:LN4Parser.CompareExprContext):
        pass


    # Enter a parse tree produced by LN4Parser#compareOp.
    def enterCompareOp(self, ctx:LN4Parser.CompareOpContext):
        pass

    # Exit a parse tree produced by LN4Parser#compareOp.
    def exitCompareOp(self, ctx:LN4Parser.CompareOpContext):
        pass


    # Enter a parse tree produced by LN4Parser#addExpr.
    def enterAddExpr(self, ctx:LN4Parser.AddExprContext):
        pass

    # Exit a parse tree produced by LN4Parser#addExpr.
    def exitAddExpr(self, ctx:LN4Parser.AddExprContext):
        pass


    # Enter a parse tree produced by LN4Parser#mulExpr.
    def enterMulExpr(self, ctx:LN4Parser.MulExprContext):
        pass

    # Exit a parse tree produced by LN4Parser#mulExpr.
    def exitMulExpr(self, ctx:LN4Parser.MulExprContext):
        pass


    # Enter a parse tree produced by LN4Parser#unaryExpr.
    def enterUnaryExpr(self, ctx:LN4Parser.UnaryExprContext):
        pass

    # Exit a parse tree produced by LN4Parser#unaryExpr.
    def exitUnaryExpr(self, ctx:LN4Parser.UnaryExprContext):
        pass


    # Enter a parse tree produced by LN4Parser#memberExpression.
    def enterMemberExpression(self, ctx:LN4Parser.MemberExpressionContext):
        pass

    # Exit a parse tree produced by LN4Parser#memberExpression.
    def exitMemberExpression(self, ctx:LN4Parser.MemberExpressionContext):
        pass


    # Enter a parse tree produced by LN4Parser#memberTail.
    def enterMemberTail(self, ctx:LN4Parser.MemberTailContext):
        pass

    # Exit a parse tree produced by LN4Parser#memberTail.
    def exitMemberTail(self, ctx:LN4Parser.MemberTailContext):
        pass


    # Enter a parse tree produced by LN4Parser#primaryExpression.
    def enterPrimaryExpression(self, ctx:LN4Parser.PrimaryExpressionContext):
        pass

    # Exit a parse tree produced by LN4Parser#primaryExpression.
    def exitPrimaryExpression(self, ctx:LN4Parser.PrimaryExpressionContext):
        pass


    # Enter a parse tree produced by LN4Parser#argList.
    def enterArgList(self, ctx:LN4Parser.ArgListContext):
        pass

    # Exit a parse tree produced by LN4Parser#argList.
    def exitArgList(self, ctx:LN4Parser.ArgListContext):
        pass



del LN4Parser