# coding:utf-8
import os
import fiona
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# 设置中文字体支持
def setup_chinese_font():
    """设置中文字体支持"""
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        print(f"设置中文字体时出错: {str(e)}")

# 读取GDB文件中的DLTB图层
def read_dltb_layer(gdb_path):
    """
    只读取GDB文件中的DLTB图层
    
    Args:
        gdb_path: GDB文件路径
    
    Returns:
        dict: 包含DLTB图层的字典，如果不存在则返回None
    """
    try:
        # 检查路径是否存在
        if not os.path.exists(gdb_path):
            print(f"错误: GDB文件路径不存在: {gdb_path}")
            return None
        
        # 检查是否是.gdb文件夹
        if not os.path.basename(gdb_path).endswith('.gdb'):
            print(f"错误: 请提供有效的.gdb文件夹路径，当前路径: {gdb_path}")
            return None
        
        print(f"正在读取GDB文件: {gdb_path}")
        
        # 尝试直接读取DLTB图层
        print("\n读取DLTB图层...")
        try:
            # 使用优化参数读取
            gdf = gpd.read_file(
                gdb_path,
                layer='DLTB',
                engine='pyogrio',
                use_arrow=True  # 使用Arrow加速读取
            )
            
            print(f"  ✓ 成功读取DLTB图层，包含 {len(gdf)} 个要素")
            print(f"  ✓ 字段列表: {list(gdf.columns)}")
            
            # 打印图层的基本信息
            if not gdf.empty:
                print(f"  ✓ 几何类型: {gdf.geometry.type.iloc[0] if len(gdf.geometry.type.unique()) == 1 else '混合类型'}")
                
                # 如果有坐标系统信息，打印出来
                if gdf.crs:
                    print(f"  ✓ 坐标系统: {gdf.crs.name if hasattr(gdf.crs, 'name') else gdf.crs}")
                else:
                    print(f"  ✓ 坐标系统: 未定义")
            
            return {'DLTB': gdf}
            
        except Exception as e:
            print(f"  ✗ 读取DLTB图层失败: {str(e)}")
            # 尝试使用fiona引擎重试
            print("  尝试使用fiona引擎重试...")
            try:
                gdf = gpd.read_file(
                    gdb_path,
                    layer='DLTB',
                    engine='fiona'
                )
                print(f"  ✓ 使用fiona引擎成功读取DLTB图层，包含 {len(gdf)} 个要素")
                return {'DLTB': gdf}
            except Exception as e2:
                print(f"  ✗ 使用fiona引擎读取也失败: {str(e2)}")
                return None
        
    except Exception as e:
        print(f"读取GDB文件时发生错误: {str(e)}")
        return None

# 保存图层信息摘要
def save_layers_summary(gdb_data, output_dir):
    """
    保存图层信息摘要到CSV文件
    """
    if not gdb_data:
        return
    
    # 创建摘要数据
    summary_data = []
    for layer_name, gdf in gdb_data.items():
        summary_data.append({
            '图层名称': layer_name,
            '要素数量': len(gdf),
            '字段数量': len(gdf.columns),
            '字段列表': ', '.join(gdf.columns),
            '几何类型': gdf.geometry.type.iloc[0] if not gdf.empty and len(gdf.geometry.type.unique()) == 1 else '混合类型/空',
            '坐标系统': str(gdf.crs) if gdf.crs else '未定义'
        })
    
    # 创建DataFrame并保存
    df_summary = pd.DataFrame(summary_data)
    output_file = os.path.join(output_dir, 'gdb_layers_summary.csv')
    df_summary.to_csv(output_file, encoding='utf-8-sig', index=False)
    print(f"\n图层信息摘要已保存到: {output_file}")

# 简单预览图层
def preview_layer(gdf, layer_name, output_dir):
    """
    简单预览图层并保存为图片
    """
    if gdf.empty:
        return
    
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        gdf.plot(ax=ax, color='lightblue', edgecolor='blue', alpha=0.5)
        ax.set_title(f'图层预览: {layer_name}', fontsize=14)
        ax.set_xlabel('X坐标')
        ax.set_ylabel('Y坐标')
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 保存预览图
        output_file = os.path.join(output_dir, f'{layer_name}_preview.png')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"图层预览已保存到: {output_file}")
    except Exception as e:
        print(f"生成图层预览时出错: {str(e)}")

