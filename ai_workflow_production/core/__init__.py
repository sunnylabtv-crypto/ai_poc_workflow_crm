# core/__init__.py

"""
AI Workflow Production - Core Package

워크플로우 엔진:
- WorkflowEngine: 이메일 자동 처리 엔진
"""

from .workflow_engine import WorkflowEngine

__all__ = ['WorkflowEngine']

__version__ = '2.0.0'