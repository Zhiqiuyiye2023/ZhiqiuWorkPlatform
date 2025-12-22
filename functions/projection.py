# coding:utf-8
"""
修改与定义数据投影功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QFileDialog, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import PrimaryPushButton, TransparentPushButton, ComboBox, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd
import sys
import os


class ProjectionThread(QThread):
    """投影转换线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, file_path, proj_index, operation_type, parent=None):
        """
        Args:
            file_path: 矢量文件路径
            proj_index: 投影索引
            operation_type: '修改数据投影' 或 '定义数据投影'
        """
        super().__init__(parent)
        self.file_path = file_path
        self.proj_index = proj_index
        self.operation_type = operation_type
    
    def run(self):
        """线程运行方法"""
        try:
            # 导入投影转换函数
            from gis_workflow.投影转换 import 修改数据投影, 定义数据投影
            
            # 根据操作类型调用相应的函数
            if self.operation_type == '修改数据投影':
                result = 修改数据投影(self.file_path, self.proj_index)
            elif self.operation_type == '定义数据投影':
                result = 定义数据投影(self.file_path, self.proj_index)
            else:
                raise ValueError(f"未知的操作类型: {self.operation_type}")
            
            if result:
                self.success.emit(f"投影操作成功完成！\n输出文件: {result}")
            else:
                self.error.emit("投影操作执行失败！")
                
        except Exception as e:
            self.error.emit(f"发生错误: {str(e)}")


