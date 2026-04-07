from typing import List, Optional, Any
from analyzer.lexer import Token

class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class VarDecl(ASTNode):
    def __init__(self, type_name: str, var_name: str, line: int, init_expr: Optional['Expression'] = None):
        self.type_name = type_name
        self.var_name = var_name
        self.line = line
        self.init_expr = init_expr

class Expression(ASTNode):
    pass

class Assignment(Expression):
    def __init__(self, var_name: str, expr: Expression, line: int):
        self.var_name = var_name
        self.expr = expr
        self.line = line

class BinaryExpr(Expression):
    def __init__(self, left, op: str, right):
        self.left = left
        self.op = op
        self.right = right

class Literal(Expression):
    def __init__(self, value, type_str):
        self.value = value
        self.type_str = type_str

class Identifier(Expression):
    def __init__(self, name):
        self.name = name

class Block(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class ReturnStatement(ASTNode):
    def __init__(self, expr: Optional[Expression], line: int):
        self.expr = expr
        self.line = line

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors = []
        
    def peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]
        
    def advance(self) -> Token:
        t = self.peek()
        if t.type != "EOF":
            self.pos += 1
        return t
        
    def check(self, token_type: str, value: Optional[str] = None) -> bool:
        t = self.peek()
        if t.type == token_type:
            if value is None or t.value == value:
                return True
        return False
        
    def match(self, token_type: str, value: Optional[str] = None) -> bool:
        if self.check(token_type, value):
            self.advance()
            return True
        return False
        
    def consume(self, token_type: str, value: Optional[str], err_code: str, err_msg: str, hint: str) -> Token:
        if self.check(token_type, value):
            return self.advance()
            
        t = self.peek()
        # To get a better location, use the previous token if available
        prev_t = self.tokens[self.pos - 1] if self.pos > 0 else t
        line = prev_t.line
        col = prev_t.column + len(prev_t.value)
        
        self.errors.append({
            "type": "Syntax Error",
            "code": err_code,
            "message": err_msg,
            "line": line,
            "column": col,
            "hint": hint,
            "suggestion": None,
            "auto_corrected": False,
            "recovery_method": "Panic Mode" if err_code in ["MISSING_CLOSING_BRACE", "MISSING_PARENTHESIS", "MISSING_CLOSING_PARENTHESIS"] else "Statement Mode"
        })
        raise ParseError()

    def synchronize(self):
        """Panic-mode recovery: advance until a synchronization point."""
        if not self.check("EOF"):
            self.advance()
        while not self.check("EOF"):
            prev = self.tokens[self.pos - 1] if self.pos > 0 else None
            if prev and prev.value == ";":
                return
                
            t = self.peek()
            if t.type == "KEYWORD" and t.value in ["int", "float", "char", "if", "while", "for", "return"]:
                return
                
            if t.value == "{" or t.value == "}":
                return
                
            self.advance()

    def parse_program(self):
        statements = []
        while not self.check("EOF"):
            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            except ParseError:
                self.synchronize()
        return Program(statements)
        
    def parse_statement(self):
        t = self.peek()
        # 0. Empty statement (extra semicolons)
        if t.value == ";":
            self.advance()
            self.errors.append({
                "type": "Warning",
                "code": "EXTRA_SEMICOLON",
                "message": "Extra semicolon found.",
                "line": t.line,
                "column": t.column,
                "hint": "Remove the extra semicolon.",
                "suggestion": "",
                "auto_corrected": True,
                "recovery_method": "None"
            })
            return None
            
        # 1. Variable Declarations
        if t.type == "KEYWORD" and t.value in ["int", "float", "char"]:
            return self.parse_declaration()
            
        # 2. Block statement
        if t.value == "{":
            self.advance()
            stmts = []
            while not self.check("EOF") and not self.check("PUNCTUATION", "}"):
                try:
                    s = self.parse_statement()
                    if s: stmts.append(s)
                except ParseError:
                    self.synchronize()
            self.consume("PUNCTUATION", "}", "MISSING_CLOSING_BRACE", "Expected '}' to close block.", "Check for unmatched braces.")
            return Block(stmts)
            
        # Control structures - stubbed for minimal compliance, they would normally parse bodies
        if t.type == "KEYWORD" and t.value in ["if", "while", "for"]:
            self.advance()
            # Just skip the parenthesis condition for now if there are any to avoid complexity, or parse it as expressions
            if self.match("PUNCTUATION", "("):
                while not self.check("EOF") and not self.check("PUNCTUATION", ")"):
                    self.advance()
                self.consume("PUNCTUATION", ")", "MISSING_PARENTHESIS", "Expected ')' after condition.", "Close parenthesis.")
            # Then statement
            return self.parse_statement()
            
        if t.type == "KEYWORD" and t.value == "return":
            ret_line = t.line
            self.advance()
            ret_expr = None
            if not self.check("PUNCTUATION", ";"):
                ret_expr = self.parse_expression()
            if self.match("PUNCTUATION", ";"):
                pass
            return ReturnStatement(ret_expr, ret_line)
            
        # 3. Expression statement
        expr = self.parse_expression()
        if self.match("PUNCTUATION", ";"):
            pass
        return expr
        
    def parse_declaration(self):
        type_token = self.advance() # int, float, char
        
        # Support optional pointers like `char*` or `char *`
        if self.match("OPERATOR", "*"):
            type_token.value += "*"
            
        if not self.check("IDENTIFIER"):
            self.consume("IDENTIFIER", None, "MISSING_IDENTIFIER", "Expected variable name in declaration.", "Provide a valid variable name explicitly.")
            
        id_token = self.advance()
        
        # Check if it's a function declaration (e.g., int main() or int foo(int x))
        if self.match("PUNCTUATION", "("):
            # Parse parameters by skipping for now
            while not self.check("EOF") and not self.check("PUNCTUATION", ")"):
                self.advance()
            self.consume("PUNCTUATION", ")", "MISSING_CLOSING_PARENTHESIS", "Expected closing parenthesis for function.", "Add ')'.")
            
            # If there's a block, parse it
            if self.check("PUNCTUATION", "{"):
                return self.parse_statement()
            else:
                if self.match("PUNCTUATION", ";"):
                    pass
                return None
                
        decl = VarDecl(type_token.value, id_token.value, id_token.line)
        
        # Variable Initialization
        if self.match("OPERATOR", "="):
            expr = self.parse_expression()
            decl.init_expr = expr
            
        if self.match("PUNCTUATION", ";"):
            pass
            
        return decl
        
    def parse_expression(self):
        return self.parse_equality()
        
    def parse_equality(self):
        expr = self.parse_comparison()
        while self.match("OPERATOR", "==") or self.match("OPERATOR", "!="):
            op = self.tokens[self.pos - 1]
            right = self.parse_comparison()
            expr = BinaryExpr(expr, op.value, right)
        return expr
        
    def parse_comparison(self):
        expr = self.parse_term()
        while self.match("OPERATOR", "<") or self.match("OPERATOR", "<=") or \
              self.match("OPERATOR", ">") or self.match("OPERATOR", ">="):
            op = self.tokens[self.pos - 1]
            right = self.parse_term()
            expr = BinaryExpr(expr, op.value, right)
        return expr
        
    def parse_term(self):
        expr = self.parse_factor()
        while self.match("OPERATOR", "+") or self.match("OPERATOR", "-"):
            op = self.tokens[self.pos - 1]
            right = self.parse_factor()
            expr = BinaryExpr(expr, op.value, right)
        return expr
        
    def parse_factor(self):
        expr = self.parse_primary()
        while self.match("OPERATOR", "*") or self.match("OPERATOR", "/"):
            op = self.tokens[self.pos - 1]
            right = self.parse_primary()
            expr = BinaryExpr(expr, op.value, right)
        return expr
        
    def parse_primary(self):
        if self.match("NUMBER"):
            return Literal(self.tokens[self.pos - 1].value, "NUMBER")
        if self.match("STRING"):
            return Literal(self.tokens[self.pos - 1].value, "STRING")
        if self.match("IDENTIFIER"):
            id_t = self.tokens[self.pos - 1]
            
            # Assignment handling inside an expression statement
            if self.match("OPERATOR", "="):
                val = self.parse_expression()
                return Assignment(id_t.value, val, id_t.line)
                
            # Function call checking
            if self.match("PUNCTUATION", "("):
                while not self.check("EOF") and not self.check("PUNCTUATION", ")"):
                    self.advance()
                self.consume("PUNCTUATION", ")", "MISSING_CLOSING_PARENTHESIS", "Expected closing parenthesis.", "Add closing parenthesis ')'.")
                return Identifier(f"{id_t.value}()")
                
            return Identifier(id_t.value)
            
        if self.match("PUNCTUATION", "("):
            expr = self.parse_expression()
            self.consume("PUNCTUATION", ")", "MISSING_CLOSING_PARENTHESIS", "Expected ')' after expression.", "Add a closing parenthesis.")
            return expr
            
        # Error path
        t = self.peek()
        self.errors.append({
            "type": "Syntax Error",
            "code": "UNEXPECTED_TOKEN",
            "message": f"Unexpected token '{t.value}'.",
            "line": t.line,
            "column": t.column,
            "hint": "Check your syntax here. This token isn't allowed in this expression.",
            "suggestion": None,
            "auto_corrected": False,
            "recovery_method": "Panic Mode"
        })
        raise ParseError()

def analyze_syntax(tokens: List[Token]):
    """
    Parses a token stream into an AST.
    Returns a tuple (ast_root, syntax_errors).
    """
    parser = Parser(tokens)
    ast = parser.parse_program()
    return ast, parser.errors
