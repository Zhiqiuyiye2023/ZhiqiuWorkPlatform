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
            # 矢量处理类
            ('data_overlay', FIF.TILES, '数据叠加套合', '计算矢量数据套合占比'),
            ('field_split', FIF.CUT, '字段分离要素', '按字段值分离矢量要素'),
            ('area_adjust', FIF.ZOOM, '面积调整要素', '按指定面积调整要素'),
            ('merge_features', FIF.ACCEPT, '合并要素', '合并目录所有要素'),
            ('dissolve_features', FIF.ACCEPT, '融合要素', '融合相同类型要素'),
            ('identify_features', FIF.MARKET, '标识卡片', '支持图层添加与顺序调整'),
            ('fix_sharp_angle', FIF.CHECKBOX, '修复尖锐角', '修复矢量要素尖锐角'),
            ('eliminate_features', FIF.DELETE, '消除面', '合并小面到邻近面'),
            ('polygon_to_line', FIF.TAG, '要素面转线', '多边形转线要素'),
            ('change_map_tool', FIF.SYNC, '变更上图工具', '变更上图完整工作流'),
            ('organize_fields', FIF.DOCUMENT, '字段整理', '整理要素字段结构'),
            ('spatial_join_fields', FIF.GLOBE, '空间挂接字段', '空间挂接要素字段'),
            
            # 格式转换类
            ('dxf_convert', FIF.DOCUMENT, 'DXF转SHP', 'DXF图层转SHP'),
            ('shp_to_kmz', FIF.FOLDER, 'SHP转KMZ', '转奥维地图格式'),
            ('kmz_to_shp', FIF.FOLDER, 'KMZ转SHP', '奥维格式转SHP'),
            ('shp_to_wkt', FIF.CODE, 'SHP转WKT', '转WKT文本格式'),
            ('wkt_to_shp', FIF.CODE, 'WKT转SHP', 'WKT转矢量文件'),
            ('land_department_coords', FIF.DOCUMENT, '征地部坐标转换', '征地部坐标转SHP'),
            
            # 投影处理类
            ('projection', FIF.GLOBE, '投影转换', '修改定义数据投影'),
            
            # 影像处理类
            ('image_mosaic', FIF.PHOTO, '影像拼接', '多影像拼接'),
            ('image_crop', FIF.CUT, '影像裁剪', '矢量裁剪影像'),
            ('image_crop_by_admin_region', FIF.CUT, '影像裁剪-行政区', '按行政区裁剪影像'),
            
            # 坐标处理类
            ('center_point', FIF.PIN, '获取中心点', '获取要素中心坐标'),
            ('coords_to_shp', FIF.PIN, '坐标转SHP', '坐标点转矢量'),
            
            # 文件处理类
            ('file_stat', FIF.FOLDER, '文件统计', '统计文件信息'),
            ('move_copy', FIF.MOVE, '移动复制', '移动复制文件'),
            ('data_process', FIF.ALIGNMENT, '数据处理', '单数据多信息处理'),
            ('batch_rename', FIF.EDIT, '批量重命名', '批量重命名文件'),
            ('batch_change_extension', FIF.EDIT, '批量修改后缀', '批量修改后缀'),
            ('batch_copy_move', FIF.SYNC, '批量操作', '批量复制移动'),
            ('file_folder_content_modifier', FIF.EDIT, '文件内容修改', '修改文件名称内容'),
            
            # 数据分析类
            ('file_table_compare', FIF.SEARCH, '表格比对', '比对Excel表格'),
            ('trial_plan_summary', FIF.DOCUMENT, '试划成果统计', '管理边界面积计算'),
            ('feature_check', FIF.CHECKBOX, '要素常规检查', '检查要素问题'),
            
            # 文档工具类
            ('pdf_tools', FIF.DOCUMENT, 'PDF工具', 'PDF合并分离转换'),
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
