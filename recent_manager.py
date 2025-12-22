# coding:utf-8
"""
最近使用管理器
集中管理应用的最近使用记录
"""

import json
import os
from datetime import datetime


class RecentAppsManager:
    """最近使用应用管理器（单例模式）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        # 将recent_apps.json保存到用户目录的configs文件夹中
        user_dir = os.path.expanduser('~')
        config_dir = os.path.join(user_dir, '知秋工作平台', 'configs')
        self.recent_file = os.path.join(config_dir, 'recent_apps.json')
        
        # 确保configs文件夹存在
        os.makedirs(config_dir, exist_ok=True)
        
        # 应用标题映射
        self.app_titles = {
            'data_overlay': '数据叠加套合',
            'field_split': '字段分离要素',
            'area_adjust': '面积调整要素',
            'projection': '投影转换',
            'dxf_convert': 'DXF转SHP',
            'merge_features': '合并要素',
            'shp_to_kmz': 'SHP转KMZ',
            'kmz_to_shp': 'KMZ转SHP',
            'shp_to_wkt': 'SHP转WKT',
            'wkt_to_shp': 'WKT转SHP',
            'pdf_tools': 'PDF工具',
            'image_mosaic': '影像拼接',
            'center_point': '获取中心点',
            'image_crop': '影像裁剪',
            'image_crop_by_admin_region': '影像裁剪-行政区',
            'coords_to_shp': '坐标转SHP',
            'land_department_coords': '征地部坐标转换',
            'file_stat': '文件统计',
            'move_copy': '移动复制',
            'data_process': '数据处理',
            'batch_rename': '批量重命名',
            'batch_change_extension': '批量修改后缀',
            'batch_copy_move': '批量操作',
            'file_table_compare': '表格比对',
            'file_folder_content_modifier': '文件与文件夹内容修改',
            'dissolve_features': '融合要素',
            'identify_features': '标识卡片',
            'trial_plan_summary': '试划成果总结统计',
            'feature_check': '要素常规检查',
        }
        
        # 应用图标映射
        self.app_icons = {
            'data_overlay': 'TILES',
            'field_split': 'CUT',
            'area_adjust': 'ZOOM',
            'projection': 'GLOBE',
            'dxf_convert': 'DOCUMENT',
            'merge_features': 'ACCEPT',
            'dissolve_features': 'ACCEPT',
            'shp_to_kmz': 'FOLDER',
            'kmz_to_shp': 'FOLDER',
            'shp_to_wkt': 'CODE',
            'wkt_to_shp': 'CODE',
            'pdf_tools': 'DOCUMENT',
            'image_mosaic': 'PHOTO',
            'center_point': 'PIN',
            'image_crop': 'CUT',
            'image_crop_by_admin_region': 'CUT',
            'coords_to_shp': 'PIN',
            'land_department_coords': 'DOCUMENT',
            'file_stat': 'FOLDER',
            'move_copy': 'MOVE',
            'data_process': 'ALIGNMENT',
            'batch_rename': 'EDIT',
            'batch_change_extension': 'EDIT',
            'batch_copy_move': 'SYNC',
            'file_table_compare': 'SEARCH',
            'file_folder_content_modifier': 'EDIT',
            'identify_features': 'MARKET',
            'trial_plan_summary': 'DOCUMENT',
            'feature_check': 'CHECK',
        }
    
    def add_recent_app(self, app_id: str):
        """添加最近使用的应用"""
        title = self.app_titles.get(app_id, app_id)
        icon_name = self.app_icons.get(app_id, 'APPLICATION')
        
        recent_apps = self.load_recent_apps()
        
        # 移除旧条目（如果存在）
        recent_apps = [item for item in recent_apps if item[0] != app_id]
        
        # 添加新条目到开头，记录实际的使用时间
        now = datetime.now()
        time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        recent_apps.insert(0, (app_id, icon_name, title, time_str))
        
        # 只保留前3个
        recent_apps = recent_apps[:3]
        
        # 保存到文件
        self.save_recent_apps(recent_apps)
        
        print(f"✅ 已添加到最近使用: {title} - {time_str}")
    
    def load_recent_apps(self):
        """加载最近使用的应用"""
        if not os.path.exists(self.recent_file):
            # 返回默认数据，只返回3条记录
            return [
                ('data_overlay', 'TILES', '数据叠加套合', '2小时前'),
                ('field_split', 'CUT', '字段分离要素', '5小时前'),
                ('image_mosaic', 'PHOTO', '影像拼接', '昨天 14:30'),
            ]
        
        try:
            with open(self.recent_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                recent_apps = data.get('recent_apps', [])
                
                # 将保存的实际时间转换为用户友好的时间字符串
                now = datetime.now()
                for i, item in enumerate(recent_apps):
                    app_id, icon_name, title, time_str = item
                    # 尝试解析时间字符串
                    try:
                        used_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                        # 计算时间差
                        delta = now - used_time
                        seconds = delta.total_seconds()
                        
                        if seconds < 60:
                            # 1分钟内显示"刚刚"
                            friendly_time = "刚刚"
                        elif seconds < 3600:
                            # 1小时内显示"X分钟前"
                            minutes = int(seconds // 60)
                            friendly_time = f"{minutes}分钟前"
                        elif seconds < 86400:
                            # 24小时内显示"X小时前"
                            hours = int(seconds // 3600)
                            friendly_time = f"{hours}小时前"
                        elif seconds < 172800:
                            # 48小时内显示"昨天 HH:MM"
                            friendly_time = f"昨天 {used_time.strftime('%H:%M')}"
                        elif seconds < 2592000:
                            # 30天内显示"X天前"
                            days = int(seconds // 86400)
                            friendly_time = f"{days}天前"
                        else:
                            # 超过30天显示"YYYY-MM-DD"
                            friendly_time = used_time.strftime('%Y-%m-%d')
                        
                        # 更新时间字符串为友好格式
                        recent_apps[i] = (app_id, icon_name, title, friendly_time)
                    except:
                        # 如果解析失败，保留原时间字符串
                        pass
                
                return recent_apps
        except:
            return []
    
    def save_recent_apps(self, recent_apps):
        """保存最近使用的应用"""
        try:
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                json.dump({'recent_apps': recent_apps}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存最近使用失败: {e}")


# 创建全局单例
recent_manager = RecentAppsManager()