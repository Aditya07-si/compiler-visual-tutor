from analyzer.syntax import ASTNode, Program, Block, VarDecl, Assignment, BinaryExpr, Literal, Identifier

def analyze_semantics(ast: ASTNode):
    """
    Detects semantic errors by traversing the AST:
    - Use of undeclared variables
    - Unused variables
    - Type Mismatch (e.g., string to int)
    """
    errors = []
    declared_variables = {}
    used_variables = set()
    
    def traverse(node):
        if not node:
            return
            
        if isinstance(node, Program):
            for stmt in node.statements:
                traverse(stmt)
                
        elif isinstance(node, Block):
            for stmt in node.statements:
                traverse(stmt)
                
        elif isinstance(node, VarDecl):
            if node.var_name in declared_variables:
                errors.append({
                    "type": "Semantic Error",
                    "code": "MULTIPLE_DECLARATION",
                    "message": f"Variable '{node.var_name}' is already declared.",
                    "line": node.line,
                    "column": 1,
                    "hint": f"Remove duplicate declaration of '{node.var_name}'.",
                    "suggestion": None,
                    "auto_corrected": False,
                    "recovery_method": "None"
                })
            else:
                declared_variables[node.var_name] = {"type": node.type_name, "line": node.line}
                
            if getattr(node, "init_expr", None) is not None:
                # Type Checking (very basic literal checks)
                if isinstance(node.init_expr, Literal) and node.init_expr.type_str == "STRING":
                    expected_type = node.type_name
                    if expected_type in ["int", "float", "long", "double"]:
                        errors.append({
                            "type": "Semantic Error",
                            "code": "TYPE_MISMATCH",
                            "message": f"Assigning a string literal to '{expected_type}' variable '{node.var_name}'.",
                            "line": node.line,
                            "column": 1,
                            "hint": f"Remove quotes for numbers, or change the type of '{node.var_name}'.",
                            "suggestion": None,
                            "auto_corrected": False,
                            "recovery_method": "None"
                        })
                traverse(node.init_expr)
                
        elif isinstance(node, Assignment):
            var_name = node.var_name
            if var_name not in declared_variables:
                errors.append({
                    "type": "Semantic Error",
                    "code": "UNDECLARED_VARIABLE",
                    "message": f"Variable '{var_name}' used without declaration.",
                    "line": node.line,
                    "column": 1,
                    "hint": f"Declare '{var_name}' (e.g., int {var_name};) before using it.",
                    "suggestion": None,
                    "auto_corrected": False,
                    "recovery_method": "None"
                })
            else:
                used_variables.add(var_name)
                # Type Checking (very basic literal checks)
                if isinstance(node.expr, Literal) and node.expr.type_str == "STRING":
                    expected_type = declared_variables[var_name]["type"]
                    if expected_type in ["int", "float"]:
                        errors.append({
                            "type": "Semantic Error",
                            "code": "TYPE_MISMATCH",
                            "message": f"Assigning a string literal to '{expected_type}' variable '{var_name}'.",
                            "line": node.line,
                            "column": 1,
                            "hint": f"Remove quotes for numbers, or change the type of '{var_name}'.",
                            "suggestion": None,
                            "auto_corrected": False,
                            "recovery_method": "None"
                        })
                        
            traverse(node.expr)
            
        elif isinstance(node, BinaryExpr):
            traverse(node.left)
            traverse(node.right)
            
        elif isinstance(node, Identifier):
            name = node.name.replace("()", "")
            # Ignore built-ins or implicitly allowed things
            if name not in declared_variables and name not in ["printf", "scanf", "main"]:
                # Often AST doesn't pass lines deep into Identifiers if we skimped on them, so use generic line 1 if missing. 
                # (We didn't add line tracking to Identifier but we can improve it later)
                errors.append({
                    "type": "Semantic Error",
                    "code": "UNDECLARED_VARIABLE",
                    "message": f"Variable '{name}' used without declaration.",
                    "line": getattr(node, "line", 1), # Fallback to 1 if missing
                    "column": 1,
                    "hint": f"Declare '{name}' before using it.",
                    "suggestion": None,
                    "auto_corrected": False,
                    "recovery_method": "None"
                })
            else:
                used_variables.add(name)

    traverse(ast)

    # Check for unused variables
    for var, info in declared_variables.items():
        if var not in used_variables:
            errors.append({
                "type": "Warning",
                "code": "UNUSED_VARIABLE",
                "message": f"Variable '{var}' is declared but never used.",
                "line": info["line"],
                "column": 1,
                "hint": "Consider removing unused variables to clean up your code.",
                "severity": "warning",
                "suggestion": "",
                "auto_corrected": True,
                "recovery_method": "None"
            })

    return errors
    """ new code for the scope and cound checking"""
