#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化工具模块
"""

from .browser_connector import BrowserConnector
from .table_data_manager import TableDataManager
from .element_module import ElementModule, ConditionConfig
from .element_module_manager import ElementModuleManager
from .automation_flow import AutomationFlow

__all__ = [
    'BrowserConnector',
    'TableDataManager',
    'ElementModule',
    'ConditionConfig',
    'ElementModuleManager',
    'AutomationFlow'
]
