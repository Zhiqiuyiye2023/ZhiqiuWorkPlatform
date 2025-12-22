# coding:utf-8
"""
gis_workflow - GIS工作流相关功能模块

此包包含GIS工作流中的核心功能模块，如投影转换、相交分析、字段筛选和定义查询等。
"""

# 导出主要类和函数
from .投影转换 import 定义数据投影, 修改数据投影, epsg_codes
try:
    from .相交分析 import IntersectAnalysis, 相交分析
    INTERSECT_AVAILABLE = True
except ImportError:
    INTERSECT_AVAILABLE = False

try:
    from .擦除分析 import EraseAnalysis, 擦除分析
    ERASE_AVAILABLE = True
except ImportError:
    ERASE_AVAILABLE = False

try:
    from .标识分析 import IdentityAnalysis, 标识分析
    IDENTITY_AVAILABLE = True
except ImportError:
    IDENTITY_AVAILABLE = False

try:
    from .融合分析 import UnionAnalysis, 融合分析
    UNION_AVAILABLE = True
except ImportError:
    UNION_AVAILABLE = False

# 导出字段筛选模块中的类和函数
from .字段筛选 import 字段筛选, 获取所有字段, FieldFilter

__all__ = [
    '定义数据投影', '修改数据投影', 'epsg_codes',
    'IntersectAnalysis', '相交分析', 'INTERSECT_AVAILABLE',
    'EraseAnalysis', '擦除分析', 'ERASE_AVAILABLE',
    'IdentityAnalysis', '标识分析', 'IDENTITY_AVAILABLE',
    'UnionAnalysis', '融合分析', 'UNION_AVAILABLE',
    '字段筛选', '获取所有字段', 'FieldFilter'
]
__version__ = '1.0.0'