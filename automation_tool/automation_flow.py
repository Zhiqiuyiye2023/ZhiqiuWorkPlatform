#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化流程模块
"""
import threading
import time
from tkinter import messagebox
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from .browser_connector import BrowserConnector
from .table_data_manager import TableDataManager
from .element_module_manager import ElementModuleManager


class AutomationFlow(QObject):
    """自动化流程类，负责协调整个自动化流程"""
    
    # 定义信号，用于向界面发送调试信息
    debug_info = pyqtSignal(str)
    
    def __init__(self):
        """初始化自动化流程"""
        super().__init__()
        self.browser = BrowserConnector()
        self.table_manager = TableDataManager()
        self.module_manager = ElementModuleManager()
        self.is_running = False
        self.is_paused = False
    
    def connect_browser(self) -> bool:
        """
        连接浏览器
        :return: 连接成功返回True，失败返回False
        """
        return self.browser.connect()
    
    def disconnect_browser(self) -> None:
        """
        断开浏览器连接
        """
        self.browser.disconnect()
    
    def load_table(self, file_path: str) -> bool:
        """
        加载表格文件
        :param file_path: 表格文件路径
        :return: 加载成功返回True，失败返回False
        """
        return self.table_manager.load_table(file_path)
    
    def start_automation(self) -> None:
        """
        开始自动化流程
        """
        if not self.browser.is_connected:
            print("浏览器未连接，无法开始自动化流程")
            messagebox.showerror("错误", "浏览器未连接，无法开始自动化流程")
            return
        
        if not self.table_manager.data:
            print("未加载表格数据，无法开始自动化流程")
            messagebox.showerror("错误", "未加载表格数据，无法开始自动化流程")
            return
        
        if not self.module_manager.modules:
            print("未添加元素模块，无法开始自动化流程")
            messagebox.showerror("错误", "未添加元素模块，无法开始自动化流程")
            return
        
        self.is_running = True
        self.is_paused = False
        self.table_manager.reset()
        
        # 启动自动化线程
        automation_thread = threading.Thread(target=self._run_automation)
        automation_thread.daemon = True
        automation_thread.start()
    
    def pause_automation(self) -> None:
        """
        暂停自动化流程
        """
        self.is_paused = not self.is_paused
    
    def stop_automation(self) -> None:
        """
        停止自动化流程
        """
        self.is_running = False
        self.is_paused = False
    
    def _run_automation(self) -> None:
        """
        运行自动化流程的核心逻辑
        """
        page = self.browser.get_page()
        if not page:
            self.is_running = False
            self.debug_info.emit("浏览器页面获取失败，自动化流程结束")
            return
        
        # 处理每条记录
        total_records = len(self.table_manager.data)
        current_record = 0
        
        self.debug_info.emit("开始自动化流程")
        self.debug_info.emit(f"共需处理 {total_records} 条记录")
        
        while self.is_running:
            # 检查是否暂停
            while self.is_paused and self.is_running:
                time.sleep(0.5)
            
            if not self.is_running:
                break
            
            # 获取下一条记录
            record = self.table_manager.get_next_record()
            if not record:
                break  # 所有记录处理完毕
            
            current_record += 1
            self.debug_info.emit(f"\n{'='*50}")
            self.debug_info.emit(f"开始处理第 {current_record}/{total_records} 条记录: {record}")
            self.debug_info.emit(f"{'='*50}")
            
            # 执行所有元素模块
            success = self.module_manager.execute_all(page, record)
            if success:
                self.debug_info.emit(f"第 {current_record}/{total_records} 条记录处理成功")
            else:
                self.debug_info.emit(f"第 {current_record}/{total_records} 条记录处理失败: {record}")
                # 可以选择继续处理下一条或停止
                # 这里选择继续处理下一条
        
        self.is_running = False
        self.debug_info.emit("\n自动化流程结束")
        self.debug_info.emit(f"共处理 {current_record} 条记录")
