# coding:utf-8
"""
根据指定面积调整要素功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QFileDialog, QVBoxLayout, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
from qfluentwidgets import LineEdit, PrimaryPushButton, TransparentPushButton, ComboBox, ProgressBar, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd


class AreaAdjustThread(QThread):
    """面积调整线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    progress = pyqtSignal(int)  # 进度信号，传递进度值
    
    def __init__(self, file_path, field1, field2, area_value, parent=None):
        """
        Args:
            file_path: 矢量文件路径
            field1: 第一个字段名
            field2: 第二个字段名
            area_value: 指定的面积值
        """
        super().__init__(parent)
        self.file_path = file_path
        self.field1 = field1
        self.field2 = field2
        self.area_value = area_value
    
    def run(self):
        """线程运行方法"""
        try:
            # 从根目录导入数据处理方法
            import sys
            import os
            # 获取项目根目录
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
            
            from .矢量操作 import 根据指定面积缓冲调整要素
            
            # 定义更新进度条的回调函数
            def update_progress(progress):
                self.progress.emit(int(progress))
            
            # 调用处理函数
            根据指定面积缓冲调整要素(
                self.file_path,
                self.field1,
                self.field2,
                self.area_value,
                update_progress
            )
            
            self.success.emit("面积调整完成！")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(f"面积调整失败: {str(e)}\n\n{traceback.format_exc()}")


