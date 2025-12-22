#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元素模块管理器模块
"""
import json
from typing import List, Dict, Any, Optional
from .element_module import ElementModule
from DrissionPage import ChromiumPage


class ElementModuleManager:
    """元素模块管理器，负责管理多个元素模块"""
    
    def __init__(self):
        """
        初始化元素模块管理器"""
        self.modules = []
        self.module_counter = 0
    
    def add_module(self, name: str) -> ElementModule:
        """
        添加新的元素模块
        :param name: 模块名称
        :return: 新创建的元素模块实例
        """
        module_id = f"module_{self.module_counter}"
        self.module_counter += 1
        module = ElementModule(module_id, name)
        self.modules.append(module)
        return module
    
    def get_module(self, module_id: str) -> Optional[ElementModule]:
        """
        获取指定ID的元素模块
        :param module_id: 模块ID
        :return: 元素模块实例，未找到返回None
        """
        for module in self.modules:
            if module.module_id == module_id:
                return module
        return None
    
    def remove_module(self, module_id: str) -> bool:
        """
        删除指定ID的元素模块
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
    
    def get_all_modules(self) -> List[ElementModule]:
        """
        获取所有元素模块
        :return: 元素模块列表
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
        i = 0
        print(f"\n{'='*50}")
        print(f"开始处理记录: {variables}")
        print(f"{'='*50}")
        
        while i < len(self.modules):
            module = self.modules[i]
            print(f"\n当前执行第 {i+1}/{len(self.modules)} 个模块: {module.name}")
            print(f"模块操作类型: {module.action_type}")
            print(f"模块XPath: {module.xpath}")
            print(f"模块操作值: {module.action_value} (变量: {module.is_variable})")
            print(f"模块等待时间: {module.wait_time}秒")
            
            # 检查是否需要循环执行模块链
            if hasattr(module, 'loop_start_module') and module.loop_start_module:
                # 找到起始模块的索引
                start_index = -1
                for idx, m in enumerate(self.modules):
                    if m.module_id == module.loop_start_module:
                        start_index = idx
                        break
                
                if start_index != -1 and start_index < i:  # 确保起始模块在当前模块之前
                    # 先检查当前模块的文本是否已经与变量内容一致，只有不一致时才执行循环
                    print(f"开始执行循环链：从模块 {self.modules[start_index].name} 到模块 {module.name}  ")
                    print(f"应该是先比对是否与变量内容一致，不一致才执行循环")
                    
                    # 先执行一次当前模块的比对
                    result, value = module.execute(page, current_variables)
                    if result:
                        print(f"当前模块 '{module.name}' 比对已成功，跳过循环")
                        # 如果模块配置了变量名称且获取到了值，将其存储到变量字典中
                        if module.variable_name and value is not None:
                            current_variables[module.variable_name] = value
                            print(f"元素模块 '{module.name}' 将值 '{value}' 存储为变量 '{module.variable_name}'")
                    else:
                        # 循环执行从起始模块到当前模块的所有模块，直到当前模块比对成功
                        loop_success = False
                        loop_count = 0
                        while not loop_success and i < len(self.modules) and loop_count < 100:  # 添加循环次数限制
                            loop_count += 1
                            print(f"\n--- 循环链执行第 {loop_count} 次 ---)")
                            print(f"当前模块 '{module.name}' 比对失败，开始执行循环链")
                            
                            # 执行从起始模块到当前模块的所有模块
                            for j in range(start_index, i + 1):
                                loop_module = self.modules[j]
                                print(f"循环中执行第 {j+1}/{len(self.modules)} 个模块: {loop_module.name}")
                                result, value = loop_module.execute(page, current_variables)
                                
                                if not result:
                                    if j == i:  # 如果当前模块执行失败（比对失败），继续循环
                                        print(f"循环链中当前模块 '{loop_module.name}' 比对失败，继续循环...")
                                        break  # 退出当前循环，重新开始
                                    else:  # 如果中间模块执行失败，返回整体失败
                                        print(f"循环链中模块 '{loop_module.name}' 执行失败，退出循环")
                                        return False
                                
                                # 如果模块配置了变量名称且获取到了值，将其存储到变量字典中
                                if loop_module.variable_name and value is not None:
                                    current_variables[loop_module.variable_name] = value
                                    print(f"元素模块 '{loop_module.name}' 将值 '{value}' 存储为变量 '{loop_module.variable_name}'")
                                
                                if j == i:  # 如果当前模块执行成功（比对成功），退出循环
                                    print(f"循环链中当前模块 '{loop_module.name}' 比对成功，退出循环")
                                    loop_success = True
            else:
                # 正常执行模块
                result, value = module.execute(page, current_variables)
                if not result:
                    print(f"模块 '{module.name}' 执行失败")
                    return False
                
                # 如果模块配置了变量名称且获取到了值，将其存储到变量字典中
                if module.variable_name and value is not None:
                    current_variables[module.variable_name] = value
                    print(f"元素模块 '{module.name}' 将值 '{value}' 存储为变量 '{module.variable_name}'")
            
            i += 1
        
        # 将更新后的变量字典合并回原始字典，以便外部使用
        variables.update(current_variables)
        
        print(f"\n{'='*50}")
        print(f"记录处理完成: {variables}")
        print(f"{'='*50}")
        
        return True
    
    def save_config(self, file_path: str) -> bool:
        """
        保存元素模块配置
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
        加载元素模块配置
        :param file_path: 配置文件路径
        :return: 加载成功返回True，失败返回False
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            self.modules = [ElementModule.from_dict(data) for data in config.get("modules", [])]
            self.module_counter = config.get("module_counter", 0)
            
            return True
        except Exception as e:
            print(f"加载配置失败: {e}")
            return False