class ProjectionFunction(BaseFunction):
    """修改与定义数据投影功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "1. <b>修改数据投影</b>功能用于将矢量数据从当前投影转换为指定投影<br>"
            "2. <b>定义数据投影</b>功能用于为无投影信息的矢量数据指定投影坐标系"
        )
        super().__init__("修改与定义数据投影", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮，使用自定义的修改投影和定义投影按钮
        self.stateTooltip = None
        self._running = False
    
    def _initUI(self):
        """初始化界面"""
        # 功能说明标签
        vBoxLayout_info = QVBoxLayout()
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>功能说明：</span>"
            "<br>1. <b>修改数据投影</b>功能用于将矢量数据从当前投影转换为指定投影"
            "<br>2. <b>定义数据投影</b>功能用于为无投影信息的矢量数据指定投影坐标系"
            "<br>3. <b>操作步骤：</b>"
            "<br>   - 点击'添加矢量路径'按钮选择矢量文件"
            "<br>   - 从下拉框选择目标投影参数"
            "<br>   - 点击'修改投影'或'定义投影'按钮"
            "<br>4. <b>输出结果：</b>"
            "<br>   - 在源文件目录下生成带有新投影的SHP文件"
        )
        infoLabel.setWordWrap(True)
        infoLabel.setStyleSheet('''
            QLabel {
                padding: 10px;
                font-size: 13px;
                line-height: 1.5;
            }
        ''')
        vBoxLayout_info.addWidget(infoLabel)
        self.contentLayout.addLayout(vBoxLayout_info)
        
        # 第一行：按钮和控件行
        hBoxLayout1 = QHBoxLayout()
        
        # 修改投影按钮
        self.buttonModify = PrimaryPushButton(self.tr('修改投影'), self, FIF.SEND)
        self.buttonModify.clicked.connect(lambda: self._executeProjection('修改数据投影'))
        
        # 定义投影按钮
        self.buttonDefine = PrimaryPushButton(self.tr('定义投影'), self, FIF.SEND)
        self.buttonDefine.clicked.connect(lambda: self._executeProjection('定义数据投影'))
        
        # 添加矢量路径按钮
        self.buttonAddVector = TransparentPushButton(self.tr('添加矢量路径'), self, FIF.DOCUMENT)
        self.buttonAddVector.clicked.connect(self._selectVectorFile)
        
        # 投影参数下拉框
        self.comboBox = ComboBox(self)
        self.comboBox.setPlaceholderText("选择投影参数")
        items = [
            'CGCS2000_3_Degree_GK_Zone_25', 'CGCS2000_3_Degree_GK_Zone_26', 'CGCS2000_3_Degree_GK_Zone_27',
            'CGCS2000_3_Degree_GK_Zone_28', 'CGCS2000_3_Degree_GK_Zone_29', 'CGCS2000_3_Degree_GK_Zone_30',
            'CGCS2000_3_Degree_GK_Zone_31', 'CGCS2000_3_Degree_GK_Zone_32', 'CGCS2000_3_Degree_GK_Zone_33',
            'CGCS2000_3_Degree_GK_Zone_34', 'CGCS2000_3_Degree_GK_Zone_35', 'CGCS2000_3_Degree_GK_Zone_36',
            'CGCS2000_3_Degree_GK_Zone_37',
            'CGCS2000_3_Degree_GK_Zone_38', 'CGCS2000_3_Degree_GK_Zone_39', 'CGCS2000_3_Degree_GK_Zone_40',
            'CGCS2000_3_Degree_GK_Zone_41', 'CGCS2000_3_Degree_GK_Zone_42', 'CGCS2000_3_Degree_GK_Zone_43',
            'CGCS2000_3_Degree_GK_Zone_44', 'CGCS2000_3_Degree_GK_Zone_45', 'GCS_China_Geodetic_Coordinate_System_2000'
        ]
        self.comboBox.addItems(items)
        self.comboBox.setCurrentIndex(-1)
        
        # 文件路径标签
        self.label7 = QLabel()
        
        # 添加到布局
        hBoxLayout1.addWidget(self.buttonModify)
        hBoxLayout1.addWidget(self.buttonDefine)
        hBoxLayout1.addWidget(self.buttonAddVector)
        hBoxLayout1.addWidget(self.comboBox)
        hBoxLayout1.addWidget(self.label7)
        self.contentLayout.addLayout(hBoxLayout1)
        
        # 第二行：坐标系信息显示
        hBoxLayout2 = QHBoxLayout()
        self.crsInfoLabel = QLabel()
        self.crsInfoLabel.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 13px;
                padding: 10px;
                background-color: #e8f4ff;
                border: 1px solid #b3d4ff;
                border-radius: 6px;
                margin: 5px;
                min-height: 80px;
            }
        """)
        self.crsInfoLabel.setWordWrap(True)
        self.crsInfoLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.crsInfoLabel.hide()  # 初始时隐藏
        hBoxLayout2.addWidget(self.crsInfoLabel)
        self.contentLayout.addLayout(hBoxLayout2)
    
    def _selectVectorFile(self):
        """选择矢量文件并显示坐标系信息"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择矢量文件", "", "矢量文件 (*.shp)")
        if file_path:
            self.label7.setText(file_path)
            try:
                # 尝试读取矢量文件
                try:
                    gdf = gpd.read_file(file_path)
                except Exception as shx_error:
                    # 检查是否为缺少.shx文件的错误
                    if "SHAPE_RESTORE_SHX" in str(shx_error):
                        import os
                        os.environ['SHAPE_RESTORE_SHX'] = 'YES'
                        gdf = gpd.read_file(file_path)
                    else:
                        raise
                
                # 获取并显示坐标系统信息
                if gdf.crs is None:
                    crs_info = "无坐标系统"
                else:
                    # 获取EPSG代码
                    epsg_code = gdf.crs.to_epsg()
                    if epsg_code == 4490:
                        crs_info = "EPSG:4490 (GCS_China_Geodetic_Coordinate_System_2000)"
                    else:
                        crs_info = f"EPSG:{epsg_code} ({gdf.crs.name})"
                
                bounds = gdf.total_bounds
                bounds_info = f"范围: X({bounds[0]:.2f}~{bounds[2]:.2f}), Y({bounds[1]:.2f}~{bounds[3]:.2f})"
                
                # 更新界面上的标签
                info_text = f"📊 矢量文件信息\n\n" \
                            f"📍 坐标系统：\n{crs_info}\n\n" \
                            f"📐 数据范围：\n{bounds_info}"
                self.crsInfoLabel.setText(info_text)
                self.crsInfoLabel.show()
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'读取矢量文件信息失败: {str(e)}')
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.label7.text():
            return False, "请选择矢量文件"
        if self.comboBox.currentIndex() == -1:
            return False, "请选择目标投影参数"
        return True, ""
    
    def _executeProjection(self, operation_type: str):
        """执行投影操作
        
        Args:
            operation_type: '修改数据投影' 或 '定义数据投影'
        """
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
        
        # 创建并启动投影转换线程
        self.projection_thread = ProjectionThread(
            file_path=self.label7.text(),
            proj_index=self.comboBox.currentIndex(),
            operation_type=operation_type,
            parent=self
        )
        
        # 连接信号
        self.projection_thread.success.connect(self._onProjectionSuccess)
        self.projection_thread.error.connect(self._onProjectionError)
        self.projection_thread.finished.connect(self._onProjectionFinished)
        
        # 启动线程
        self.projection_thread.start()
    
    def _onProjectionSuccess(self, message: str):
        """投影操作成功处理"""
        if self.stateTooltip:
            self.stateTooltip.setContent('处理完成 ✅')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showSuccess(message)
    
    def _onProjectionError(self, message: str):
        """投影操作错误处理"""
        if self.stateTooltip:
            self.stateTooltip.setContent('处理失败 ❌')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showError(message)
    
    def _onProjectionFinished(self):
        """投影线程结束处理"""
        self._running = False
    
    def execute(self):
        """执行功能（基类接口，默认执行修改投影）"""
        self._executeProjection('修改数据投影')
