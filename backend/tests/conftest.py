"""Pytest config — make the backend root importable (auditors use absolute
imports like `from models.schemas import ...`)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
