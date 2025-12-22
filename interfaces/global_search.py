# coding:utf-8
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QLabel
from PyQt6.QtGui import QFont, QCursor
from qfluentwidgets import (SearchLineEdit, CardWidget, IconWidget, BodyLabel, 
                            CaptionLabel, isDarkTheme, themeColor)
from qfluentwidgets import FluentIcon as FIF


class SearchResultItem(CardWidget):
    """搜索结果项"""
    clicked = pyqtSignal(str, str)  # app_id, title
    
    def __init__(self, app_id: str, icon, title: str, description: str, parent=None):
        super().__init__(parent)
        self.app_id = app_id
        self.setFixedHeight(70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 创建布局
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(16, 12, 16, 12)
        self.hBoxLayout.setSpacing(12)
        
        # 图标
        self.iconWidget = IconWidget(icon, self)
        self.iconWidget.setFixedSize(36, 36)
        
        # 文字容器
        self.textLayout = QVBoxLayout()
        self.textLayout.setSpacing(4)
        
        # 标题
        self.titleLabel = BodyLabel(title, self)
        self.titleLabel.setFont(QFont('Microsoft YaHei', 11, QFont.Weight.DemiBold))
        
        # 描述
        self.descLabel = CaptionLabel(description, self)
        
        # 添加到布局
        self.textLayout.addWidget(self.titleLabel)
        self.textLayout.addWidget(self.descLabel)
        
        self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.textLayout)
        self.hBoxLayout.addStretch(1)
        
        # 设置样式
        self._updateStyle()
    
    def _updateStyle(self):
        """更新样式"""
        if isDarkTheme():
            hover_bg = 'rgba(255, 255, 255, 0.08)'
            border_color = 'rgba(255, 255, 255, 0.05)'
        else:
            hover_bg = 'rgba(0, 0, 0, 0.05)'
            border_color = 'rgba(0, 0, 0, 0.05)'
        
        self.setStyleSheet(f"""
            SearchResultItem {{
                border: 1px solid {border_color};
                border-radius: 8px;
                background: transparent;
            }}
            SearchResultItem:hover {{
                background: {hover_bg};
                border: 1px solid {themeColor().name()};
            }}
        """)
    
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.clicked.emit(self.app_id, self.titleLabel.text())


