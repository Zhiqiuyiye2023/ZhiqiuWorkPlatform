#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元素模块管理器模块
"""
import json
import re
from typing import List, Dict, Any, Optional, Union
from .element_module import ElementModule
from .condition_module import ConditionModule
from DrissionPage import ChromiumPage


class ElementModuleManager:
    """元素模块管理器，负责管理多个元素模块"""
    
    def __init__(self):
        """
        初始化元素模块管理器"""
        self.modules = []  # 存储所有模块，包括普通模块和条件模块
        self.module_counter = 0
    
    def add_module(self, name: str, index: Optional[int] = None) -> ElementModule:
        """
        添加新的元素模块
        :param name: 模块名称
        :param index: 模块添加的位置索引，None表示添加到末尾
        :return: 新创建的元素模块实例
        """
        module_id = f"module_{self.module_counter}"
        self.module_counter += 1
        module = ElementModule(module_id, name)
        if index is None or index >= len(self.modules):
            self.modules.append(module)
        else:
            self.modules.insert(index, module)
        return module
    
    def add_condition_module(self, name: str, index: Optional[int] = None) -> ConditionModule:
        """
        添加新的条件模块
        :param name: 模块名称
        :param index: 模块添加的位置索引，None表示添加到末尾
        :return: 新创建的条件模块实例
        """
        module_id = f"condition_{self.module_counter}"
        self.module_counter += 1
        module = ConditionModule(module_id, name)
        if index is None or index >= len(self.modules):
            self.modules.append(module)
        else:
            self.modules.insert(index, module)
        return module
    
    def get_module(self, module_id: str) -> Optional[Union[ElementModule, ConditionModule]]:
        """
        获取指定ID的模块
        :param module_id: 模块ID
        :return: 模块实例，未找到返回None
        """
        for module in self.modules:
            if module.module_id == module_id:
                return module
        return None
    
    def remove_module(self, module_id: str) -> bool:
        """
        删除指定ID的模块
        :param module_id: 模块ID
        :return: 删除成功返回True，失败返回False
        """
        for i, module in enumerate(self.modules):
            if module.module_id == module_id:
                del self.modules[i]
                return True
        return False
    
    def reorder_modules(self, module_order: List[str]) -> None:
        """
        重新排序元素模块
        :param module_order: 新的模块ID顺序列表
        """
        # 创建模块ID到模块对象的映射
        module_map = {module.module_id: module for module in self.modules}
        
        # 按照新的顺序重新组织模块列表
        new_modules = []
        for module_id in module_order:
            if module_id in module_map:
                new_modules.append(module_map[module_id])
        
        # 保留未在order中出现的模块
        for module in self.modules:
            if module.module_id not in module_order:
                new_modules.append(module)
        
        self.modules = new_modules
    
    def get_module_order(self) -> List[str]:
        """
        获取当前模块顺序
        :return: 模块ID顺序列表
        """
        return [module.module_id for module in self.modules]
    
    def get_all_modules(self) -> List[Union[ElementModule, ConditionModule]]:
        """
        获取所有模块，包括普通模块和条件模块
        :return: 模块列表
        """
        return self.modules.copy()
    
    def clear(self) -> None:
        """
        清空所有元素模块
        """
        self.modules.clear()
        self.module_counter = 0
    
    def execute_all(self, page: ChromiumPage, variables: Dict[str, str]) -> bool:
        """
        执行所有元素模块
        :param page: 浏览器页面实例
        :param variables: 可用变量字典
        :return: 所有模块执行成功返回True，否则返回False
        """
        # 创建变量字典的副本，以便在执行过程中更新
        current_variables = variables.copy()
        
        # 执行所有模块
        print(f"\n{'='*50}")
        print(f"开始处理记录: {variables}")
        print(f"{'='*50}")
        
        i = 0
        module_count = len(self.modules)
        loop_stack = []  # 用于存储循环信息的栈：(start_index, loop_module, loop_count, current_iteration)
        
        while i < module_count and len(loop_stack) < 10:  # 防止无限循环，最多支持10层嵌套
            module = self.modules[i]
            print(f"\n当前执行第 {i+1}/{module_count} 个模块: {module.name}")
            
            # 检查模块类型
            if isinstance(module, ElementModule):
                # 普通元素模块，正常执行
                print(f"模块操作类型: {module.action_type}")
                print(f"模块XPath: {module.xpath}")
                print(f"模块操作值: {module.action_value} (变量: {module.is_variable})")
                print(f"模块等待时间: {module.wait_time}秒")
                
                # 正常执行模块
                result, value = module.execute(page, current_variables)
                if not result:
                    print(f"模块 '{module.name}' 执行失败")
                    return False
                
                # 对于获取文本操作，直接以模块名作为变量名
                if module.action_type == "获取文本" and value is not None:
                    current_variables[module.name] = value
                    print(f"元素模块 '{module.name}' 将值 '{value}' 存储为变量 '{module.name}'")
                # 对于其他操作，如果配置了变量名称且获取到了值，将其存储到变量字典中
                elif module.variable_name and value is not None:
                    current_variables[module.variable_name] = value
                    print(f"元素模块 '{module.name}' 将值 '{value}' 存储为变量 '{module.variable_name}'")
                
                i += 1
            else:
                # ConditionModule，处理循环逻辑
                print(f"条件模块类型: {module.condition_type}")
                print(f"循环类型: {module.loop_type}")
                
                if module.loop_type == "开始循环":
                    # 计算循环次数
                    loop_count = 1  # 默认循环1次
                    if module.is_table_field and module.table_field in current_variables:
                        # 从表格字段获取循环次数，支持从字符串中提取整数
                        try:
                            field_value = current_variables[module.table_field]
                            # 尝试直接转换为整数
                            loop_count = int(field_value)
                        except (ValueError, TypeError):
                            # 如果直接转换失败，尝试从字符串中提取整数
                            try:
                                field_value = str(current_variables[module.table_field])
                                # 使用正则表达式提取第一个整数
                                match = re.search(r'\d+', field_value)
                                if match:
                                    loop_count = int(match.group())
                                else:
                                    loop_count = 1  # 没有找到整数，使用默认值
                            except Exception:
                                loop_count = 1
                    elif module.is_variable and module.variable_name in current_variables:
                        # 从变量获取循环次数，支持从字符串中提取整数
                        try:
                            variable_value = current_variables[module.variable_name]
                            # 尝试直接转换为整数
                            loop_count = int(variable_value)
                        except (ValueError, TypeError):
                            # 如果直接转换失败，尝试从字符串中提取整数
                            try:
                                variable_value = str(current_variables[module.variable_name])
                                # 使用正则表达式提取第一个整数
                                match = re.search(r'\d+', variable_value)
                                if match:
                                    loop_count = int(match.group())
                                else:
                                    loop_count = 1  # 没有找到整数，使用默认值
                            except Exception:
                                loop_count = 1
                    elif module.loop_count.isdigit():
                        # 固定次数
                        loop_count = int(module.loop_count)
                    
                    print(f"开始循环，循环次数: {loop_count}")
                    
                    # 将循环信息压入栈
                    loop_stack.append((i, module, loop_count, 0))
                    i += 1  # 继续执行下一个模块
                
                elif module.loop_type == "结束循环":
                    # 处理结束循环
                    if loop_stack:
                        # 从栈中弹出最近的循环信息
                        start_index, loop_module, loop_count, current_iteration = loop_stack.pop()
                        current_iteration += 1
                        
                        if current_iteration < loop_count:
                            # 还需要继续循环，将循环信息重新压入栈，并跳转到循环开始位置
                            print(f"结束循环，当前循环第 {current_iteration} 次，共需循环 {loop_count} 次，继续下一次循环")
                            loop_stack.append((start_index, loop_module, loop_count, current_iteration))
                            i = start_index + 1  # 跳转到循环开始后的第一个模块
                        else:
                            # 循环结束
                            print(f"结束循环，共循环 {current_iteration} 次，循环结束")
                            i += 1  # 继续执行下一个模块
                    else:
                        # 没有对应的开始循环，忽略该结束循环模块
                        print("警告：遇到结束循环模块，但没有对应的开始循环模块，忽略该模块")
                        i += 1
                
                else:
                    # 未知的循环类型，忽略
                    i += 1
        
        # 清理所有未结束的循环
        if loop_stack:
            print(f"警告：存在 {len(loop_stack)} 个未结束的循环")
        
        # 将更新后的变量字典合并回原始字典，以便外部使用
        variables.update(current_variables)
        
        print(f"\n{'='*50}")
        print(f"记录处理完成: {variables}")
        print(f"{'='*50}")
        
        return True
    
    def save_config(self, file_path: str) -> bool:
        """
        保存模块配置，包括普通模块和条件模块
        :param file_path: 配置文件路径
        :return: 保存成功返回True，失败返回False
        """
        try:
            config = {
                "modules": [module.to_dict() for module in self.modules],
                "module_counter": self.module_counter
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def load_config(self, file_path: str) -> bool:
        """
        加载模块配置，包括普通模块和条件模块
        :param file_path: 配置文件路径
        :return: 加载成功返回True，失败返回False
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 加载模块，区分普通模块和条件模块
            self.modules = []
            for data in config.get("modules", []):
                if "condition_type" in data:
                    # 条件模块
                    module = ConditionModule.from_dict(data)
                else:
                    # 普通元素模块
                    module = ElementModule.from_dict(data)
                self.modules.append(module)
            
            self.module_counter = config.get("module_counter", 0)
            
            return True
        except Exception as e:
            print(f"加载配置失败: {e}")
            return False