# 将图层导出为Shapefile
def export_layers(gdb_data, output_dir):
    """
    将所有图层导出为Shapefile
    """
    if not gdb_data:
        return
    
    shapefile_dir = os.path.join(output_dir, 'exported_shapefiles')
    os.makedirs(shapefile_dir, exist_ok=True)
    
    for layer_name, gdf in gdb_data.items():
        if gdf.empty:
            print(f"跳过空图层导出: {layer_name}")
            continue
        
        try:
            # 处理图层名称中的非法字符
            safe_layer_name = ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in layer_name)
            output_file = os.path.join(shapefile_dir, f'{safe_layer_name}.shp')
            gdf.to_file(output_file, driver='ESRI Shapefile', encoding='utf-8')
            print(f"图层已导出为Shapefile: {output_file}")
        except Exception as e:
            print(f"导出图层 {layer_name} 失败: {str(e)}")

# 提取DLTB图层中DLBM字段开头包含特定字符的记录并导出为Shapefile
def extract_and_export_dltb_dlbm(gdb_data, output_dir, pattern="01"):
    """
    从DLTB图层中提取DLBM字段开头包含特定字符的记录并导出为Shapefile
    
    Args:
        gdb_data: GDB数据字典
        output_dir: 输出目录
        pattern: 要匹配的字符模式，默认为"01"
    """
    if not gdb_data:
        return
    
    # 检查是否存在DLTB图层
    if "DLTB" not in gdb_data:
        print("错误: GDB文件中不存在DLTB图层")
        return
    
    dltb_gdf = gdb_data["DLTB"]
    
    # 检查是否存在DLBM字段
    if "DLBM" not in dltb_gdf.columns:
        print("错误: DLTB图层中不存在DLBM字段")
        return
    
    # 提取DLBM字段开头包含特定字符的记录
    filtered_gdf = dltb_gdf[dltb_gdf["DLBM"].astype(str).str.startswith(pattern)]
    
    print(f"\n从DLTB图层中提取DLBM字段开头包含'{pattern}'的记录")
    print(f"原始记录数: {len(dltb_gdf)}")
    print(f"提取后记录数: {len(filtered_gdf)}")
    
    if filtered_gdf.empty:
        print("没有找到匹配的记录")
        return
    
    # 创建导出目录
    extract_dir = os.path.join(output_dir, 'extracted_shapefiles')
    os.makedirs(extract_dir, exist_ok=True)
    
    # 导出为Shapefile
    output_file = os.path.join(extract_dir, f'DLTB_DLBM_contains_{pattern}.shp')
    try:
        filtered_gdf.to_file(output_file, driver='ESRI Shapefile', encoding='utf-8')
        print(f"\n成功导出Shapefile: {output_file}")
        print(f"导出的字段列表: {list(filtered_gdf.columns)}")
    except Exception as e:
        print(f"导出失败: {str(e)}")
        return
    
    # 返回导出的文件路径
    return output_file

# 主函数
def main():
    """主函数"""
    # 要读取的GDB文件路径
    gdb_path = r"C:/Project/511703达川区检查通过数据目录/导出成果/511703达川区.gdb"
    print(f"使用默认GDB文件路径: {gdb_path}")
    
    # 设置中文字体
    setup_chinese_font()
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gdb_output')
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}")
    
    # 读取GDB中的DLTB图层
    gdb_data = read_dltb_layer(gdb_path)
    
    if gdb_data and 'DLTB' in gdb_data:
        print(f"\n成功读取DLTB图层")
        
        # 提取DLTB图层中DLBM字段包含"01"的记录并导出
        extract_and_export_dltb_dlbm(gdb_data, output_dir, pattern="01")
        
        print("\n任务完成！")
    else:
        print("无法读取DLTB图层或GDB文件，请检查路径是否正确")

if __name__ == "__main__":
    main()