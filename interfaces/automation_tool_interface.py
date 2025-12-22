# coding:utf-8
"""
自动化工具界面
"""

import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSplitter,
                             QListWidget, QListWidgetItem, QFileDialog, QGroupBox, QFormLayout,
                             QCheckBox, QDoubleSpinBox, QFrame, QScrollArea, QMessageBox, QTabWidget,
                             QDialog, QAbstractItemView, QLayout)  # 添加QLayout导入
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
            xpathLayout = QHBoxLayout()
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
            
            layout.addLayout(xpathLayout)
            
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
            self.actionTypeCombo.addItems(["输入文本", "点击", "选择下拉选项", "上传文件", "获取文本", "清除内容", "获取表格字段"])
            self.actionTypeCombo.setCurrentText(self.module.action_type)
            self.actionTypeCombo.currentIndexChanged.connect(self.onActionTypeChanged)
            self.actionTypeCombo.setFixedHeight(28)  # 调整高度
            self.actionTypeCombo.setMinimumWidth(140)  # 调整最小宽度
            actionTypeLayout.addWidget(self.actionTypeCombo, 1)  # 增加拉伸因子
            
            # 使用变量开关 - 根据操作类型动态显示
            self.variableSwitch = SwitchButton("使用变量")
            self.variableSwitch.setObjectName("variableSwitch")
            self.variableSwitch.setChecked(self.module.is_variable)
            # SwitchButton使用checkedChanged信号，不是toggled信号
            self.variableSwitch.checkedChanged.connect(self.onVariableSwitchChanged)
            actionTypeLayout.addWidget(self.variableSwitch, 0, Qt.AlignmentFlag.AlignVCenter)
            
            layout.addLayout(actionTypeLayout)
            
            # 第4行：操作值、循环按钮
            self.actionValueContainer = QWidget()
            actionValueLayout = QHBoxLayout(self.actionValueContainer)
            actionValueLayout.setContentsMargins(0, 0, 0, 0)
            actionValueLayout.setSpacing(6)  # 减小间距
            
            self.actionValueLabel = QLabel("操作值:")
            self.actionValueLabel.setFixedWidth(60)  # 调整标签宽度
            self.actionValueLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            actionValueLayout.addWidget(self.actionValueLabel)
            
            self.actionValueEdit = LineEdit()
            self.actionValueEdit.setObjectName("actionValueEdit")
            self.actionValueEdit.setText(self.module.action_value)
            self.actionValueEdit.setPlaceholderText("操作值")
            self.actionValueEdit.setFixedHeight(28)  # 调整高度
            actionValueLayout.addWidget(self.actionValueEdit, 1)  # 增加拉伸因子
            
            # 为获取文本操作类型添加循环按钮
            self.loopBtn = PushButton(FIF.SYNC, "循环")
            self.loopBtn.setObjectName("loopBtn")
            self.loopBtn.setFixedHeight(28)  # 调整高度
            self.loopBtn.setFixedWidth(70)  # 调整宽度
            self.loopBtn.clicked.connect(self.onLoopBtnClicked)
            actionValueLayout.addWidget(self.loopBtn)
            
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
            
            # 初始状态处理
            self.onActionTypeChanged(self.actionTypeCombo.currentIndex())
        
        def onActionTypeChanged(self, index):
            """操作类型变化事件"""
            action_type = self.actionTypeCombo.currentText()
            
            # 确定哪些操作类型需要操作值和使用变量开关
            # 获取文本也需要操作值和使用变量开关，用于比对文本是否正确
            need_action_value = action_type in ["输入文本", "选择下拉选项", "上传文件", "获取表格字段", "获取文本"]
            
            # 显示或隐藏操作值相关容器
            self.actionValueContainer.setVisible(need_action_value)
            self.variableSwitch.setVisible(need_action_value)
            
            # 确定哪些操作类型需要变量名称
            # 获取文本不再需要变量名称，改为使用操作值进行比对
            need_variable_name = action_type in ["获取表格字段"]
            
            # 显示或隐藏变量名称相关容器
            self.variableContainer.setVisible(need_variable_name)
            
            # 显示或隐藏循环功能控件
            # 只有获取文本操作类型需要循环功能
            if hasattr(self, 'loopBtn'):
                self.loopBtn.setVisible(action_type == "获取文本")
        
        def onVariableSwitchChanged(self, checked):
            """使用变量开关变化事件"""
            # 当使用变量时，可以在操作值中显示表格字段下拉选择
            # 这里可以添加表格字段选择的逻辑
            pass
        
        def onLoopBtnClicked(self):
            """循环按钮点击事件 - 打开模块列表选择对话框"""
            # 创建对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("选择循环起始模块")
            dialog.setFixedSize(400, 300)
            
            # 应用主题样式，确保在深色主题下显示正确
            from qfluentwidgets import isDarkTheme
            if isDarkTheme():
                dialog.setStyleSheet("""
                    QDialog {
                        background-color: #2E2E2E;
                        color: #FFFFFF;
                    }
                    QListWidget {
                        background-color: #3E3E3E;
                        color: #FFFFFF;
                        border: 1px solid #555555;
                        border-radius: 4px;
                    }
                    QListWidget::item {
                        background-color: transparent;
                    }
                    QListWidget::item:selected {
                        background-color: #0078D4;
                        color: #FFFFFF;
                    }
                """)
            else:
                dialog.setStyleSheet("""
                    QDialog {
                        background-color: #FFFFFF;
                        color: #000000;
                    }
                    QListWidget {
                        background-color: #F5F5F5;
                        color: #000000;
                        border: 1px solid #DDDDDD;
                        border-radius: 4px;
                    }
                """)
            
            # 对话框布局
            layout = QVBoxLayout(dialog)
            
            # 添加说明文字
            description_label = QLabel("选择循环起始模块，将形成从该模块到当前模块的循环链，直到当前模块判定通过。")
            description_label.setWordWrap(True)
            description_label.setStyleSheet("margin-bottom: 10px; font-size: 12px;")
            layout.addWidget(description_label)
            
            # 模块列表
            list_widget = QListWidget()
            list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # 改为单选模式
            
            # 获取所有模块
            # 正确获取AutomationToolInterface实例
            parent = None
            current_widget = self.parent()
            # 向上查找直到找到AutomationToolInterface实例
            while current_widget and not hasattr(current_widget, 'module_cards'):
                current_widget = current_widget.parent()
            parent = current_widget
            
            if parent and hasattr(parent, 'module_cards'):
                for module_id, card in parent.module_cards.items():
                    if module_id != self.module_id:  # 排除当前模块
                        item = QListWidgetItem(card.nameEdit.text())
                        item.setData(Qt.ItemDataRole.UserRole, module_id)
                        list_widget.addItem(item)
            
            layout.addWidget(list_widget)
            
            # 按钮布局
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            # 确定按钮
            ok_btn = PushButton(FIF.ACCEPT, "确定")
            # 初始状态下禁用确定按钮，因为还没有选择模块
            ok_btn.setEnabled(False)
            ok_btn.clicked.connect(lambda: self.onLoopModulesSelected(dialog, list_widget))
            button_layout.addWidget(ok_btn)
            
            # 取消按钮
            cancel_btn = PushButton(FIF.CLOSE, "取消")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            # 连接列表控件的选择变化信号，动态启用/禁用确定按钮
            def onSelectionChanged():
                selected_items = list_widget.selectedItems()
                ok_btn.setEnabled(len(selected_items) > 0)
            
            list_widget.itemSelectionChanged.connect(onSelectionChanged)
            
            layout.addLayout(button_layout)
            
            # 显示对话框
            dialog.exec()
        
        def _updateLoopButtonText(self):
            """更新循环按钮文字，显示循环状态"""
            # 检查模块是否有loop_start_module属性
            if hasattr(self.module, 'loop_start_module') and self.module.loop_start_module:
                # 显示循环起始模块名称
                parent = self.parent()
                while parent and not hasattr(parent, 'module_cards'):
                    parent = parent.parent()
                if parent and hasattr(parent, 'module_cards'):
                    if self.module.loop_start_module in parent.module_cards:
                        start_module_name = parent.module_cards[self.module.loop_start_module].nameEdit.text()
                        self.loopBtn.setText(f"循环({start_module_name}...)")
                    else:
                        self.loopBtn.setText("循环")
                else:
                    self.loopBtn.setText("循环")
            else:
                self.loopBtn.setText("循环")
        
        def onLoopModulesSelected(self, dialog, list_widget):
            """循环模块选择确认"""
            # 获取选中的模块 - 现在是单选
            selected_module = None
            selected_items = list_widget.selectedItems()
            if selected_items:
                selected_module = selected_items[0].data(Qt.ItemDataRole.UserRole)
            
            # 保存选中的模块到当前模块配置
            if hasattr(self.module, 'loop_start_module'):
                self.module.loop_start_module = selected_module
            else:
                self.module.loop_start_module = selected_module
            
            # 为起始模块和当前模块添加循环图标
            parent = self.parent()
            while parent and not hasattr(parent, 'module_cards'):
                parent = parent.parent()
            
            # 统一导入ToolButton，避免未定义错误
            from qfluentwidgets import ToolButton
            
            if parent and hasattr(parent, 'module_cards'):
                # 先清除所有模块的循环图标
                for card in parent.module_cards.values():
                    if hasattr(card, 'loopIcon'):
                        try:
                            card.loopIcon.deleteLater()
                            delattr(card, 'loopIcon')
                        except RuntimeError:
                            # 忽略已被删除的对象错误
                            delattr(card, 'loopIcon')
                
                # 为起始模块添加循环图标
                if selected_module and selected_module in parent.module_cards:
                    start_card = parent.module_cards[selected_module]
                    # 添加循环图标到起始模块卡片 - 使用ToolButton简化图标显示
                    start_card.loopIcon = ToolButton(FIF.SYNC, self)
                    start_card.loopIcon.setToolTip("循环起始模块")
                    start_card.loopIcon.setFixedSize(20, 20)
                    start_card.loopIcon.setStyleSheet("border: none; background: transparent;")
                    # 将图标添加到起始模块卡片布局中
                    if hasattr(start_card, 'nameEdit'):
                        start_name_parent = start_card.nameEdit.parent()
                        if start_name_parent and isinstance(start_name_parent, QLayout):
                            start_name_parent.addWidget(start_card.loopIcon)
                
                # 为当前模块添加循环图标
                current_card = parent.module_cards[self.module_id]
                current_card.loopIcon = ToolButton(FIF.SYNC, self)
                current_card.loopIcon.setToolTip("循环结束模块")
                current_card.loopIcon.setFixedSize(20, 20)
                current_card.loopIcon.setStyleSheet("border: none; background: transparent;")
                # 将图标添加到当前模块卡片布局中
                if hasattr(current_card, 'nameEdit'):
                    current_name_parent = current_card.nameEdit.parent()
                    if current_name_parent and isinstance(current_name_parent, QLayout):
                        current_name_parent.addWidget(current_card.loopIcon)
            
            # 更新循环按钮文字，显示循环状态
            self._updateLoopButtonText()
            
            dialog.accept()
        
        def saveModule(self):
            """保存模块配置"""
            # 更新模块属性
            self.module.name = self.nameEdit.text() or "新模块"
            self.module.set_xpath(self.xpathEdit.text())
            self.module.set_action(
                self.actionTypeCombo.currentText(),
                self.actionValueEdit.text(),
                self.variableSwitch.isChecked(),
                self.variableNameEdit.text()
            )
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
            
            # 触发操作类型变化事件，确保控件可见性正确
            self.onActionTypeChanged(self.actionTypeCombo.currentIndex())
            
            # 更新循环按钮文字，显示选择的模块数量
            self._updateLoopButtonText()
    
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
        """创建中间模块列表面板 - 以列表形式显示模块名"""
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
        
        # 模块列表 - 使用QListWidget显示模块名
        self.moduleListWidget = QListWidget()
        self.moduleListWidget.setObjectName("moduleListWidget")
        self.moduleListWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.moduleListWidget.itemClicked.connect(self.onModuleListItemClicked)
        
        layout.addWidget(self.moduleListWidget)
        
        # 模块控制按钮 - 添加模块、上移、下移、删除
        moduleControlLayout = QHBoxLayout()
        moduleControlLayout.setContentsMargins(0, 0, 0, 0)
        moduleControlLayout.setSpacing(10)
        
        self.addModuleBtn = PrimaryPushButton(FIF.ADD, "添加模块")
        self.addModuleBtn.clicked.connect(self.addModule)
        moduleControlLayout.addWidget(self.addModuleBtn)
        
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
    
    def onModuleListItemClicked(self, item):
        """模块列表项点击事件 - 显示选中模块的配置"""
        module_id = item.data(Qt.ItemDataRole.UserRole)
        if module_id and module_id in self.module_cards:
            # 清空当前配置内容
            self.clearConfigPanel()
            
            # 添加选中模块的配置卡片
            card = self.module_cards[module_id]
            self.configContentLayout.addWidget(card)
            
            # 特别处理表格模块，确保配置页面正确更新
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
        current_item = self.moduleListWidget.currentItem()
        if current_item:
            module_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.onModuleMoved(module_id, True)
    
    def onMoveDownBtnClicked(self):
        """下移按钮点击事件"""
        current_item = self.moduleListWidget.currentItem()
        if current_item:
            module_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.onModuleMoved(module_id, False)
    
    def onDeleteModuleBtnClicked(self):
        """删除按钮点击事件"""
        current_item = self.moduleListWidget.currentItem()
        if current_item:
            module_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.onModuleDeleted(module_id)
        
    def updateModuleList(self):
        """更新模块列表"""
        # 清空列表
        self.moduleListWidget.clear()
        
        # 从模块管理器获取最新的模块列表（带正确顺序）
        modules = self.automation_flow.module_manager.get_all_modules()
        
        # 添加所有模块
        for module in modules:
            if module.module_id in self.module_cards:
                card = self.module_cards[module.module_id]
                item = QListWidgetItem(card.nameEdit.text())
                item.setData(Qt.ItemDataRole.UserRole, module.module_id)
                self.moduleListWidget.addItem(item)
    
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
                    border: 1px solid #0078d4;
                    background-color: #3a3a3a;
                    outline: none;
                    box-shadow: 0 0 0 2px rgba(0, 120, 212, 0.2);
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
                    selection-background-color: #0078d4;
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
                    selection-background-color: #0078d4;
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
                    background-color: #0078d4;
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
                    border: 1px solid #0078d4;
                    outline: none;
                    box-shadow: 0 0 0 2px rgba(0, 120, 212, 0.2);
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
                    selection-background-color: #0078d4;
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
                    selection-background-color: #0078d4;
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
                    background-color: #0078d4;
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
        if hasattr(self, 'moduleListWidget') and self.moduleListWidget:
            # 列表控件样式已在全局样式表中定义，这里不再重复设置
            pass
    
    def connectBrowser(self):
        """连接浏览器"""
        if self.automation_flow.connect_browser():
            self.connectBrowserBtn.setEnabled(False)
            self.disconnectBrowserBtn.setEnabled(True)
            self.browserStatusLabel.setText("浏览器: 已连接")
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
        InfoBar.success(
            title="成功",
            content="浏览器已断开连接",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
    
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
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="错误",
                    content="表格加载失败",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
    
    def addModule(self):
        """添加元素模块"""
        module = self.automation_flow.module_manager.add_module("新模块")
        
        # 创建模块卡片
        card = self.ModuleCard(module)
        
        # 连接信号
        card.moduleUpdated.connect(self.onModuleUpdated)
        card.moduleDeleted.connect(self.onModuleDeleted)
        card.moduleMoved.connect(self.onModuleMoved)
        
        # 存储映射关系
        self.module_cards[module.module_id] = card
        
        # 更新模块列表
        self.updateModuleList()
        
        # 更新当前模块ID
        self.current_module_id = module.module_id
    
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
                    # 创建模块卡片
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
