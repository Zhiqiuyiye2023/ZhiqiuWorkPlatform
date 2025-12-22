# coding:utf-8
"""
格式转换相关功能模块
"""

import os
import geopandas as gpd
import simplekml


def SHP转KMZ奥维格式(矢量路径, 分离字段, 标注字段, 颜色值, 线宽值, 是否分离=False):
    """
    将SHP文件转换为KMZ奥维格式，保持原始坐标系
    
    参数:
    矢量路径: SHP文件路径
    分离字段: 用于分离的字段名
    标注字段: 用于标注的字段名
    颜色值: 线条颜色值 (ABGR格式)
    线宽值: 线条宽度值
    是否分离: 是否按字段分离
    """
    try:
        # 添加更详细的调试信息
        print(f"\n开始处理KMZ转换:")
        print(f"输入参数:")
        print(f"矢量路径: {矢量路径}")
        print(f"分离字段: {分离字段}")
        print(f"标注字段: {标注字段}")
        print(f"颜色值: {颜色值}")
        print(f"线宽值: {线宽值}")
        print(f"是否分离: {是否分离}")
        
        # 读取SHP文件
        gdf = gpd.read_file(矢量路径)
        print(f"\n读取到的属性字段: {list(gdf.columns)}")
        print(f"原始坐标系: {gdf.crs}")
        
        # 确保数据在WGS84坐标系下（KMZ/KML要求）
        if gdf.crs is None:
            raise ValueError("输入数据没有坐标系信息")
            
        # 如果不在WGS84坐标系下，进行转换
        if gdf.crs != 'EPSG:4326':
            print(f"将数据从 {gdf.crs} 转换到 WGS84 (EPSG:4326)")
            gdf = gdf.to_crs('EPSG:4326')
        
        if 是否分离 and 分离字段:
            print(f"\n开始按字段分离处理:")
            print(f"分离字段 '{分离字段}' 的唯一值: {gdf[分离字段].unique()}")
            
            # 检查分离字段是否存在
            if 分离字段 not in gdf.columns:
                raise ValueError(f"分离字段 '{分离字段}' 在SHP文件中不存在")
            
            # 获取所有唯一值
            unique_values = gdf[分离字段].unique()
            
            # 按字段值分组处理
            for value in unique_values:
                # 创建KML对象
                kml = simplekml.Kml()
                
                # 添加坐标系信息
                kml.document.name = f"{os.path.splitext(os.path.basename(矢量路径))[0]}_{value}"
                kml.document.description = f"坐标系: WGS84 (EPSG:4326)\n原始坐标系: {gdf.crs}"
                
                # 筛选当前值的数据
                mask = gdf[分离字段] == value
                current_gdf = gdf[mask]
                
                # 遍历每个要素并添加到KML中
                for _, row in current_gdf.iterrows():
                    geom = row.geometry
                    
                    # 创建新的KML要素
                    if geom.geom_type == 'Point':
                        feature = kml.newpoint()
                        feature.coords = [(geom.x, geom.y)]
                        if 标注字段 and 标注字段 in gdf.columns:
                            feature.name = str(row[标注字段])
                    elif geom.geom_type == 'LineString':
                        feature = kml.newlinestring()
                        feature.coords = list(geom.coords)
                        feature.style.linestyle.color = 颜色值
                        feature.style.linestyle.width = int(线宽值)
                        if 标注字段 and 标注字段 in gdf.columns:
                            feature.name = str(row[标注字段])
                    elif geom.geom_type == 'Polygon':
                        feature = kml.newpolygon()
                        feature.outerboundaryis = list(geom.exterior.coords)
                        feature.style.linestyle.color = 颜色值
                        feature.style.linestyle.width = int(线宽值)
                        feature.style.polystyle.fill = 0
                        if 标注字段 and 标注字段 in gdf.columns:
                            feature.name = str(row[标注字段])
                    elif geom.geom_type == 'MultiPolygon':
                        for poly_geom in geom.geoms:
                            feature = kml.newpolygon()
                            feature.outerboundaryis = list(poly_geom.exterior.coords)
                            feature.style.linestyle.color = 颜色值
                            feature.style.linestyle.width = int(线宽值)
                            feature.style.polystyle.fill = 0
                            if 标注字段 and 标注字段 in gdf.columns:
                                feature.name = str(row[标注字段])
                
                # 生成输出文件名（使用分类字段值）
                output_filename = f"{os.path.splitext(os.path.basename(矢量路径))[0]}_{value}.kmz"
                output_path = os.path.join(os.path.dirname(矢量路径), output_filename)
                
                # 保存为KMZ文件
                kml.savekmz(output_path)
                print(f"转换成功: {output_path}")
                
        else:
            # 不分离时使用原始文件名
            output_filename = os.path.splitext(os.path.basename(矢量路径))[0] + '.kmz'
            output_path = os.path.join(os.path.dirname(矢量路径), output_filename)
            
            # 创建KMZ
            kml = simplekml.Kml()
            
            # 添加坐标系信息
            kml.document.name = os.path.splitext(os.path.basename(矢量路径))[0]
            kml.document.description = f"坐标系: WGS84 (EPSG:4326)\n原始坐标系: {gdf.crs}"
            
            for _, row in gdf.iterrows():
                geom = row.geometry
                
                # 创建新的KML要素
                if geom.geom_type == 'Point':
                    feature = kml.newpoint()
                    feature.coords = [(geom.x, geom.y)]
                    if 标注字段 and 标注字段 in gdf.columns:
                        feature.name = str(row[标注字段])
                elif geom.geom_type == 'LineString':
                    feature = kml.newlinestring()
                    feature.coords = list(geom.coords)
                    feature.style.linestyle.color = 颜色值
                    feature.style.linestyle.width = int(线宽值)
                    if 标注字段 and 标注字段 in gdf.columns:
                        feature.name = str(row[标注字段])
                elif geom.geom_type == 'Polygon':
                    feature = kml.newpolygon()
                    feature.outerboundaryis = list(geom.exterior.coords)
                    feature.style.linestyle.color = 颜色值
                    feature.style.linestyle.width = int(线宽值)
                    feature.style.polystyle.fill = 0
                    if 标注字段 and 标注字段 in gdf.columns:
                        feature.name = str(row[标注字段])
                elif geom.geom_type == 'MultiPolygon':
                    for poly_geom in geom.geoms:
                        feature = kml.newpolygon()
                        feature.outerboundaryis = list(poly_geom.exterior.coords)
                        feature.style.linestyle.color = 颜色值
                        feature.style.linestyle.width = int(线宽值)
                        feature.style.polystyle.fill = 0
                        if 标注字段 and 标注字段 in gdf.columns:
                            feature.name = str(row[标注字段])
            
            # 保存KMZ文件
            kml.savekmz(output_path)
            print(f"转换成功: {output_path}")
            
        return True
        
    except Exception as e:
        print(f"转换过程中出错: {str(e)}")
        raise Exception(f"转换KMZ失败: {str(e)}")


