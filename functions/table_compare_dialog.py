"""
表格比对功能对话框
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                            QFileDialog, QLabel, QTableWidgetItem, QHeaderView, 
                            QRadioButton, QButtonGroup)
from qfluentwidgets import (BodyLabel, PushButton, MessageBox, 
                           InfoBar, InfoBarPosition, TableWidget, ComboBox)
from .base_dialog import BaseFileProcessDialog
from functions.processor import FileBatchProcessor


class TableCompareDialog(BaseFileProcessDialog):
    """表格比对功能对话框"""
    
    def __init__(self, parent=None):
        super().__init__("表格内容比对", parent)
        self.processor = FileBatchProcessor()
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 第一个Excel文件选择区域
        excel1_layout = QHBoxLayout()
        self.excel1_label = BodyLabel("第一个Excel文件:")
        self.excel1_edit = QLineEdit()
        self.excel1_edit.setPlaceholderText("请选择第一个Excel文件")
        self.excel1_edit.setFixedHeight(35)  # 增加高度
        self.excel1_browse_button = PushButton("选择Excel")
        self.excel1_browse_button.setFixedHeight(35)
        self.excel1_browse_button.clicked.connect(lambda: self.select_excel(1))
        
        excel1_layout.addWidget(self.excel1_label)
        excel1_layout.addWidget(self.excel1_edit)
        excel1_layout.addWidget(self.excel1_browse_button)
        self.addContentLayout(excel1_layout)
        
        # 第二个Excel文件选择区域
        excel2_layout = QHBoxLayout()
        self.excel2_label = BodyLabel("第二个Excel文件:")
        self.excel2_edit = QLineEdit()
        self.excel2_edit.setPlaceholderText("请选择第二个Excel文件")
        self.excel2_edit.setFixedHeight(35)  # 增加高度
        self.excel2_browse_button = PushButton("选择Excel")
        self.excel2_browse_button.setFixedHeight(35)
        self.excel2_browse_button.clicked.connect(lambda: self.select_excel(2))
        
        excel2_layout.addWidget(self.excel2_label)
        excel2_layout.addWidget(self.excel2_edit)
        excel2_layout.addWidget(self.excel2_browse_button)
        self.addContentLayout(excel2_layout)
        
        # 标红设置区域
        mark_settings_layout = QHBoxLayout()
        mark_settings_layout.addWidget(BodyLabel("标红方式:"))
        
        # 标红方式选择（文字颜色/单元格背景）
        self.mark_type_group = QButtonGroup(self)
        self.text_color_radio = QRadioButton("标红文字")
        self.cell_bg_radio = QRadioButton("标红单元格")
        self.cell_bg_radio.setChecked(True)  # 默认标红单元格
        
        self.mark_type_group.addButton(self.text_color_radio)
        self.mark_type_group.addButton(self.cell_bg_radio)
        
        mark_settings_layout.addWidget(self.text_color_radio)
        mark_settings_layout.addWidget(self.cell_bg_radio)
        
        # 颜色选择
        mark_settings_layout.addWidget(BodyLabel("标红颜色:"))
        self.color_combo = ComboBox(self)
        self.color_combo.addItems(["红色", "蓝色", "黄色", "绿色", "橙色"])
        self.color_combo.setCurrentText("红色")  # 默认红色
        mark_settings_layout.addWidget(self.color_combo)
        
        mark_settings_layout.addStretch()
        self.addContentLayout(mark_settings_layout)
        
        # 执行比对按钮区域
        button_layout = QHBoxLayout()
        self.compare_button = PushButton("执行整表比对")
        self.compare_button.setFixedHeight(35)
        self.compare_button.clicked.connect(self.compare_tables)
        
        button_layout.addWidget(self.compare_button)
        self.addContentLayout(button_layout)
        
        # 结果显示区域
        self.result_table = TableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["序号", "第一个表格内容", "第二个表格内容", "差异类型"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setFixedHeight(300)
        self.result_table.setBorderVisible(True)
        self.addContentWidget(self.result_table)
    
    def select_excel(self, excel_num):
        """选择Excel文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"选择第{excel_num}个Excel文件", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            if excel_num == 1:
                self.excel1_edit.setText(file_path)
            else:
                self.excel2_edit.setText(file_path)
    
    def compare_tables(self):
        """比对两个表格的完整内容"""
        excel1_path = self.excel1_edit.text()
        excel2_path = self.excel2_edit.text()
        
        if not excel1_path or not excel2_path:
            InfoBar.warning(
                title='警告',
                content='请选择两个Excel文件',
                parent=self,
                duration=2000
            )
            return
        
        try:
            # 执行比对
            results, different_cells, columns_list = self.processor.compare_full_tables(excel1_path, excel2_path)
            
            # 显示结果
            self.display_results(results)
            
            # 如果有差异，询问是否标红
            if different_cells:
                # 获取用户选择的标红方式和颜色
                is_cell_bg = self.cell_bg_radio.isChecked()
                mark_color = self.color_combo.currentText()
                
                # 在第一个表格中标红差异
                try:
                    mark_result = self.processor.mark_differences_in_excel(excel1_path, different_cells, columns_list, 
                                                                          is_cell_bg, mark_color)
                    if mark_result:
                        output_path, marked_count = mark_result
                        InfoBar.success(
                            title='成功',
                            content=f'整表比对完成，发现 {len(results)} 处差异\n差异已标红并保存到: {output_path}\n成功标红: {marked_count} 个单元格',
                            parent=self,
                            duration=5000
                        )
                    else:
                        InfoBar.success(
                            title='完成',
                            content=f'整表比对完成，发现 {len(results)} 处差异',
                            parent=self,
                            duration=3000
                        )
                except Exception as e:
                    InfoBar.warning(
                        title='警告',
                        content=f'整表比对完成，发现 {len(results)} 处差异\n标红时出错: {str(e)}',
                        parent=self,
                        duration=3000
                    )
            else:
                InfoBar.success(
                    title='完成',
                    content=f'整表比对完成，未发现差异',
                    parent=self,
                    duration=2000
                )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'比对表格时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def display_results(self, results):
        """显示比对结果"""
        self.result_table.setRowCount(len(results))
        for i, (index, content1, content2, diff_type) in enumerate(results):
            self.result_table.setItem(i, 0, QTableWidgetItem(str(index)))
            self.result_table.setItem(i, 1, QTableWidgetItem(str(content1)))
            self.result_table.setItem(i, 2, QTableWidgetItem(str(content2)))
            self.result_table.setItem(i, 3, QTableWidgetItem(str(diff_type)))