import ast
import io
import os
import tokenize
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")


def python_files():
    for folder, _, files in os.walk(ROOT):
        if ".git" in folder.split(os.sep):
            continue
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(folder, name)


class TestSourceStyle(unittest.TestCase):
    def test_no_comments(self):
        for path in python_files():
            with open(path, encoding="utf-8") as f:
                source = f.read()
            for token in tokenize.generate_tokens(io.StringIO(source).readline):
                self.assertNotEqual(token.type, tokenize.COMMENT, f"{path}: comment found")

    def test_no_docstrings(self):
        for path in python_files():
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.assertIsNone(ast.get_docstring(node), f"{path}: docstring found")

    def test_no_arabic_text(self):
        for path in python_files():
            with open(path, encoding="utf-8") as f:
                source = f.read()
            for ch in source:
                self.assertFalse("\u0600" <= ch <= "\u06ff", f"{path}: Arabic character found")


if __name__ == "__main__":
    unittest.main()
