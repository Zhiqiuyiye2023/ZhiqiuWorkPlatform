# coding:utf-8
"""
批量创建功能模块文件的脚本
运行此脚本将自动创建所有缺失的功能模块
"""

import os

# 功能模块配置
FUNCTIONS = [
    {
        'filename': 'area_adjust.py',
        'class_name': 'AreaAdjustFunction',
        'title': '根据指定面积调整要素',
        'description': '根据指定面积缩放或缓冲调整要素',
    },
    {
        'filename': 'projection.py',
        'class_name': 'ProjectionFunction',
        'title': '修改与定义数据投影',
        'description': '修改数据投影坐标系或定义无投影数据',
    },
    {
        'filename': 'dxf_convert.py',
        'class_name': 'DxfConvertFunction',
        'title': 'DXF转SHP',
        'description': '提取DXF指定图层面要素转SHP格式',
    },
    {
        'filename': 'merge_features.py',
        'class_name': 'MergeFeaturesFunction',
        'title': '合并指定目录中的所有要素',
        'description': '合并目录及子目录中的所有要素文件',
    },
    {
        'filename': 'shp_to_kmz.py',
        'class_name': 'ShpToKmzFunction',
        'title': 'SHP转KMZ奥维格式',
        'description': '将SHP文件转换为KMZ奥维地图格式',
    },
    {
        'filename': 'shp_to_wkt.py',
        'class_name': 'ShpToWktFunction',
        'title': 'SHP转WKT文本格式',
        'description': '将SHP文件转换为WKT文本格式（含ZIP）',
    },
    {
        'filename': 'pdf_tools.py',
        'class_name': 'PdfToolsFunction',
        'title': 'PDF文件处理功能',
        'description': 'PDF合并、分离、转图片、图片转PDF',
    },
    {
        'filename': 'image_mosaic.py',
        'class_name': 'ImageMosaicFunction',
        'title': '影像拼接功能',
        'description': '多影像文件拼接处理',
    },
    {
        'filename': 'center_point.py',
        'class_name': 'CenterPointFunction',
        'title': '获取矢量要素中心点',
        'description': '获取矢量要素的中心点坐标',
    },
    {
        'filename': 'image_crop.py',
        'class_name': 'ImageCropFunction',
        'title': '影像裁剪功能',
        'description': '根据矢量范围裁剪影像',
    },
    {
        'filename': 'coords_to_shp.py',
        'class_name': 'CoordsToShpFunction',
        'title': '坐标转SHP',
        'description': '将坐标点转换为矢量文件',
    },
]

# 模板代码
TEMPLATE = '''# coding:utf-8
"""
{title}功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QFileDialog, QMessageBox
from qfluentwidgets import LineEdit, PushButton, TextEdit
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import threading


class {class_name}(BaseFunction):
    """{title}功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "{description}<br>"
            "此功能正在实现中，完整功能请参考'数据处理'页面"
        )
        super().__init__("{title}", description, parent)
        
        self._initUI()
        self.addExecuteButton("开始执行", self.execute)
    
    def _initUI(self):
        """初始化界面"""
        # 示例：文件选择
        row = QHBoxLayout()
        row.addWidget(QLabel("输入文件："))
        
        self.fileBtn = PushButton("选择文件", self, FIF.DOCUMENT)
        self.fileBtn.clicked.connect(self._selectFile)
        self.fileBtn.setFixedWidth(100)
        
        self.filePath = LineEdit(self)
        self.filePath.setPlaceholderText("点击按钮选择文件")
        self.filePath.setReadOnly(True)
        
        row.addWidget(self.fileBtn)
        row.addWidget(self.filePath, 1)
        self.contentLayout.addLayout(row)
        
        # 结果显示（可选）
        self.resultText = TextEdit(self)
        self.resultText.setReadOnly(True)
        self.resultText.setPlaceholderText("处理结果将显示在这里...")
        self.resultText.setFixedHeight(150)
        self.contentLayout.addWidget(self.resultText)
    
    def _selectFile(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", 
            "所有支持的文件 (*.shp *.tif *.pdf *.xlsx);;所有文件 (*.*)"
        )
        if file_path:
            self.filePath.setText(file_path)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.filePath.text():
            return False, "请选择输入文件"
        return True, ""
    
    def execute(self):
        """执行功能"""
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        # 提示：功能需要从数据处理.py迁移
        QMessageBox.information(
            self, 
            "提示", 
            "此功能正在实现中\\n\\n"
            "完整功能请前往侧边栏的'数据处理'页面使用\\n"
            "或参考 functions/功能模块模板.py 实现此功能"
        )
'''


def create_function_files():
    """创建所有功能模块文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    created = []
    skipped = []
    
    for func in FUNCTIONS:
        filepath = os.path.join(current_dir, func['filename'])
        
        # 检查文件是否已存在
        if os.path.exists(filepath):
            skipped.append(func['filename'])
            continue
        
        # 生成代码
        code = TEMPLATE.format(
            title=func['title'],
            class_name=func['class_name'],
            description=func['description']
        )
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        
        created.append(func['filename'])
        print(f"✓ 已创建: {func['filename']}")
    
    # 输出统计
    print(f"\n{'='*50}")
    print(f"创建完成！")
    print(f"新创建: {len(created)} 个文件")
    print(f"已跳过: {len(skipped)} 个文件（已存在）")
    print(f"{'='*50}\n")
    
    if created:
        print("新创建的文件：")
        for filename in created:
            print(f"  - {filename}")
    
    if skipped:
        print("\n已存在的文件：")
        for filename in skipped:
            print(f"  - {filename}")


if __name__ == '__main__':
    print("开始创建功能模块文件...\n")
    create_function_files()
    print("\n完成！所有功能模块文件已就绪。")
