# Generated from ln4_lsp/grammar/LN4.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .LN4Parser import LN4Parser
else:
    from LN4Parser import LN4Parser

# This class defines a complete generic visitor for a parse tree produced by LN4Parser.

class LN4Visitor(ParseTreeVisitor):

    # Visit a parse tree produced by LN4Parser#program.
    def visitProgram(self, ctx:LN4Parser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#statementList.
    def visitStatementList(self, ctx:LN4Parser.StatementListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#separator.
    def visitSeparator(self, ctx:LN4Parser.SeparatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#statement.
    def visitStatement(self, ctx:LN4Parser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#ifBlock.
    def visitIfBlock(self, ctx:LN4Parser.IfBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#elseIfBlock.
    def visitElseIfBlock(self, ctx:LN4Parser.ElseIfBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#elseBlock.
    def visitElseBlock(self, ctx:LN4Parser.ElseBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#inlineStatements.
    def visitInlineStatements(self, ctx:LN4Parser.InlineStatementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#inlineStmt.
    def visitInlineStmt(self, ctx:LN4Parser.InlineStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#forBlock.
    def visitForBlock(self, ctx:LN4Parser.ForBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#whileBlock.
    def visitWhileBlock(self, ctx:LN4Parser.WhileBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#doBlock.
    def visitDoBlock(self, ctx:LN4Parser.DoBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#returnStatement.
    def visitReturnStatement(self, ctx:LN4Parser.ReturnStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#assignmentOrCall.
    def visitAssignmentOrCall(self, ctx:LN4Parser.AssignmentOrCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#expression.
    def visitExpression(self, ctx:LN4Parser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#orExpr.
    def visitOrExpr(self, ctx:LN4Parser.OrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#andExpr.
    def visitAndExpr(self, ctx:LN4Parser.AndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#notExpr.
    def visitNotExpr(self, ctx:LN4Parser.NotExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#compareExpr.
    def visitCompareExpr(self, ctx:LN4Parser.CompareExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#compareOp.
    def visitCompareOp(self, ctx:LN4Parser.CompareOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#addExpr.
    def visitAddExpr(self, ctx:LN4Parser.AddExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#mulExpr.
    def visitMulExpr(self, ctx:LN4Parser.MulExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#unaryExpr.
    def visitUnaryExpr(self, ctx:LN4Parser.UnaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#memberExpression.
    def visitMemberExpression(self, ctx:LN4Parser.MemberExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#memberTail.
    def visitMemberTail(self, ctx:LN4Parser.MemberTailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#primaryExpression.
    def visitPrimaryExpression(self, ctx:LN4Parser.PrimaryExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LN4Parser#argList.
    def visitArgList(self, ctx:LN4Parser.ArgListContext):
        return self.visitChildren(ctx)



del LN4Parser