import ast
import operator as op
from kivy import require
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.metrics import dp
import ctypes

require('2.0.0')
_kivy_file = "./calc.kv"

# get the native window handle
hwnd = ctypes.windll.user32.GetActiveWindow()

# window styles
GWL_STYLE = -16
WS_MAXIMIZEBOX = 0x00010000  # maximize button
WS_THICKFRAME   = 0x00040000  # resizable border

# get current style
style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)

# remove maximize button and resize border
style &= ~WS_MAXIMIZEBOX
style &= ~WS_THICKFRAME

# apply new style
ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)

FONTS = {
    "regular": 'data/fonts/JetBrainsMono-Regular.ttf',
    "italic": 'data/fonts/JetBrainsMono-Italic.ttf',
    "bold": 'data/fonts/JetBrainsMono-Bold.ttf',
    "bold_italic": 'data/fonts/JetBrainsMono-BoldItalic.ttf',
}

def get_font(bold=False, italic=False):
    if bold and italic:
        return FONTS["bold_italic"]
    elif bold:
        return FONTS["bold"]
    elif italic:
        return FONTS["italic"]
    return FONTS["regular"]


ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

def safe_eval(expr: str):
    try:
        node = ast.parse(expr, mode="eval")
    except Exception as e:
        raise ValueError("Syntax error") from e

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in ALLOWED_OPERATORS:
                try:
                    return ALLOWED_OPERATORS[op_type](left, right)
                except Exception as e:
                    raise ValueError("Math error") from e
            raise ValueError(f"Operator {op_type} not allowed")
        if isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in ALLOWED_OPERATORS:
                return ALLOWED_OPERATORS[op_type](operand)
            raise ValueError("Unary operator not allowed")
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers allowed")
        if isinstance(node, ast.Num):
            return node.n
        raise ValueError("Unsupported expression")
    result = _eval(node)
    if isinstance(result, float) and result.is_integer():
        return int(result)
    return result

class CalcLayout(BoxLayout):
    display = StringProperty("")

    def append_text(self, txt: str):
        self.display += txt

    def clear(self):
        self.display = ""

    def backspace(self):
        self.display = self.display[:-1]

    def negate(self):
        if not self.display:
            return
        try:
            val = safe_eval(self.display)
            self.display = f"({-val})"
        except Exception:
            s = self.display
            for i in range(len(s)-1, -1, -1):
                if s[i] in "+-*/%(":
                    self.display = s[:i+1] + "(-" + s[i+1:] + ")"
                    return
            self.display = "(-" + self.display + ")"

    def calculate(self):
        expr = self.display.strip()
        if not expr:
            return
        try:
            result = safe_eval(expr)
            self.display = str(result)
        except Exception:
            self.display = "Error"

class CalculatorApp(App):
    def get_font(self, **kwargs):
        return get_font(**kwargs)
    
    def build(self):
        self.title = "Ali Almasi - Calculator"
        Builder.load_file(_kivy_file)
        Window.size = (dp(400), dp(710))
        Window.bind(on_key_down=self._on_keyboard_down)
        return CalcLayout()
    

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        root = self.root
        if not root:
            return
        if codepoint and codepoint in "0123456789+-*/().%":
            root.append_text(codepoint)
            return True
        if key in (13, 271):
            root.calculate()
            return True
        if key == 8:
            root.backspace()
            return True
        if key == 27:
            root.clear()
            return True
        return False

if __name__ == "__main__":
    CalculatorApp().run()
