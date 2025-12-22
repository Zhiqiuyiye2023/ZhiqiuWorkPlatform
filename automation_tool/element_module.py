#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元素模块和条件配置模块
"""
import time
from typing import List, Dict, Any, Optional
from DrissionPage import ChromiumPage


class ElementModule:
    """元素模块类，封装网页元素的定位和操作"""
    
    # 操作类型枚举
    ACTION_TYPES = [
        "输入文本",
        "点击",
        "选择下拉选项",
        "上传文件",
        "获取文本",
        "清除内容",
        "获取表格字段"
    ]
    
    def __init__(self, module_id: str, name: str):
        """
        初始化元素模块
        :param module_id: 模块唯一标识符
        :param name: 模块名称
        """
        self.module_id = module_id
        self.name = name
        self.xpath = ""
        self.action_type = "输入文本"  # 默认操作类型
        self.action_value = ""  # 操作值，可以是固定值或变量名
        self.is_variable = False  # 操作值是否为变量
        self.wait_time = 1.0  # 操作等待时间
        self.variable_name = ""  # 存储变量名称，用于获取文本或表格字段时
        self.loop_start_module = None  # 循环起始模块ID，形成从该模块到当前模块的循环链
    
    def set_xpath(self, xpath: str) -> None:
        """
        设置元素XPath
        :param xpath: XPath表达式
        """
        self.xpath = xpath
    
    def set_action(self, action_type: str, action_value: str, is_variable: bool = False, variable_name: str = "") -> None:
        """
        设置元素操作
        :param action_type: 操作类型
        :param action_value: 操作值
        :param is_variable: 是否为变量
        :param variable_name: 存储变量名称（用于获取文本或表格字段时）
        """
        if action_type in self.ACTION_TYPES:
            self.action_type = action_type
        self.action_value = action_value
        self.is_variable = is_variable
        self.variable_name = variable_name
    
    def set_wait_time(self, wait_time: float) -> None:
        """
        设置操作等待时间
        :param wait_time: 等待时间（秒）
        """
        self.wait_time = max(0.1, wait_time)  # 确保等待时间不小于0.1秒
    
    def execute(self, page: ChromiumPage, variables: Dict[str, str]) -> tuple[bool, Optional[str]]:
        """
        执行元素操作
        :param page: 浏览器页面实例
        :param variables: 可用变量字典
        :return: 执行成功返回(True, 获取到的值)，失败返回(False, None)
        """
        try:
            # 等待元素加载
            time.sleep(self.wait_time)
            
            # 查找元素
            element = page.ele(f'x:{self.xpath}')
            if not element:
                result_text = f"元素模块 '{self.name}' 未找到元素，XPath: {self.xpath}"
                print(result_text)
                return False, result_text
            
            # 获取实际操作值
            if self.is_variable and self.action_value in variables:
                actual_value = variables[self.action_value]
            else:
                actual_value = self.action_value
            
            # 执行对应操作
            if self.action_type == "输入文本":
                element.input(actual_value)
                result_text = f"元素模块 '{self.name}' 执行输入文本: {actual_value}"
                print(result_text)
                return True, None
            elif self.action_type == "点击":
                element.click(by_js=True)
                result_text = f"元素模块 '{self.name}' 执行点击操作"
                print(result_text)
                return True, None
            elif self.action_type == "选择下拉选项":
                element.click(by_js=True)  # 先点击展开下拉框
                time.sleep(0.5)
                option_xpath = f"//li[not(contains(@style, 'display: none'))]//span[text()='{actual_value}']"
                option = page.ele(f'x:{option_xpath}')
                if option:
                    option.click(by_js=True)
                    result_text = f"元素模块 '{self.name}' 执行选择操作: {actual_value}"
                    print(result_text)
                    return True, None
                else:
                    result_text = f"元素模块 '{self.name}' 未找到选项: {actual_value}"
                    print(result_text)
                    return False, None
            elif self.action_type == "上传文件":
                element.input(actual_value)
                result_text = f"元素模块 '{self.name}' 执行上传文件: {actual_value}"
                print(result_text)
                return True, None
            elif self.action_type == "获取文本":
                text = element.text.strip()
                result_text = f"元素模块 '{self.name}' 获取文本: {text}"
                print(result_text)
                
                # 处理文本比对逻辑
                # 如果设置了is_variable=True，表示需要使用操作值进行比对
                if self.is_variable:
                    expected_value = actual_value  # 实际值是从变量或直接值获取的
                    if text != expected_value:
                        compare_text = f"元素模块 '{self.name}' 文本比对失败: 实际值={text}, 期望值={expected_value}"
                        print(compare_text)
                        result_text += f"\n{compare_text}"
                        return False, text
                    compare_text = f"元素模块 '{self.name}' 文本比对成功: 实际值={text}, 期望值={expected_value}"
                    print(compare_text)
                    result_text += f"\n{compare_text}"
                
                # 对于获取文本操作，返回实际文本值，用于变量存储
                return True, text
            elif self.action_type == "清除内容":
                element.clear()
                result_text = f"元素模块 '{self.name}' 执行清除内容操作"
                print(result_text)
                return True, None
            elif self.action_type == "获取表格字段":
                # 实现获取表格字段值的逻辑
                # 1. 找到表格行，其中包含指定文本的列
                # 2. 从该行中提取目标字段的值
                
                # 解析action_value，格式："比较字段文本,目标列索引"
                # 例如："产品名称,2" 表示找到包含"产品名称"的行，然后获取第2列的值
                try:
                    compare_text, target_col_index = actual_value.split(",")
                    target_col_index = int(target_col_index)
                    
                    # 查找表格行，其中包含指定文本
                    # 使用XPath查找包含指定文本的行
                    row_xpath = f"{self.xpath}//tr[contains(., '{compare_text}')]"
                    row = page.ele(f'x:{row_xpath}')
                    
                    if not row:
                        result_text = f"元素模块 '{self.name}' 未找到包含文本 '{compare_text}' 的行"
                        print(result_text)
                        return False, None
                    
                    # 从该行中获取所有单元格
                    cells = row.eles(f'x:td') or row.eles(f'x:th')
                    if not cells:
                        result_text = f"元素模块 '{self.name}' 未找到单元格"
                        print(result_text)
                        return False, None
                    
                    # 检查目标列索引是否有效
                    if target_col_index < 0 or target_col_index >= len(cells):
                        result_text = f"元素模块 '{self.name}' 目标列索引 {target_col_index} 无效，共有 {len(cells)} 列"
                        print(result_text)
                        return False, None
                    
                    # 获取目标单元格的文本
                    target_text = cells[target_col_index].text.strip()
                    result_text = f"元素模块 '{self.name}' 从表格中获取字段值: {target_text}"
                    print(result_text)
                    # 对于获取表格字段操作，返回实际字段值，用于变量存储
                    return True, target_text
                except ValueError as e:
                    result_text = f"元素模块 '{self.name}' 配置错误: {e}，格式应为 '比较文本,目标列索引'"
                    print(result_text)
                    return False, result_text
            
            result_text = f"元素模块 '{self.name}' 执行未知操作"
            print(result_text)
            return True, result_text
        except Exception as e:
            result_text = f"元素模块 '{self.name}' 执行操作失败: {e}"
            print(result_text)
            return False, result_text
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将元素模块转换为字典
        :return: 元素模块字典
        """
        return {
            "module_id": self.module_id,
            "name": self.name,
            "xpath": self.xpath,
            "action_type": self.action_type,
            "action_value": self.action_value,
            "is_variable": self.is_variable,
            "wait_time": self.wait_time,
            "variable_name": self.variable_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ElementModule":
        """
        从字典创建元素模块
        :param data: 元素模块字典
        :return: 元素模块实例
        """
        module = cls(data["module_id"], data["name"])
        module.set_xpath(data.get("xpath", ""))
        module.set_action(
            data.get("action_type", "输入文本"),
            data.get("action_value", ""),
            data.get("is_variable", False),
            data.get("variable_name", "")
        )
        module.set_wait_time(data.get("wait_time", 1.0))
        module.variable_name = data.get("variable_name", "")
        return module


class ConditionConfig:
    """条件配置类，用于定义条件判断逻辑"""
    
    # 条件运算符枚举
    OPERATORS = [
        "等于",
        "不等于",
        "包含",
        "不包含",
        "大于",
        "小于",
        "大于等于",
        "小于等于"
    ]
    
    def __init__(self):
        """
        初始化条件配置
        """
        self.field_name = ""  # 要判断的字段名
        self.operator = "等于"  # 条件运算符
        self.compare_value = ""  # 比较值
        self.true_group = "group1"  # 条件为真时执行的模块组
        self.false_group = "group2"  # 条件为假时执行的模块组
    
    def evaluate(self, variables: Dict[str, str]) -> str:
        """
        评估条件
        :param variables: 变量字典
        :return: 条件为真返回true_group，否则返回false_group
        """
        if self.field_name not in variables:
            return self.false_group
        
        field_value = variables[self.field_name]
        compare_value = self.compare_value
        
        try:
            # 根据运算符执行比较
            if self.operator == "等于":
                return self.true_group if field_value == compare_value else self.false_group
            elif self.operator == "不等于":
                return self.true_group if field_value != compare_value else self.false_group
            elif self.operator == "包含":
                return self.true_group if compare_value in field_value else self.false_group
            elif self.operator == "不包含":
                return self.true_group if compare_value not in field_value else self.false_group
            elif self.operator == "大于":
                return self.true_group if float(field_value) > float(compare_value) else self.false_group
            elif self.operator == "小于":
                return self.true_group if float(field_value) < float(compare_value) else self.false_group
            elif self.operator == "大于等于":
                return self.true_group if float(field_value) >= float(compare_value) else self.false_group
            elif self.operator == "小于等于":
                return self.true_group if float(field_value) <= float(compare_value) else self.false_group
        except (ValueError, TypeError):
            # 类型转换失败时，条件为假
            return self.false_group
        
        return self.false_group
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        """
        return {
            "field_name": self.field_name,
            "operator": self.operator,
            "compare_value": self.compare_value,
            "true_group": self.true_group,
            "false_group": self.false_group
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConditionConfig":
        """
        从字典创建条件配置
        """
        config = cls()
        config.field_name = data.get("field_name", "")
        config.operator = data.get("operator", "等于")
        config.compare_value = data.get("compare_value", "")
        config.true_group = data.get("true_group", "group1")
        config.false_group = data.get("false_group", "group2")
        return config
