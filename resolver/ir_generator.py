import json
from analyzer.syntax import ASTNode, Program, Block, VarDecl, Assignment, BinaryExpr, Literal, Identifier, ReturnStatement

class IRGenerator:
    def __init__(self):
        self.code = []
        self.temp_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def emit(self, instruction: str):
        self.code.append(instruction)

    def generate(self, node: ASTNode) -> list:
        self.code = []
        self.temp_count = 0
        self._traverse(node)
        return self.code

    def _traverse(self, node: ASTNode):
        if not node:
            return None
            
        if isinstance(node, Program) or isinstance(node, Block):
            for stmt in node.statements:
                self._traverse(stmt)
                
        elif isinstance(node, VarDecl):
            if getattr(node, "init_expr", None) is not None:
                val = self._traverse(node.init_expr)
                self.emit(f"{node.var_name} = {val}")
                
        elif isinstance(node, Assignment):
            val = self._traverse(node.expr)
            self.emit(f"{node.var_name} = {val}")
            
        elif isinstance(node, BinaryExpr):
            left_val = self._traverse(node.left)
            right_val = self._traverse(node.right)
            t = self.new_temp()
            self.emit(f"{t} = {left_val} {node.op} {right_val}")
            return t
            
        elif isinstance(node, Literal):
            return str(node.value)
            
        elif isinstance(node, Identifier):
            # If function call like printf(), just ignore for TAC in this simplified scenario, or emit call
            if node.name.endswith("()"):
                t = self.new_temp()
                self.emit(f"{t} = call {node.name[:-2]}")
                return t
            return node.name
            
        elif isinstance(node, ReturnStatement):
            if getattr(node, "expr", None) is not None:
                val = self._traverse(node.expr)
                self.emit(f"return {val}")
            else:
                self.emit("return")
                
        return None

def generate_ir(ast: ASTNode):
    generator = IRGenerator()
    return generator.generate(ast)
