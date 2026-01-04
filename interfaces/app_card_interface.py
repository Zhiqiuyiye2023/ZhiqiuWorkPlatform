# coding:utf-8
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtGui import QFont
from qfluentwidgets import (ScrollArea, FlowLayout, CardWidget, IconWidget, 
                            BodyLabel, CaptionLabel, PrimaryPushButton, isDarkTheme, Theme)
from qfluentwidgets import FluentIcon as FIF
from configs.config import cfg


class AppCard(CardWidget):
    """应用卡片"""
    clicked = pyqtSignal(str)  # 发送应用ID
    
    def __init__(self, app_id: str, icon, title: str, description: str, parent=None):
        super().__init__(parent)
        self.app_id = app_id
        self.setFixedSize(200, 90)  # 减小卡片尺寸，使其更紧凑
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 创建布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(12, 12, 12, 12)  # 调整边距，减小内边距
        self.vBoxLayout.setSpacing(0)  # 重置整体间距，通过spacer精确控制
        
        # 图标
        self.iconWidget = IconWidget(icon, self)
        self.iconWidget.setFixedSize(24, 24)  # 减小图标大小，更适合紧凑布局
        
        # 标题
        self.titleLabel = BodyLabel(title, self)
        self.titleLabel.setFont(QFont('Microsoft YaHei', 10, QFont.Weight.DemiBold))  # 保持字体大小
        self.titleLabel.setWordWrap(True)  # 标题允许换行
        self.titleLabel.setMaximumHeight(22)  # 调整标题高度
        
        # 描述
        self.descLabel = CaptionLabel(description, self)
        self.descLabel.setWordWrap(True)  # 描述允许换行
        self.descLabel.setFixedHeight(30)  # 减小描述区域高度
        self.descLabel.setStyleSheet("QLabel { font-size: 8px; line-height: 12px; }")  # 调整描述字体大小和行高
        
        # 添加到布局
        self.vBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignmentFlag.AlignLeft)
        # 图标与标题之间的间距
        self.vBoxLayout.addSpacing(8)
        self.vBoxLayout.addWidget(self.titleLabel)
        # 标题与描述之间的间距
        self.vBoxLayout.addSpacing(6)
        self.vBoxLayout.addWidget(self.descLabel)
        self.vBoxLayout.addStretch(1)
        
        # 移除阴影效果，使用简约样式
        self.shadow_effect = None
        
        # 连接主题变化信号，实现自动跟随系统主题
        cfg.themeChanged.connect(self._onThemeChanged)
        
        # 初始化时应用一次主题样式
        self._onThemeChanged()
    
    def _onThemeChanged(self):
        """主题变化时更新卡片样式"""
        if isDarkTheme():
            # 深色主题样式 - 简约设计，无阴影
            self.setStyleSheet("""
                AppCard {
                    background-color: #2d2d2d;
                    border-radius: 10px;
                    border: 1px solid #3d3d3d;
                    color: #ffffff;
                    transition: background-color 0.3s ease;
                }
                AppCard:hover {
                    background-color: #3a3a3a;
                    border: 1px solid #4d4d4d;
                }
            """)
            # 标题使用更亮的白色，提高可读性
            self.titleLabel.setStyleSheet("color: #ffffff;")
            # 描述使用柔和的浅灰色，确保与背景有足够的对比度
            self.descLabel.setStyleSheet("color: #cccccc;")
        else:
            # 浅色主题样式 - 简约设计，无阴影
            self.setStyleSheet("""
                AppCard {
                    background-color: #ffffff;
                    border-radius: 10px;
                    border: 1px solid #e0e0e0;
                    color: #333333;
                    transition: background-color 0.3s ease;
                }
                AppCard:hover {
                    background-color: #f8f8f8;
                    border: 1px solid #d0d0d0;
                }
            """)
            # 标题使用深灰色而非纯黑色，视觉更舒适
            self.titleLabel.setStyleSheet("color: #333333;")
            # 描述使用中等灰色，确保可读性同时不抢夺标题的注意力
            self.descLabel.setStyleSheet("color: #666666;")
        
    def mousePressEvent(self, e):
        """鼠标按下事件 - 仅处理基本事件，不发送点击信号"""
        super().mousePressEvent(e)
    
    def mouseReleaseEvent(self, e):
        """鼠标释放事件 - 完全覆盖父类行为，避免信号冲突"""
        # 不调用父类的mouseReleaseEvent，完全防止冲突
        # 只发出我们自己的带有app_id参数的clicked信号
        self.clicked.emit(self.app_id)
        # 调用QWidget的mouseReleaseEvent确保基本功能正常
        super(CardWidget, self).mouseReleaseEvent(e)