def KMZ转SHP格式(kmz_file_path, output_path):
    """
    将KMZ文件转换为SHP格式
    
    参数:
        kmz_file_path: str, KMZ文件路径
        output_path: str, 输出SHP文件路径
    """
    try:
        import zipfile
        import tempfile
        import os
        from shapely.geometry import Point, LineString, Polygon, MultiPolygon
        from shapely import wkt
        
        # 临时目录用于解压KMZ文件
        with tempfile.TemporaryDirectory() as temp_dir:
            # 解压KMZ文件
            with zipfile.ZipFile(kmz_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 查找KML文件
            kml_files = [f for f in os.listdir(temp_dir) if f.endswith('.kml')]
            if not kml_files:
                raise Exception("KMZ文件中未找到KML文件")
            
            kml_file = os.path.join(temp_dir, kml_files[0])
            
            # 读取KML文件
            with open(kml_file, 'r', encoding='utf-8') as f:
                kml_content = f.read()
            
            # 使用simplekml解析KML
            kml = simplekml.Kml()
            kml.from_string(kml_content)
            
            # 提取几何对象
            geometries = []
            names = []
            
            def process_feature(feature):
                """递归处理KML要素"""
                if hasattr(feature, 'geometry'):
                    geom = feature.geometry
                    if geom:
                        # 处理点
                        if hasattr(geom, 'coords') and len(geom.coords) > 0:
                            if len(geom.coords) == 1:
                                # 点
                                point = Point(geom.coords[0])
                                geometries.append(point)
                                names.append(feature.name if feature.name else f"Point_{len(geometries)}")
                            else:
                                # 线
                                line = LineString(geom.coords)
                                geometries.append(line)
                                names.append(feature.name if feature.name else f"Line_{len(geometries)}")
                    elif hasattr(geom, 'outerboundaryis'):
                        # 处理多边形
                        outer_coords = geom.outerboundaryis.coords
                        if outer_coords:
                            polygon = Polygon(outer_coords)
                            geometries.append(polygon)
                            names.append(feature.name if feature.name else f"Polygon_{len(geometries)}")
                
                # 递归处理子要素
                if hasattr(feature, 'features'):
                    for sub_feature in feature.features():
                        process_feature(sub_feature)
            
            # 处理KML文档中的所有要素
            process_feature(kml.document)
            
            if not geometries:
                raise Exception("未从KMZ文件中提取到几何对象")
            
            # 创建GeoDataFrame
            gdf = gpd.GeoDataFrame({'name': names, 'geometry': geometries}, crs='EPSG:4326')
            
            # 保存为SHP文件
            gdf.to_file(output_path, encoding='utf-8')
            
            print(f"KMZ转SHP成功，输出文件: {output_path}")
            return output_path
            
    except Exception as e:
        print(f"KMZ转SHP失败: {str(e)}")
        raise Exception(f"KMZ转SHP失败: {str(e)}")


def SHP转WKT文本格式(shp_path):
    """
    将SHP文件中的几何对象转换为WKT格式，并添加为新字段，同时输出WKT文本文件
    
    Args:
        shp_path: SHP文件的路径
    """
    if not shp_path:
        raise ValueError("请选择SHP文件")
        
    try:
        # 读取矢量文件
        gdf = gpd.read_file(shp_path)
        print(f"\n读取到 {len(gdf)} 个要素")
        
        # 创建WKT字段列表
        wkt_list = []
        
        for idx, row in gdf.iterrows():
            geom = row.geometry
            if geom is not None:
                try:
                    # 打印调试信息
                    print(f"\n处理第 {idx+1} 个几何对象:")
                    print(f"几何类型: {geom.geom_type}")
                    
                    # 处理不同类型的几何对象
                    if geom.geom_type == 'MultiPolygon':
                        # 对于MultiPolygon，处理每个子多边形
                        coords_list = []
                        for poly in geom.geoms:
                            # 获取外环坐标，只取x,y值
                            exterior_coords = [(x, y) for x, y, *_ in poly.exterior.coords]
                            # 确保首尾相连
                            if exterior_coords[0] != exterior_coords[-1]:
                                exterior_coords.append(exterior_coords[0])
                            coords_list.append(f"(({', '.join([f'{x} {y}' for x, y in exterior_coords])}))")
                        wkt = f"MULTIPOLYGON({', '.join(coords_list)})"
                    elif geom.geom_type == 'Polygon':
                        # 对于Polygon，直接处理外环坐标
                        exterior_coords = [(x, y) for x, y, *_ in geom.exterior.coords]
                        # 确保首尾相连
                        if exterior_coords[0] != exterior_coords[-1]:
                            exterior_coords.append(exterior_coords[0])
                        wkt = f"POLYGON(({', '.join([f'{x} {y}' for x, y in exterior_coords])}))"
                    elif geom.geom_type == 'LineString':
                        # 对于线，处理所有坐标点
                        coords = [(x, y) for x, y, *_ in geom.coords]
                        wkt = f"LINESTRING({', '.join([f'{x} {y}' for x, y in coords])})"
                    elif geom.geom_type == 'Point':
                        # 对于点，直接处理
                        x, y, *_ = geom.coords[0]
                        wkt = f"POINT({x} {y})"
                    else:
                        print(f"未处理的几何类型: {geom.geom_type}")
                        wkt = ""
                    
                    print(f"处理后的WKT: {wkt}")
                    wkt_list.append(wkt)
                    
                except Exception as e:
                    print(f"处理第 {idx+1} 个几何对象时出错: {str(e)}")
                    print(f"错误详情: {type(e).__name__}")
                    import traceback
                    print(f"错误堆栈: {traceback.format_exc()}")
                    wkt_list.append("")
                    continue
            else:
                wkt_list.append("")
                
        if not wkt_list:
            raise Exception("没有有效的几何对象可以转换")
        
        # 将WKT字段添加到GeoDataFrame中
        gdf['WKT_坐标串'] = wkt_list
        
        # 保存更新后的SHP文件
        shp_output_path = os.path.splitext(shp_path)[0] + '_带WKT字段.shp'
        gdf.to_file(shp_output_path, encoding='utf-8')
        
        # 同时输出WKT文本文件
        txt_output_path = os.path.splitext(shp_path)[0] + '_wkt.txt'
        with open(txt_output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(wkt_list))
            
        print(f"\n转换完成，共处理 {len(wkt_list)} 个几何对象")
        print(f"已在SHP文件中添加 'WKT_坐标串' 字段")
        print(f"SHP输出文件: {shp_output_path}")
        print(f"WKT文本文件: {txt_output_path}")
        return shp_output_path, txt_output_path
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise Exception(f"转换WKT格式失败: {str(e)}")


def SHP转ZIP格式(shp_path):
    """
    将SHP文件及其相关文件压缩为ZIP格式
    
    Args:
        shp_path: SHP文件的路径
    """
    if not shp_path:
        raise ValueError("请选择SHP文件")
        
    try:
        import zipfile
        import os
        
        # 获取SHP文件的基本路径
        base_name = os.path.splitext(shp_path)[0]
        
        # 定义需要压缩的文件扩展名
        shp_extensions = ['.shp', '.dbf', '.shx', '.prj', '.cpg', '.fix']
        
        # 创建ZIP文件路径
        zip_path = base_name + '.zip'
        
        # 创建ZIP文件并添加相关文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for ext in shp_extensions:
                file_path = base_name + ext
                if os.path.exists(file_path):
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
                    print(f"已添加文件: {file_path}")
        
        print(f"\nZIP压缩完成，输出文件: {zip_path}")
        return zip_path
        
    except Exception as e:
        print(f"ZIP压缩过程中出现错误: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise Exception(f"SHP转ZIP格式失败: {str(e)}")


def WKT转SHP格式(wkt_string, output_path):
    """
    将WKT坐标串转换为SHP矢量文件
    
    Args:
        wkt_string: WKT格式的坐标串
        output_path: 输出SHP文件的路径
    """
    if not wkt_string:
        raise ValueError("请输入WKT坐标串")
    
    if not output_path:
        raise ValueError("请选择输出文件路径")
    
    try:
        import geopandas as gpd
        from shapely.wkt import loads
        
        print(f"\n开始处理WKT转SHP:")
        print(f"输入WKT: {wkt_string}")
        print(f"输出路径: {output_path}")
        
        # 解析WKT字符串
        geom = loads(wkt_string)
        print(f"解析结果几何类型: {geom.geom_type}")
        
        # 创建GeoDataFrame
        gdf = gpd.GeoDataFrame({
            'geometry': [geom],
            '名称': ['WKT转换要素']
        }, crs='EPSG:4326')  # 默认使用WGS84坐标系
        
        # 保存为SHP文件
        gdf.to_file(output_path, encoding='utf-8')
        
        print(f"\nWKT转SHP成功！")
        print(f"输出文件: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"WKT转SHP过程中出现错误: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise Exception(f"WKT转SHP格式失败: {str(e)}")