class AreaAdjustFunction(BaseFunction):
    """根据指定面积调整要素功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "根据指定面积缓冲调整要素<br>"
            "<span style='color: orange; font-weight: bold;'>提示：</span>调整面积只可能比原图斑小，不可能比原图斑大~~"
        )
        super().__init__("根据指定面积调整要素", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮，使用自定义的缓冲调整按钮
        self.stateTooltip = None
        self._running = False
    
    def _initUI(self):
        """初始化界面"""
        # 第一行：提示标签
        vBoxLayout1 = QHBoxLayout()
        self.label = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>提示：</span>调整面积只可能比原图斑小，不可能比原图斑大~~")
        vBoxLayout1.addWidget(self.label)
        self.contentLayout.addLayout(vBoxLayout1)
        
        # 第二行：按钮和控件行
        vBoxLayout2 = QHBoxLayout()
        
        # 缓冲调整按钮
        self.buttonAE = PrimaryPushButton(self.tr('缓冲调整'), self, FIF.SEND)
        self.buttonAE.clicked.connect(self.execute)
        
        # 添加矢量按钮
        self.AddVectorButton = TransparentPushButton(self.tr('添加矢量'), self, FIF.DOCUMENT)
        self.AddVectorButton.clicked.connect(self._selectVectorFile)
        
        # 标签
        self.labelBH = QLabel("唯一编号:")
        self.labelMJ = QLabel("指定面积（亩）：")
        self.labelWC = QLabel("允许误差（平方米）：")
        
        # 字段下拉框
        self.AddShpVectorFieldDisplay = ComboBox(self)
        self.AddShpVectorFieldDisplay.setPlaceholderText("添加矢量后选择编号字段")
        self.AddShpVectorFieldDisplay.setCurrentIndex(-1)
        
        self.AddShpVectorFieldDisplay2 = ComboBox(self)
        self.AddShpVectorFieldDisplay2.setPlaceholderText("添加矢量后选择面积字段")
        self.AddShpVectorFieldDisplay2.setCurrentIndex(-1)
        
        # 误差输入框
        self.lineEdit11 = LineEdit(self)
        self.lineEdit11.setText("1")
        
        # 添加到布局
        vBoxLayout2.addWidget(self.buttonAE)
        vBoxLayout2.addWidget(self.AddVectorButton)
        vBoxLayout2.addWidget(self.labelBH)
        vBoxLayout2.addWidget(self.AddShpVectorFieldDisplay)
        vBoxLayout2.addWidget(self.labelMJ)
        vBoxLayout2.addWidget(self.AddShpVectorFieldDisplay2)
        vBoxLayout2.addWidget(self.labelWC)
        vBoxLayout2.addWidget(self.lineEdit11)
        self.contentLayout.addLayout(vBoxLayout2)
        
        # 第三行：文件路径显示
        vBoxLayout3 = QHBoxLayout()
        self.FilePathLabel = QLabel("")
        vBoxLayout3.addWidget(self.FilePathLabel)
        self.contentLayout.addLayout(vBoxLayout3)
        
        # 第四行：进度条
        vBoxLayout4 = QHBoxLayout()
        self.progressBar = ProgressBar(self)
        self.progressBar.setFixedWidth(1070)
        vBoxLayout4.addWidget(self.progressBar)
        self.contentLayout.addLayout(vBoxLayout4)
    
    def _selectVectorFile(self):
        """选择矢量文件并获取字段列表"""
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
                        import os
                        os.environ['SHAPE_RESTORE_SHX'] = 'YES'
                        # 重新尝试读取文件
                        gdf = gpd.read_file(file_path)
                    else:
                        # 其他错误，重新抛出
                        raise
                    
                fields = gdf.columns.tolist()
                
                # 移除几何字段
                if 'geometry' in fields:
                    fields.remove('geometry')
                    
                # 更新两个下拉框
                self.AddShpVectorFieldDisplay.clear()
                self.AddShpVectorFieldDisplay.addItems(fields)
                self.AddShpVectorFieldDisplay.setCurrentIndex(-1)
                
                self.AddShpVectorFieldDisplay2.clear()
                self.AddShpVectorFieldDisplay2.addItems(fields)
                self.AddShpVectorFieldDisplay2.setCurrentIndex(-1)
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'读取矢量文件字段失败: {str(e)}')
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.FilePathLabel.text():
            return False, "请选择矢量文件"
        if not self.AddShpVectorFieldDisplay.currentText():
            return False, "请选择唯一编号字段"
        if not self.AddShpVectorFieldDisplay2.currentText():
            return False, "请选择指定面积字段"
        if not self.lineEdit11.text():
            return False, "请输入允许误差"
        try:
            float(self.lineEdit11.text())
        except ValueError:
            return False, "允许误差必须是数字"
        return True, ""
    
    def execute(self):
        """执行功能"""
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        if self._running:
            return
        
        self._running = True
        self.stateTooltip = StateToolTip('正在运行程序', '客官请耐心等待哦~~', self)
        self.stateTooltip.move(510, 30)
        self.stateTooltip.show()
        
        # 创建并启动面积调整线程
        self.area_thread = AreaAdjustThread(
            file_path=self.FilePathLabel.text(),
            field1=self.AddShpVectorFieldDisplay.currentText(),
            field2=self.AddShpVectorFieldDisplay2.currentText(),
            area_value=self.lineEdit11.text(),
            parent=self
        )
        
        # 连接信号
        self.area_thread.success.connect(self._onAreaAdjustSuccess)
        self.area_thread.error.connect(self._onAreaAdjustError)
        self.area_thread.progress.connect(self._onAreaAdjustProgress)
        self.area_thread.finished.connect(self._onAreaAdjustFinished)
        
        # 启动线程
        self.area_thread.start()
    
    def _onAreaAdjustProgress(self, progress: int):
        """面积调整进度更新处理"""
        self.progressBar.setValue(progress)
    
    def _onAreaAdjustSuccess(self, message: str):
        """面积调整成功处理"""
        if self.stateTooltip:
            self.stateTooltip.setContent('处理完成 ✅')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showSuccess(message)
    
    def _onAreaAdjustError(self, message: str):
        """面积调整错误处理"""
        if self.stateTooltip:
            self.stateTooltip.setContent('处理失败 ❌')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showError(message)
    
    def _onAreaAdjustFinished(self):
        """面积调整线程结束处理"""
        self._running = False