"""from analyzer.syntax import ASTNode, Program, Block, VarDecl, Assignment, BinaryExpr, Literal, Identifier

class SymbolTable:
    """Manages hierarchical scopes for variables."""
    def __init__(self, parent=None):
        self.symbols = {}  # name -> {"type": str, "line": int, "size": int or None}
        self.parent = parent
        self.used_variables = set()

    def define(self, name, type_info):
        self.symbols[name] = type_info

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def mark_used(self, name):
        if name in self.symbols:
            self.used_variables.add(name)
        elif self.parent:
            self.parent.mark_used(name)

def analyze_semantics(ast: ASTNode):
    errors = []
    current_scope = SymbolTable()  # Global scope

    def add_error(code, message, node, hint="", severity="Semantic Error"):
        errors.append({
            "type": severity,
            "code": code,
            "message": message,
            "line": getattr(node, 'line', 1),
            "column": getattr(node, 'column', 1),
            "hint": hint,
            "auto_corrected": False
        })

    def visit(node):
        nonlocal current_scope
        if not node: return

        # --- Dispatcher Pattern for Optimization ---
        nodetype = type(node)
        
        if nodetype is Program or nodetype is Block:
            # Enter new scope
            previous_scope = current_scope
            current_scope = SymbolTable(parent=previous_scope)
            
            for stmt in node.statements:
                visit(stmt)
            
            # Check for unused variables in this scope before exiting
            for var, info in current_scope.symbols.items():
                if var not in current_scope.used_variables:
                    add_error("UNUSED_VARIABLE", f"'{var}' is never used.", info['node'], 
                              "Remove it to save memory.", "Warning")
            
            current_scope = previous_scope

        elif nodetype is VarDecl:
            if node.var_name in current_scope.symbols:
                add_error("MULTIPLE_DECLARATION", f"'{node.var_name}' already declared.", node)
            else:
                # Handle Array Sizes for Bound Checking
                array_size = getattr(node, "size", None)
                current_scope.define(node.var_name, {
                    "type": node.type_name, 
                    "line": node.line, 
                    "size": array_size,
                    "node": node
                })
            
            if getattr(node, "init_expr", None):
                visit(node.init_expr)

        elif nodetype is Assignment:
            info = current_scope.lookup(node.var_name)
            if not info:
                add_error("UNDECLARED_VARIABLE", f"'{node.var_name}' not declared.", node)
            else:
                current_scope.mark_used(node.var_name)
                
                # --- Array Bound Checking ---
                index_expr = getattr(node, "index", None)
                if index_expr:
                    if info["size"] is None:
                        add_error("NOT_AN_ARRAY", f"'{node.var_name}' is not an array.", node)
                    elif isinstance(index_expr, Literal) and index_expr.type_str == "INT":
                        idx_val = int(index_expr.value)
                        if idx_val < 0 or idx_val >= info["size"]:
                            add_error("OUT_OF_BOUNDS", 
                                     f"Index {idx_val} out of bounds for array '{node.var_name}' (size {info['size']}).", node)
                
                visit(node.expr)

        elif nodetype is Identifier:
            name = node.name.replace("()", "")
            if name not in ["printf", "scanf", "main"]:
                info = current_scope.lookup(name)
                if not info:
                    add_error("UNDECLARED_VARIABLE", f"'{name}' not declared.", node)
                else:
                    current_scope.mark_used(name)

        elif nodetype is BinaryExpr:
            visit(node.left)
            visit(node.right)

    visit(ast)
    return errors """
