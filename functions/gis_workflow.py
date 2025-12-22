# coding:utf-8
"""
GIS工作流功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QWidget, QSplitter, QListWidget, QPushButton, QFrame
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from qfluentwidgets import LineEdit, ComboBox, PushButton, TextEdit, CardWidget, FlowLayout
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction


class ModuleCard(CardWidget):
    """模块卡片"""
    
    def __init__(self, module_id: str, title: str, category: str, parent=None):
        super().__init__(parent)
        self.module_id = module_id
        self.title = title
        self.category = category
        self.setFixedSize(140, 65)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # 标题
        titleLabel = QLabel(title)
        titleLabel.setStyleSheet("font-weight: bold; font-size: 12px;")
        titleLabel.setWordWrap(True)
        
        # 分类
        categoryLabel = QLabel(category)
        categoryLabel.setStyleSheet("font-size: 10px; color: gray;")
        
        layout.addWidget(titleLabel)
        layout.addWidget(categoryLabel)


class ModulePropertyPanel(QWidget):
    """模块属性面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.module_id = None
        self.setupUI()
    
    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        self.titleLabel = QLabel("模块属性")
        self.titleLabel.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.titleLabel)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # 属性内容区域
        self.propertyContent = TextEdit()
        self.propertyContent.setPlaceholderText("双击模块以查看和编辑属性...")
        layout.addWidget(self.propertyContent)
        
        # 操作按钮
        buttonLayout = QHBoxLayout()
        self.saveBtn = PushButton("保存", self, FIF.SAVE)
        self.cancelBtn = PushButton("取消", self, FIF.CANCEL)
        buttonLayout.addWidget(self.saveBtn)
        buttonLayout.addWidget(self.cancelBtn)
        layout.addLayout(buttonLayout)
    
    def setModule(self, module_id: str, title: str):
        """设置当前编辑的模块"""
        self.module_id = module_id
        self.titleLabel.setText(f"{title} 属性")
        self.propertyContent.setText(f"模块ID: {module_id}\n模块名称: {title}\n\n在这里可以配置模块的详细参数...")


class CanvasWidget(QWidget):
    """工作流画布"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.modules = []  # 存储已添加的模块
        self.setupUI()


class WorkflowThread(QThread):
    """工作流执行线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, canvas_widget, workflow_data, parent=None):
        """
        Args:
            canvas_widget: 画布组件
            workflow_data: 工作流数据
        """
        super().__init__(parent)
        self.canvas_widget = canvas_widget
        self.workflow_data = workflow_data
    
    def run(self):
        """线程运行方法"""
        try:
            # 直接在当前环境中执行工作流
            # 导入并使用gis_workflow_interface中的WorkflowCanvas类
            from interfaces.gis_workflow_interface import WorkflowCanvas
            
            # 创建一个临时的WorkflowCanvas实例来执行工作流
            temp_canvas = WorkflowCanvas()
            # 从JSON加载工作流
            temp_canvas.fromJson(self.workflow_data)
            # 执行工作流
            temp_canvas.executeWorkflowWithProgress()
            
            result_msg = f"工作流执行完成！\n共处理 {len(self.canvas_widget.modules)} 个模块"
            self.success.emit(result_msg)
        except Exception as e:
            import traceback
            error_msg = f"工作流执行失败: {str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_msg)
    
    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 画布区域
        self.canvasArea = QWidget()
        self.canvasArea.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        canvasLayout = QVBoxLayout(self.canvasArea)
        canvasLayout.setContentsMargins(20, 20, 20, 20)
        
        # 提示文本
        hintLabel = QLabel("将模块从左侧拖拽到此处进行工作流设计\n双击模块可编辑属性")
        hintLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hintLabel.setStyleSheet("color: #888; font-style: italic;")
        canvasLayout.addWidget(hintLabel)
        
        layout.addWidget(self.canvasArea)
    
    def addModule(self, module_id: str, title: str):
        """添加模块到画布"""
        self.modules.append({"id": module_id, "title": title})
        # 这里可以实现实际的模块显示逻辑


