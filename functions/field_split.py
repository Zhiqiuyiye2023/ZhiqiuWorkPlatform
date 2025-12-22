# coding:utf-8
"""
根据矢量字段分离要素功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import QThread, pyqtSignal
from qfluentwidgets import LineEdit, ComboBox, PushButton
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd


class SplitThread(QThread):
    """字段分离线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, file_path, field_name, parent=None):
        """
        Args:
            file_path: 矢量文件路径
            field_name: 用于分离的字段名
        """
        super().__init__(parent)
        self.file_path = file_path
        self.field_name = field_name
    
    def run(self):
        """线程运行方法"""
        try:
            from .矢量操作 import 根据矢量字段分离要素
            根据矢量字段分离要素(self.file_path, self.field_name)
            self.success.emit(f"分离完成！\n文件已保存到源文件目录")
        except Exception as e:
            import traceback
            self.error.emit(f"分离失败: {str(e)}\n\n{traceback.format_exc()}")


class FieldSplitFunction(BaseFunction):
    """根据矢量字段分离要素功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "1. 根据指定字段的值将矢量数据分离成多个文件<br>"
            "2. 选择矢量文件<br>"
            "3. 选择用于分离的字段<br>"
            "4. 在源文件目录下生成以字段值命名的多个SHP文件"
        )
        super().__init__("根据矢量字段分离要素", description, parent)
        
        self._initUI()
        self.addExecuteButton("开始分离", self.execute)
    
    def _initUI(self):
        """初始化界面"""
        row = QHBoxLayout()
        row.addWidget(QLabel("矢量文件："))
        
        self.vectorBtn = PushButton("选择文件", self, FIF.DOCUMENT)
        self.vectorBtn.clicked.connect(self._selectVector)
        self.vectorBtn.setFixedWidth(120)  # 增加宽度以完整显示文字
        
        self.vectorPath = LineEdit(self)
        self.vectorPath.setPlaceholderText("点击按钮选择矢量文件")
        self.vectorPath.setReadOnly(True)
        
        self.fieldCombo = ComboBox(self)
        self.fieldCombo.setPlaceholderText("选择分离字段")
        self.fieldCombo.setFixedWidth(150)
        
        row.addWidget(self.vectorBtn)
        row.addWidget(self.vectorPath, 1)
        row.addWidget(self.fieldCombo)
        self.contentLayout.addLayout(row)
    
    def _selectVector(self):
        """选择矢量文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择矢量文件", "", "SHP文件 (*.shp)"
        )
        if file_path:
            self.vectorPath.setText(file_path)
            self._loadFields(file_path)
    
    def _loadFields(self, file_path):
        """加载字段列表"""
        try:
            gdf = gpd.read_file(file_path)
            fields = [col for col in gdf.columns if col != 'geometry']
            
            # 检查UI元素是否仍然存在
            if hasattr(self, 'fieldCombo') and self.fieldCombo is not None:
                self.fieldCombo.clear()
                self.fieldCombo.addItems(fields)
        except RuntimeError:
            # 捕获UI元素已被删除的错误
            pass
        except Exception as e:
            try:
                # 检查showError方法是否仍然可用
                if hasattr(self, 'showError'):
                    self.showError(f"读取字段失败: {str(e)}")
            except RuntimeError:
                # 捕获UI元素已被删除的错误
                pass
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.vectorPath.text():
            return False, "请选择矢量文件"
        if not self.fieldCombo.currentText():
            return False, "请选择分离字段"
        return True, ""
    
    def execute(self):
        """执行分离"""
        try:
            valid, message = self.validate()
            if not valid:
                if hasattr(self, 'showError'):
                    self.showError(message)
                return
            
            if hasattr(self, 'showProgress'):
                self.showProgress("正在分离要素...")
            
            # 创建并启动分离线程
            self.split_thread = SplitThread(
                file_path=self.vectorPath.text(),
                field_name=self.fieldCombo.currentText(),
                parent=self
            )
            
            # 连接信号
            self.split_thread.success.connect(self._onSplitSuccess)
            self.split_thread.error.connect(self._onSplitError)
            self.split_thread.finished.connect(self._onSplitFinished)
            
            # 启动线程
            self.split_thread.start()
        except RuntimeError:
            # 捕获UI元素已被删除的错误
            pass
    
    def _onSplitSuccess(self, message: str):
        """分离成功处理"""
        if hasattr(self, 'showSuccess'):
            self.showSuccess(message)
    
    def _onSplitError(self, message: str):
        """分离错误处理"""
        if hasattr(self, 'showError'):
            self.showError(message)
    
    def _onSplitFinished(self):
        """分离线程结束处理"""
        if hasattr(self, 'hideProgress'):
            self.hideProgress()
