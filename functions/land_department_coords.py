# coding:utf-8
"""
征地部坐标转换功能
"""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QTextEdit
from qfluentwidgets import (LineEdit, PushButton, PrimaryPushButton, 
                           StateToolTip, TextEdit, ComboBox, SwitchButton)
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os


class LandDepartmentCoordsThread(QThread):
    """征地部坐标转换线程类"""
    success = pyqtSignal(list)  # 成功信号，传递输出文件列表
    error = pyqtSignal(str)     # 错误信号
    
    def __init__(self, file_path, output_dir, merge_plots):
        super().__init__()
        self.file_path = file_path
        self.output_dir = output_dir
        self.merge_plots = merge_plots
    
    def run(self):
        """执行征地部坐标转换"""
        try:
            # 导入坐标处理模块
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from .坐标处理 import 征地部坐标转换
            
            # 直接调用坐标处理模块中的函数
            output_files = 征地部坐标转换(self.file_path, self.output_dir, self.merge_plots)
            
            # 发送成功信号
            self.success.emit(output_files)
            
        except Exception as e:
            import traceback
            error_msg = f'转换失败: {str(e)}\n\n{traceback.format_exc()}'
            # 发送错误信号
            self.error.emit(error_msg)


class LandDepartmentCoordsFunction(BaseFunction):
    """征地部坐标转换功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "将征地部标准坐标文件转换为SHP矢量文件"
        )
        super().__init__("征地部坐标转换", description, parent)
        
        self._initUI()
        self._running = False
        self.stateTooltip = None
    
    def _initUI(self):
        """初始化界面"""
        # 功能说明标签
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>功能说明：</span>"
            "<br>1. 选择征地部标准坐标文件"
            "<br>2. 设置输出目录"
            "<br>3. 转换为SHP矢量文件"
            "<br>4. 支持多个地块的批量转换"
        )
        infoLabel.setWordWrap(True)
        infoLabel.setStyleSheet('''
            QLabel {
                padding: 10px 0 18px 0;
                font-size: 13px;
                line-height: 1.5;
            }
        ''')
        self.contentLayout.addWidget(infoLabel)
        
        # 输入文件选择
        inputRow = QHBoxLayout()
        inputLabel = QLabel("输入文件：")
        inputRow.addWidget(inputLabel)
        
        self.inputPathEdit = LineEdit(self)
        self.inputPathEdit.setPlaceholderText("请选择征地部标准坐标文件")
        inputRow.addWidget(self.inputPathEdit, 1)
        
        self.browseInputBtn = PushButton("浏览", self, FIF.DOCUMENT)
        self.browseInputBtn.clicked.connect(self._selectInputFile)
        inputRow.addWidget(self.browseInputBtn)
        
        self.contentLayout.addLayout(inputRow)
        
        # 输出目录选择
        outputRow = QHBoxLayout()
        outputLabel = QLabel("输出目录：")
        outputRow.addWidget(outputLabel)
        
        self.outputDirEdit = LineEdit(self)
        self.outputDirEdit.setPlaceholderText("请选择输出目录")
        outputRow.addWidget(self.outputDirEdit, 1)
        
        self.browseOutputBtn = PushButton("浏览", self, FIF.FOLDER)
        self.browseOutputBtn.clicked.connect(self._selectOutputDir)
        outputRow.addWidget(self.browseOutputBtn)
        
        self.contentLayout.addLayout(outputRow)
        
        # 合并地块开关
        mergeRow = QHBoxLayout()
        mergeLabel = QLabel("合并选项：")
        mergeRow.addWidget(mergeLabel)
        
        self.mergePlotsSwitch = SwitchButton(self)
        self.mergePlotsSwitch.setText("合并所有地块为一个SHP文件")
        self.mergePlotsSwitch.setChecked(True)  # 默认开启合并
        mergeRow.addWidget(self.mergePlotsSwitch)
        
        mergeRow.addStretch(1)
        self.contentLayout.addLayout(mergeRow)
        
        # 执行按钮
        buttonRow = QHBoxLayout()
        buttonRow.addStretch(1)
        
        self.executeBtn = PrimaryPushButton("开始转换", self, FIF.SEND)
        self.executeBtn.clicked.connect(self.execute)
        buttonRow.addWidget(self.executeBtn)
        
        buttonRow.addStretch(1)
        self.contentLayout.addLayout(buttonRow)
    
    def _selectInputFile(self):
        """选择输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择征地部标准坐标文件", "", "文本文件 (*.txt *.dat);;所有文件 (*.*)"
        )
        if file_path:
            self.inputPathEdit.setText(file_path)
    
    def _selectOutputDir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", ""
        )
        if dir_path:
            self.outputDirEdit.setText(dir_path)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        input_path = self.inputPathEdit.text().strip()
        if not input_path:
            return False, "请选择输入文件"
        
        if not os.path.exists(input_path):
            return False, "输入文件不存在"
        
        output_dir = self.outputDirEdit.text().strip()
        if not output_dir:
            return False, "请选择输出目录"
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                return False, f"无法创建输出目录: {str(e)}"
        
        return True, ""
    
    def execute(self):
        """执行征地部坐标转换"""
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        if self._running:
            return
        
        self._running = True
        
        # 显示进度提示
        self.stateTooltip = StateToolTip('正在转换', '请稍候...', self)
        self.stateTooltip.move(self.width()//2 - 100, 30)
        self.stateTooltip.show()
        
        # 获取参数
        input_path = self.inputPathEdit.text().strip()
        output_dir = self.outputDirEdit.text().strip()
        merge_plots = self.mergePlotsSwitch.isChecked()
        
        # 创建转换线程
        self.coords_thread = LandDepartmentCoordsThread(input_path, output_dir, merge_plots)
        
        # 连接信号槽
        self.coords_thread.success.connect(self._on_conversion_success)
        self.coords_thread.error.connect(self._on_conversion_error)
        
        # 启动线程
        self.coords_thread.start()
    
    def _on_conversion_success(self, output_files):
        """转换成功处理"""
        if output_files:
            result_msg = f"征地部坐标转换成功！\n共生成 {len(output_files)} 个文件：\n"
            for file_path in output_files:
                result_msg += f"- {os.path.basename(file_path)}\n"
            result_msg += f"\n输出目录：{os.path.dirname(output_files[0])}"
            self.showSuccess(result_msg)
        else:
            self.showSuccess("征地部坐标转换成功！")
        
        if hasattr(self, 'stateTooltip') and self.stateTooltip:
            try:
                self.stateTooltip.close()
            except:
                pass
        self._running = False
    
    def _on_conversion_error(self, error_msg):
        """转换错误处理"""
        self.showError(error_msg)
        if hasattr(self, 'stateTooltip') and self.stateTooltip:
            try:
                self.stateTooltip.close()
            except:
                pass
        self._running = False
