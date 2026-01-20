# coding:utf-8
"""
自动化工具界面
"""

import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSplitter,
                             QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QFileDialog, QGroupBox, QFormLayout,
                             QCheckBox, QDoubleSpinBox, QFrame, QScrollArea, QMessageBox, QTabWidget,
                             QDialog, QAbstractItemView, QLayout, QHeaderView)  # 添加QLayout和QHeaderView导入
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from qfluentwidgets import (ScrollArea, isDarkTheme, CardWidget, PushButton, PrimaryPushButton,
                           LineEdit, ComboBox, TextEdit, ToolButton, FluentIcon as FIF, SwitchButton,
                           TitleLabel, SubtitleLabel, InfoBar, InfoBarPosition, IndeterminateProgressBar,
                           MessageBox, FluentIconBase)
from typing import Optional

# 导入自动化工具核心模块
from automation_tool import AutomationFlow


class AutomationToolInterface(QWidget):
    """自动化工具界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("automationToolInterface")
        self.automation_flow = AutomationFlow()
        self.current_module_id = None
        self.is_running = False
        self.module_cards = {}  # 存储模块ID到卡片的映射
        self.setupUI()
        
        # 连接主题变化信号
        from configs.config import cfg
        cfg.themeChanged.connect(self.updateTheme)
        self.updateTheme()
        
        # 初始化网页标题更新定时器
        self.title_update_timer = QTimer(self)
        self.title_update_timer.setInterval(1000)  # 每秒更新一次
        self.title_update_timer.timeout.connect(self.updateBrowserStatus)
    
    class ModuleCard(CardWidget):
        """元素模块卡片控件"""
        
        moduleUpdated = pyqtSignal(str)  # 模块更新信号
        moduleDeleted = pyqtSignal(str)  # 模块删除信号
        moduleMoved = pyqtSignal(str, bool)  # 模块移动信号 (module_id, is_up)
        
        def __init__(self, module, parent=None):
            super().__init__(parent=parent)
            self.module = module
            self.module_id = module.module_id
            self.setObjectName(f"moduleCard_{self.module_id}")
            # 最小高度在setupUI中设置，这里不再重复设置
            self.setupUI()
        
        def setupUI(self):
            """设置卡片UI - 优化布局"""
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)  # 调整外边距，使布局更紧凑
            layout.setSpacing(6)  # 减小间距，使布局更紧凑
            self.setMinimumHeight(200)  # 设置足够的最小高度，给出预留空间
            self.setFixedHeight(200)  # 设置固定高度，避免操作类型变化时调整布局
            
            # 第1行：模块名称、等待时间、保存按钮
            headerLayout = QHBoxLayout()
            headerLayout.setContentsMargins(0, 0, 0, 0)
            headerLayout.setSpacing(6)  # 减小间距
            
            # 模块名称 - 添加标签
            nameLayout = QHBoxLayout()
            nameLayout.setContentsMargins(0, 0, 0, 0)
            nameLayout.setSpacing(4)
            
            nameLabel = QLabel("名称:")
            nameLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            nameLabel.setFixedWidth(50)  # 调整标签宽度
            nameLayout.addWidget(nameLabel)
            
            self.nameEdit = LineEdit()
            self.nameEdit.setObjectName("moduleNameEdit")
            self.nameEdit.setText(self.module.name)
            self.nameEdit.setPlaceholderText("模块名称")
            self.nameEdit.setFixedHeight(28)  # 调整高度
            nameLayout.addWidget(self.nameEdit, 1)  # 增加拉伸因子
            
            headerLayout.addLayout(nameLayout, 2)  # 调整拉伸因子
            
            # 等待时间 - 移到模块名后面
            waitTimeLayout = QHBoxLayout()
            waitTimeLayout.setContentsMargins(0, 0, 0, 0)
            waitTimeLayout.setSpacing(4)
            
            waitTimeLabel = QLabel("等待:")
            waitTimeLabel.setFixedWidth(50)  # 调整标签宽度
            waitTimeLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            waitTimeLayout.addWidget(waitTimeLabel)
            
            self.waitTimeSpin = QDoubleSpinBox()
            self.waitTimeSpin.setObjectName("waitTimeSpin")
            self.waitTimeSpin.setRange(0.1, 10.0)
            self.waitTimeSpin.setSingleStep(0.1)
            self.waitTimeSpin.setValue(self.module.wait_time)
            self.waitTimeSpin.setFixedHeight(28)  # 调整高度
            self.waitTimeSpin.setFixedWidth(70)  # 调整宽度
            waitTimeLayout.addWidget(self.waitTimeSpin)
            
            headerLayout.addLayout(waitTimeLayout, 1)  # 调整拉伸因子
            
            # 保存按钮 - 移到模块名后面，确保文字完整显示
            self.saveBtn = PushButton(FIF.SAVE, "保存")
            self.saveBtn.setObjectName("saveBtn")
            self.saveBtn.setFixedHeight(28)  # 调整高度
            self.saveBtn.setFixedWidth(80)  # 增加宽度，确保文字完整显示
            self.saveBtn.clicked.connect(self.saveModule)
            headerLayout.addWidget(self.saveBtn, 0, Qt.AlignmentFlag.AlignVCenter)
            
            layout.addLayout(headerLayout)
            
            # 第2行：XPath表达式
            self.xpathContainer = QWidget()
            xpathLayout = QHBoxLayout(self.xpathContainer)
            xpathLayout.setContentsMargins(0, 0, 0, 0)
            xpathLayout.setSpacing(6)  # 减小间距
            
            xpathLabel = QLabel("XPath:")
            xpathLabel.setFixedWidth(50)  # 调整标签宽度
            xpathLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            xpathLayout.addWidget(xpathLabel)
            
            self.xpathEdit = LineEdit()
            self.xpathEdit.setObjectName("xpathEdit")
            self.xpathEdit.setText(self.module.xpath)
            self.xpathEdit.setPlaceholderText("//input[@id='example']")
            self.xpathEdit.setFixedHeight(28)  # 调整高度
            xpathLayout.addWidget(self.xpathEdit, 1)  # 增加拉伸因子
            
            layout.addWidget(self.xpathContainer)
            
            # 第3行：操作类型
            actionTypeLayout = QHBoxLayout()
            actionTypeLayout.setContentsMargins(0, 0, 0, 0)
            actionTypeLayout.setSpacing(6)  # 减小间距
            
            actionTypeLabel = QLabel("操作类型:")
            actionTypeLabel.setFixedWidth(80)  # 调整标签宽度
            actionTypeLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            actionTypeLayout.addWidget(actionTypeLabel)
            
            self.actionTypeCombo = ComboBox()
            self.actionTypeCombo.setObjectName("actionTypeCombo")
            self.actionTypeCombo.addItems(["输入文本", "点击", "选择下拉选项", "上传文件", "获取文本", "清除内容", "下载文件", "网页截图"])
            self.actionTypeCombo.setCurrentText(self.module.action_type)
            self.actionTypeCombo.currentIndexChanged.connect(self.onActionTypeChanged)
            self.actionTypeCombo.setFixedHeight(28)  # 调整高度
            self.actionTypeCombo.setMinimumWidth(140)  # 调整最小宽度
            actionTypeLayout.addWidget(self.actionTypeCombo, 1)  # 增加拉伸因子
            
            # 使用变量开关 - 根据操作类型动态显示
            self.variableSwitch = SwitchButton("使用变量")
            self.variableSwitch.setObjectName("variableSwitch")
            self.variableSwitch.setOnText("使用变量")  # 设置开关打开时的文本与关闭时相同
            self.variableSwitch.setChecked(self.module.is_variable)
            # SwitchButton使用checkedChanged信号，不是toggled信号
            self.variableSwitch.checkedChanged.connect(self.onVariableSwitchChanged)
            actionTypeLayout.addWidget(self.variableSwitch, 0, Qt.AlignmentFlag.AlignVCenter)
            
            layout.addLayout(actionTypeLayout)
            
            # 第4行：操作值、表格字段下拉框、循环按钮
            self.actionValueContainer = QWidget()
            actionValueLayout = QHBoxLayout(self.actionValueContainer)
            actionValueLayout.setContentsMargins(0, 0, 0, 0)
            actionValueLayout.setSpacing(6)  # 减小间距
            
            self.actionValueLabel = QLabel("操作值:")
            self.actionValueLabel.setFixedWidth(60)  # 调整标签宽度
            self.actionValueLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            actionValueLayout.addWidget(self.actionValueLabel)
            
            # 操作值输入框
            self.actionValueEdit = LineEdit()
            self.actionValueEdit.setObjectName("actionValueEdit")
            self.actionValueEdit.setText(self.module.action_value)
            self.actionValueEdit.setPlaceholderText("操作值")
            self.actionValueEdit.setFixedHeight(28)  # 调整高度
            actionValueLayout.addWidget(self.actionValueEdit, 1)  # 增加拉伸因子
            
            # 表格字段下拉框（初始隐藏）
            self.tableFieldCombo = ComboBox()
            self.tableFieldCombo.setObjectName("tableFieldCombo")
            self.tableFieldCombo.setPlaceholderText("选择表格字段")
            self.tableFieldCombo.setFixedHeight(28)  # 调整高度
            self.tableFieldCombo.setMinimumWidth(140)  # 调整最小宽度
            self.tableFieldCombo.setVisible(False)  # 初始隐藏
            actionValueLayout.addWidget(self.tableFieldCombo, 1)  # 增加拉伸因子
            
            # 下载板块下的所有src开关（仅对下载文件操作显示）
            self.downloadAllSrcSwitch = SwitchButton("下载板块下的所有src")
            self.downloadAllSrcSwitch.setObjectName("downloadAllSrcSwitch")
            self.downloadAllSrcSwitch.setOnText("下载板块下的所有src")  # 设置开关打开时的文本与关闭时相同
            self.downloadAllSrcSwitch.setChecked(getattr(self.module, 'download_all_src', False))
            self.downloadAllSrcSwitch.setVisible(False)  # 初始隐藏
            actionValueLayout.addWidget(self.downloadAllSrcSwitch, 0, Qt.AlignmentFlag.AlignVCenter)
            
            layout.addWidget(self.actionValueContainer)
            
            # 第5行：变量名称
            self.variableContainer = QWidget()
            variableLayout = QHBoxLayout(self.variableContainer)
            variableLayout.setContentsMargins(0, 0, 0, 0)
            variableLayout.setSpacing(6)  # 减小间距
            
            self.variableNameLabel = QLabel("变量名称:")
            self.variableNameLabel.setFixedWidth(80)  # 调整标签宽度
            self.variableNameLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            variableLayout.addWidget(self.variableNameLabel)
            
            self.variableNameEdit = LineEdit()
            self.variableNameEdit.setObjectName("variableNameEdit")
            self.variableNameEdit.setText(self.module.variable_name)
            self.variableNameEdit.setPlaceholderText("存储变量名")
            self.variableNameEdit.setFixedHeight(28)  # 调整高度
            variableLayout.addWidget(self.variableNameEdit, 1)  # 增加拉伸因子
            
            layout.addWidget(self.variableContainer)
            
            # 第6行：下载路径配置（仅对下载文件操作显示）
            self.downloadPathContainer = QWidget()
            downloadPathLayout = QHBoxLayout(self.downloadPathContainer)
            downloadPathLayout.setContentsMargins(0, 0, 0, 0)
            downloadPathLayout.setSpacing(6)  # 减小间距
            
            self.downloadPathLabel = QLabel("下载路径:")
            self.downloadPathLabel.setFixedWidth(80)  # 调整标签宽度
            self.downloadPathLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            downloadPathLayout.addWidget(self.downloadPathLabel)
            
            self.downloadPathEdit = LineEdit()
            self.downloadPathEdit.setObjectName("downloadPathEdit")
            self.downloadPathEdit.setText(getattr(self.module, 'download_path', ''))
            self.downloadPathEdit.setPlaceholderText("下载路径，留空使用默认路径")
            self.downloadPathEdit.setFixedHeight(28)  # 调整高度
            downloadPathLayout.addWidget(self.downloadPathEdit, 1)  # 增加拉伸因子
            
            # 添加浏览按钮
            self.browseBtn = PushButton(FIF.FOLDER, "浏览")
            self.browseBtn.setObjectName("browseBtn")
            self.browseBtn.setFixedHeight(28)  # 调整高度
            self.browseBtn.setFixedWidth(100)  # 加宽按钮宽度
            self.browseBtn.clicked.connect(self.onBrowseBtnClicked)
            downloadPathLayout.addWidget(self.browseBtn)
            
            layout.addWidget(self.downloadPathContainer)
            
            # 第8行：截图类型配置（仅对网页截图操作显示）
            # 移除局部截图功能，只保留全页面截图
            self.screenshotConfigContainer = QWidget()
            screenshotConfigLayout = QHBoxLayout(self.screenshotConfigContainer)
            screenshotConfigLayout.setContentsMargins(0, 0, 0, 0)
            screenshotConfigLayout.setSpacing(6)  # 减小间距
            
            # 截图类型选择 - 只保留全页面截图
            screenshotTypeLabel = QLabel("截图类型:")
            screenshotTypeLabel.setFixedWidth(80)  # 调整标签宽度
            screenshotTypeLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            screenshotConfigLayout.addWidget(screenshotTypeLabel)
            
            self.screenshotTypeCombo = ComboBox()
            self.screenshotTypeCombo.setObjectName("screenshotTypeCombo")
            self.screenshotTypeCombo.addItems(["全页面截图"])  # 只保留全页面截图选项
            # 获取模块的截图类型，如果不存在则使用默认值
            screenshot_type = getattr(self.module, 'screenshot_type', '全页面截图')
            self.screenshotTypeCombo.setCurrentText('全页面截图')  # 强制设置为全页面截图
            self.screenshotTypeCombo.setFixedHeight(28)  # 调整高度
            self.screenshotTypeCombo.setMinimumWidth(140)  # 调整最小宽度
            self.screenshotTypeCombo.setEnabled(False)  # 禁用下拉框，只能选择全页面截图
            screenshotConfigLayout.addWidget(self.screenshotTypeCombo)
            
            screenshotConfigLayout.addStretch()  # 增加拉伸因子，将元素挤到左侧
            
            layout.addWidget(self.screenshotConfigContainer)
            
            # 初始状态处理
            self.onActionTypeChanged(self.actionTypeCombo.currentIndex())
            
        def onBrowseBtnClicked(self):
            """浏览按钮点击事件"""
            from PyQt6.QtWidgets import QFileDialog
            
            # 打开文件夹选择对话框
            folder_path = QFileDialog.getExistingDirectory(
                self, 
                "选择下载路径", 
                self.downloadPathEdit.text() or ""
            )
            
            if folder_path:
                self.downloadPathEdit.setText(folder_path)
                

        def onActionTypeChanged(self, index):
            """操作类型变化事件"""
            action_type = self.actionTypeCombo.currentText()
            
            # 确定哪些操作类型需要操作值和使用变量开关
            # 获取文本不需要操作值和使用变量开关，直接以模块名作为变量名
            need_action_value = action_type in ["输入文本", "选择下拉选项", "上传文件", "下载文件", "网页截图"]
            
            # 显示或隐藏操作值相关容器
            self.actionValueContainer.setVisible(need_action_value)
            self.variableSwitch.setVisible(need_action_value)
            
            # 确定哪些操作类型需要变量名称
            # 当前没有操作类型需要变量名称
            need_variable_name = False
            
            # 显示或隐藏变量名称相关容器
            self.variableContainer.setVisible(need_variable_name)
            
            # 显示或隐藏下载路径配置容器（对下载文件和网页截图操作显示）
            is_download_action = action_type in ["下载文件", "网页截图"]
            self.downloadPathContainer.setVisible(is_download_action)
            
            # 显示或隐藏下载板块下的所有src开关（仅对下载文件操作显示）
            self.downloadAllSrcSwitch.setVisible(action_type == "下载文件")
            
            # 显示或隐藏XPath容器（网页截图不需要XPath）
            self.xpathContainer.setVisible(action_type != "网页截图")
            
            # 隐藏截图类型容器（用户要求不显示截图类型）
            self.screenshotConfigContainer.setVisible(False)
            

        
        def onVariableSwitchChanged(self, checked):
            """使用变量开关变化事件"""
            # 当使用变量时，隐藏操作值输入框，显示表格字段下拉框
            if checked:
                self.actionValueEdit.setVisible(False)
                self.tableFieldCombo.setVisible(True)
                # 加载表格字段
                self.loadTableFields()
            else:
                self.actionValueEdit.setVisible(True)
                self.tableFieldCombo.setVisible(False)
        
        def loadTableFields(self):
            """加载表格字段到下拉框"""
            # 清空现有选项
            self.tableFieldCombo.clear()
            
            # 获取表格字段
            # 正确获取AutomationToolInterface实例
            parent = None
            current_widget = self.parent()
            # 向上查找直到找到AutomationToolInterface实例
            while current_widget and not hasattr(current_widget, 'automation_flow'):
                current_widget = current_widget.parent()
            parent = current_widget
            
            if parent and hasattr(parent, 'automation_flow'):
                # 获取表格字段
                table_fields = parent.automation_flow.table_manager.get_fields()
                if table_fields:
                    # 先启用下拉框
                    self.tableFieldCombo.setEnabled(True)
                    self.tableFieldCombo.addItems(table_fields)
                else:
                    self.tableFieldCombo.addItem("无可用字段")
                    self.tableFieldCombo.setEnabled(False)
            else:
                self.tableFieldCombo.addItem("无可用字段")
                self.tableFieldCombo.setEnabled(False)
        



        def saveModule(self):
            """保存模块配置"""
            # 更新模块属性
            self.module.name = self.nameEdit.text() or "新模块"
            self.module.set_xpath(self.xpathEdit.text())
            
            # 确定操作值
            action_value = ""
            if self.variableSwitch.isChecked():
                # 使用表格字段作为操作值
                action_value = self.tableFieldCombo.currentText()
            else:
                # 使用操作值输入框中的值
                action_value = self.actionValueEdit.text()
            
            self.module.set_action(
                self.actionTypeCombo.currentText(),
                action_value,
                self.variableSwitch.isChecked(),
                self.variableNameEdit.text()
            )
            
            # 保存下载配置
            if self.actionTypeCombo.currentText() == "下载文件":
                self.module.download_path = self.downloadPathEdit.text()
                self.module.download_all_src = self.downloadAllSrcSwitch.isChecked()
            elif self.actionTypeCombo.currentText() == "网页截图":
                # 保存网页截图配置
                self.module.screenshot_path = self.downloadPathEdit.text()
                self.module.screenshot_type = self.screenshotTypeCombo.currentText()
            
            self.module.set_wait_time(self.waitTimeSpin.value())
            
            # 发送更新信号
            self.moduleUpdated.emit(self.module_id)
        
        def updateModule(self, module):
            """更新模块数据"""
            self.module = module
            self.nameEdit.setText(module.name)
            self.xpathEdit.setText(module.xpath)
            self.actionTypeCombo.setCurrentText(module.action_type)
            self.actionValueEdit.setText(module.action_value)
            self.variableSwitch.setChecked(module.is_variable)
            self.variableNameEdit.setText(module.variable_name)
            self.waitTimeSpin.setValue(module.wait_time)
            
            # 更新下载配置
            if hasattr(module, 'download_path'):
                self.downloadPathEdit.setText(module.download_path)
            else:
                self.downloadPathEdit.setText("")
            
            if hasattr(module, 'download_all_src'):
                self.downloadAllSrcSwitch.setChecked(module.download_all_src)
            else:
                self.downloadAllSrcSwitch.setChecked(False)
            
            # 更新网页截图配置
            if hasattr(module, 'screenshot_path'):
                # 如果有screenshot_path属性，更新下载路径编辑框
                self.downloadPathEdit.setText(module.screenshot_path)
            
            if hasattr(module, 'screenshot_type'):
                # 如果有screenshot_type属性，更新截图类型组合框
                self.screenshotTypeCombo.setCurrentText(module.screenshot_type)
            else:
                # 否则使用默认值
                self.screenshotTypeCombo.setCurrentText('全页面截图')
            
            # 触发操作类型变化事件，确保控件可见性正确
            self.onActionTypeChanged(self.actionTypeCombo.currentIndex())
            
            # 处理变量开关状态
            if module.is_variable:
                self.actionValueEdit.setVisible(False)
                self.tableFieldCombo.setVisible(True)
                # 加载表格字段
                self.loadTableFields()
                # 设置当前表格字段
                if module.action_value:
                    index = self.tableFieldCombo.findText(module.action_value)
                    if index != -1:
                        self.tableFieldCombo.setCurrentIndex(index)
            else:
                self.actionValueEdit.setVisible(True)
                self.tableFieldCombo.setVisible(False)
            
    
    class ConditionCard(CardWidget):
        """条件模块卡片控件"""
        
        moduleUpdated = pyqtSignal(str)  # 模块更新信号
        moduleDeleted = pyqtSignal(str)  # 模块删除信号
        moduleMoved = pyqtSignal(str, bool)  # 模块移动信号 (module_id, is_up)
        
        def __init__(self, module, parent=None):
            super().__init__(parent=parent)
            self.module = module
            self.module_id = module.module_id
            self.setObjectName(f"conditionCard_{self.module_id}")
            self.setupUI()
            # 延迟加载表格字段和获取文本变量，确保模块已经被添加到列表中
            QTimer.singleShot(100, self.delayedLoad)
        
        def delayedLoad(self):
            """延迟加载表格字段和获取文本变量"""
            self.loadTableFields()
            self.loadTextVariables()
        
        def setupUI(self):
            """设置卡片界面"""
            # 主布局
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)  # 调整外边距，使布局更紧凑
            layout.setSpacing(6)  # 减小间距
            self.setMinimumHeight(200)  # 设置足够的最小高度，给出预留空间
            self.setFixedHeight(200)  # 设置固定高度，避免操作类型变化时调整布局
            
            # 第1行：模块名称、保存按钮
            headerLayout = QHBoxLayout()
            headerLayout.setContentsMargins(0, 0, 0, 0)
            headerLayout.setSpacing(6)  # 减小间距
            
            # 模块名称 - 添加标签
            nameLayout = QHBoxLayout()
            nameLayout.setContentsMargins(0, 0, 0, 0)
            nameLayout.setSpacing(4)
            
            nameLabel = QLabel("名称:")
            nameLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            nameLabel.setFixedWidth(50)  # 调整标签宽度
            nameLayout.addWidget(nameLabel)
            
            self.nameEdit = LineEdit()
            self.nameEdit.setObjectName("nameEdit")
            self.nameEdit.setText(self.module.name)
            self.nameEdit.setPlaceholderText("条件名称")
            self.nameEdit.setFixedHeight(28)  # 调整高度
            nameLayout.addWidget(self.nameEdit, 1)  # 增加拉伸因子
            
            headerLayout.addLayout(nameLayout, 2)  # 调整拉伸因子
            
            # 保存按钮
            self.saveBtn = PushButton(FIF.SAVE, "保存")
            self.saveBtn.setObjectName("saveBtn")
            self.saveBtn.setFixedHeight(28)  # 调整高度
            self.saveBtn.setFixedWidth(80)  # 增加宽度，确保文字完整显示
            self.saveBtn.clicked.connect(self.saveModule)
            headerLayout.addWidget(self.saveBtn, 0, Qt.AlignmentFlag.AlignVCenter)
            
            layout.addLayout(headerLayout)
            
            # 第2行：条件类型和循环类型
            typeLayout = QHBoxLayout()
            typeLayout.setContentsMargins(0, 0, 0, 0)
            typeLayout.setSpacing(6)  # 减小间距
            
            typeLabel = QLabel("条件类型:")
            typeLabel.setFixedWidth(80)  # 调整标签宽度
            typeLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            typeLayout.addWidget(typeLabel)
            
            self.conditionTypeLabel = QLabel(self.module.condition_type)
            self.conditionTypeLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            typeLayout.addWidget(self.conditionTypeLabel)
            
            # 循环类型选择
            loopTypeLabel = QLabel("类型:")
            loopTypeLabel.setFixedWidth(40)  # 调整标签宽度
            loopTypeLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            typeLayout.addWidget(loopTypeLabel)
            
            self.loopTypeCombo = ComboBox()
            self.loopTypeCombo.setObjectName("loopTypeCombo")
            self.loopTypeCombo.addItems(["开始循环", "结束循环"])
            self.loopTypeCombo.setCurrentText(self.module.loop_type)
            self.loopTypeCombo.setFixedHeight(28)  # 调整高度
            self.loopTypeCombo.setMinimumWidth(100)  # 调整最小宽度
            # 添加循环类型变化信号连接
            self.loopTypeCombo.currentIndexChanged.connect(self.onLoopTypeChanged)
            typeLayout.addWidget(self.loopTypeCombo)
            
            typeLayout.addStretch()  # 增加拉伸因子，将元素挤到左侧
            layout.addLayout(typeLayout)
            
            # 第3行：循环次数来源选择
            self.sourceContainer = QWidget()
            self.sourceLayout = QHBoxLayout(self.sourceContainer)
            self.sourceLayout.setContentsMargins(0, 0, 0, 0)
            self.sourceLayout.setSpacing(6)  # 减小间距
            
            sourceLabel = QLabel("循环来源:")
            sourceLabel.setFixedWidth(80)  # 调整标签宽度
            sourceLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.sourceLayout.addWidget(sourceLabel)
            
            # 固定次数选项
            self.fixedRadio = QCheckBox("固定次数")
            self.fixedRadio.setChecked(not (self.module.is_variable or self.module.is_table_field))
            self.fixedRadio.clicked.connect(self.onSourceChanged)
            self.sourceLayout.addWidget(self.fixedRadio)
            
            # 表格字段选项
            self.tableRadio = QCheckBox("表格字段")
            self.tableRadio.setChecked(self.module.is_table_field)
            self.tableRadio.clicked.connect(self.onSourceChanged)
            self.sourceLayout.addWidget(self.tableRadio)
            
            # 变量选项
            self.variableRadio = QCheckBox("获取文本变量")
            self.variableRadio.setChecked(self.module.is_variable)
            self.variableRadio.clicked.connect(self.onSourceChanged)
            self.sourceLayout.addWidget(self.variableRadio)
            
            layout.addWidget(self.sourceContainer)
            
            # 第4行：固定次数输入框
            self.fixedCountContainer = QWidget()
            fixedLayout = QHBoxLayout(self.fixedCountContainer)
            fixedLayout.setContentsMargins(0, 0, 0, 0)
            fixedLayout.setSpacing(6)  # 减小间距
            
            fixedLabel = QLabel("循环次数:")
            fixedLabel.setFixedWidth(80)  # 调整标签宽度
            fixedLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            fixedLayout.addWidget(fixedLabel)
            
            self.fixedCountEdit = LineEdit()
            self.fixedCountEdit.setObjectName("fixedCountEdit")
            self.fixedCountEdit.setText(self.module.loop_count)
            self.fixedCountEdit.setPlaceholderText("循环次数")
            self.fixedCountEdit.setFixedHeight(28)  # 调整高度
            fixedLayout.addWidget(self.fixedCountEdit, 1)  # 增加拉伸因子
            
            layout.addWidget(self.fixedCountContainer)
            
            # 第5行：表格字段下拉框
            self.tableFieldContainer = QWidget()
            tableLayout = QHBoxLayout(self.tableFieldContainer)
            tableLayout.setContentsMargins(0, 0, 0, 0)
            tableLayout.setSpacing(6)  # 减小间距
            
            tableLabel = QLabel("表格字段:")
            tableLabel.setFixedWidth(80)  # 调整标签宽度
            tableLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            tableLayout.addWidget(tableLabel)
            
            self.tableFieldCombo = ComboBox()
            self.tableFieldCombo.setObjectName("tableFieldCombo")
            self.tableFieldCombo.setPlaceholderText("选择表格字段")
            self.tableFieldCombo.setFixedHeight(28)  # 调整高度
            self.tableFieldCombo.setMinimumWidth(140)  # 调整最小宽度
            # 加载表格字段
            self.loadTableFields()
            # 设置当前表格字段
            if self.module.is_table_field and self.module.table_field:
                index = self.tableFieldCombo.findText(self.module.table_field)
                if index != -1:
                    self.tableFieldCombo.setCurrentIndex(index)
            tableLayout.addWidget(self.tableFieldCombo, 1)  # 增加拉伸因子
            
            layout.addWidget(self.tableFieldContainer)
            
            # 第6行：变量下拉框
            self.variableContainer = QWidget()
            variableLayout = QHBoxLayout(self.variableContainer)
            variableLayout.setContentsMargins(0, 0, 0, 0)
            variableLayout.setSpacing(6)  # 减小间距
            
            variableLabel = QLabel("变量名称:")
            variableLabel.setFixedWidth(80)  # 调整标签宽度
            variableLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            variableLayout.addWidget(variableLabel)
            
            self.variableCombo = ComboBox()
            self.variableCombo.setObjectName("variableCombo")
            self.variableCombo.setPlaceholderText("选择获取文本变量")
            self.variableCombo.setFixedHeight(28)  # 调整高度
            self.variableCombo.setMinimumWidth(140)  # 调整最小宽度
            # 加载获取文本变量
            self.loadTextVariables()
            # 设置当前变量
            if self.module.is_variable and self.module.variable_name:
                index = self.variableCombo.findText(self.module.variable_name)
                if index != -1:
                    self.variableCombo.setCurrentIndex(index)
            variableLayout.addWidget(self.variableCombo, 1)  # 增加拉伸因子
            
            layout.addWidget(self.variableContainer)
            
            # 操作按钮区域 - 只保留保存按钮，移除上移下移删除按钮
            buttonLayout = QHBoxLayout()
            buttonLayout.setContentsMargins(0, 0, 0, 0)
            buttonLayout.setSpacing(10)
            buttonLayout.addStretch()  # 增加拉伸因子，将按钮挤到右侧
            
            # 只保留保存按钮，移除上移下移删除按钮
            # 保存按钮已经在headerLayout中，这里不需要重复添加
            layout.addLayout(buttonLayout)
            
            # 初始状态处理
            self.onSourceChanged()
            # 初始调用循环类型变化处理，确保状态正确
            self.onLoopTypeChanged()
        
        def onSourceChanged(self):
            """循环次数来源变化事件"""
            # 确保只有一个选项被选中
            if self.sender() == self.fixedRadio and self.fixedRadio.isChecked():
                self.tableRadio.setChecked(False)
                self.variableRadio.setChecked(False)
            elif self.sender() == self.tableRadio and self.tableRadio.isChecked():
                self.fixedRadio.setChecked(False)
                self.variableRadio.setChecked(False)
                # 重新加载表格字段
                self.loadTableFields()
            elif self.sender() == self.variableRadio and self.variableRadio.isChecked():
                self.fixedRadio.setChecked(False)
                self.tableRadio.setChecked(False)
                # 重新加载获取文本变量
                self.loadTextVariables()
            
            # 显示/隐藏相关控件
            self.fixedCountContainer.setVisible(self.fixedRadio.isChecked())
            self.tableFieldContainer.setVisible(self.tableRadio.isChecked())
            self.variableContainer.setVisible(self.variableRadio.isChecked())
        
        def loadTableFields(self):
            """加载表格字段到下拉框"""
            # 清空现有选项
            self.tableFieldCombo.clear()
            
            # 获取表格字段
            # 正确获取AutomationToolInterface实例
            parent = None
            current_widget = self.parent()
            # 向上查找直到找到AutomationToolInterface实例
            while current_widget and not hasattr(current_widget, 'automation_flow'):
                current_widget = current_widget.parent()
            parent = current_widget
            
            if parent and hasattr(parent, 'automation_flow'):
                # 获取表格字段
                table_fields = parent.automation_flow.table_manager.get_fields()
                if table_fields:
                    # 先启用下拉框
                    self.tableFieldCombo.setEnabled(True)
                    self.tableFieldCombo.addItems(table_fields)
                else:
                    self.tableFieldCombo.addItem("无可用字段")
                    self.tableFieldCombo.setEnabled(False)
            else:
                self.tableFieldCombo.addItem("无可用字段")
                self.tableFieldCombo.setEnabled(False)
        
        def loadTextVariables(self):
            """加载获取文本变量到下拉框"""
            # 清空现有选项
            self.variableCombo.clear()
            
            # 获取所有获取文本的模块名
            # 正确获取AutomationToolInterface实例
            parent = None
            current_widget = self.parent()
            # 向上查找直到找到AutomationToolInterface实例
            while current_widget and not hasattr(current_widget, 'automation_flow'):
                current_widget = current_widget.parent()
            parent = current_widget
            
            if parent and hasattr(parent, 'automation_flow'):
                # 获取所有模块
                modules = parent.automation_flow.module_manager.get_all_modules()
                # 获取当前条件模块的索引
                current_index = -1
                for i, module in enumerate(modules):
                    if module.module_id == self.module_id:
                        current_index = i
                        break
                
                # 只添加当前条件模块之前的获取文本模块
                text_modules = []
                if current_index >= 0:
                    for module in modules[:current_index]:
                        if hasattr(module, 'action_type') and module.action_type == "获取文本":
                            text_modules.append(module.name)
                
                if text_modules:
                    # 先启用下拉框
                    self.variableCombo.setEnabled(True)
                    self.variableCombo.addItems(text_modules)
                else:
                    self.variableCombo.addItem("无可用获取文本变量")
                    self.variableCombo.setEnabled(False)
            else:
                self.variableCombo.addItem("无可用获取文本变量")
                self.variableCombo.setEnabled(False)
        
        def onLoopTypeChanged(self, index=None):
            """循环类型变化事件"""
            loop_type = self.loopTypeCombo.currentText()
            is_end_loop = loop_type == "结束循环"
            
            # 当选择结束循环时，隐藏循环次数相关控件
            # 隐藏循环次数来源选择
            self.sourceContainer.setVisible(not is_end_loop)
            # 隐藏固定次数输入框
            self.fixedCountContainer.setVisible(not is_end_loop)
            # 隐藏表格字段下拉框
            self.tableFieldContainer.setVisible(not is_end_loop)
            # 隐藏变量下拉框
            self.variableContainer.setVisible(not is_end_loop)
        
        def saveModule(self):
            """保存模块配置"""
            # 更新模块属性
            self.module.name = self.nameEdit.text() or "循环条件"
            
            # 保存循环类型
            self.module.loop_type = self.loopTypeCombo.currentText()
            
            # 只有开始循环需要配置循环次数
            if self.loopTypeCombo.currentText() == "开始循环":
                if self.fixedRadio.isChecked():
                    # 固定次数
                    self.module.loop_count = self.fixedCountEdit.text() or "1"
                    self.module.is_variable = False
                    self.module.is_table_field = False
                    self.module.variable_name = ""
                    self.module.table_field = ""
                elif self.tableRadio.isChecked():
                    # 表格字段
                    self.module.loop_count = ""
                    self.module.is_variable = False
                    self.module.is_table_field = True
                    self.module.variable_name = ""
                    self.module.table_field = self.tableFieldCombo.currentText()
                elif self.variableRadio.isChecked():
                    # 变量
                    self.module.loop_count = ""
                    self.module.is_variable = True
                    self.module.is_table_field = False
                    self.module.variable_name = self.variableCombo.currentText()
                    self.module.table_field = ""
            
            # 发送更新信号
            self.moduleUpdated.emit(self.module_id)
        
        def deleteModule(self):
            """删除模块"""
            self.moduleDeleted.emit(self.module_id)
    
    def setupUI(self):
        """设置界面布局"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        titleLabel = TitleLabel("模块化浏览器自动化工具")
        layout.addWidget(titleLabel, alignment=Qt.AlignmentFlag.AlignTop)
        
        # 描述
        self.descLabel = QLabel("通过模块化配置实现浏览器自动化操作，支持条件判断和批量数据处理")
        self.descLabel.setObjectName("descLabel")
        layout.addWidget(self.descLabel, alignment=Qt.AlignmentFlag.AlignTop)
        
        # 主内容区域 - 分为两部分：左侧控制面板、右侧内容区域
        mainSplitter = QSplitter(Qt.Orientation.Horizontal)
        mainSplitter.setHandleWidth(1)  # 进一步调细，几乎不可见
        mainSplitter.setObjectName("mainSplitter")
        # 美化分隔条样式 - 使其更融入背景，与主题更协调
        mainSplitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
                border: none;
            }
            QSplitter::handle:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        
        # 左侧控制面板 - 增加宽度解决拥挤问题
        leftPanel = self.createLeftPanel()
        leftPanel.setMinimumWidth(300)  # 增加左侧面板最小宽度，解决拥挤问题
        mainSplitter.addWidget(leftPanel)
        
        # 右侧内容区域 - 垂直分割为模块列表和模块配置
        rightContent = QWidget()
        rightContentLayout = QVBoxLayout(rightContent)
        rightContentLayout.setContentsMargins(0, 0, 0, 0)
        rightContentLayout.setSpacing(0)
        
        # 上方模块列表面板 - 为主显示
        self.moduleListPanel = self.createModuleListPanel()
        self.moduleListPanel.setMinimumHeight(300)  # 增加最小高度，为主显示
        rightContentLayout.addWidget(self.moduleListPanel, 2)  # 增加拉伸因子，占据更大比例
        
        # 下方配置面板 - 为辅显示
        self.configPanel = self.createConfigPanel()
        self.configPanel.setMinimumHeight(250)  # 固定高度，避免布局调整
        self.configPanel.setMaximumHeight(300)  # 设置最大高度，给出预留空间
        rightContentLayout.addWidget(self.configPanel, 1)  # 减小拉伸因子，为辅显示
        
        mainSplitter.addWidget(rightContent)
        
        # 设置初始大小比例 - 将中心线向右调整，增加左侧面板宽度
        mainSplitter.setSizes([350, 700])  # 增加左侧面板初始宽度，从250改为350
        
        layout.addWidget(mainSplitter, 1)
        
        # 状态信息
        self.statusBar = QFrame()
        self.statusBar.setObjectName("statusBar")
        statusLayout = QHBoxLayout(self.statusBar)
        statusLayout.setContentsMargins(10, 5, 10, 5)
        
        self.browserStatusLabel = QLabel("浏览器: 未连接")
        self.tableStatusLabel = QLabel("表格数据: 未加载")
        self.automationStatusLabel = QLabel("自动化: 就绪")
        
        statusLayout.addWidget(self.browserStatusLabel)
        statusLayout.addStretch()
        statusLayout.addWidget(self.tableStatusLabel)
        statusLayout.addStretch()
        statusLayout.addWidget(self.automationStatusLabel)
        
        layout.addWidget(self.statusBar)
    
    def createLeftPanel(self):
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 浏览器连接区域
        browserGroup = CardWidget()
        browserGroup.setObjectName("browserGroup")
        browserLayout = QVBoxLayout(browserGroup)
        browserLayout.setContentsMargins(15, 15, 15, 15)
        browserLayout.setSpacing(10)
        
        browserTitle = SubtitleLabel("浏览器连接")
        browserLayout.addWidget(browserTitle)
        
        # 水平布局放置浏览器连接按钮
        browserButtonsLayout = QHBoxLayout()
        browserButtonsLayout.setSpacing(10)
        
        self.connectBrowserBtn = PrimaryPushButton(FIF.LINK, "连接浏览器")
        self.connectBrowserBtn.clicked.connect(self.connectBrowser)
        browserButtonsLayout.addWidget(self.connectBrowserBtn)
        
        self.disconnectBrowserBtn = PushButton(FIF.CLOSE, "断开浏览器")
        self.disconnectBrowserBtn.clicked.connect(self.disconnectBrowser)
        self.disconnectBrowserBtn.setEnabled(False)
        browserButtonsLayout.addWidget(self.disconnectBrowserBtn)
        
        browserLayout.addLayout(browserButtonsLayout)
        
        layout.addWidget(browserGroup)
        
        # 表格数据区域 - 进一步压缩上下间距
        tableGroup = CardWidget()
        tableGroup.setObjectName("tableGroup")
        tableGroup.setMinimumHeight(80)  # 进一步减小最小高度
        tableLayout = QVBoxLayout(tableGroup)
        tableLayout.setContentsMargins(15, 10, 15, 10)  # 减小上下边距
        tableLayout.setSpacing(4)  # 进一步减小垂直间距
        
        tableTitle = SubtitleLabel("表格数据")
        tableTitle.setStyleSheet("font-size: 14px; margin: 0;")  # 调整字体大小和边距
        tableLayout.addWidget(tableTitle)
        
        # 加载表格按钮和字段下拉选择框放在同一行
        loadAndFieldsLayout = QHBoxLayout()
        loadAndFieldsLayout.setContentsMargins(0, 0, 0, 0)
        loadAndFieldsLayout.setSpacing(6)  # 减小间距
        
        self.loadTableBtn = PushButton(FIF.FOLDER, "加载表格")  # 缩短按钮文字
        self.loadTableBtn.clicked.connect(self.loadTable)
        self.loadTableBtn.setFixedHeight(26)  # 进一步减小按钮高度
        loadAndFieldsLayout.addWidget(self.loadTableBtn, 1)  # 增加拉伸因子
        
        # 表格字段下拉选择框
        fieldsLabel = QLabel("字段:")
        fieldsLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        fieldsLabel.setStyleSheet("font-size: 12px; margin: 0;")  # 减小标签字体大小和边距
        loadAndFieldsLayout.addWidget(fieldsLabel)
        
        self.fieldsComboBox = ComboBox()
        self.fieldsComboBox.setObjectName("fieldsComboBox")
        self.fieldsComboBox.setPlaceholderText("选择字段")  # 简化占位文字
        self.fieldsComboBox.setFixedHeight(26)  # 进一步减小高度
        self.fieldsComboBox.setMinimumWidth(120)  # 减小最小宽度
        loadAndFieldsLayout.addWidget(self.fieldsComboBox, 1)  # 增加拉伸因子
        
        # 清除表格按钮
        self.clearTableBtn = ToolButton(FIF.CLOSE)  # 使用CLOSE图标
        self.clearTableBtn.setToolTip("清除表格数据")  # 添加提示文本
        self.clearTableBtn.setFixedHeight(26)  # 设置高度与其他按钮一致
        self.clearTableBtn.setFixedWidth(26)  # 设置宽度与高度一致，形成圆形按钮效果
        self.clearTableBtn.clicked.connect(self.clearTable)
        loadAndFieldsLayout.addWidget(self.clearTableBtn)
        
        tableLayout.addLayout(loadAndFieldsLayout)
        
        layout.addWidget(tableGroup)
        
        # 自动化控制区域
        controlGroup = CardWidget()
        controlGroup.setObjectName("controlGroup")
        controlLayout = QVBoxLayout(controlGroup)
        controlLayout.setContentsMargins(15, 15, 15, 15)
        controlLayout.setSpacing(10)
        
        controlTitle = SubtitleLabel("自动化控制")
        controlLayout.addWidget(controlTitle)
        
        # 水平排列的按钮布局
        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSpacing(10)
        buttonsLayout.setContentsMargins(0, 0, 0, 0)
        
        self.startBtn = PrimaryPushButton(FIF.PLAY, "开始")
        self.startBtn.clicked.connect(self.startAutomation)
        # 设置按钮宽度适配框架，使用拉伸因子平均分配空间
        buttonsLayout.addWidget(self.startBtn, 1)  # 拉伸因子为1
        
        self.pauseBtn = PushButton(FIF.PAUSE, "暂停/继续")
        self.pauseBtn.clicked.connect(self.pauseAutomation)
        self.pauseBtn.setEnabled(False)
        # 设置按钮宽度适配框架，使用拉伸因子平均分配空间
        buttonsLayout.addWidget(self.pauseBtn, 1)  # 拉伸因子为1
        
        self.stopBtn = PushButton(FIF.CLOSE, "停止")
        self.stopBtn.clicked.connect(self.stopAutomation)
        self.stopBtn.setEnabled(False)
        # 设置按钮宽度适配框架，使用拉伸因子平均分配空间
        buttonsLayout.addWidget(self.stopBtn, 1)  # 拉伸因子为1
        
        controlLayout.addLayout(buttonsLayout)
        
        # 进度条
        self.progressBar = IndeterminateProgressBar()
        self.progressBar.setVisible(False)
        controlLayout.addWidget(self.progressBar)
        
        layout.addWidget(controlGroup)
        
        # 配置管理区域
        configGroup = CardWidget()
        configGroup.setObjectName("configGroup")
        configLayout = QVBoxLayout(configGroup)
        configLayout.setContentsMargins(15, 15, 15, 15)
        configLayout.setSpacing(10)
        
        configTitle = SubtitleLabel("配置管理")
        configLayout.addWidget(configTitle)
        
        # 水平布局放置配置管理按钮
        configButtonsLayout = QHBoxLayout()
        configButtonsLayout.setSpacing(10)
        
        self.saveConfigBtn = PushButton(FIF.SAVE, "保存配置")
        self.saveConfigBtn.clicked.connect(self.saveConfig)
        configButtonsLayout.addWidget(self.saveConfigBtn)
        
        self.loadConfigBtn = PushButton(FIF.FOLDER, "加载配置")
        self.loadConfigBtn.clicked.connect(self.loadConfig)
        configButtonsLayout.addWidget(self.loadConfigBtn)
        
        configLayout.addLayout(configButtonsLayout)
        
        layout.addWidget(configGroup)
        
        layout.addStretch()
        
        return panel
    
    def createModuleListPanel(self):
        """创建中间模块列表面板 - 以表格形式显示模块列表和循环条件"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 模块列表标题
        moduleListHeaderLayout = QHBoxLayout()
        moduleListHeaderLayout.setContentsMargins(0, 0, 0, 0)
        
        moduleListTitleLabel = QLabel("模块列表")
        moduleListTitleLabel.setStyleSheet("font-weight: bold; font-size: 14px;")
        moduleListHeaderLayout.addWidget(moduleListTitleLabel)
        moduleListHeaderLayout.addStretch()
        
        layout.addLayout(moduleListHeaderLayout)
        
        # 模块列表 - 使用QTableWidget显示模块列表和循环条件
        self.moduleTableWidget = QTableWidget()
        self.moduleTableWidget.setObjectName("moduleTableWidget")
        self.moduleTableWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.moduleTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.moduleTableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # 禁用直接编辑，使用控件编辑
        self.moduleTableWidget.itemClicked.connect(self.onModuleTableItemClicked)
        
        # 设置列
        self.moduleTableWidget.setColumnCount(3)
        self.moduleTableWidget.setHorizontalHeaderLabels(["序号", "模块名", "操作类型"])
        
        # 设置宽度自适应
        self.moduleTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # 但为序号列设置固定宽度
        self.moduleTableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.moduleTableWidget.setColumnWidth(0, 50)
        
        # 启用水平滚动条
        self.moduleTableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 初始设置表格样式，具体颜色将在updateTheme中根据主题调整
        self.updateTableTheme()
        
        # 隐藏垂直表头
        self.moduleTableWidget.verticalHeader().setVisible(False)
        
        layout.addWidget(self.moduleTableWidget)
        
        # 模块控制按钮 - 添加模块、添加条件、上移、下移、删除
        moduleControlLayout = QHBoxLayout()
        moduleControlLayout.setContentsMargins(0, 0, 0, 0)
        moduleControlLayout.setSpacing(10)
        
        self.addModuleBtn = PrimaryPushButton(FIF.ADD, "添加模块")
        self.addModuleBtn.clicked.connect(self.addModule)
        moduleControlLayout.addWidget(self.addModuleBtn)
        
        self.addConditionBtn = PrimaryPushButton(FIF.CODE, "添加条件")
        self.addConditionBtn.clicked.connect(self.addCondition)
        moduleControlLayout.addWidget(self.addConditionBtn)
        
        self.moveUpBtn = PushButton(FIF.UP, "上移")
        self.moveUpBtn.clicked.connect(self.onMoveUpBtnClicked)
        moduleControlLayout.addWidget(self.moveUpBtn)
        
        self.moveDownBtn = PushButton(FIF.DOWN, "下移")
        self.moveDownBtn.clicked.connect(self.onMoveDownBtnClicked)
        moduleControlLayout.addWidget(self.moveDownBtn)
        
        self.deleteModuleBtn = PushButton(FIF.DELETE, "删除")
        self.deleteModuleBtn.clicked.connect(self.onDeleteModuleBtnClicked)
        moduleControlLayout.addWidget(self.deleteModuleBtn)
        
        layout.addLayout(moduleControlLayout)
        
        return panel
    
    def createConfigPanel(self):
        """创建右侧固定配置面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 配置标题
        configTitleLabel = QLabel("模块配置")
        configTitleLabel.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(configTitleLabel)
        
        # 配置内容区域 - 初始为空，选中模块后填充
        self.configContent = QWidget()
        self.configContentLayout = QVBoxLayout(self.configContent)
        self.configContentLayout.setContentsMargins(0, 0, 0, 0)
        self.configContentLayout.setSpacing(10)
        
        # 初始提示信息
        self.configPlaceholder = QLabel("请从左侧模块列表中选择一个模块进行配置")
        self.configPlaceholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.configPlaceholder.setStyleSheet("color: #888888; font-style: italic;")
        self.configContentLayout.addWidget(self.configPlaceholder)
        
        layout.addWidget(self.configContent)
        
        return panel
    
    def onModuleTableItemClicked(self, item):
        """模块列表项点击事件 - 显示选中模块的配置"""
        row = item.row()
        module_id_item = self.moduleTableWidget.item(row, 1)  # 模块ID存储在第二列的UserData中
        if module_id_item:
            module_id = module_id_item.data(Qt.ItemDataRole.UserRole)
            if module_id and module_id in self.module_cards:
                # 更新当前模块ID
                self.current_module_id = module_id
                
                # 清空当前配置内容
                self.clearConfigPanel()
                
                # 添加选中模块的配置卡片
                card = self.module_cards[module_id]
                self.configContentLayout.addWidget(card)
                
                # 特别处理普通模块，确保配置页面正确更新
                if hasattr(card, 'onActionTypeChanged'):
                    card.onActionTypeChanged(card.actionTypeCombo.currentIndex())
    

    
    def clearConfigPanel(self):
        """清空配置面板内容"""
        # 清空当前配置内容
        for i in reversed(range(self.configContentLayout.count())):
            item = self.configContentLayout.takeAt(i)
            if item:
                widget = item.widget()
                if widget:
                    self.configContentLayout.removeWidget(widget)
                    widget.setParent(None)  # 移除父控件，避免重叠
    
    def onMoveUpBtnClicked(self):
        """上移按钮点击事件"""
        current_row = self.moduleTableWidget.currentRow()
        if current_row > 0:
            # 获取当前行的模块ID
            module_id_item = self.moduleTableWidget.item(current_row, 1)
            if module_id_item:
                module_id = module_id_item.data(Qt.ItemDataRole.UserRole)
                self.onModuleMoved(module_id, True)
    
    def onMoveDownBtnClicked(self):
        """下移按钮点击事件"""
        current_row = self.moduleTableWidget.currentRow()
        if current_row < self.moduleTableWidget.rowCount() - 1:
            # 获取当前行的模块ID
            module_id_item = self.moduleTableWidget.item(current_row, 1)
            if module_id_item:
                module_id = module_id_item.data(Qt.ItemDataRole.UserRole)
                self.onModuleMoved(module_id, False)
    
    def onDeleteModuleBtnClicked(self):
        """删除按钮点击事件"""
        current_row = self.moduleTableWidget.currentRow()
        if current_row >= 0:
            # 获取当前行的模块ID
            module_id_item = self.moduleTableWidget.item(current_row, 1)
            if module_id_item:
                module_id = module_id_item.data(Qt.ItemDataRole.UserRole)
                self.onModuleDeleted(module_id)
        
    def updateModuleList(self):
        """更新模块列表"""
        # 保存当前选中的模块ID
        selected_module_id = None
        current_row = self.moduleTableWidget.currentRow()
        if current_row >= 0:
            name_item = self.moduleTableWidget.item(current_row, 1)
            if name_item:
                selected_module_id = name_item.data(Qt.ItemDataRole.UserRole)
        
        # 清空表格
        self.moduleTableWidget.setRowCount(0)
        
        # 从模块管理器获取最新的模块列表（带正确顺序）
        modules = self.automation_flow.module_manager.get_all_modules()
        
        # 添加所有模块到表格
        for idx, module in enumerate(modules):
            if module.module_id in self.module_cards:
                card = self.module_cards[module.module_id]
                
                # 创建新行
                self.moduleTableWidget.insertRow(idx)
                
                # 设置序号
                index_item = QTableWidgetItem(str(idx + 1))
                
                # 设置模块名
                name_item = QTableWidgetItem(card.nameEdit.text())
                name_item.setData(Qt.ItemDataRole.UserRole, module.module_id)
                
                # 设置类型
                type_item = QTableWidgetItem("条件模块" if hasattr(module, 'condition_type') else module.action_type)
                
                # 检查是否为条件模块，设置不同的颜色
                is_dark = isDarkTheme()
                if hasattr(module, 'condition_type'):
                    # 条件模块，设置不同的背景颜色
                    if is_dark:
                        # 深色主题下的条件模块样式
                        for item in [index_item, name_item, type_item]:
                            item.setBackground(Qt.GlobalColor.darkGreen)
                            item.setForeground(Qt.GlobalColor.white)
                    else:
                        # 浅色主题下的条件模块样式
                        for item in [index_item, name_item, type_item]:
                            item.setBackground(Qt.GlobalColor.lightGreen)
                            item.setForeground(Qt.GlobalColor.darkGreen)
                
                # 添加到表格
                self.moduleTableWidget.setItem(idx, 0, index_item)
                self.moduleTableWidget.setItem(idx, 1, name_item)
                self.moduleTableWidget.setItem(idx, 2, type_item)
        
        # 确定要选中的模块ID：优先使用current_module_id（新创建的模块），其次使用之前选中的模块ID
        target_module_id = self.current_module_id if self.current_module_id else selected_module_id
        
        # 恢复选中状态
        if target_module_id:
            # 遍历表格查找对应的模块ID并选中
            for row in range(self.moduleTableWidget.rowCount()):
                name_item = self.moduleTableWidget.item(row, 1)
                if name_item and name_item.data(Qt.ItemDataRole.UserRole) == target_module_id:
                    self.moduleTableWidget.setCurrentCell(row, 0)
                    self.moduleTableWidget.selectRow(row)
                    break
    
    def updateTheme(self):
        """更新主题 - 更专业的样式设计"""
        is_dark = isDarkTheme()
        
        # 更新样式
        if is_dark:
            self.setStyleSheet("""
                /* 基础样式 */
                QWidget {
                    color: #e0e0e0;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                    font-size: 13px;
                }
                
                /* 面板和卡片样式 */
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #404040;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                    background-color: #2d2d2d;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #e0e0e0;
                    font-size: 14px;
                }
                
                /* 状态栏 */
                QFrame#statusBar {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 8px;
                    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
                }
                
                /* 输入控件样式 */
                QLineEdit,
                QComboBox,
                QDoubleSpinBox,
                QTextEdit {
                    background-color: #333333;
                    color: #e0e0e0;
                    border: 1px solid #404040;
                    border-radius: 6px;
                    padding: 6px 8px;
                    margin: 0;
                    transition: all 0.2s ease;
                }
                
                QLineEdit:focus,
                QComboBox:focus,
                QDoubleSpinBox:focus,
                QTextEdit:focus {
                    border: 1px solid #4CAF50;
                    background-color: #3a3a3a;
                    outline: none;
                    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
                }
                
                /* 组合框下拉样式 */
                QComboBox::drop-down {
                    background-color: #333333;
                    border: none;
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                }
                QComboBox::down-arrow {
                    color: #e0e0e0;
                    padding: 2px;
                }
                QComboBox QAbstractItemView {
                    background-color: #333333;
                    color: #e0e0e0;
                    border: 1px solid #404040;
                    border-radius: 6px;
                    selection-background-color: #4CAF50;
                }
                
                /* 双精度输入框按钮 */
                QDoubleSpinBox::up-button,
                QDoubleSpinBox::down-button {
                    background-color: #444444;
                    color: #e0e0e0;
                    border: none;
                    border-radius: 0;
                }
                QDoubleSpinBox::up-button {
                    border-top-right-radius: 6px;
                }
                QDoubleSpinBox::down-button {
                    border-bottom-right-radius: 6px;
                }
                
                /* 滚动区域样式 */
                QScrollArea {
                    background-color: transparent;
                    border: none;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: transparent;
                }
                
                /* 滚动条样式 */
                QScrollBar:vertical {
                    background-color: #333333;
                    width: 10px;
                    border-radius: 5px;
                }
                QScrollBar:horizontal {
                    background-color: #333333;
                    height: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical,
                QScrollBar::handle:horizontal {
                    background-color: #555555;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover,
                QScrollBar::handle:horizontal:hover {
                    background-color: #666666;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical,
                QScrollBar::add-line:horizontal,
                QScrollBar::sub-line:horizontal {
                    background-color: transparent;
                }
                
                /* 列表控件样式 */
                QListWidget {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #404040;
                    border-radius: 8px;
                    selection-background-color: #4CAF50;
                    selection-color: #ffffff;
                    show-decoration-selected: 1;
                }
                QListWidget::item {
                    padding: 8px 12px;
                    border-bottom: 1px solid #404040;
                }
                QListWidget::item:last-child {
                    border-bottom: none;
                }
                QListWidget::item:hover {
                    background-color: #3a3a3a;
                }
                QListWidget::item:selected {
                    background-color: #4CAF50;
                }
                
                /* 标签样式 */
                QLabel {
                    color: #e0e0e0;
                    margin: 0;
                    padding: 0;
                }
                
                /* 模块容器 */
                #moduleContainer {
                    background-color: transparent;
                }
                
                /* 按钮样式增强 */
                QPushButton {
                    transition: all 0.2s ease;
                }
                
                /* 分割器样式 */
                QSplitter::handle {
                    background-color: #404040;
                }
                QSplitter::handle:hover {
                    background-color: #555555;
                }
            """)
        else:
            self.setStyleSheet("""
                /* 基础样式 */
                QWidget {
                    color: #333333;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                    font-size: 13px;
                }
                
                /* 面板和卡片样式 */
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                    background-color: #ffffff;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #333333;
                    font-size: 14px;
                }
                
                /* 状态栏 */
                QFrame#statusBar {
                    background-color: #f5f5f5;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
                }
                
                /* 输入控件样式 */
                QLineEdit,
                QComboBox,
                QDoubleSpinBox,
                QTextEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    padding: 6px 8px;
                    margin: 0;
                    transition: all 0.2s ease;
                }
                
                QLineEdit:focus,
                QComboBox:focus,
                QDoubleSpinBox:focus,
                QTextEdit:focus {
                    border: 1px solid #4CAF50;
                    outline: none;
                    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
                }
                
                /* 组合框下拉样式 */
                QComboBox::drop-down {
                    background-color: #ffffff;
                    border: none;
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                }
                QComboBox::down-arrow {
                    color: #666666;
                    padding: 2px;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    selection-background-color: #4CAF50;
                    selection-color: #ffffff;
                }
                
                /* 双精度输入框按钮 */
                QDoubleSpinBox::up-button,
                QDoubleSpinBox::down-button {
                    background-color: #f5f5f5;
                    color: #333333;
                    border: none;
                    border-radius: 0;
                }
                QDoubleSpinBox::up-button {
                    border-top-right-radius: 6px;
                }
                QDoubleSpinBox::down-button {
                    border-bottom-right-radius: 6px;
                }
                
                /* 滚动区域样式 */
                QScrollArea {
                    background-color: transparent;
                    border: none;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: transparent;
                }
                
                /* 滚动条样式 */
                QScrollBar:vertical {
                    background-color: #f5f5f5;
                    width: 10px;
                    border-radius: 5px;
                }
                QScrollBar:horizontal {
                    background-color: #f5f5f5;
                    height: 10px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical,
                QScrollBar::handle:horizontal {
                    background-color: #c0c0c0;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover,
                QScrollBar::handle:horizontal:hover {
                    background-color: #a0a0a0;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical,
                QScrollBar::add-line:horizontal,
                QScrollBar::sub-line:horizontal {
                    background-color: transparent;
                }
                
                /* 列表控件样式 */
                QListWidget {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    selection-background-color: #4CAF50;
                    selection-color: #ffffff;
                    show-decoration-selected: 1;
                }
                QListWidget::item {
                    padding: 8px 12px;
                    border-bottom: 1px solid #f0f0f0;
                }
                QListWidget::item:last-child {
                    border-bottom: none;
                }
                QListWidget::item:hover {
                    background-color: #f5f5f5;
                }
                QListWidget::item:selected {
                    background-color: #4CAF50;
                }
                
                /* 标签样式 */
                QLabel {
                    color: #333333;
                    margin: 0;
                    padding: 0;
                }
                
                /* 模块容器 */
                #moduleContainer {
                    background-color: transparent;
                }
                
                /* 按钮样式增强 */
                QPushButton {
                    transition: all 0.2s ease;
                }
                
                /* 分割器样式 */
                QSplitter::handle {
                    background-color: #e0e0e0;
                }
                QSplitter::handle:hover {
                    background-color: #c0c0c0;
                }
            """)
        
        # 更新标签颜色
        self.descLabel.setStyleSheet(f"color: {'#a0a0a0' if is_dark else '#666666'}; font-size: 13px;")
        
        # 更新列表控件样式
        if hasattr(self, 'moduleTableWidget') and self.moduleTableWidget:
            self.updateTableTheme()
    
    def updateTableTheme(self):
        """根据当前主题更新表格样式"""
        is_dark = isDarkTheme()
        
        # 获取系统主题的强调色，与PrimaryPushButton保持一致
        from qfluentwidgets import themeColor
        # 获取当前主题的强调色，themeColor()会根据当前主题自动返回正确的颜色
        accent_color = themeColor().name()  # 获取颜色的十六进制表示
        
        if is_dark:
            # 深色主题表格样式
            table_style = f"""
                QTableWidget {{
                    border: 1px solid #404040;
                    border-radius: 4px;
                    background-color: #333333;
                    gridline-color: #404040;
                }}
                QTableWidget::item {{
                    padding: 8px;
                    border-bottom: 1px solid #404040;
                    color: #e0e0e0;
                }}
                QTableWidget::item:selected {{
                    background-color: {accent_color};
                    color: #000000;
                }}
                QTableWidget::header {{
                    background-color: #2a2a2a;
                    border: none;
                    border-bottom: 2px solid #404040;
                    font-weight: bold;
                    font-size: 13px;
                    color: #e0e0e0;
                    padding: 10px;
                }}
                QTableWidget::horizontalHeader {{
                    background-color: #2a2a2a;
                    border: none;
                    border-bottom: 2px solid #404040;
                }}
                QTableWidget::horizontalHeader::section {{
                    background-color: #2a2a2a;
                    border: none;
                    border-bottom: 2px solid #404040;
                    font-weight: bold;
                    font-size: 13px;
                    color: #e0e0e0;
                    padding: 6px;
                    min-height: 20px;
                }}
                QTableWidget::verticalHeader {{
                    background-color: #2a2a2a;
                    border: none;
                    border-right: 1px solid #404040;
                    color: #e0e0e0;
                }}
                QTableWidget QComboBox {{
                    background-color: #333333;
                    color: #e0e0e0;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    padding: 4px 8px;
                    margin: 0;
                }}
                QTableWidget QComboBox::drop-down {{
                    background-color: #333333;
                    border: none;
                    border-top-right-radius: 4px;
                    border-bottom-right-radius: 4px;
                }}
                QTableWidget QComboBox::down-arrow {{
                    color: #e0e0e0;
                    padding: 2px;
                }}
                QTableWidget QComboBox QAbstractItemView {{
                    background-color: #333333;
                    color: #e0e0e0;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    selection-background-color: {accent_color};
                }}
                QTableWidget QDoubleSpinBox {{
                    background-color: #333333;
                    color: #e0e0e0;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    padding: 4px 8px;
                    margin: 0;
                }}
                QTableWidget QDoubleSpinBox::up-button,
                QTableWidget QDoubleSpinBox::down-button {{
                    background-color: #444444;
                    color: #e0e0e0;
                    border: none;
                    border-radius: 0;
                }}
                QTableWidget QDoubleSpinBox::up-button {{
                    border-top-right-radius: 4px;
                }}
                QTableWidget QDoubleSpinBox::down-button {{
                    border-bottom-right-radius: 4px;
                }}
            """
        else:
            # 浅色主题表格样式
            table_style = f"""
                QTableWidget {{
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    background-color: #FFFFFF;
                    gridline-color: #E0E0E0;
                }}
                QTableWidget::item {{
                    padding: 8px;
                    border-bottom: 1px solid #F0F0F0;
                    color: #333333;
                }}
                QTableWidget::item:selected {{
                    background-color: {accent_color};
                    color: #000000;
                }}
                QTableWidget::header {{
                    background-color: #F5F5F5;
                    border: none;
                    border-bottom: 2px solid #E0E0E0;
                    font-weight: bold;
                    font-size: 13px;
                    color: #333333;
                    padding: 10px;
                }}
                QTableWidget::horizontalHeader {{
                    background-color: #F5F5F5;
                    border: none;
                    border-bottom: 2px solid #E0E0E0;
                }}
                QTableWidget::horizontalHeader::section {{
                    background-color: #F5F5F5;
                    border: none;
                    border-bottom: 2px solid #E0E0E0;
                    font-weight: bold;
                    font-size: 13px;
                    color: #333333;
                    padding: 6px;
                    min-height: 20px;
                }}
                QTableWidget::verticalHeader {{
                    background-color: #F5F5F5;
                    border: none;
                    border-right: 1px solid #E0E0E0;
                    color: #333333;
                }}
                QTableWidget QComboBox {{
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    margin: 0;
                }}
                QTableWidget QComboBox::drop-down {{
                    background-color: #ffffff;
                    border: none;
                    border-top-right-radius: 4px;
                    border-bottom-right-radius: 4px;
                }}
                QTableWidget QComboBox::down-arrow {{
                    color: #666666;
                    padding: 2px;
                }}
                QTableWidget QComboBox QAbstractItemView {{
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    selection-background-color: {accent_color};
                }}
                QTableWidget QDoubleSpinBox {{
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    margin: 0;
                }}
                QTableWidget QDoubleSpinBox::up-button,
                QTableWidget QDoubleSpinBox::down-button {{
                    background-color: #f0f0f0;
                    color: #333333;
                    border: none;
                    border-radius: 0;
                }}
                QTableWidget QDoubleSpinBox::up-button {{
                    border-top-right-radius: 4px;
                }}
                QTableWidget QDoubleSpinBox::down-button {{
                    border-bottom-right-radius: 4px;
                }}
            """
        
        # 应用表格样式
        self.moduleTableWidget.setStyleSheet(table_style)
        
        # 额外设置表头样式，确保被正确应用
        header = self.moduleTableWidget.horizontalHeader()
        if is_dark:
            header.setStyleSheet("""
                QHeaderView::section {
                    background-color: #2a2a2a;
                    border: none;
                    border-bottom: 2px solid #404040;
                    font-weight: bold;
                    font-size: 13px;
                    color: #e0e0e0;
                    padding: 6px;
                    min-height: 20px;
                }
            """)
        else:
            header.setStyleSheet("""
                QHeaderView::section {
                    background-color: #F5F5F5;
                    border: none;
                    border-bottom: 2px solid #E0E0E0;
                    font-weight: bold;
                    font-size: 13px;
                    color: #333333;
                    padding: 6px;
                    min-height: 20px;
                }
            """)
    
    def connectBrowser(self):
        """连接浏览器"""
        if self.automation_flow.connect_browser():
            self.connectBrowserBtn.setEnabled(False)
            self.disconnectBrowserBtn.setEnabled(True)
            # 更新浏览器状态，包含网页标题
            self.updateBrowserStatus()
            # 启动定时器，定期更新网页标题
            self.title_update_timer.start()
            InfoBar.success(
                title="成功",
                content="浏览器连接成功",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
        else:
            InfoBar.error(
                title="错误",
                content="浏览器连接失败，请确保浏览器已打开并启用调试模式",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
    
    def disconnectBrowser(self):
        """断开浏览器"""
        self.automation_flow.disconnect_browser()
        self.connectBrowserBtn.setEnabled(True)
        self.disconnectBrowserBtn.setEnabled(False)
        self.browserStatusLabel.setText("浏览器: 未连接")
        # 停止定时器
        self.title_update_timer.stop()
        InfoBar.success(
            title="成功",
            content="浏览器已断开连接",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
    
    def updateBrowserStatus(self):
        """更新浏览器状态，包含当前网页标题"""
        if self.automation_flow.browser.is_connected:
            # 获取当前网页标题
            page_title = self.automation_flow.browser.get_page_title()
            if page_title:
                self.browserStatusLabel.setText(f"浏览器: 已连接 - {page_title}")
            else:
                self.browserStatusLabel.setText("浏览器: 已连接")
        else:
            self.browserStatusLabel.setText("浏览器: 未连接")
    
    def loadTable(self):
        """加载表格文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择表格文件",
            "",
            "Excel文件 (*.xlsx *.xls);;所有文件 (*.*)"
        )
        
        if file_path:
            if self.automation_flow.load_table(file_path):
                fields = self.automation_flow.table_manager.get_fields()
                
                # 更新字段下拉选择框
                self.fieldsComboBox.clear()
                self.fieldsComboBox.addItems(fields)
                
                self.tableStatusLabel.setText(f"表格数据: 已加载 {self.automation_flow.table_manager.get_total_records()} 条记录")
                
                # 表格字段加载成功，可用于模块配置中的变量引用
                InfoBar.success(
                    title="成功",
                    content=f"表格加载成功，共 {len(fields)} 个字段，{len(self.automation_flow.table_manager.data)} 条记录",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def clearTable(self):
        """清除表格数据"""
        self.automation_flow.clear_table()
        
        # 更新界面状态
        self.fieldsComboBox.clear()
        self.fieldsComboBox.setPlaceholderText("选择字段")
        self.tableStatusLabel.setText("表格数据: 未加载")
        
        InfoBar.success(
            title="成功",
            content="表格数据已清除",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
    def addModule(self):
        """添加元素模块"""
        # 获取当前选中的行
        current_row = self.moduleTableWidget.currentRow()
        
        # 计算要添加的位置
        if current_row >= 0:
            # 如果有选中行，获取选中模块ID
            name_item = self.moduleTableWidget.item(current_row, 1)
            if name_item:
                selected_module_id = name_item.data(Qt.ItemDataRole.UserRole)
                if selected_module_id:
                    # 获取所有模块
                    modules = self.automation_flow.module_manager.get_all_modules()
                    # 查找选中模块的索引
                    for i, module in enumerate(modules):
                        if module.module_id == selected_module_id:
                            # 在选中模块的下方添加新模块
                            module = self.automation_flow.module_manager.add_module("新模块", i + 1)
                            break
                    else:
                        # 如果找不到选中模块，添加到末尾
                        module = self.automation_flow.module_manager.add_module("新模块")
                else:
                    module = self.automation_flow.module_manager.add_module("新模块")
            else:
                module = self.automation_flow.module_manager.add_module("新模块")
        else:
            # 如果没有选中行，添加到末尾
            module = self.automation_flow.module_manager.add_module("新模块")
        
        # 创建模块卡片
        card = self.ModuleCard(module)
        
        # 连接信号
        card.moduleUpdated.connect(self.onModuleUpdated)
        card.moduleDeleted.connect(self.onModuleDeleted)
        card.moduleMoved.connect(self.onModuleMoved)
        
        # 存储映射关系
        self.module_cards[module.module_id] = card
        
        # 更新当前模块ID
        self.current_module_id = module.module_id
        
        # 更新模块列表
        self.updateModuleList()
        
        # 显示新模块的配置面板
        if self.current_module_id in self.module_cards:
            # 清空当前配置内容
            self.clearConfigPanel()
            
            # 添加新模块的配置卡片
            card = self.module_cards[self.current_module_id]
            self.configContentLayout.addWidget(card)
            
            # 特别处理表格模块，确保配置页面正确更新
            card.onActionTypeChanged(card.actionTypeCombo.currentIndex())
    
    def addCondition(self):
        """添加条件模块"""
        # 获取当前选中的行
        current_row = self.moduleTableWidget.currentRow()
        
        # 计算要添加的位置
        if current_row >= 0:
            # 如果有选中行，获取选中模块ID
            name_item = self.moduleTableWidget.item(current_row, 1)
            if name_item:
                selected_module_id = name_item.data(Qt.ItemDataRole.UserRole)
                if selected_module_id:
                    # 获取所有模块
                    modules = self.automation_flow.module_manager.get_all_modules()
                    # 查找选中模块的索引
                    for i, module in enumerate(modules):
                        if module.module_id == selected_module_id:
                            # 在选中模块的下方添加新条件模块
                            module = self.automation_flow.module_manager.add_condition_module("循环条件", i + 1)
                            break
                    else:
                        # 如果找不到选中模块，添加到末尾
                        module = self.automation_flow.module_manager.add_condition_module("循环条件")
                else:
                    module = self.automation_flow.module_manager.add_condition_module("循环条件")
            else:
                module = self.automation_flow.module_manager.add_condition_module("循环条件")
        else:
            # 如果没有选中行，添加到末尾
            module = self.automation_flow.module_manager.add_condition_module("循环条件")
        
        # 创建模块卡片
        card = self.ConditionCard(module)
        
        # 连接信号
        card.moduleUpdated.connect(self.onModuleUpdated)
        card.moduleDeleted.connect(self.onModuleDeleted)
        card.moduleMoved.connect(self.onModuleMoved)
        
        # 存储映射关系
        self.module_cards[module.module_id] = card
        
        # 更新当前模块ID
        self.current_module_id = module.module_id
        
        # 更新模块列表
        self.updateModuleList()
        
        # 显示新模块的配置面板
        if self.current_module_id in self.module_cards:
            # 清空当前配置内容
            self.clearConfigPanel()
            
            # 添加新模块的配置卡片
            card = self.module_cards[self.current_module_id]
            self.configContentLayout.addWidget(card)
    
    def onModuleUpdated(self, module_id: str):
        """模块更新事件"""
        InfoBar.success(
            title="成功",
            content="模块配置保存成功",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        
        # 更新模块列表中的显示
        self.updateModuleList()
    
    def onModuleDeleted(self, module_id: str):
        """模块删除事件"""
        if self.automation_flow.module_manager.remove_module(module_id):
            # 从映射中移除卡片
            card = self.module_cards.pop(module_id, None)
            if card:
                card.deleteLater()
            
            # 更新模块列表
            self.updateModuleList()
            
            # 更新当前模块ID
            if self.current_module_id == module_id:
                self.current_module_id = None
                # 清空配置面板
                for i in reversed(range(self.configContentLayout.count())):
                    widget = self.configContentLayout.itemAt(i).widget()
                    if widget:
                        widget.deleteLater()
                self.configContentLayout.addWidget(self.configPlaceholder)
    
    def onModuleMoved(self, module_id: str, is_up: bool):
        """模块移动事件"""
        # 获取所有模块
        modules = self.automation_flow.module_manager.get_all_modules()
        
        # 查找当前模块的索引
        current_index = -1
        for i, module in enumerate(modules):
            if module.module_id == module_id:
                current_index = i
                break
        
        if current_index == -1:
            return
        
        # 计算目标索引
        target_index = current_index - 1 if is_up else current_index + 1
        
        # 检查边界
        if target_index < 0 or target_index >= len(modules):
            return
        
        # 重新排序模块
        new_module_order = [module.module_id for module in modules]
        # 交换位置
        new_module_order[current_index], new_module_order[target_index] = new_module_order[target_index], new_module_order[current_index]
        
        # 更新模块管理器中的顺序
        self.automation_flow.module_manager.reorder_modules(new_module_order)
        
        # 更新模块列表
        self.updateModuleList()
    
    def clearModuleCards(self):
        """清空所有模块卡片"""
        # 清除所有卡片
        for card in self.module_cards.values():
            card.deleteLater()
        
        # 清空映射字典
        self.module_cards.clear()
        self.current_module_id = None
        
        # 更新模块列表
        self.updateModuleList()
        
        # 清空配置面板
        self.clearConfigPanel()
        self.configContentLayout.addWidget(self.configPlaceholder)
    
    def reorderModules(self):
        """重新排序元素模块 - 已不再需要，保留用于向后兼容"""
        pass
    

    
    def saveConfig(self):
        """保存配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存配置",
            "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            if self.automation_flow.module_manager.save_config(file_path):
                InfoBar.success(
                    title="成功",
                    content="配置保存成功",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="错误",
                    content="配置保存失败",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
    
    def loadConfig(self):
        """加载配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "加载配置",
            "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            if self.automation_flow.module_manager.load_config(file_path):
                # 清空现有模块卡片
                self.clearModuleCards()
                
                # 重新加载模块卡片
                for module in self.automation_flow.module_manager.get_all_modules():
                    # 根据模块类型创建不同的卡片
                    if hasattr(module, 'condition_type'):
                        # 条件模块
                        card = self.ConditionCard(module)
                    else:
                        # 普通模块
                        card = self.ModuleCard(module)
                    
                    # 连接信号
                    card.moduleUpdated.connect(self.onModuleUpdated)
                    card.moduleDeleted.connect(self.onModuleDeleted)
                    card.moduleMoved.connect(self.onModuleMoved)
                    
                    # 存储映射关系
                    self.module_cards[module.module_id] = card
                
                # 更新模块列表
                self.updateModuleList()
                
                InfoBar.success(
                    title="成功",
                    content="配置加载成功",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="错误",
                    content="配置加载失败",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
    
    def clearModuleCards(self):
        """清空所有模块卡片"""
        # 清除所有卡片
        for card in self.module_cards.values():
            card.deleteLater()
        
        # 清空映射字典
        self.module_cards.clear()
        self.current_module_id = None
        
        # 更新模块列表
        self.updateModuleList()
        
        # 清空配置面板
        self.clearConfigPanel()
        self.configContentLayout.addWidget(self.configPlaceholder)
    
    def startAutomation(self):
        """开始自动化"""
        if not self.automation_flow.browser.is_connected:
            w = MessageBox(
                "警告",
                "浏览器未连接，无法开始自动化流程",
                self
            )
            w.exec()
            return
        
        if not self.automation_flow.table_manager.data:
            w = MessageBox(
                "警告",
                "未加载表格数据，无法开始自动化流程",
                self
            )
            w.exec()
            return
        
        if not self.automation_flow.module_manager.modules:
            w = MessageBox(
                "警告",
                "未添加元素模块，无法开始自动化流程",
                self
            )
            w.exec()
            return
        
        # 更新按钮状态
        self.startBtn.setEnabled(False)
        self.pauseBtn.setEnabled(True)
        self.stopBtn.setEnabled(True)
        self.is_running = True
        self.automationStatusLabel.setText("自动化: 运行中")
        
        # 显示进度条
        self.progressBar.setVisible(True)
        
        # 开始自动化
        self.automation_flow.start_automation()
        
        # 启动状态检查定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.checkAutomationStatus)
        self.status_timer.start(1000)
    
    def pauseAutomation(self):
        """暂停自动化"""
        self.automation_flow.pause_automation()
        if self.automation_flow.is_paused:
            self.automationStatusLabel.setText("自动化: 已暂停")
        else:
            self.automationStatusLabel.setText("自动化: 运行中")
    
    def stopAutomation(self):
        """停止自动化"""
        self.automation_flow.stop_automation()
        self.is_running = False
        
        # 更新按钮状态
        self.startBtn.setEnabled(True)
        self.pauseBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)
        self.automationStatusLabel.setText("自动化: 已停止")
        
        # 隐藏进度条
        self.progressBar.setVisible(False)
        
        # 停止状态检查定时器
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
    
    def checkAutomationStatus(self):
        """检查自动化状态"""
        if not self.automation_flow.is_running and self.is_running:
            self.is_running = False
            self.startBtn.setEnabled(True)
            self.pauseBtn.setEnabled(False)
            self.stopBtn.setEnabled(False)
            self.automationStatusLabel.setText("自动化: 已完成")
            self.progressBar.setVisible(False)
            
            # 停止定时器
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            
            InfoBar.success(
                title="成功",
                content="自动化流程已完成",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
