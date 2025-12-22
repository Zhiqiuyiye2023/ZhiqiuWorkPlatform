# coding:utf-8
"""
功能模块模板
复制此文件并修改为具体功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt
from qfluentwidgets import LineEdit, ComboBox, PushButton, TextEdit
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import threading


class TemplatFunction(BaseFunction):
    """【功能名称】"""
    
    def __init__(self, parent=None):
        description = (
            "📢 功能说明：\n"
            "1. 【功能描述第1点】\n"
            "2. 【功能描述第2点】\n"
            "3. 【功能描述第3点】\n"
            "4. 【输出说明】"
        )
        super().__init__("【功能标题】", description, parent)
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮
        self.addExecuteButton("开始执行", self.execute)
        
        # 可选：添加其他自定义按钮
        # self.addCustomButton("预览", FIF.VIEW, self._preview)
    
    def _initUI(self):
        """初始化界面控件"""
        # 示例：文件选择行
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("输入文件："))
        
        self.fileBtn = PushButton("选择文件", self, FIF.DOCUMENT)
        self.fileBtn.clicked.connect(self._selectFile)
        
        self.filePath = LineEdit(self)
        self.filePath.setPlaceholderText("点击按钮选择文件")
        self.filePath.setReadOnly(True)
        
        row1.addWidget(self.fileBtn)
        row1.addWidget(self.filePath, 1)  # 1 表示拉伸因子
        self.contentLayout.addLayout(row1)
        
        # 示例：参数输入行
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("参数设置："))
        
        self.paramInput = LineEdit(self)
        self.paramInput.setPlaceholderText("请输入参数")
        
        row2.addWidget(self.paramInput, 1)
        self.contentLayout.addLayout(row2)
        
        # 示例：下拉选择
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("选择选项："))
        
        self.optionCombo = ComboBox(self)
        self.optionCombo.addItems(["选项1", "选项2", "选项3"])
        self.optionCombo.setPlaceholderText("请选择")
        
        row3.addWidget(self.optionCombo, 1)
        self.contentLayout.addLayout(row3)
        
        # 示例：结果显示区域（可选）
        # self.resultText = TextEdit(self)
        # self.resultText.setReadOnly(True)
        # self.resultText.setPlaceholderText("处理结果将显示在这里...")
        # self.resultText.setFixedHeight(150)
        # self.contentLayout.addWidget(self.resultText)
    
    def _selectFile(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择文件", 
            "", 
            "支持的文件 (*.shp *.tif *.txt);;所有文件 (*.*)"
        )
        if file_path:
            self.filePath.setText(file_path)
            # 可选：加载文件后的处理
            # self._onFileSelected(file_path)
    
    def _onFileSelected(self, file_path: str):
        """文件选择后的处理（可选）"""
        # 例如：读取文件信息、更新其他控件等
        pass
    
    def validate(self) -> tuple[bool, str]:
        """
        验证输入参数
        返回: (是否有效, 错误消息)
        """
        # 示例验证
        if not self.filePath.text():
            return False, "请选择输入文件"
        
        if not self.paramInput.text():
            return False, "请输入参数"
        
        if not self.optionCombo.currentText():
            return False, "请选择选项"
        
        # 所有验证通过
        return True, ""
    
    def execute(self):
        """执行功能"""
        # 1. 验证输入
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        # 2. 获取参数
        file_path = self.filePath.text()
        param = self.paramInput.text()
        option = self.optionCombo.currentText()
        
        # 3. 显示进度
        self.showProgress("正在处理...")
        
        # 4. 在线程中执行处理
        def run_process():
            try:
                # ==========================================
                # 在这里调用实际的处理函数
                # ==========================================
                
                # 示例：调用处理方法
                result = self._processData(file_path, param, option)
                
                # 更新进度（可选）
                # self.updateProgress(50, "处理中...")
                
                # 完成后显示成功消息
                self.showSuccess(f"处理完成！\n{result}")
                
                # 可选：更新结果显示
                # self.resultText.setText(result)
                
            except Exception as e:
                # 捕获并显示错误
                import traceback
                error_msg = f"处理失败: {str(e)}\n\n{traceback.format_exc()}"
                self.showError(error_msg)
        
        # 启动线程
        threading.Thread(target=run_process, daemon=True).start()
    
    def _processData(self, file_path: str, param: str, option: str) -> str:
        """
        实际的数据处理逻辑
        
        参数:
            file_path: 文件路径
            param: 参数
            option: 选项
            
        返回:
            处理结果描述
        """
        # ==========================================
        # 在这里实现具体的处理逻辑
        # ==========================================
        
        # 示例：简单的处理
        import time
        time.sleep(2)  # 模拟处理时间
        
        result_msg = f"文件: {file_path}\n参数: {param}\n选项: {option}"
        return result_msg
    
    def _preview(self):
        """预览功能（自定义按钮示例）"""
        # 实现预览逻辑
        pass


# ==========================================
# 使用说明
# ==========================================
"""
1. 复制此模板文件
2. 重命名为具体功能名（如 data_overlay.py）
3. 修改类名（如 DataOverlayFunction）
4. 更新 description 描述
5. 实现 _initUI() 方法（添加所需控件）
6. 实现 validate() 方法（验证输入）
7. 实现 execute() 方法（执行逻辑）
8. 实现 _processData() 方法（核心处理）
9. 在 __init__.py 中导入
10. 在 app_functions.py 中注册
"""
