#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器连接器模块
"""
from typing import Optional
from DrissionPage import ChromiumOptions, ChromiumPage


class BrowserConnector:
    """浏览器连接器类，负责连接和管理浏览器实例"""
    
    def __init__(self, debug_port: int = 9222):
        """
        初始化浏览器连接器
        :param debug_port: 浏览器调试端口，默认为9222
        """
        self.co = ChromiumOptions()
        self.co.set_local_port(debug_port)
        self.page = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """
        连接到已打开的浏览器
        :return: 连接成功返回True，失败返回False
        """
        try:
            self.page = ChromiumPage(self.co)
            self.is_connected = True
            return True
        except Exception as e:
            print(f"连接浏览器失败: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        """
        断开浏览器连接
        """
        if self.page:
            try:
                self.page.close()
            except Exception:
                pass
            self.page = None
            self.is_connected = False
    
    def get_page(self) -> Optional[ChromiumPage]:
        """
        获取当前浏览器页面实例
        :return: 浏览器页面实例，未连接返回None
        """
        return self.page
