# app_functions.py - 应用功能管理模块
# 用于管理YOLO工具箱和GIS工作流界面的各种功能
import os
from recent_manager import recent_manager
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from qfluentwidgets import FluentWindow, InfoBar, InfoBarPosition

class FunctionWidgetFactory:
    """功能组件工厂"""
    
    @staticmethod
    def create_widget(app_id: str):
        """根据app_id创建对应的功能widget"""
        try:
            # 动态导入对应模块
            print(f"尝试创建功能模块: {app_id}")
            if app_id == 'data_overlay':
                from functions.data_overlay import DataOverlayFunction
                return DataOverlayFunction()
            
            elif app_id == 'field_split':
                from functions.field_split import FieldSplitFunction
                return FieldSplitFunction()
            
            elif app_id == 'projection':
                from functions.projection import ProjectionFunction
                return ProjectionFunction()
                
            elif app_id == 'area_adjust':
                from functions.area_adjust import AreaAdjustFunction
                return AreaAdjustFunction()
                
            elif app_id == 'dxf_convert':
                from functions.dxf_convert import DxfConvertFunction
                return DxfConvertFunction()
                
            elif app_id == 'merge_features':
                from functions.merge_features import MergeFeaturesFunction
                return MergeFeaturesFunction()
            
            elif app_id == 'dissolve_features':
                from functions.dissolve_features import DissolveFeaturesFunction
                return DissolveFeaturesFunction()
            
            elif app_id == 'identify_features':
                from functions.identify_features import IdentifyFeaturesFunction
                return IdentifyFeaturesFunction()
            
            elif app_id == 'shp_to_kmz':
                from functions.shp_to_kmz import ShpToKmzFunction
                return ShpToKmzFunction()
                
            elif app_id == 'kmz_to_shp':
                from functions.kmz_to_shp import KmzToShpFunction
                return KmzToShpFunction()
                
            elif app_id == 'shp_to_wkt':
                from functions.shp_to_wkt import ShpToWktFunction
                return ShpToWktFunction()
                
            elif app_id == 'pdf_tools':
                from functions.pdf_tools import PdfToolsFunction
                return PdfToolsFunction()
                
            elif app_id == 'image_mosaic':
                print("尝试导入 ImageMosaicFunction")
                try:
                    from functions.image_mosaic import ImageMosaicFunction
                    return ImageMosaicFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.image_mosaic')
                    ImageMosaicFunction = getattr(module, 'ImageMosaicFunction')
                    return ImageMosaicFunction()
                
            elif app_id == 'center_point':
                print("尝试导入 CenterPointFunction")
                try:
                    from functions.center_point import CenterPointFunction
                    return CenterPointFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.center_point')
                    CenterPointFunction = getattr(module, 'CenterPointFunction')
                    return CenterPointFunction()
                
            elif app_id == 'image_crop':
                print("尝试导入 ImageCropFunction")
                try:
                    from functions.image_crop import ImageCropFunction
                    return ImageCropFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.image_crop')
                    ImageCropFunction = getattr(module, 'ImageCropFunction')
                    return ImageCropFunction()
                
            elif app_id == 'image_crop_by_admin_region':
                print("尝试导入 ImageCropByAdminRegionFunction")
                try:
                    from functions.image_crop_by_admin_region import ImageCropByAdminRegionFunction
                    return ImageCropByAdminRegionFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.image_crop_by_admin_region')
                    ImageCropByAdminRegionFunction = getattr(module, 'ImageCropByAdminRegionFunction')
                    return ImageCropByAdminRegionFunction()
                
            elif app_id == 'coords_to_shp':
                try:
                    from functions.coords_to_shp import CoordsToShpFunction
                    return CoordsToShpFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.coords_to_shp')
                    CoordsToShpFunction = getattr(module, 'CoordsToShpFunction')
                    return CoordsToShpFunction()
                
            elif app_id == 'wkt_to_shp':
                try:
                    from functions.wkt_to_shp import WktToShpFunction
                    return WktToShpFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.wkt_to_shp')
                    WktToShpFunction = getattr(module, 'WktToShpFunction')
                    return WktToShpFunction()
                
            elif app_id == 'land_department_coords':
                try:
                    from functions.land_department_coords import LandDepartmentCoordsFunction
                    return LandDepartmentCoordsFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.land_department_coords')
                    LandDepartmentCoordsFunction = getattr(module, 'LandDepartmentCoordsFunction')
                    return LandDepartmentCoordsFunction()
                

                
            elif app_id == 'trial_plan_summary':
                try:
                    from functions.trial_plan_summary import TrialPlanSummaryFunction
                    return TrialPlanSummaryFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.trial_plan_summary')
                    TrialPlanSummaryFunction = getattr(module, 'TrialPlanSummaryFunction')
                    return TrialPlanSummaryFunction()
                
            elif app_id == 'feature_check':
                try:
                    from functions.feature_check import FeatureCheckFunction
                    return FeatureCheckFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.feature_check')
                    FeatureCheckFunction = getattr(module, 'FeatureCheckFunction')
                    return FeatureCheckFunction()
                
            # 文件处理功能
            elif app_id == 'file_stat':
                # 文件统计功能
                try:
                    from functions.file_stat import FileStatFunction
                    return FileStatFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.file_stat')
                    FileStatFunction = getattr(module, 'FileStatFunction')
                    return FileStatFunction()
                
            elif app_id == 'move_copy':
                # 移动复制功能
                try:
                    from functions.move_copy import MoveCopyFunction
                    return MoveCopyFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.move_copy')
                    MoveCopyFunction = getattr(module, 'MoveCopyFunction')
                    return MoveCopyFunction()
                
            elif app_id == 'data_process':
                # 数据处理功能
                try:
                    from functions.data_process import DataProcessFunction
                    return DataProcessFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.data_process')
                    DataProcessFunction = getattr(module, 'DataProcessFunction')
                    return DataProcessFunction()
                
            elif app_id == 'batch_rename':
                # 批量重命名功能
                try:
                    from functions.batch_rename import BatchRenameFunction
                    return BatchRenameFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.batch_rename')
                    BatchRenameFunction = getattr(module, 'BatchRenameFunction')
                    return BatchRenameFunction()
                
            elif app_id == 'batch_change_extension':
                # 批量修改后缀功能
                try:
                    from functions.batch_change_extension import BatchChangeExtensionFunction
                    return BatchChangeExtensionFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.batch_change_extension')
                    BatchChangeExtensionFunction = getattr(module, 'BatchChangeExtensionFunction')
                    return BatchChangeExtensionFunction()
                
            elif app_id == 'batch_copy_move':
                # 批量操作功能
                try:
                    from functions.batch_copy_move import BatchCopyMoveFunction
                    return BatchCopyMoveFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.batch_copy_move')
                    BatchCopyMoveFunction = getattr(module, 'BatchCopyMoveFunction')
                    return BatchCopyMoveFunction()
                
            elif app_id == 'file_table_compare':
                # 文件表格比对功能
                try:
                    from functions.file_table_compare import FileTableCompareFunction
                    return FileTableCompareFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.file_table_compare')
                    FileTableCompareFunction = getattr(module, 'FileTableCompareFunction')
                    return FileTableCompareFunction()
                
            elif app_id == 'file_folder_content_modifier':
                # 文件与文件夹内容修改功能
                try:
                    from functions.file_folder_content_modifier import FileFolderContentModifierFunction
                    return FileFolderContentModifierFunction()
                except Exception as e:
                    print(f"直接导入失败，尝试动态导入: {e}")
                    # 动态导入
                    import importlib
                    module = importlib.import_module('functions.file_folder_content_modifier')
                    FileFolderContentModifierFunction = getattr(module, 'FileFolderContentModifierFunction')
                    return FileFolderContentModifierFunction()
            
            else:
                print(f"未找到对应的功能模块: {app_id}")
                return FunctionWidgetFactory._create_placeholder(app_id)
                
        except Exception as e:
            print(f"创建功能模块 {app_id} 失败: {e}")
            import traceback
            traceback.print_exc()
            return FunctionWidgetFactory._create_placeholder(app_id)
    
    @staticmethod
    def _create_placeholder(app_id: str):
        """创建占位符widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(f"功能模块 '{app_id}' 正在开发中...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        return widget


class AppFunctionManager:
    """
    应用功能管理器类
    负责管理应用程序中的各种功能模块和操作
    """
    
    def __init__(self):
        """
        初始化应用功能管理器
        """
        # 功能模块列表
        self.functions = {}
        # 初始化状态
        self.initialized = False
        # 应用配置
        self.config = {}
        # 当前工作目录
        self.work_dir = os.getcwd()
    
    def initialize(self):
        """
        初始化功能管理器
        """
        # 初始化默认功能
        self._register_default_functions()
        # 加载默认配置
        self._load_default_config()
        self.initialized = True
        return True
    
    def _register_default_functions(self):
        """
        注册默认功能模块
        """
        # 注册GIS相关功能
        self.register_function('gis_workflow', {
            'name': 'GIS工作流', 
            'description': '地理信息处理工作流',
            'module': 'GIS',
            'type': 'workflow'
        })
        
        # 注册文件处理功能
        self.register_function('file_processing', {
            'name': '文件处理',
            'description': '影像和地理数据文件处理',
            'module': 'Common',
            'type': 'utility'
        })
        
        # 注册可视化功能
        self.register_function('visualization', {
            'name': '数据可视化',
            'description': '地理数据可视化',
            'module': 'Visualization',
            'type': 'display'
        })
    
    def _load_default_config(self):
        """
        加载默认配置
        """
        self.config = {
            'yolo_models_dir': os.path.join(self.work_dir, 'models'),
            'data_dir': os.path.join(self.work_dir, 'data'),
            'output_dir': os.path.join(self.work_dir, 'output'),
            'temp_dir': os.path.join(self.work_dir, 'temp'),
            'max_file_size': 500 * 1024 * 1024,  # 500MB
            'supported_image_formats': ['.tif', '.tiff', '.jpg', '.jpeg', '.png', '.bmp']
        }
        
        # 确保必要的目录存在
        for dir_key in ['yolo_models_dir', 'data_dir', 'output_dir', 'temp_dir']:
            dir_path = self.config[dir_key]
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
    
    def register_function(self, func_id, func_info):
        """
        注册新功能
        
        Args:
            func_id: 功能ID
            func_info: 功能信息字典
        """
        self.functions[func_id] = func_info
    
    def get_function(self, func_id):
        """
        获取功能信息
        
        Args:
            func_id: 功能ID
            
        Returns:
            功能信息字典，如果不存在返回None
        """
        return self.functions.get(func_id)
    
    def list_functions(self):
        """
        列出所有注册的功能
        
        Returns:
            功能ID列表
        """
        return list(self.functions.keys())
    
    def list_functions_by_category(self, category):
        """
        按类别列出功能
        
        Args:
            category: 功能类别
            
        Returns:
            该类别下的功能ID列表
        """
        result = []
        for func_id, func_info in self.functions.items():
            if func_info.get('module') == category:
                result.append(func_id)
        return result
    
    def is_initialized(self):
        """
        检查功能管理器是否已初始化
        
        Returns:
            是否已初始化
        """
        return self.initialized
    
    def get_config(self, key=None):
        """
        获取配置值
        
        Args:
            key: 配置键名，如果为None则返回所有配置
            
        Returns:
            配置值或配置字典
        """
        if key is None:
            return self.config
        return self.config.get(key)
    
    def set_config(self, key, value):
        """
        设置配置值
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self.config[key] = value
    
    def validate_file_format(self, file_path):
        """
        验证文件格式是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持的文件格式
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.config['supported_image_formats']
    
    def validate_file_size(self, file_path):
        """
        验证文件大小是否符合要求
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否符合文件大小要求
        """
        if not os.path.exists(file_path):
            return False
        file_size = os.path.getsize(file_path)
        return file_size <= self.config['max_file_size']
    
    def get_output_path(self, filename):
        """
        获取输出文件的完整路径
        
        Args:
            filename: 文件名
            
        Returns:
            完整的输出文件路径
        """
        return os.path.join(self.config['output_dir'], filename)
    
    @staticmethod
    def openApp(app_id: str, parent=None):
        """
        打开应用并记录到最近使用
        
        Args:
            app_id: 应用ID
            parent: 父窗口组件
        """
        try:
            # 记录到最近使用
            recent_manager.add_recent_app(app_id)
            print(f"尝试打开应用: {app_id}")
            
            # 使用工厂类创建功能widget
            widget = FunctionWidgetFactory.create_widget(app_id)
            
            # 显示功能widget - 使用独立的弹窗窗口
            if widget:
                from PyQt6.QtWidgets import QDialog, QVBoxLayout
                from PyQt6.QtCore import Qt
                from qfluentwidgets import Theme, setTheme
                from configs.config import cfg
                
                # 安全获取窗口标题
                try:
                    title = widget.title if hasattr(widget, 'title') else app_id.replace('_', ' ').title()
                except Exception as e:
                    title = app_id.replace('_', ' ').title()
                
                # 创建独立的弹窗窗口
                dialog = QDialog(parent)
                dialog.setWindowTitle(title)
                dialog.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | 
                                    Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinMaxButtonsHint)
                
                # 创建布局
                layout = QVBoxLayout(dialog)
                layout.setContentsMargins(0, 0, 0, 0)
                
                # 将功能widget添加到弹窗中
                layout.addWidget(widget)
                
                # 设置弹窗大小
                dialog.resize(800, 600)
                
                # 不强制设置主题，使用应用的全局主题设置
                
                # 根据当前主题设置dialog窗口的背景色
                from qfluentwidgets import isDarkTheme
                if isDarkTheme():
                    dialog.setStyleSheet("background-color: #1e1e1e;")
                else:
                    dialog.setStyleSheet("background-color: #f3f3f3;")
                
                # 监听主题变化，确保dialog背景色同步更新
                def onDialogThemeChanged():
                    if isDarkTheme():
                        dialog.setStyleSheet("background-color: #1e1e1e;")
                    else:
                        dialog.setStyleSheet("background-color: #f3f3f3;")
                
                cfg.themeChanged.connect(onDialogThemeChanged)
                
                # 显示弹窗
                dialog.exec()
            
            return widget
            
        except Exception as e:
            print(f"打开应用失败: {e}")
            import traceback
            traceback.print_exc()
            if parent:
                from PyQt6.QtCore import Qt
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.error(
                    title='打开应用失败',
                    content=f'无法打开应用 {app_id}: {str(e)}',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=parent
                )
            return None
