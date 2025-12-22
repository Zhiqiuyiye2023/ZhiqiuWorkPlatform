# coding:utf-8
import sys
import os

# 确保可以导入上级目录的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import geopandas as gpd
from shapely.geometry import GeometryCollection

class EraseAnalysis:
    """
    擦除分析功能类
    提供矢量图层擦除分析的核心功能
    擦除操作从第一个图层中移除与第二个图层重叠的部分
    """
    
    def __init__(self):
        self.keep_all = True
        self.precision = False
    
    def set_params(self, keep_all=True, precision=False):
        """
        设置擦除分析参数
        
        Args:
            keep_all (bool): 是否保留所有结果
            precision (bool): 是否使用高精度计算
        """
        self.keep_all = keep_all
        self.precision = precision
    
    def perform_erase(self, main_gdf, erase_gdf):
        """
        执行擦除操作
        
        Args:
            main_gdf (GeoDataFrame): 主输入图层（被擦除的图层）
            erase_gdf (GeoDataFrame): 擦除图层（用于擦除主图层的部分）
            
        Returns:
            GeoDataFrame: 擦除结果图层
        """
        if main_gdf is None or erase_gdf is None:
            print("警告：输入图层为空")
            return None
        
        # 检查并确保两个图层使用相同的坐标系
        try:
            # 如果第一个图层没有坐标系统，尝试使用第二个图层的
            if main_gdf.crs is None:
                print("警告：主图层没有定义坐标系，尝试使用擦除图层的坐标系")
                if erase_gdf.crs is not None:
                    main_gdf = main_gdf.set_crs(erase_gdf.crs)
            # 如果第二个图层没有坐标系统，使用第一个图层的
            elif erase_gdf.crs is None:
                print("警告：擦除图层没有定义坐标系，使用主图层的坐标系")
                erase_gdf = erase_gdf.set_crs(main_gdf.crs)
            # 检查坐标系统是否匹配
            elif main_gdf.crs != erase_gdf.crs:
                print(f"坐标系不匹配：{main_gdf.crs} != {erase_gdf.crs}")
                return None
            
            # 打印图层信息
            print(f"主图层信息：类型={main_gdf.geometry.type.iloc[0] if not main_gdf.empty else '空'}, \
                  特征数={len(main_gdf)}, 列={list(main_gdf.columns)}")
            print(f"擦除图层信息：类型={erase_gdf.geometry.type.iloc[0] if not erase_gdf.empty else '空'}, \
                  特征数={len(erase_gdf)}, 列={list(erase_gdf.columns)}")
            
            # 执行擦除操作 (使用difference叠加操作)
            erase_result = gpd.overlay(main_gdf, erase_gdf, how='difference')
            print(f"擦除结果特征数：{len(erase_result)}")
            
            if erase_result.empty:
                print("警告：擦除结果为空，两个图层可能没有重叠区域或主图层完全被擦除")
            else:
                print(f"擦除结果列：{list(erase_result.columns)}")
            
            return erase_result
            
        except Exception as e:
            print(f"执行擦除操作时发生错误：{e}")
            # 尝试使用替代方法
            try:
                # 首先确保擦除图层是一个有效的GeoDataFrame
                if erase_gdf is not None and not erase_gdf.empty:
                    # 创建一个单一的多边形覆盖所有擦除区域
                    erase_geom = erase_gdf.unary_union
                    # 对主图层中的每个几何对象应用difference操作
                    main_gdf['geometry'] = main_gdf.geometry.difference(erase_geom)
                    # 移除空几何对象
                    erase_result = main_gdf[~main_gdf.geometry.is_empty]
                    print("使用替代方法完成擦除操作")
                    return erase_result
                else:
                    print("擦除图层无效，无法执行擦除操作")
                    return None
            except Exception as inner_e:
                print(f"替代方法也失败：{inner_e}")
                return None
    
    def process_input_data(self, input_data):
        """
        处理输入数据，提取所有可用的图层
        
        Args:
            input_data (list): 输入数据列表
            
        Returns:
            list: 提取的图层数据列表 [(gdf, source), ...]
        """
        all_layer_data = []
        
        # 遍历所有输入数据，收集其中的所有图层
        for data_item in input_data:
            if isinstance(data_item, dict) and "layer_data" in data_item:
                layer_data_list = data_item["layer_data"]
                for layer in layer_data_list:
                    gdf = layer.get("data")
                    source = layer.get("source")
                    if gdf is not None:
                        all_layer_data.append((gdf, source))
        
        return all_layer_data
    
    def validate_inputs(self, layer_data):
        """
        验证输入是否满足擦除分析的要求
        
        Args:
            layer_data (list): 图层数据列表
            
        Returns:
            tuple: (is_valid, message)
        """
        if len(layer_data) < 2:
            return False, f"擦除操作需要至少两个矢量图层，当前可用图层数: {len(layer_data)}"
        
        # 检查图层是否包含有效的几何数据
        for i, (gdf, _) in enumerate(layer_data[:2]):
            if gdf is None or gdf.empty:
                return False, f"图层 {i+1} 为空或无效"
            if 'geometry' not in gdf.columns:
                return False, f"图层 {i+1} 没有几何列"
        
        return True, ""

# 示例使用
def main():
    # 示例代码，展示如何使用擦除分析类
    erase_analyzer = EraseAnalysis()
    erase_analyzer.set_params(keep_all=True, precision=True)
    
    print("擦除分析模块已加载")
    print("使用示例:")
    print("1. 创建分析实例: analyzer = EraseAnalysis()")
    print("2. 设置参数: analyzer.set_params(keep_all=True, precision=False)")
    print("3. 处理输入数据: layer_data = analyzer.process_input_data(input_data)")
    print("4. 验证输入: is_valid, message = analyzer.validate_inputs(layer_data)")
    print("5. 执行擦除: result = analyzer.perform_erase(main_gdf, erase_gdf)")

if __name__ == "__main__":
    main()