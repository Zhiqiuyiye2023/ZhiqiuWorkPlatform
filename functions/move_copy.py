"""
移动复制功能
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog
from qfluentwidgets import LineEdit, PushButton, TextEdit
from qfluentwidgets import FluentIcon as FIF
from .file_processor_base import BaseFileProcessorFunction
import os
import shutil


class MoveCopyFunction(BaseFileProcessorFunction):
    """移动复制功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "移动、复制或删除文件和文件夹<br>" 
            "支持单个或批量文件/文件夹的移动复制删除操作"
        )
        super().__init__("移动复制", description, parent)
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 源路径选择区域
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("源路径:"))
        
        self.source_edit = LineEdit(self)
        self.source_edit.setPlaceholderText("请选择源文件或文件夹")
        
        self.source_browse_button = PushButton("浏览", self, FIF.DOCUMENT)
        self.source_browse_button.clicked.connect(lambda: self.browse_file(self.source_edit, allow_dir=True))
        
        source_layout.addWidget(self.source_edit)
        source_layout.addWidget(self.source_browse_button)
        self.contentLayout.addLayout(source_layout)
        
        # 目标路径选择区域
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("目标路径:"))
        
        self.target_edit = LineEdit(self)
        self.target_edit.setPlaceholderText("请选择目标目录")
        
        self.target_browse_button = PushButton("浏览", self, FIF.FOLDER)
        self.target_browse_button.clicked.connect(lambda: self.browse_directory(self.target_edit))
        
        target_layout.addWidget(self.target_edit)
        target_layout.addWidget(self.target_browse_button)
        self.contentLayout.addLayout(target_layout)
        
        # 提示标签
        info_label = QLabel("📢 请填写需要移动或复制的文件/文件夹完整路径，每行一个")
        info_label.setStyleSheet("color: orange; font-weight: bold;")
        self.contentLayout.addWidget(info_label)
        
        # 文本输入区域
        text_layout = QHBoxLayout()
        self.move_copy_text = TextEdit(self)
        self.move_copy_text.setPlaceholderText("请输入要移动或复制的文件/文件夹完整路径，每行一个\n例如：\nE:\\新建文件夹 (2)\\P1BH5566\nC:\\Program Files\\test.txt\nD:\\test_folder")
        self.move_copy_text.setFixedHeight(150)
        text_layout.addWidget(self.move_copy_text)
        self.contentLayout.addLayout(text_layout)
        
        # 功能按钮区域
        button_layout = QHBoxLayout()
        self.copy_folder_button = PushButton("复制文件夹", self, FIF.COPY)
        self.move_folder_button = PushButton("移动文件夹", self, FIF.MOVE)
        self.copy_file_button = PushButton("复制文件", self, FIF.COPY)
        self.move_file_button = PushButton("移动文件", self, FIF.MOVE)
        self.delete_file_button = PushButton("删除文件", self, FIF.DELETE)
        self.delete_folder_button = PushButton("删除文件夹", self, FIF.DELETE)
        self.batch_create_folders_button = PushButton("批量创建文件夹", self, FIF.ADD)
        
        self.copy_folder_button.clicked.connect(self.copy_folder_method)
        self.move_folder_button.clicked.connect(self.move_folder_method)
        self.copy_file_button.clicked.connect(self.copy_file_method)
        self.move_file_button.clicked.connect(self.move_file_method)
        self.delete_file_button.clicked.connect(self.delete_file_method)
        self.delete_folder_button.clicked.connect(self.delete_folder_method)
        self.batch_create_folders_button.clicked.connect(self.batch_create_folders)
        
        button_layout.addWidget(self.copy_folder_button)
        button_layout.addWidget(self.move_folder_button)
        button_layout.addWidget(self.copy_file_button)
        button_layout.addWidget(self.move_file_button)
        button_layout.addWidget(self.delete_file_button)
        button_layout.addWidget(self.delete_folder_button)
        button_layout.addWidget(self.batch_create_folders_button)
        self.contentLayout.addLayout(button_layout)
    
    def validate(self, need_source=True) -> tuple[bool, str]:
        """验证输入
        need_source: 是否需要源路径验证
        """
        if need_source:
            if not self.source_edit.text():
                return False, "请选择源路径"
            if not os.path.exists(self.source_edit.text()):
                return False, "源路径不存在"
        
        if not self.target_edit.text():
            return False, "请选择目标路径"
        if not os.path.exists(self.target_edit.text()):
            return False, "目标路径不存在"
        
        # 验证文本区域内容
        text_content = self.move_copy_text.toPlainText().strip()
        if not text_content:
            return False, "请输入要移动或复制的文件/文件夹名"
        
        return True, ""
    
    def copy_folder_method(self):
        """复制文件夹方法"""
        # 验证目标路径，源路径可以从文本中获取
        if not self.target_edit.text():
            self.showError("请选择目标路径")
            return
        if not os.path.exists(self.target_edit.text()):
            self.showError("目标路径不存在")
            return
            
        text_content = self.move_copy_text.toPlainText().strip()
        if not text_content:
            self.showError("请输入要复制的文件夹路径")
            return
            
        try:
            self.showProgress("正在复制文件夹...")
            target_path = self.target_edit.text()
            
            # 按行分割，支持完整路径
            folder_paths = [line.strip() for line in text_content.split('\n') if line.strip()]
            success_count = 0
            
            for folder_path in folder_paths:
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    # 如果是完整路径，直接使用
                    folder_name = os.path.basename(folder_path)
                    target_folder = os.path.join(target_path, folder_name)
                    
                    if os.path.exists(target_folder):
                        shutil.rmtree(target_folder)
                    shutil.copytree(folder_path, target_folder)
                    success_count += 1
            
            self.showSuccess(f"文件夹复制完成\n共复制 {success_count} 个文件夹")
        except Exception as e:
            self.showError(f"复制文件夹时出错: {str(e)}")
        finally:
            self.hideProgress()
    
    def move_folder_method(self):
        """移动文件夹方法"""
        # 验证目标路径，源路径可以从文本中获取
        if not self.target_edit.text():
            self.showError("请选择目标路径")
            return
        if not os.path.exists(self.target_edit.text()):
            self.showError("目标路径不存在")
            return
            
        text_content = self.move_copy_text.toPlainText().strip()
        if not text_content:
            self.showError("请输入要移动的文件夹路径")
            return
            
        try:
            self.showProgress("正在移动文件夹...")
            target_path = self.target_edit.text()
            
            # 按行分割，支持完整路径
            folder_paths = [line.strip() for line in text_content.split('\n') if line.strip()]
            success_count = 0
            
            for folder_path in folder_paths:
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    # 如果是完整路径，直接使用
                    folder_name = os.path.basename(folder_path)
                    target_folder = os.path.join(target_path, folder_name)
                    shutil.move(folder_path, target_folder)
                    success_count += 1
            
            self.showSuccess(f"文件夹移动完成\n共移动 {success_count} 个文件夹")
        except Exception as e:
            self.showError(f"移动文件夹时出错: {str(e)}")
        finally:
            self.hideProgress()
    
    def copy_file_method(self):
        """复制文件方法"""
        # 验证目标路径，源路径可以从文本中获取
        if not self.target_edit.text():
            self.showError("请选择目标路径")
            return
        if not os.path.exists(self.target_edit.text()):
            self.showError("目标路径不存在")
            return
            
        text_content = self.move_copy_text.toPlainText().strip()
        if not text_content:
            self.showError("请输入要复制的文件路径")
            return
            
        try:
            self.showProgress("正在复制文件...")
            target_path = self.target_edit.text()
            
            # 按行分割，支持完整路径
            paths = [line.strip() for line in text_content.split('\n') if line.strip()]
            success_count = 0
            
            for path in paths:
                if os.path.exists(path):
                    if os.path.isfile(path):
                        # 单个文件，直接复制
                        file_name = os.path.basename(path)
                        target_file = os.path.join(target_path, file_name)
                        shutil.copy2(path, target_file)
                        success_count += 1
                    elif os.path.isdir(path):
                        # 目录
                        if path.endswith('\\') or path.endswith('/'):
                            # 带斜杠结尾，表示复制该目录下的所有文件
                            for item in os.listdir(path):
                                item_path = os.path.join(path, item)
                                if os.path.isfile(item_path):
                                    file_name = os.path.basename(item_path)
                                    target_file = os.path.join(target_path, file_name)
                                    shutil.copy2(item_path, target_file)
                                    success_count += 1
            
            self.showSuccess(f"文件复制完成\n共复制 {success_count} 个文件")
        except Exception as e:
            self.showError(f"复制文件时出错: {str(e)}")
        finally:
            self.hideProgress()
    
    def move_file_method(self):
        """移动文件方法"""
        # 验证目标路径，源路径可以从文本中获取
        if not self.target_edit.text():
            self.showError("请选择目标路径")
            return
        if not os.path.exists(self.target_edit.text()):
            self.showError("目标路径不存在")
            return
            
        text_content = self.move_copy_text.toPlainText().strip()
        if not text_content:
            self.showError("请输入要移动的文件路径")
            return
            
        try:
            self.showProgress("正在移动文件...")
            target_path = self.target_edit.text()
            
            # 按行分割，支持完整路径
            paths = [line.strip() for line in text_content.split('\n') if line.strip()]
            success_count = 0
            
            for path in paths:
                if os.path.exists(path):
                    if os.path.isfile(path):
                        # 单个文件，直接移动
                        file_name = os.path.basename(path)
                        target_file = os.path.join(target_path, file_name)
                        shutil.move(path, target_file)
                        success_count += 1
                    elif os.path.isdir(path):
                        # 目录
                        if path.endswith('\\') or path.endswith('/'):
                            # 带斜杠结尾，表示移动该目录下的所有文件
                            for item in os.listdir(path):
                                item_path = os.path.join(path, item)
                                if os.path.isfile(item_path):
                                    file_name = os.path.basename(item_path)
                                    target_file = os.path.join(target_path, file_name)
                                    shutil.move(item_path, target_file)
                                    success_count += 1
            
            self.showSuccess(f"文件移动完成\n共移动 {success_count} 个文件")
        except Exception as e:
            self.showError(f"移动文件时出错: {str(e)}")
        finally:
            self.hideProgress()
    
    def batch_create_folders(self):
        """批量创建文件夹"""
        valid, message = self.validate(need_source=False)
        if not valid:
            self.showError(message)
            return
            
        try:
            self.showProgress("正在创建文件夹...")
            target_path = self.target_edit.text()
            folder_names_text = self.move_copy_text.toPlainText()
            
            folder_names = folder_names_text.strip().split()
            success_count = 0
            
            for folder in folder_names:
                if folder.strip():
                    full_path = os.path.join(target_path, folder.strip())
                    os.makedirs(full_path, exist_ok=True)
                    success_count += 1
            
            self.showSuccess(f"文件夹创建完成\n共创建 {success_count} 个文件夹")
        except Exception as e:
            self.showError(f"创建文件夹时出错: {str(e)}")
        finally:
            self.hideProgress()
    
    def copy_file(self):
        """复制文件（兼容旧接口）"""
        self.copy_file_method()
    
    def delete_file_method(self):
        """删除文件方法"""
        text_content = self.move_copy_text.toPlainText().strip()
        if not text_content:
            self.showError("请输入要删除的文件路径")
            return
            
        try:
            self.showProgress("正在删除文件...")
            
            # 按行分割，支持完整路径
            paths = [line.strip() for line in text_content.split('\n') if line.strip()]
            success_count = 0
            
            for path in paths:
                if os.path.exists(path) and os.path.isfile(path):
                    # 单个文件，直接删除
                    os.remove(path)
                    success_count += 1
            
            self.showSuccess(f"文件删除完成\n共删除 {success_count} 个文件")
        except Exception as e:
            self.showError(f"删除文件时出错: {str(e)}")
        finally:
            self.hideProgress()
    
    def delete_folder_method(self):
        """删除文件夹方法"""
        text_content = self.move_copy_text.toPlainText().strip()
        if not text_content:
            self.showError("请输入要删除的文件夹路径")
            return
            
        try:
            self.showProgress("正在删除文件夹...")
            
            # 按行分割，支持完整路径
            paths = [line.strip() for line in text_content.split('\n') if line.strip()]
            success_count = 0
            
            for path in paths:
                if os.path.exists(path) and os.path.isdir(path):
                    # 单个文件夹，直接删除
                    shutil.rmtree(path)
                    success_count += 1
            
            self.showSuccess(f"文件夹删除完成\n共删除 {success_count} 个文件夹")
        except Exception as e:
            self.showError(f"删除文件夹时出错: {str(e)}")
        finally:
            self.hideProgress()
    
    def move_file(self):
        """移动文件（兼容旧接口）"""
        self.move_file_method()