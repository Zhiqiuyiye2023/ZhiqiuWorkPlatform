#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
字段筛选模块
实现数据字段的筛选功能
支持不同数据处理场景下的字段处理
支持字段查询表达式进行数据筛选
"""

import os
import re
import geopandas as gpd

class FieldFilter:
    """
    字段筛选功能类
    提供矢量数据字段筛选的核心功能
    支持字段查询表达式进行数据筛选
    """
    
    def __init__(self):
        self.selected_fields = []
        self.field_filter_enabled = False
        self.field_queries = {}
    
    def set_params(self, selected_fields=None, field_filter_enabled=True, field_queries=None):
        """
        设置字段筛选参数
        
        Args:
            selected_fields (list): 要保留的字段列表
            field_filter_enabled (bool): 是否启用字段筛选
            field_queries (dict): 字段查询表达式字典，键为字段名，值为查询表达式
        """
        self.selected_fields = selected_fields if selected_fields else []
        self.field_filter_enabled = field_filter_enabled
        self.field_queries = field_queries or {}
    
    def _parse_query_expression(self, field, expression):
        """
        解析查询表达式并生成对应的pandas筛选条件
        
        Args:
            field (str): 字段名
            expression (str): 查询表达式
            
        Returns:
            function: 返回一个可应用于DataFrame的筛选函数
        """
        # 处理常见的查询表达式格式
        # 例如: "等于10", "大于5", "包含'abc'", "不等于null"
        expression = expression.strip()
        
        # 匹配 "等于x", "==x"
        if expression.startswith("等于"):
            value = expression[2:].strip()
            return lambda df: df[field] == value
        elif expression.startswith("=="):
            value = expression[2:].strip()
            return lambda df: df[field] == value
        
        # 匹配 "大于x", ">x"
        elif expression.startswith("大于"):
            value = expression[2:].strip()
            try:
                value = float(value)
                return lambda df: df[field] > value
            except ValueError:
                pass
        elif expression.startswith(">" and not expression.startswith(">=")):
            value = expression[1:].strip()
            try:
                value = float(value)
                return lambda df: df[field] > value
            except ValueError:
                pass
        
        # 匹配 "大于等于x", ">=x"
        elif expression.startswith("大于等于"):
            value = expression[4:].strip()
            try:
                value = float(value)
                return lambda df: df[field] >= value
            except ValueError:
                pass
        elif expression.startswith(">="):
            value = expression[2:].strip()
            try:
                value = float(value)
                return lambda df: df[field] >= value
            except ValueError:
                pass
        
        # 匹配 "小于x", "<x"
        elif expression.startswith("小于"):
            value = expression[2:].strip()
            try:
                value = float(value)
                return lambda df: df[field] < value
            except ValueError:
                pass
        elif expression.startswith("<" and not expression.startswith("<=")):
            value = expression[1:].strip()
            try:
                value = float(value)
                return lambda df: df[field] < value
            except ValueError:
                pass
        
        # 匹配 "小于等于x", "<=x"
        elif expression.startswith("小于等于"):
            value = expression[4:].strip()
            try:
                value = float(value)
                return lambda df: df[field] <= value
            except ValueError:
                pass
        elif expression.startswith("<="):
            value = expression[2:].strip()
            try:
                value = float(value)
                return lambda df: df[field] <= value
            except ValueError:
                pass
        
        # 匹配 "包含x"
        elif expression.startswith("包含"):
            value = expression[2:].strip()
            # 去除可能的引号
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return lambda df: df[field].astype(str).str.contains(value)
        
        # 匹配 "开头包含x"
        elif expression.startswith("开头包含"):
            value = expression[4:].strip()
            # 去除可能的引号
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return lambda df: df[field].astype(str).str.startswith(value)
        
        # 匹配 "结尾包含x"
        elif expression.startswith("结尾包含"):
            value = expression[4:].strip()
            # 去除可能的引号
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return lambda df: df[field].astype(str).str.endswith(value)
        
        # 匹配 "不等于x", "!=x"
        elif expression.startswith("不等于"):
            value = expression[3:].strip()
            if value.lower() == "null":
                return lambda df: df[field].notnull()
            return lambda df: df[field] != value
        elif expression.startswith("!="):
            value = expression[2:].strip()
            if value.lower() == "null":
                return lambda df: df[field].notnull()
            return lambda df: df[field] != value
        
        # 匹配 "为空", "is null"
        elif expression in ["为空", "is null", "IS NULL"]:
            return lambda df: df[field].isnull()
        
        # 匹配 "不为空", "is not null"
        elif expression in ["不为空", "is not null", "IS NOT NULL"]:
            return lambda df: df[field].notnull()
        
        # 如果无法解析，返回None
        return None
    
    def perform_field_filter(self, file_path):
        """
        执行字段筛选操作
        
        Args:
            file_path: 矢量文件路径
        
        Returns:
            处理后的文件路径或False（如果处理失败）
        """
        if not self.field_filter_enabled or not self.selected_fields:
            print("字段筛选未启用或未选择字段，返回原文件")
            return file_path
        
        return 字段筛选(file_path, self.selected_fields, self.field_queries)

def 字段筛选(file_path, selected_fields, field_queries=None):
    """
    从矢量数据中选择指定的字段并创建新文件
    支持处理单个数据源或多个数据源处理后的结果
    支持字段查询表达式进行数据筛选
    
    Args:
        file_path: 矢量文件路径
        selected_fields: 要保留的字段列表
        field_queries (dict): 字段查询表达式字典，键为字段名，值为查询表达式
    
    Returns:
        处理后的文件路径或False（如果处理失败）
    """
    try:
        print(f"正在进行字段筛选: {file_path}, 字段列表: {selected_fields}")
        if field_queries:
            print(f"字段查询表达式: {field_queries}")
        
        # 读取数据
        gdf = gpd.read_file(file_path)
        
        # 获取数据中的所有字段
        all_fields = list(gdf.columns)
        print(f"原始数据字段: {all_fields}")
        
        # 验证选择的字段是否存在
        valid_fields = []
        missing_fields = []
        
        for field in selected_fields:
            if field in all_fields:
                valid_fields.append(field)
            else:
                missing_fields.append(field)
        
        # 如果没有有效的字段，返回失败
        if not valid_fields:
            print(f"错误：没有找到有效的字段")
            return False
        
        # 如果有缺失的字段，打印警告
        if missing_fields:
            print(f"警告：以下字段不存在: {missing_fields}")
        
        # 应用字段查询表达式进行筛选
        if field_queries:
            for field, query in field_queries.items():
                if field in gdf.columns and query:
                    # 为每个查询字段创建FieldFilter实例以使用其解析方法
                    temp_filter = FieldFilter()
                    filter_func = temp_filter._parse_query_expression(field, query)
                    if filter_func:
                        try:
                            gdf = gdf[filter_func(gdf)]
                            print(f"应用查询表达式 '{query}' 到字段 '{field}'")
                        except Exception as e:
                            print(f"应用字段'{field}'的查询表达式失败: {str(e)}")
        
        # 添加geometry字段（必需）
        if 'geometry' not in valid_fields:
            valid_fields.append('geometry')
        
        # 选择字段
        selected_gdf = gdf[valid_fields].copy()
        
        # 生成输出文件路径（添加_filt后缀）
        base_path, ext = os.path.splitext(file_path)
        output_path = f"{base_path}_filt{ext}"
        
        # 保存文件
        selected_gdf.to_file(output_path, encoding='utf-8')
        
        print(f"字段筛选成功！保留字段: {valid_fields}")
        print(f"输出文件: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"字段筛选时出错: {e}")
        return False

def 获取所有字段(file_path):
    """
    获取矢量数据中的所有字段名称
    
    Args:
        file_path: 矢量文件路径
    
    Returns:
        字段名称列表或空列表（如果处理失败）
    """
    try:
        # 读取数据
        gdf = gpd.read_file(file_path)
        
        # 获取所有字段（包括geometry）
        all_fields = list(gdf.columns)
        
        print(f"获取字段成功: {all_fields}")
        return all_fields
        
    except Exception as e:
        print(f"获取字段时出错: {e}")
        return []

# 测试代码
if __name__ == "__main__":
    print("字段筛选模块测试")