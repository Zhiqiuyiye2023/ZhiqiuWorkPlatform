#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元素模块和条件配置模块
"""
import time
import os
import re
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
        "下载文件",
        "网页截图"
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
        self.wait_time = 0.5  # 操作等待时间
        self.variable_name = ""  # 存储变量名称
        self.download_path = ""  # 下载文件保存路径
        self.download_file_name = ""  # 下载文件名（可以是固定值或变量名）
        self.verify_download = False  # 是否验证下载成功
        self.download_all_src = False  # 是否下载板块下的所有src
        self.unique_filename = True  # 是否使用唯一文件名
        self.screenshot_type = "全页面截图"  # 截图类型：全页面截图或局部截图
        self.screenshot_path = ""  # 截图保存路径
    
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
        :param variable_name: 存储变量名称
        """
        if action_type in self.ACTION_TYPES:
            self.action_type = action_type
        self.action_value = action_value
        self.is_variable = is_variable
        self.variable_name = variable_name
        
        # 对于下载文件操作，action_value是文件名，支持变量命名
        if action_type == "下载文件":
            self.download_file_name = action_value
        # 对于网页截图操作，action_value是截图文件名，支持变量命名
        elif action_type == "网页截图":
            self.download_file_name = action_value
    
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
        # 声明使用全局os模块，解决局部作用域问题
        global os
        try:
            # 等待元素加载
            time.sleep(self.wait_time)
            
            # 查找元素 - 网页截图不需要查找元素（已移除局部截图功能）
            element = None
            if self.action_type != "网页截图":
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
                
                # 对于获取文本操作，返回实际文本值，直接以模块名作为变量名
                return True, text
            elif self.action_type == "清除内容":
                element.clear()
                result_text = f"元素模块 '{self.name}' 执行清除内容操作"
                print(result_text)
                return True, None
            elif self.action_type == "下载文件":
                # 下载文件操作
                # 使用配置的下载路径或默认路径
                main_download_path = self.download_path if self.download_path else os.path.join(os.path.expanduser("~"), "Downloads")
                
                # 确保主下载路径存在
                os.makedirs(main_download_path, exist_ok=True)
                
                # 获取实际文件名
                base_file_name = ""
                if self.is_variable and self.download_file_name in variables:
                    # 使用变量作为文件名
                    base_file_name = variables[self.download_file_name]
                else:
                    # 使用固定文件名
                    base_file_name = self.download_file_name
                
                # 导入必要的库
                import requests
                import warnings
                import uuid
                import concurrent.futures
                
                # 忽略urllib3的InsecureRequestWarning警告
                warnings.filterwarnings('ignore', category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
                
                # 生成唯一标识符（只生成一次，提高效率）
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                
                # 定义下载单个文件的函数
                def download_single_file(url, file_name_prefix=""):
                    try:
                        # 获取文件扩展名
                        file_ext = os.path.splitext(url.split("?")[0])[1]
                        if not file_ext:
                            # 如果没有扩展名，尝试从Content-Type获取，或使用默认扩展名
                            file_ext = ".png"  # 默认使用.png扩展名
                        
                        # 从URL中提取文件名（不含扩展名）
                        url_file_name = os.path.splitext(os.path.basename(url.split("?")[0]))[0]
                        
                        # 生成基本文件名
                        if file_name_prefix:
                            file_name = file_name_prefix
                        elif base_file_name:
                            file_name = base_file_name
                        else:
                            file_name = url_file_name
                        
                        # 使用更高效的方式生成唯一ID，减少UUID的生成次数
                        unique_id = str(hash(url + str(time.time())) % 1000000).zfill(6)
                        
                        # 完整的文件名（添加时间戳和唯一ID，确保不重复）
                        full_file_name = f"{file_name}_{timestamp}_{unique_id}{file_ext}"
                        full_file_path = os.path.join(main_download_path, full_file_name)
                        
                        # 下载文件时使用不带查询参数的URL，以获取原图
                        original_url = url.split("?")[0]
                        
                        # 下载文件 - 增加timeout和verify=False（避免证书验证问题）
                        response = requests.get(original_url, stream=True, timeout=10, verify=False)  # 减少超时时间，禁用证书验证
                        response.raise_for_status()
                        
                        with open(full_file_path, 'wb') as f:
                            # 增加chunk_size提高下载速度
                            for chunk in response.iter_content(chunk_size=32768):
                                f.write(chunk)
                        
                        # 简化输出，只显示成功信息，不显示路径
                        result_text = f"元素模块 '{self.name}' 下载文件成功"
                        print(result_text)
                        return True, full_file_path
                    except Exception as e:
                        result_text = f"元素模块 '{self.name}' 下载文件失败: {e}"
                        print(result_text)
                        return False, None
                
                # 检查是否需要下载板块下的所有src，或者当前元素是否有src
                has_src = False
                current_src = ""
                child_elements = []
                src_count = 0
                
                # 只有当设置了download_all_src为True时，才检测当前板块下的src元素
                if self.download_all_src:
                    try:
                        # 查找当前元素下的所有带有src属性的子元素
                        child_elements = page.eles(f'x:{self.xpath}//*[@src]')
                        src_count = len(child_elements)
                        # 只在有src元素时打印信息
                        if src_count > 0:
                            print(f"元素模块 '{self.name}' 检测到当前板块下有 {src_count} 个带有src属性的元素")
                    except Exception as e:
                        result_text = f"元素模块 '{self.name}' 检测src数量失败: {e}"
                        print(result_text)
                        return False, None
                
                # 尝试获取当前元素的src属性
                try:
                    current_src = element.attr("src")
                    has_src = bool(current_src)
                except Exception as e:
                    print(f"获取元素src属性失败: {e}")
                
                # 检查是否需要下载板块下的所有src
                if self.download_all_src and src_count > 0:
                    # 下载板块下的所有src - 使用并发下载提高效率
                    success_count = 0
                    fail_count = 0
                    downloaded_files = []
                    
                    print(f"开始批量下载 {src_count} 个文件")
                    
                    # 收集所有要下载的URL和文件名前缀
                    download_tasks = []
                    for idx, child_ele in enumerate(child_elements):
                        src_url = child_ele.attr("src")
                        if src_url:
                            prefix = f"{base_file_name}_item{idx+1}" if base_file_name else f"item{idx+1}"
                            download_tasks.append((src_url, prefix))
                    
                    # 使用线程池并发下载
                    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                        # 提交所有下载任务
                        future_to_task = {executor.submit(download_single_file, url, prefix): (url, prefix) for url, prefix in download_tasks}
                        
                        # 处理下载结果
                        for future in concurrent.futures.as_completed(future_to_task):
                            result, file_path = future.result()
                            if result:
                                success_count += 1
                                downloaded_files.append(file_path)
                            else:
                                fail_count += 1
                    
                    result_text = f"元素模块 '{self.name}' 批量下载完成，成功: {success_count}, 失败: {fail_count}"
                    print(result_text)
                    
                    # 如果成功下载了至少一个文件，返回成功
                    if success_count > 0:
                        return True, downloaded_files
                    else:
                        # 如果没有成功下载任何文件，返回失败
                        result_text = f"元素模块 '{self.name}' 批量下载失败，所有文件均下载失败"
                        print(result_text)
                        return False, None
                elif has_src:
                    # 只下载当前元素的src
                    return download_single_file(current_src)
                else:
                    # 原有逻辑：点击元素触发下载
                    # 记录下载前的文件列表
                    before_files = set(os.listdir(main_download_path))
                    
                    # 点击下载链接或按钮 - 使用更高效的点击方式
                    element.click(by_js=True)
                    
                    # 等待下载完成 - 优化等待时间，使用更高效的轮询方式
                    max_wait_time = 2  # 最大等待时间2秒
                    check_interval = 0.2  # 检查间隔0.2秒
                    wait_time = 0
                    new_files = set()
                    
                    while wait_time < max_wait_time:
                        time.sleep(check_interval)
                        wait_time += check_interval
                        after_files = set(os.listdir(main_download_path))
                        new_files = after_files - before_files
                        if new_files:
                            break  # 检测到新文件，跳出等待循环
                    
                    if new_files:
                        # 下载成功，获取新文件名
                        downloaded_file = new_files.pop()
                        downloaded_file_path = os.path.join(main_download_path, downloaded_file)
                        
                        # 只在必要时重命名文件，减少不必要的IO操作
                        # 如果指定了文件名，或者需要使用唯一文件名，才重命名
                        if base_file_name or self.unique_filename:
                            # 生成唯一ID - 更高效的方式
                            unique_id = str(hash(downloaded_file + str(time.time())) % 1000000).zfill(6)
                            
                            # 获取文件扩展名
                            file_ext = os.path.splitext(downloaded_file)[1]
                            
                            # 生成基本文件名
                            if base_file_name:
                                file_base = base_file_name
                            else:
                                # 如果没有指定文件名，使用原文件名的基础部分
                                file_base = os.path.splitext(downloaded_file)[0]
                            
                            # 新文件名 - 直接使用已生成的timestamp，避免重复计算
                            new_file_name = f"{file_base}_{timestamp}_{unique_id}{file_ext}"
                            new_file_path = os.path.join(main_download_path, new_file_name)
                            
                            try:
                                # 重命名文件
                                os.rename(downloaded_file_path, new_file_path)
                                downloaded_file = new_file_name
                                downloaded_file_path = new_file_path
                            except Exception as e:
                                # 如果重命名失败，使用原始文件名继续
                                print(f"重命名文件失败: {e}，继续使用原始文件名")
                        
                        # 简化输出，只显示成功信息，不显示路径
                        result_text = f"元素模块 '{self.name}' 下载文件成功"
                        print(result_text)
                        return True, downloaded_file_path
                    else:
                        # 下载失败
                        result_text = f"元素模块 '{self.name}' 执行下载文件操作，下载路径: {main_download_path}, 未检测到新文件，下载可能失败"
                        print(result_text)
                        return False, None
            elif self.action_type == "网页截图":
                # 网页截图操作（仅保留全页面截图功能）
                # 使用配置的截图路径或默认路径
                main_screenshot_path = self.screenshot_path if self.screenshot_path else self.download_path if self.download_path else os.path.join(os.path.expanduser("~"), "Downloads")
                
                # 确保截图路径存在
                os.makedirs(main_screenshot_path, exist_ok=True)
                
                # 获取实际文件名
                base_file_name = ""
                if self.is_variable and self.download_file_name in variables:
                    # 使用变量作为文件名
                    base_file_name = variables[self.download_file_name]
                else:
                    # 使用固定文件名
                    base_file_name = self.download_file_name
                
                # 生成唯一标识符（时间戳）
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                
                # 生成唯一ID
                unique_id = str(hash(str(time.time())) % 1000000).zfill(6)
                
                # 完整的文件名（添加时间戳和唯一ID，确保不重复）
                full_file_name = f"{base_file_name}_{timestamp}_{unique_id}.png" if base_file_name else f"screenshot_{timestamp}_{unique_id}.png"
                full_file_path = os.path.join(main_screenshot_path, full_file_name)
                
                try:
                    # 使用DrissionPage 4.1.1.2官方截图方法，仅支持全页面截图
                    print(f"DEBUG: 开始使用DrissionPage官方截图方法")
                    
                    # 执行全页面截图
                    page.get_screenshot(path=os.path.dirname(full_file_path), 
                                      name=os.path.basename(full_file_path),
                                      full_page=True)
                    result_text = f"元素模块 '{self.name}' 全页面截图成功"
                    
                    print(result_text)
                    return True, full_file_path
                except Exception as e:
                    result_text = f"元素模块 '{self.name}' 截图失败: {e}"
                    print(result_text)
                    return False, None
            
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
            "variable_name": self.variable_name,
            "download_path": self.download_path,
            "download_all_src": self.download_all_src,
            "unique_filename": self.unique_filename,
            "screenshot_type": self.screenshot_type,
            "screenshot_path": self.screenshot_path
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
        module.set_wait_time(data.get("wait_time", 0.5))
        module.variable_name = data.get("variable_name", "")
        module.download_path = data.get("download_path", "")
        module.download_all_src = data.get("download_all_src", False)
        module.unique_filename = data.get("unique_filename", True)
        module.screenshot_type = data.get("screenshot_type", "全页面截图")
        module.screenshot_path = data.get("screenshot_path", "")
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