class GisWorkflowFunction(BaseFunction):
    """GIS工作流功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "1. 类似于FME的拖拽式GIS数据处理工作流<br>"
            "2. 从左侧模块栏拖拽模块到操作台进行流程设计<br>"
            "3. 双击模块可打开属性面板进行参数配置<br>"
            "4. 支持添加数据、分析功能、数据处理和导出数据等操作"
        )
        super().__init__("GIS工作流", description, parent)
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮
        self.addExecuteButton("运行工作流", self.execute)
        self.addCustomButton("清空画布", FIF.DELETE, self._clearCanvas)
    
    def _initUI(self):
        """初始化界面"""
        # 创建主分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        
        # 左侧模块栏
        modulePanel = self._createModulePanel()
        splitter.addWidget(modulePanel)
        
        # 中间画布区域
        self.canvasWidget = CanvasWidget()
        splitter.addWidget(self.canvasWidget)
        
        # 右侧属性面板
        self.propertyPanel = ModulePropertyPanel()
        splitter.addWidget(self.propertyPanel)
        
        # 设置初始大小
        splitter.setSizes([200, 600, 250])
        
        self.contentLayout.addWidget(splitter)
    
    def _createModulePanel(self):
        """创建模块面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        titleLabel = QLabel("模块库")
        titleLabel.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(titleLabel)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # 模块分类
        categories = {
            "添加数据": [
                ("add_file", "添加文件")
            ],
            "分析功能": [
                ("intersect", "相交"),
                ("erase", "擦除"),
                ("identity", "标识")
            ],
            "数据处理": [
                ("dissolve", "融合"),
                ("merge", "合并")
            ],
            "导出数据": [
                ("export_data", "导出数据")
            ]
        }
        
        # 创建模块卡片容器
        moduleContainer = QWidget()
        moduleLayout = FlowLayout(moduleContainer, needAni=True)
        moduleLayout.setContentsMargins(0, 0, 0, 0)
        moduleLayout.setHorizontalSpacing(10)
        moduleLayout.setVerticalSpacing(10)
        
        # 添加模块卡片
        for category, modules in categories.items():
            for module_id, title in modules:
                card = ModuleCard(module_id, title, category)
                # 连接点击事件（这里简化为点击添加到画布）
                # 使用默认参数修复lambda表达式错误
                card.clicked.connect(lambda checked=False, mid=module_id, t=title: self._addModuleToCanvas(mid, t))
                moduleLayout.addWidget(card)
        
        # 添加滚动区域
        from qfluentwidgets import ScrollArea
        scrollArea = ScrollArea()
        scrollArea.setWidget(moduleContainer)
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        layout.addWidget(scrollArea)
        return panel
    
    def _addModuleToCanvas(self, module_id: str, title: str):
        """添加模块到画布"""
        self.canvasWidget.addModule(module_id, title)
        self.showSuccess(f"已添加模块: {title}")
    
    def _clearCanvas(self):
        """清空画布"""
        self.canvasWidget.modules.clear()
        self.showSuccess("画布已清空")
    
    def validate(self) -> tuple[bool, str]:
        """
        验证工作流
        返回: (是否有效, 错误消息)
        """
        if not self.canvasWidget.modules:
            return False, "请至少添加一个模块到工作流中"
        
        # 所有验证通过
        return True, ""
    
    def execute(self):
        """执行工作流"""
        # 1. 验证工作流
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        # 2. 显示进度
        self.showProgress("正在执行GIS工作流...")
        
        # 3. 在线程中执行处理
        def run_workflow():
            try:
                # 导入必要的模块
                import sys
                import os
                
                # 确保可以导入gis_workflow_interface模块
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
                # 获取画布中的工作流数据
                workflow_data = self.canvasWidget.toJson()
                
                # 直接在当前环境中执行工作流（通过调用gis_workflow_interface中的方法）
                # 导入并使用gis_workflow_interface中的WorkflowCanvas类
                from gis_workflow_interface import WorkflowCanvas
                
                # 创建一个临时的WorkflowCanvas实例来执行工作流
                temp_canvas = WorkflowCanvas()
                # 从JSON加载工作流
                temp_canvas.fromJson(workflow_data)
                # 执行工作流
                temp_canvas.executeWorkflowWithProgress()
                
                result_msg = f"工作流执行完成！\n共处理 {len(self.canvasWidget.modules)} 个模块"
                self.showSuccess(result_msg)
                
            except Exception as e:
                # 捕获并显示错误
                import traceback
                error_msg = f"工作流执行失败: {str(e)}\n\n{traceback.format_exc()}"
                self.showError(error_msg)
        
        # 创建并启动工作流线程
        self.workflow_thread = WorkflowThread(
            canvas_widget=self.canvasWidget,
            workflow_data=workflow_data,
            parent=self
        )
        
        # 连接信号
        self.workflow_thread.success.connect(self._onWorkflowSuccess)
        self.workflow_thread.error.connect(self._onWorkflowError)
        
        # 启动线程
        self.workflow_thread.start()
    
    def _onWorkflowSuccess(self, message: str):
        """工作流执行成功处理"""
        self.showSuccess(message)
    
    def _onWorkflowError(self, message: str):
        """工作流执行错误处理"""
        self.showError(message)