class GlobalSearchDropdown(QWidget):
    """全局搜索下拉框"""
    appSelected = pyqtSignal(str, str)  # app_id, title
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用 ToolTip 窗口类型，不会抢夺焦点
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 确保不激活窗口，不抢夺焦点
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # 创建主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        
        # 创建卡片容器
        self.container = CardWidget(self)
        self.containerLayout = QVBoxLayout(self.container)
        self.containerLayout.setContentsMargins(8, 8, 8, 8)
        self.containerLayout.setSpacing(4)
        
        # 添加到主布局
        self.vBoxLayout.addWidget(self.container)
        
        # 应用数据 - 包含所有应用
        self.apps_data = [
            # 原有应用
            ('data_overlay', FIF.TILES, '数据叠加套合', '计算两个矢量数据集的套合占比'),
            ('field_split', FIF.CUT, '字段分离要素', '根据字段值分离矢量要素'),
            ('area_adjust', FIF.ZOOM, '面积调整要素', '根据指定面积缓冲调整要素'),
            ('projection', FIF.GLOBE, '投影转换', '修改与定义数据投影'),
            ('dxf_convert', FIF.DOCUMENT, 'DXF转SHP', '提取DXF图层转SHP格式'),
            ('merge_features', FIF.ACCEPT, '合并要素', '合并目录中所有要素'),
            ('shp_to_kmz', FIF.FOLDER, 'SHP转KMZ', '转换为奥维地图格式'),
            ('kmz_to_shp', FIF.FOLDER, 'KMZ转SHP', '将KMZ奥维格式转换为SHP矢量文件'),
            ('shp_to_wkt', FIF.CODE, 'SHP转WKT', '转换为WKT文本格式'),
            ('wkt_to_shp', FIF.CODE, 'WKT转SHP', 'WKT坐标串转矢量文件'),
            ('pdf_tools', FIF.DOCUMENT, 'PDF工具', 'PDF合并、分离、转换'),
            ('image_mosaic', FIF.PHOTO, '影像拼接', '多影像文件拼接处理'),
            ('center_point', FIF.PIN, '获取中心点', '获取矢量要素中心坐标'),
            ('image_crop', FIF.CUT, '影像裁剪', '根据矢量裁剪影像'),
            ('image_crop_by_admin_region', FIF.CUT, '影像裁剪-行政区', '按行政区域分类裁剪影像'),
            ('coords_to_shp', FIF.PIN, '坐标转SHP', '坐标点转矢量文件'),
            ('land_department_coords', FIF.DOCUMENT, '征地部坐标转换', '征地部标准坐标转SHP'),
            
            # 文件处理功能
            ('file_stat', FIF.FOLDER, '文件统计', '统计文件与文件夹信息'),
            ('move_copy', FIF.MOVE, '移动复制', '移动或复制文件/文件夹'),
            ('data_process', FIF.ALIGNMENT, '数据处理', '单数据对应多信息处理'),
            ('batch_rename', FIF.EDIT, '批量重命名', '批量重命名文件/文件夹'),
            ('batch_copy_move', FIF.SYNC, '批量操作', '批量复制/移动文件/文件夹'),
            ('file_table_compare', FIF.SEARCH, '表格比对', '比对两个Excel表格内容'),
            ('file_folder_content_modifier', FIF.EDIT, '文件与文件夹内容修改', '删除或插入文件与文件夹名称内容'),
            # 新功能
            ('trial_plan_summary', FIF.DOCUMENT, '试划成果总结统计', '管理边界相交面积计算表1'),
            ('feature_check', FIF.CHECKBOX, '要素常规检查', '检查GDB或SHP要素的常规问题'),
        ]
        
        self.result_items = []
        
        # 设置样式
        self._updateStyle()
    
    def _updateStyle(self):
        """更新样式"""
        if isDarkTheme():
            bg_color = 'rgba(32, 32, 32, 0.95)'
        else:
            bg_color = 'rgba(249, 249, 249, 0.95)'
        
        self.container.setStyleSheet(f"""
            CardWidget {{
                background: {bg_color};
                border: 1px solid {themeColor().name()};
                border-radius: 10px;
            }}
        """)
    
    def updateResults(self, keyword: str):
        """更新搜索结果"""
        # 清空现有结果
        for item in self.result_items:
            item.deleteLater()
        self.result_items.clear()
        
        if not keyword:
            self.hide()
            return
        
        # 搜索匹配的应用
        keyword = keyword.lower()
        matched_apps = []
        
        for app_id, icon, title, desc in self.apps_data:
            if keyword in title.lower() or keyword in desc.lower():
                matched_apps.append((app_id, icon, title, desc))
        
        if not matched_apps:
            # 显示无结果提示
            no_result_label = BodyLabel('未找到匹配的应用', self.container)
            no_result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_result_label.setFixedHeight(60)
            self.containerLayout.addWidget(no_result_label)
            self.result_items.append(no_result_label)
        else:
            # 最多显示6个结果
            for app_id, icon, title, desc in matched_apps[:6]:
                item = SearchResultItem(app_id, icon, title, desc, self.container)
                item.clicked.connect(self._onItemClicked)
                self.containerLayout.addWidget(item)
                self.result_items.append(item)
        
        # 调整下拉框大小
        item_count = min(len(matched_apps), 6) if matched_apps else 1
        height = item_count * 74 + 16  # 每项70px高度 + 4px间距 + 上下边距
        self.setFixedHeight(height)
    
    def _onItemClicked(self, app_id: str, title: str):
        """处理项目点击"""
        self.appSelected.emit(app_id, title)
        self.hide()
    
    def showAtPosition(self, pos: QPoint, width: int):
        """在指定位置显示"""
        self.setFixedWidth(width)
        self.move(pos)
        self.show()
        self.raise_()
