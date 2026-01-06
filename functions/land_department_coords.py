# coding:utf-8
"""
征地部坐标转换功能
"""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QTextEdit, QGroupBox
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
        # 输入设置区域
        input_group = QGroupBox("输入设置", self)
        input_layout = QVBoxLayout(input_group)
        
        # 输入文件选择
        input_file_layout = QHBoxLayout()
        input_file_label = QLabel("征地部文件：")
        self.inputPathEdit = LineEdit(self)
        self.inputPathEdit.setPlaceholderText("选择征地部标准坐标文件")
        self.inputPathEdit.setReadOnly(True)
        
        self.browseInputBtn = PushButton("选择文件", self, FIF.DOCUMENT)
        self.browseInputBtn.clicked.connect(self._selectInputFile)
        
        input_file_layout.addWidget(input_file_label)
        input_file_layout.addWidget(self.inputPathEdit, 1)
        input_file_layout.addWidget(self.browseInputBtn)
        input_layout.addLayout(input_file_layout)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # 输出类型选择
        output_type_layout = QHBoxLayout()
        output_type_label = QLabel("输出类型：")
        self.output_type_combo = ComboBox(self)
        self.output_type_combo.addItems(["SHP文件", "GDB图层"])
        self.output_type_combo.currentTextChanged.connect(self._on_output_type_changed)
        
        output_type_layout.addWidget(output_type_label)
        output_type_layout.addWidget(self.output_type_combo, 1)
        output_layout.addLayout(output_type_layout)
        
        # SHP输出路径
        self.shp_output_layout = QHBoxLayout()
        shp_output_label = QLabel("SHP输出路径：")
        self.outputDirEdit = LineEdit(self)
        self.outputDirEdit.setPlaceholderText("选择输出SHP文件路径")
        self.outputDirEdit.setReadOnly(True)
        
        self.browseOutputBtn = PushButton("选择输出路径", self, FIF.SAVE)
        self.browseOutputBtn.clicked.connect(self._selectOutputDir)
        
        self.shp_output_layout.addWidget(shp_output_label)
        self.shp_output_layout.addWidget(self.outputDirEdit, 1)
        self.shp_output_layout.addWidget(self.browseOutputBtn)
        output_layout.addLayout(self.shp_output_layout)
        
        # GDB输出设置
        self.gdb_output_layout = QHBoxLayout()
        gdb_output_label = QLabel("GDB输出路径：")
        self.output_gdb_path = LineEdit(self)
        self.output_gdb_path.setPlaceholderText("选择输出GDB文件路径")
        self.output_gdb_path.setReadOnly(True)
        
        self.output_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.output_gdb_btn.clicked.connect(self._select_output_gdb)
        
        self.gdb_output_layout.addWidget(gdb_output_label)
        self.gdb_output_layout.addWidget(self.output_gdb_path, 1)
        self.gdb_output_layout.addWidget(self.output_gdb_btn)
        output_layout.addLayout(self.gdb_output_layout)
        
        # GDB图层名称设置
        self.gdb_layer_layout = QHBoxLayout()
        gdb_layer_label = QLabel("GDB图层名称：")
        self.output_gdb_layer = LineEdit(self)
        self.output_gdb_layer.setPlaceholderText("输入输出图层名称")
        
        self.gdb_layer_layout.addWidget(gdb_layer_label)
        self.gdb_layer_layout.addWidget(self.output_gdb_layer, 1)
        output_layout.addLayout(self.gdb_layer_layout)
        
        # 合并地块选项
        merge_row = QHBoxLayout()
        merge_label = QLabel("合并地块：")
        self.mergeSwitch = SwitchButton()
        self.mergeSwitch.setChecked(True)
        merge_row.addWidget(merge_label)
        merge_row.addWidget(self.mergeSwitch)
        merge_row.addStretch(1)
        output_layout.addLayout(merge_row)
        
        # 初始显示SHP输出选项
        self._on_output_type_changed("SHP文件")
        
        # 将分组框添加到主布局
        self.contentLayout.addWidget(input_group)
        self.contentLayout.addWidget(output_group)
        
        # 添加执行按钮
        self.executeBtn = PrimaryPushButton("开始转换", self, FIF.PLAY)
        self.executeBtn.clicked.connect(self.execute)
        self.contentLayout.addWidget(self.executeBtn, 0, Qt.AlignmentFlag.AlignCenter)
    
    def _selectInputFile(self):
        """选择输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择征地部标准坐标文件", "", "文本文件 (*.txt *.dat);;所有文件 (*.*)"
        )
        if file_path:
            self.inputPathEdit.setText(file_path)
            # 自动生成GDB图层名称
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.output_gdb_layer.setText(base_name)
            
            # 自动生成SHP输出路径，基于输入文件路径
            input_dir = os.path.dirname(file_path)
            shp_path = os.path.join(input_dir, f"{base_name}.shp")
            self.outputDirEdit.setText(shp_path)
    
    def _selectOutputDir(self):
        """选择SHP输出目录"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存SHP文件", "", "SHP文件 (*.shp)"
        )
        if file_path:
            if not file_path.endswith('.shp'):
                file_path += '.shp'
            self.outputDirEdit.setText(file_path)
    
    def _select_output_gdb(self):
        """选择GDB输出文件"""
        file_path = QFileDialog.getExistingDirectory(
            self, "选择输出GDB文件", ""
        )
        if file_path and file_path.endswith('.gdb'):
            self.output_gdb_path.setText(file_path)
    
    def _on_output_type_changed(self, output_type):
        """输出类型变化处理"""
        if output_type == "SHP文件":
            # 显示SHP输出选项，隐藏GDB输出选项
            for i in range(self.shp_output_layout.count()):
                widget = self.shp_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            
            for i in range(self.gdb_output_layout.count()):
                widget = self.gdb_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            
            for i in range(self.gdb_layer_layout.count()):
                widget = self.gdb_layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
        else:
            # 显示GDB输出选项，隐藏SHP输出选项
            for i in range(self.shp_output_layout.count()):
                widget = self.shp_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            
            for i in range(self.gdb_output_layout.count()):
                widget = self.gdb_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            
            for i in range(self.gdb_layer_layout.count()):
                widget = self.gdb_layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        input_path = self.inputPathEdit.text().strip()
        if not input_path:
            return False, "请选择输入文件"
        
        if not os.path.exists(input_path):
            return False, "输入文件不存在"
        
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            # 验证SHP输出设置
            output_path = self.outputDirEdit.text().strip()
            if not output_path:
                return False, "请选择SHP输出路径"
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    return False, f"无法创建输出目录: {str(e)}"
        else:
            # 验证GDB输出设置
            output_gdb = self.output_gdb_path.text().strip()
            if not output_gdb:
                return False, "请选择GDB输出路径"
            
            if not os.path.exists(output_gdb):
                return False, "GDB文件不存在"
            
            if not output_gdb.endswith('.gdb'):
                return False, "请选择有效的GDB文件"
            
            output_layer = self.output_gdb_layer.text().strip()
            if not output_layer:
                return False, "请输入GDB图层名称"
        
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
        output_type = self.output_type_combo.currentText()
        merge_plots = self.mergeSwitch.isChecked()
        
        # 创建转换线程
        if output_type == "SHP文件":
            output_path = self.outputDirEdit.text().strip()
            output_dir = os.path.dirname(output_path)
            base_name = os.path.splitext(os.path.basename(output_path))[0]
            output_shp_path = output_path
        else:
            # GDB输出：需要先转换为SHP，再转换为GDB
            gdb_path = self.output_gdb_path.text().strip()
            layer_name = self.output_gdb_layer.text().strip()
            # 创建临时SHP文件路径
            temp_dir = os.path.dirname(input_path)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_shp_path = os.path.join(temp_dir, f"{base_name}_temp.shp")
            output_dir = temp_dir
        
        self.coords_thread = LandDepartmentCoordsThread(input_path, output_dir, merge_plots)
        
        # 连接信号槽
        self.coords_thread.success.connect(lambda output_files: self._on_conversion_success(output_files, output_type, gdb_path if output_type == "GDB图层" else None, layer_name if output_type == "GDB图层" else None))
        self.coords_thread.error.connect(self._on_conversion_error)
        
        # 启动线程
        self.coords_thread.start()
    
    def _on_conversion_success(self, output_files, output_type="SHP文件", gdb_path=None, layer_name=None):
        """转换成功处理"""
        try:
            if output_type == "GDB图层" and gdb_path and layer_name:
                # 将SHP转换为GDB
                import geopandas as gpd
                
                final_output_files = []
                for idx, shp_path in enumerate(output_files):
                    try:
                        # 读取SHP文件
                        gdf = gpd.read_file(shp_path)
                        
                        # 为每个地块生成唯一的图层名称
                        if len(output_files) > 1:
                            # 多个地块时，在GDB图层名称后添加地块编号后缀
                            gdb_layer_name = f"{layer_name}_地块{idx+1}"
                        elif len(output_files) == 1:
                            # 单个地块时，检查是否为合并模式
                            if "合并地块" in shp_path:
                                # 合并地块模式，使用原始图层名称
                                gdb_layer_name = layer_name
                            else:
                                # 非合并地块模式，添加地块1后缀
                                gdb_layer_name = f"{layer_name}_地块1"
                        else:
                            # 没有地块时，使用原始图层名称
                            gdb_layer_name = layer_name
                        
                        # 保存到GDB
                        gdb_output_path = os.path.join(gdb_path, gdb_layer_name)
                        gdf.to_file(gdb_path, layer=gdb_layer_name, driver='OpenFileGDB')
                        final_output_files.append(gdb_output_path)
                        
                        # 删除临时SHP文件
                        for ext in ['.shp', '.dbf', '.shx', '.prj', '.cpg', '.qpj']:
                            temp_file = os.path.splitext(shp_path)[0] + ext
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                                print(f"已删除临时文件: {temp_file}")
                    except Exception as e:
                        print(f"将SHP转换为GDB时出错: {str(e)}")
                
                if final_output_files:
                    result_msg = f"征地部坐标转换成功！\n共生成 {len(final_output_files)} 个GDB图层：\n"
                    for file_path in final_output_files:
                        result_msg += f"- {os.path.basename(file_path)}\n"
                    result_msg += f"\n输出GDB：{gdb_path}"
                    self.showSuccess(result_msg)
                else:
                    self.showSuccess("征地部坐标转换成功！")
            else:
                # 原始SHP输出处理
                if output_files:
                    result_msg = f"征地部坐标转换成功！\n共生成 {len(output_files)} 个文件：\n"
                    for file_path in output_files:
                        result_msg += f"- {os.path.basename(file_path)}\n"
                    result_msg += f"\n输出目录：{os.path.dirname(output_files[0])}"
                    self.showSuccess(result_msg)
                else:
                    self.showSuccess("征地部坐标转换成功！")
        except Exception as e:
            print(f"处理转换结果时出错: {str(e)}")
            self.showError(f"处理转换结果时出错: {str(e)}")
        
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