class GroupTitle(QWidget):
    """分组标题"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.titleLabel = QLabel(title, self)
        self.titleLabel.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Bold))
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 10)
        layout.addWidget(self.titleLabel)
        layout.addStretch(1)
        
        # 连接主题变化信号
        cfg.themeChanged.connect(self._onThemeChanged)
        self._onThemeChanged()
    
    def _onThemeChanged(self):
        """主题变化时更新标题样式"""
        if isDarkTheme():
            self.titleLabel.setStyleSheet("color: #ffffff; border-bottom: 2px solid #4d4d4d;")
        else:
            self.titleLabel.setStyleSheet("color: #333333; border-bottom: 2px solid #e0e0e0;")


class AppCardInterface(ScrollArea):
    """应用卡片展示界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)
        
        # 设置滚动区域
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setObjectName('appCardInterface')
        
        # 设置样式
        self.view.setStyleSheet("QWidget{background:transparent}")
        self.vBoxLayout.setContentsMargins(20, 20, 20, 20)  # 调整边距
        self.vBoxLayout.setSpacing(5)  # 调整间距
        
        # 存储所有卡片信息
        self.allApps = [
            # 矢量处理类
            ('vector', '矢量处理', [
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
                ('eliminate_overlap', FIF.DELETE, '要素去重叠', '移除要素重叠区域并保留边界'),
                ('feature_intersection', FIF.LAYOUT, '要素相交', '检测要素重叠区域，输出相交结果'),
            ]),
            # 格式转换类
            ('format', '格式转换', [
                ('dxf_convert', FIF.DOCUMENT, 'DXF转SHP', 'DXF图层转SHP'),
                ('shp_to_kmz', FIF.FOLDER, 'SHP转KMZ', '转奥维地图格式'),
                ('kmz_to_shp', FIF.FOLDER, 'KMZ转SHP', '奥维格式转SHP'),
                ('shp_to_wkt', FIF.CODE, 'SHP转WKT', '转WKT文本格式'),
                ('wkt_to_shp', FIF.CODE, 'WKT转SHP', 'WKT转矢量文件'),
                ('land_department_coords', FIF.DOCUMENT, '征地部坐标转换', '征地部坐标转SHP'),
            ]),
            # 投影处理类
            ('projection', '投影处理', [
                ('projection', FIF.GLOBE, '投影转换', '修改定义数据投影'),
            ]),
            # 影像处理类
            ('image', '影像处理', [
                ('image_mosaic', FIF.PHOTO, '影像拼接', '多影像拼接'),
                ('image_crop', FIF.CUT, '影像裁剪', '矢量裁剪影像'),
                ('image_crop_by_admin_region', FIF.CUT, '影像裁剪-行政区', '按行政区裁剪影像'),
            ]),
            # 坐标处理类
            ('coordinate', '坐标处理', [
                ('center_point', FIF.PIN, '获取中心点', '获取要素中心坐标'),
                ('coords_to_shp', FIF.PIN, '坐标转SHP', '坐标点转矢量'),
            ]),
            # 文件处理类
            ('file', '文件处理', [
                ('file_stat', FIF.FOLDER, '文件统计', '统计文件信息'),
                ('move_copy', FIF.MOVE, '移动复制', '移动复制文件'),
                ('data_process', FIF.ALIGNMENT, '数据处理', '单数据多信息处理'),
                ('batch_rename', FIF.EDIT, '批量重命名', '批量重命名文件'),
                ('batch_change_extension', FIF.EDIT, '批量修改后缀', '批量修改后缀'),
                ('batch_copy_move', FIF.SYNC, '批量操作', '批量复制移动'),
                ('file_folder_content_modifier', FIF.EDIT, '文件内容修改', '修改文件名称内容'),
            ]),
            # 数据分析类
            ('analysis', '数据分析', [
                ('file_table_compare', FIF.SEARCH, '表格比对', '比对Excel表格'),
                ('trial_plan_summary', FIF.DOCUMENT, '试划成果统计', '管理边界面积计算'),
                ('feature_check', FIF.CHECKBOX, '要素常规检查', '检查要素问题'),
            ]),
            # 文档工具类
            ('document', '文档工具', [
                ('pdf_tools', FIF.DOCUMENT, 'PDF工具', 'PDF合并分离转换'),
            ]),
        ]
        
        # 初始化应用卡片
        self.initCards()
        
        # 监听主题变化
        cfg.themeChanged.connect(self._onThemeChanged)
        
        # 应用初始主题
        self._onThemeChanged()
    
    def _onThemeChanged(self):
        """主题变化时更新背景色"""
        if isDarkTheme():
            self.setStyleSheet("AppCardInterface { background-color: #1e1e1e; border: none; }")
        else:
            self.setStyleSheet("AppCardInterface { background-color: #f3f3f3; border: none; }")
        
    def initCards(self):
        """初始化应用卡片"""
        for group_id, group_title, apps in self.allApps:
            # 添加分组标题
            group_title_widget = GroupTitle(group_title, self.view)
            self.vBoxLayout.addWidget(group_title_widget)
            
            # 创建该组的卡片容器
            group_container = QWidget(self.view)
            group_layout = FlowLayout(group_container, needAni=True)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setHorizontalSpacing(20)  # 调整水平间距
            group_layout.setVerticalSpacing(20)  # 调整垂直间距
            
            # 添加卡片到组
            for app_id, icon, title, desc in apps:
                card = AppCard(app_id, icon, title, desc, group_container)
                card.clicked.connect(self.onCardClicked)
                group_layout.addWidget(card)
            
            # 添加组容器到主布局
            self.vBoxLayout.addWidget(group_container)
        
        self.vBoxLayout.addStretch(1)
    
    def onCardClicked(self, app_id: str):
        """处理卡片点击事件"""
        # 导入应用功能管理器
        from app_functions import AppFunctionManager
        AppFunctionManager.openApp(app_id, self)
    
    def filterCards(self, keyword: str):
        """根据关键字过滤卡片"""
        keyword = keyword.lower()
        
        # 遍历所有分组
        for i in range(self.vBoxLayout.count()):
            item = self.vBoxLayout.itemAt(i)
            if item is None:
                continue
                
            widget = item.widget()
            if isinstance(widget, GroupTitle):
                # 分组标题，跳过
                continue
            elif widget and hasattr(widget, 'layout'):
                # 分组容器
                flowLayout = widget.layout()
                if flowLayout:
                    group_visible_count = 0
                    
                    # 检查该组内的所有卡片
                    for j in range(flowLayout.count()):
                        card_item = flowLayout.itemAt(j)
                        if card_item is None:
                            continue
                            
                        card_widget = card_item.widget()
                        if isinstance(card_widget, AppCard):
                            title = card_widget.titleLabel.text().lower()
                            desc = card_widget.descLabel.text().lower()
                            
                            # 显示或隐藏卡片
                            if keyword in title or keyword in desc or not keyword:
                                card_widget.show()
                                group_visible_count += 1
                            else:
                                card_widget.hide()
                    
                    # 如果该组没有任何可见卡片，则隐藏整个分组（包括标题）
                    group_title_widget = self.vBoxLayout.itemAt(i-1).widget() if i > 0 else None
                    if group_title_widget and isinstance(group_title_widget, GroupTitle):
                        if group_visible_count > 0 or not keyword:
                            group_title_widget.show()
                            widget.show()
                        else:
                            group_title_widget.hide()
                            widget.hide()
