#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
条件模块类，封装循环条件配置
"""
from typing import List, Dict, Any, Optional


class ConditionModule:
    """条件模块类，封装循环条件配置"""
    
    def __init__(self, module_id: str, name: str):
        """
        初始化条件模块
        :param module_id: 模块唯一标识符
        :param name: 模块名称
        """
        self.module_id = module_id
        self.name = name
        self.condition_type = "循环条件"  # 当前只支持循环条件
        self.loop_type = "开始循环"  # 循环类型：开始循环或结束循环
        self.loop_count = "1"  # 循环次数
        self.is_variable = False  # 是否使用变量作为循环次数
        self.variable_name = ""  # 变量名称
        self.is_table_field = False  # 是否使用表格字段作为循环次数
        self.table_field = ""  # 表格字段名称
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将条件模块转换为字典
        :return: 条件模块字典
        """
        return {
            "module_id": self.module_id,
            "name": self.name,
            "condition_type": self.condition_type,
            "loop_type": self.loop_type,
            "loop_count": self.loop_count,
            "is_variable": self.is_variable,
            "variable_name": self.variable_name,
            "is_table_field": self.is_table_field,
            "table_field": self.table_field
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConditionModule":
        """
        从字典创建条件模块
        :param data: 条件模块字典
        :return: 条件模块实例
        """
        module = cls(data["module_id"], data["name"])
        module.condition_type = data.get("condition_type", "循环条件")
        module.loop_type = data.get("loop_type", "开始循环")
        module.loop_count = data.get("loop_count", "1")
        module.is_variable = data.get("is_variable", False)
        module.variable_name = data.get("variable_name", "")
        module.is_table_field = data.get("is_table_field", False)
        module.table_field = data.get("table_field", "")
        return module
