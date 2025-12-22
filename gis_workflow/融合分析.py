# coding:utf-8
import sys
import os

# 确保可以导入上级目录的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import geopandas as gpd
from shapely.geometry import GeometryCollection

class UnionAnalysis:
    """
    融合分析功能类
    提供矢量图层融合分析的核心功能
    融合操作将两个图层的几何图形合并，去除重叠部分
    """
    
    def __init__(self):
        self.keep_all = True
        self.precision = False
    
    def set_params(self, keep_all=True, precision=False):
        """
        设置融合分析参数
        
        Args:
            keep_all (bool): 是否保留所有结果
            precision (bool): 是否使用高精度计算
        """
        self.keep_all = keep_all
        self.precision = precision
    
    def perform_union(self, first_gdf, second_gdf=None):
        """
        执行融合操作
        
        Args:
            first_gdf (GeoDataFrame): 第一个输入图层
            second_gdf (GeoDataFrame): 第二个输入图层（可选，用于多图层融合）
            
        Returns:
            GeoDataFrame: 融合结果图层
        """
        if first_gdf is None:
            print("警告：输入图层为空")
            return None
        
        # 检查并确保两个图层使用相同的坐标系
        try:
            if second_gdf is not None:
                # 如果第一个图层没有坐标系统，尝试使用第二个图层的
                if first_gdf.crs is None:
                    print("警告：第一个图层没有定义坐标系，尝试使用第二个图层的坐标系")
                    if second_gdf.crs is not None:
                        first_gdf = first_gdf.set_crs(second_gdf.crs)
                # 如果第二个图层没有坐标系统，使用第一个图层的
                elif second_gdf.crs is None:
                    print("警告：第二个图层没有定义坐标系，使用第一个图层的坐标系")
                    second_gdf = second_gdf.set_crs(first_gdf.crs)
                # 检查坐标系统是否匹配
                elif first_gdf.crs != second_gdf.crs:
                    print(f"坐标系不匹配：{first_gdf.crs} != {second_gdf.crs}")
                    return None
            
            # 打印图层信息
            print(f"图层1信息：类型={first_gdf.geometry.type.iloc[0] if not first_gdf.empty else '空'}, \
                  特征数={len(first_gdf)}, 列={list(first_gdf.columns)}")
            
            if second_gdf is not None:
                print(f"图层2信息：类型={second_gdf.geometry.type.iloc[0] if not second_gdf.empty else '空'}, \
                      特征数={len(second_gdf)}, 列={list(second_gdf.columns)}")
            
            # 执行融合操作
            if second_gdf is None:
                # 单图层融合：将同一图层中具有相同属性的要素合并
                # 默认使用所有非几何列进行分组
                group_cols = [col for col in first_gdf.columns if col != 'geometry']
                union_result = first_gdf.dissolve(by=group_cols)
                print(f"单图层融合结果特征数：{len(union_result)}")
            else:
                # 双图层融合：合并两个图层的几何图形
                union_result = gpd.overlay(first_gdf, second_gdf, how='union')
                print(f"双图层融合结果特征数：{len(union_result)}")
            
            if union_result.empty:
                print("警告：融合结果为空，图层可能存在问题")
            else:
                print(f"融合结果列：{list(union_result.columns)}")
            
            return union_result
            
        except Exception as e:
            print(f"执行融合操作时发生错误：{e}")
            # 尝试使用替代方法
            try:
                if second_gdf is None:
                    # 使用替代方法进行单图层融合
                    union_geom = first_gdf.geometry.unary_union
                    # 创建一个新的GeoDataFrame，包含合并后的几何图形
                    union_result = gpd.GeoDataFrame(geometry=[union_geom])
                    print("使用替代方法完成单图层融合操作")
                else:
                    # 使用替代方法进行双图层融合
                    # 首先合并两个GeoDataFrame
                    combined_gdf = gpd.GeoDataFrame(pd.concat([first_gdf, second_gdf], ignore_index=True))
                    # 然后执行溶解操作
                    union_result = combined_gdf.dissolve()
                    print("使用替代方法完成双图层融合操作")
                return union_result
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
        验证输入是否满足融合分析的要求
        
        Args:
            layer_data (list): 图层数据列表
            
        Returns:
            tuple: (is_valid, message)
        """
        if len(layer_data) < 1:
            return False, f"融合操作需要至少一个矢量图层，当前可用图层数: {len(layer_data)}"
        
        # 检查图层是否包含有效的几何数据
        for i, (gdf, _) in enumerate(layer_data[:2]):  # 最多检查两个图层
            if gdf is None or gdf.empty:
                return False, f"图层 {i+1} 为空或无效"
            if 'geometry' not in gdf.columns:
                return False, f"图层 {i+1} 没有几何列"
        
        return True, ""

# 示例使用
def main():
    # 示例代码，展示如何使用融合分析类
    import pandas as pd
    union_analyzer = UnionAnalysis()
    union_analyzer.set_params(keep_all=True, precision=True)
    
    print("融合分析模块已加载")
    print("使用示例:")
    print("1. 创建分析实例: analyzer = UnionAnalysis()")
    print("2. 设置参数: analyzer.set_params(keep_all=True, precision=False)")
    print("3. 处理输入数据: layer_data = analyzer.process_input_data(input_data)")
    print("4. 验证输入: is_valid, message = analyzer.validate_inputs(layer_data)")
    print("5. 执行融合: result = analyzer.perform_union(first_gdf, second_gdf)")

if __name__ == "__main__":
    main()
