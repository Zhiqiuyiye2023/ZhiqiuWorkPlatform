# coding:utf-8
"""
获取矢量要素中心点功能
"""

import sys
import os

# 添加根目录到path，以便导入数据处理方法模块
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QFileDialog, QMessageBox
from qfluentwidgets import ComboBox, PrimaryPushButton, TextEdit, TransparentPushButton
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd


class CenterPointThread(QThread):
    """中心点计算线程类，用于在后台执行中心点计算任务"""
    success = pyqtSignal(str)  # 成功信号，传递中心点结果文本
    error = pyqtSignal(str)     # 错误信号
    
    def __init__(self, file_path, field_name):
        super().__init__()
        self.file_path = file_path
        self.field_name = field_name
    
    def run(self):
        """执行中心点计算任务"""
        try:
            # 导入矢量操作模块
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from .矢量操作 import 获取矢量要素中心点
            
            # 直接调用矢量操作模块中的函数
            result_text = 获取矢量要素中心点(self.file_path, self.field_name)
            
            # 发送成功信号
            self.success.emit(result_text)
            
        except Exception as e:
            import traceback
            error_msg = f'获取中心点失败: {str(e)}\n\n{traceback.format_exc()}'
            # 发送错误信号
            self.error.emit(error_msg)


class CenterPointFunction(BaseFunction):
    """获取矢量要素中心点功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "获取矢量要素的中心点坐标<br>"
            "完整功能已实现"
        )
        super().__init__("获取矢量要素中心点", description, parent)
        
        self._running = False
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 第一行：提示标签
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>功能说明：</span>"
            "<br>1. 选择矢量文件后，可选择命名字段"
            "<br>2. 若未选择字段，将自动使用流水号命名"
            "<br>3. 中心点坐标信息将直接显示在下方"
        )
        infoLabel.setWordWrap(True)
        self.contentLayout.addWidget(infoLabel)
        
        # 第二行：按钮和控件布局
        buttonLayout = QHBoxLayout()
        
        self.buttonAX = PrimaryPushButton(self.tr('获取中心点'), self, FIF.SEND)
        self.buttonAX.clicked.connect(self.execute)
        buttonLayout.addWidget(self.buttonAX)
        
        self.AddVectorButton = TransparentPushButton(self.tr('添加矢量'), self, FIF.DOCUMENT)
        self.AddVectorButton.clicked.connect(self._selectVectorFile)
        buttonLayout.addWidget(self.AddVectorButton)
        
        self.AddShpVectorFieldDisplay = ComboBox(self)
        self.AddShpVectorFieldDisplay.setPlaceholderText("添加矢量后选择字段")
        self.AddShpVectorFieldDisplay.setCurrentIndex(-1)
        buttonLayout.addWidget(self.AddShpVectorFieldDisplay)
        
        self.FilePathLabel = QLabel("")
        buttonLayout.addWidget(self.FilePathLabel)
        
        self.contentLayout.addLayout(buttonLayout)
        
        # 第三行：文本显示区域
        self.centerPointText = TextEdit(self)
        self.centerPointText.setReadOnly(True)
        self.centerPointText.setPlaceholderText("中心点坐标信息将显示在这里...")
        self.centerPointText.setFixedHeight(200)
        self.centerPointText.setFixedWidth(1070)
        self.contentLayout.addWidget(self.centerPointText)
    
    def _selectVectorFile(self):
        """选择矢量文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择矢量文件", "", "矢量文件 (*.shp)")
        if file_path:
            self.FilePathLabel.setText(file_path)
            try:
                # 尝试读取矢量文件并获取字段列表
                try:
                    gdf = gpd.read_file(file_path)
                except Exception as shx_error:
                    # 检查是否为缺少.shx文件的错误
                    if "SHAPE_RESTORE_SHX" in str(shx_error):
                        # 设置环境变量以恢复或创建.shx文件
                        os.environ['SHAPE_RESTORE_SHX'] = 'YES'
                        # 重新尝试读取文件
                        gdf = gpd.read_file(file_path)
                    else:
                        # 其他错误，重新抛出
                        raise
                
                # 获取字段列表
                fields = gdf.columns.tolist()
                if 'geometry' in fields:
                    fields.remove('geometry')
                
                # 更新字段下拉框
                self.AddShpVectorFieldDisplay.clear()
                self.AddShpVectorFieldDisplay.addItems(fields)
                self.AddShpVectorFieldDisplay.setCurrentIndex(-1)
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'读取矢量文件字段失败: {str(e)}')
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.FilePathLabel.text():
            return False, "请选择矢量文件"
        return True, ""
    
    def execute(self):
        """执行获取中心点"""
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        if self._running:
            return
        
        self._running = True
        
        # 获取参数
        file_path = self.FilePathLabel.text()
        field_name = self.AddShpVectorFieldDisplay.currentText()
        
        # 创建中心点计算线程
        self.center_thread = CenterPointThread(
            file_path=file_path,
            field_name=field_name
        )
        
        # 连接信号槽
        self.center_thread.success.connect(self._on_center_success)
        self.center_thread.error.connect(self._on_center_error)
        
        # 启动线程
        self.center_thread.start()
    
    def _on_center_success(self, result_text):
        """中心点计算成功处理"""
        # 更新文本显示
        self.centerPointText.setText(result_text)
        self.showSuccess("中心点获取完成！")
        self._running = False
    
    def _on_center_error(self, error_msg):
        """中心点计算错误处理"""
        self.showError(error_msg)
        self._running = False
