# coding:utf-8
"""
矢量操作相关功能模块
"""

import os
import pandas as pd
import geopandas as gpd
from datetime import datetime


def 合并指定目录中的所有要素(folder_path, encoding='utf-8'):
    """
    合并指定目录中的所有SHP文件（包括子目录）
    
    参数:
        folder_path: str, 要合并的目录路径
        encoding: str, 文件编码，默认为'utf-8'，也可以是'gbk'
    """
    # 找到所有SHP文件
    shp_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".shp"):
                shp_files.append(os.path.join(root, file))
    
    if not shp_files:
        print("没有找到任何SHP文件！")
        return None
        
    # 读取第一个文件作为基准
    try:
        merged_gdf = gpd.read_file(shp_files[0], encoding=encoding)
    except Exception as e:
        print(f"使用{encoding}编码读取文件失败，尝试使用gbk编码: {e}")
        merged_gdf = gpd.read_file(shp_files[0], encoding='gbk')
        encoding = 'gbk'  # 更新编码参数
    
    # 清理字段名称，确保符合SHP格式要求
    merged_gdf = _clean_field_names(merged_gdf)
    merged_gdf['XMMC'] = os.path.basename(shp_files[0])[:-4][:10]  # 限制字段长度
    target_crs = merged_gdf.crs
    
    # 重置索引以确保唯一性
    merged_gdf = merged_gdf.reset_index(drop=True)
    
    # 合并其他文件
    for shp_file in shp_files[1:]:
        try:
            # 读取文件，尝试多种编码
            gdf = None
            encodings_to_try = [encoding, 'gbk', 'gb2312', 'utf-8']
            for enc in encodings_to_try:
                try:
                    gdf = gpd.read_file(shp_file, encoding=enc)
                    print(f"使用{enc}编码成功读取文件{shp_file}")
                    break
                except Exception as e:
                    print(f"使用{enc}编码读取文件{shp_file}失败: {e}")
                    continue
            
            if gdf is None:
                raise Exception(f"无法使用任何编码读取文件{shp_file}")
            
            # 清理字段名称，确保符合SHP格式要求
            gdf = _clean_field_names(gdf)
            gdf['XMMC'] = os.path.basename(shp_file)[:-4][:10]  # 限制字段长度
            
            # 确保坐标系一致
            if gdf.crs != target_crs:
                if target_crs is not None:
                    gdf = gdf.to_crs(target_crs)
                else:
                    target_crs = gdf.crs
            
            # 重置索引以确保唯一性
            gdf = gdf.reset_index(drop=True)
            
            # 确保字段匹配，只保留两个DataFrame共有的字段
            common_columns = list(set(merged_gdf.columns) & set(gdf.columns))
            # 确保geometry字段在common_columns中
            if 'geometry' not in common_columns:
                common_columns.append('geometry')
            
            # 合并数据，使用ignore_index=True确保新索引
            merged_gdf = pd.concat([merged_gdf[common_columns], gdf[common_columns]], ignore_index=True, sort=False)
        except Exception as e:
            print(f"处理文件 {shp_file} 时出错: {e}")
            continue
    
    # 保存合并结果
    output_path = os.path.join(folder_path, 'merged.shp')
    
    # 重置索引后再保存
    merged_gdf = merged_gdf.reset_index(drop=True)
    
    # 使用指定编码保存文件，添加错误处理
    try:
        merged_gdf.to_file(output_path, encoding=encoding)
        print(f"合并完成并保存为: {output_path}")
        return output_path
    except Exception as e:
        # 尝试使用不同的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(folder_path, f'merged_{timestamp}.shp')
        merged_gdf.to_file(output_path, encoding=encoding)
        print(f"合并完成并保存为: {output_path}")
        return output_path


def 获取矢量要素中心点(vector_path, naming_field=None):
    """
    获取矢量要素的中心点坐标
    
    参数:
        vector_path: str, 输入的矢量文件路径
        naming_field: str, 用于命名的字段名称，如果为None或空字符串则使用流水号
    """
    try:
        # 读取矢量文件
        gdf = gpd.read_file(vector_path)
        
        # 计算每个要素的中心点
        gdf['center'] = gdf.geometry.centroid
        
        # 提取X、Y坐标
        gdf['X'] = gdf['center'].x
        gdf['Y'] = gdf['center'].y
        
        # 处理命名
        if naming_field and naming_field.strip():  # 检查命名字段是否有效
            gdf['名称'] = gdf[naming_field].astype(str)
        else:
            gdf['名称'] = [f'要素_{i+1}' for i in range(len(gdf))]
        
        # 创建结果DataFrame
        result_df = gdf[['名称', 'X', 'Y']]
        
        # 格式化输出文本
        output_text = "中心点坐标信息：\n\n"
        output_text += "名称\t\tX坐标\t\tY坐标\n"
        output_text += "-" * 50 + "\n"
        
        for _, row in result_df.iterrows():
            output_text += f"{row['名称']}\t\t{row['X']:.6f}\t\t{row['Y']:.6f}\n"
        
        return output_text
        
    except Exception as e:
        raise Exception(f'获取中心点失败: {str(e)}')


def 根据矢量字段分离要素(file_path, field_name):
    """
    根据矢量字段分离要素并创建压缩文件
    """
    import os
    import shutil
    import zipfile
    from datetime import datetime
    
    # 读取文件
    data = gpd.read_file(file_path)
    grouped_data = data.groupby(field_name)
    
    # 创建文件夹
    folder_path = os.path.dirname(file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_folder = os.path.join(folder_path, f"压缩版_{timestamp}")
    os.makedirs(zip_folder, exist_ok=True)
    
    # 获取原始文件信息
    original_cpg = os.path.splitext(file_path)[0] + '.cpg'
    original_fix = os.path.splitext(file_path)[0] + '.fix'
    
    # 分组处理
    for tbbh, group in grouped_data:
        # 创建子文件夹
        tbbh_folder_path = os.path.join(folder_path, str(tbbh))
        if not os.path.exists(tbbh_folder_path):
            os.makedirs(tbbh_folder_path)
        
        # 保存分组数据
        output_file = os.path.join(tbbh_folder_path, f'{tbbh}.shp')
        group.to_file(output_file)
        
        # 处理辅助文件
        if os.path.exists(original_cpg):
            shutil.copy2(original_cpg, os.path.join(tbbh_folder_path, f'{tbbh}.cpg'))
        else:
            with open(os.path.join(tbbh_folder_path, f'{tbbh}.cpg'), 'w', encoding='utf-8') as f:
                f.write('utf-8')
        
        if os.path.exists(original_fix):
            shutil.copy2(original_fix, os.path.join(tbbh_folder_path, f'{tbbh}.fix'))
        else:
            with open(os.path.join(tbbh_folder_path, f'{tbbh}.fix'), 'w', encoding='utf-8') as f:
                f.write('')
        
        # 创建压缩文件
        zip_filename = os.path.join(zip_folder, f"{tbbh}.zip")
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            base_name = os.path.splitext(output_file)[0]
            for ext in ['.shp', '.dbf', '.shx', '.prj', '.cpg', '.fix']:
                file_path = base_name + ext
                if os.path.exists(file_path):
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
    
    print(f"处理完成，共分离出{len(grouped_data)}个要素组，已保存到: {zip_folder}")
    return zip_folder


def 融合要素(input_path, encoding='utf-8', field_name=None, layer_name=None):
    """
    融合指定目录中的所有要素或GDB图层，将相同类型的要素合并为一个
    
    参数:
        input_path: str, 要融合的目录路径或GDB文件路径
        encoding: str, 文件编码，默认为'utf-8'
        field_name: str, 用于融合的字段名称，如果为None则不按字段融合
        layer_name: str, GDB中的图层名称，如果为None则处理所有SHP文件
    """
    merged_gdf = None
    target_crs = None
    
    try:
        # 检查是否为GDB文件
        if input_path.endswith('.gdb') and layer_name:
            # 处理GDB图层
            print(f"处理GDB图层: {layer_name}")
            merged_gdf = gpd.read_file(input_path, layer=layer_name, encoding=encoding)
            target_crs = merged_gdf.crs
        else:
            # 处理SHP文件
            # 找到所有SHP文件
            shp_files = []
            for root, _, files in os.walk(input_path):
                for file in files:
                    if file.endswith(".shp"):
                        shp_files.append(os.path.join(root, file))
            
            if not shp_files:
                print("没有找到任何SHP文件！")
                return None
                
            # 读取第一个文件作为基准
            try:
                merged_gdf = gpd.read_file(shp_files[0], encoding=encoding)
            except Exception as e:
                print(f"使用{encoding}编码读取文件失败，尝试使用gbk编码: {e}")
                merged_gdf = gpd.read_file(shp_files[0], encoding='gbk')
                encoding = 'gbk'  # 更新编码参数
            
            target_crs = merged_gdf.crs
            
            # 融合其他文件
            for shp_file in shp_files[1:]:
                try:
                    # 读取文件，尝试多种编码
                    gdf = None
                    encodings_to_try = [encoding, 'gbk', 'gb2312', 'utf-8']
                    for enc in encodings_to_try:
                        try:
                            gdf = gpd.read_file(shp_file, encoding=enc)
                            print(f"使用{enc}编码成功读取文件{shp_file}")
                            break
                        except Exception as e:
                            print(f"使用{enc}编码读取文件{shp_file}失败: {e}")
                            continue
                    
                    if gdf is None:
                        raise Exception(f"无法使用任何编码读取文件{shp_file}")
                    
                    # 清理字段名称，确保符合SHP格式要求
                    gdf = _clean_field_names(gdf)
                    
                    # 确保坐标系一致
                    if gdf.crs != target_crs:
                        if target_crs is not None:
                            gdf = gdf.to_crs(target_crs)
                        else:
                            target_crs = gdf.crs
                    
                    # 重置索引以确保唯一性
                    gdf = gdf.reset_index(drop=True)
                    
                    # 确保字段匹配，只保留两个DataFrame共有的字段
                    common_columns = list(set(merged_gdf.columns) & set(gdf.columns))
                    # 确保geometry字段在common_columns中
                    if 'geometry' not in common_columns:
                        common_columns.append('geometry')
                    
                    # 融合数据，使用ignore_index=True确保新索引
                    merged_gdf = pd.concat([merged_gdf[common_columns], gdf[common_columns]], ignore_index=True, sort=False)
                except Exception as e:
                    print(f"处理文件 {shp_file} 时出错: {e}")
                    continue
    except Exception as e:
        print(f"读取数据失败: {e}")
        raise
    
    # 清理字段名称，确保符合SHP格式要求
    merged_gdf = _clean_field_names(merged_gdf)
    
    # 重置索引以确保唯一性
    merged_gdf = merged_gdf.reset_index(drop=True)
    
    # 执行融合操作 - 按照指定字段值进行融合
    # 如果field_name为None，则不按字段融合
    print(f"执行融合操作，字段: {field_name}")
    dissolved_gdf = merged_gdf.dissolve(by=field_name, aggfunc='first').reset_index(drop=True)
    
    # 确定输出路径
    if input_path.endswith('.gdb'):
        # 输出到GDB
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_layer_name = f"dissolved_{timestamp}"
        dissolved_gdf.to_file(input_path, layer=output_layer_name, driver='OpenFileGDB')
        output_path = f"{input_path}#{output_layer_name}"
        print(f"融合完成并保存到GDB: {output_path}")
        return output_path
    else:
        # 输出到SHP文件
        output_path = os.path.join(input_path, 'dissolved.shp')
        
        # 重置索引后再保存
        dissolved_gdf = dissolved_gdf.reset_index(drop=True)
        
        # 使用指定编码保存文件，添加错误处理
        try:
            dissolved_gdf.to_file(output_path, encoding=encoding)
            print(f"融合完成并保存为: {output_path}")
            return output_path
        except Exception as e:
            # 尝试使用不同的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(input_path, f'dissolved_{timestamp}.shp')
            dissolved_gdf.to_file(output_path, encoding=encoding)
            print(f"融合完成并保存为: {output_path}")
            return output_path


def 标识要素(input_layers, output_path, encoding='utf-8'):
    """
    标识要素功能，将多个图层进行标识分析，生成结果文件
    
    参数:
        input_layers: list, 输入图层列表，每个元素包含图层路径和类型
        output_path: str, 输出路径
        encoding: str, 文件编码，默认为'utf-8'
    
    返回:
        str, 生成的结果文件路径
    """
    import geopandas as gpd
    import pandas as pd
    from datetime import datetime
    
    if not input_layers:
        print("没有输入图层！")
        return None
    
    # 确保输入图层数量至少为2个（用于标识分析）
    if len(input_layers) < 2:
        print("标识分析需要至少2个图层！")
        return None
    
    try:
        # 读取第一个图层作为目标图层
        target_layer = input_layers[0]
        print(f"读取目标图层: {target_layer['path']}")
        
        if '|' in target_layer['path']:
            # 处理GDB图层
            gdb_path, layer_name = target_layer['path'].split('|', 1)
            target_gdf = gpd.read_file(gdb_path, layer=layer_name, encoding=encoding)
        else:
            # 处理SHP图层
            target_gdf = gpd.read_file(target_layer['path'], encoding=encoding)
        
        # 读取第二个图层作为标识图层
        identify_layer = input_layers[1]
        print(f"读取标识图层: {identify_layer['path']}")
        
        if '|' in identify_layer['path']:
            # 处理GDB图层
            gdb_path, layer_name = identify_layer['path'].split('|', 1)
            identify_gdf = gpd.read_file(gdb_path, layer=layer_name, encoding=encoding)
        else:
            # 处理SHP图层
            identify_gdf = gpd.read_file(identify_layer['path'], encoding=encoding)
        
        # 确保坐标系一致
        if target_gdf.crs != identify_gdf.crs:
            print(f"坐标系不一致，将标识图层转换为目标图层的坐标系: {target_gdf.crs}")
            identify_gdf = identify_gdf.to_crs(target_gdf.crs)
        
        # 执行标识分析
        print("执行标识分析...")
        # 使用geopandas的overlay方法，how='identify'相当于标识分析
        result_gdf = gpd.overlay(target_gdf, identify_gdf, how='identity', keep_geom_type=False)
        
        # 处理重复列名
        print("处理重复列名...")
        # 添加前缀区分来自不同图层的列
        target_cols = list(target_gdf.columns)
        identify_cols = list(identify_gdf.columns)
        
        # 找出重复的列名
        common_cols = set(target_cols) & set(identify_cols)
        common_cols.discard('geometry')  # 忽略geometry列
        
        # 为重复的列名添加前缀
        if common_cols:
            # 先为标识图层的列添加前缀
            for col in common_cols:
                if col in result_gdf.columns:
                    # 找到所有包含该列名的列（可能有多个，因为overlay会添加后缀）
                    cols_to_rename = [c for c in result_gdf.columns if col in c]
                    for c in cols_to_rename:
                        if c != col:  # 不为原始列添加前缀
                            new_name = f"IDENTIFY_{c}"
                            result_gdf = result_gdf.rename(columns={c: new_name})
        
        # 清理字段名称
        result_gdf = _clean_field_names(result_gdf)
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_path, f"identify_result_{timestamp}.shp")
        
        # 保存结果
        print(f"保存结果到: {output_file}")
        result_gdf.to_file(output_file, encoding=encoding)
        
        return output_file
        
    except Exception as e:
        print(f"标识要素失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def _clean_field_names(gdf):
    """
    清理GeoDataFrame的字段名称，确保符合SHP文件格式要求
    """
    # SHP文件字段名限制：最多10个字符，只能包含字母、数字、下划线
    new_columns = {}
    for col in gdf.columns:
        # 跳过geometry列
        if col == 'geometry':
            continue
            
        # 清理字段名
        cleaned_name = str(col)
        # 特别处理包含中文的字段名，使用通用方法
        if any('\u4e00' <= char <= '\u9fff' for char in cleaned_name):
            # 使用通用方法处理中文字段名
            # 提取所有字母数字字符
            cleaned_name = ''.join(c for c in cleaned_name if c.isalnum() or c == '_')
            # 如果结果为空，使用默认名称
            if not cleaned_name:
                cleaned_name = 'FIELD'
            # 添加前缀以确保有意义
            if not cleaned_name.startswith(('FIELD', 'F')):
                cleaned_name = 'F_' + cleaned_name
        
        # 移除特殊字符，只保留字母、数字和下划线
        cleaned_name = ''.join(c if c.isalnum() or c == '_' else '' for c in cleaned_name)
        # 限制长度为10个字符
        cleaned_name = cleaned_name[:10]
        # 确保不以数字开头
        if cleaned_name and cleaned_name[0].isdigit():
            cleaned_name = 'F' + cleaned_name[1:]
        # 如果字段名为空，使用默认名称
        if not cleaned_name:
            cleaned_name = 'FIELD'
        # 确保字段名不为空且符合规范
        if not cleaned_name or len(cleaned_name.strip()) == 0:
            cleaned_name = 'FIELD'
        
        # 确保字段名可以被编码为ISO-8859-1
        try:
            cleaned_name.encode('iso-8859-1')
        except UnicodeEncodeError:
            # 如果不能编码，使用默认名称
            cleaned_name = 'FIELD_' + ''.join(c for c in cleaned_name if c.isalnum())[:5]
            # 再次检查编码
            try:
                cleaned_name.encode('iso-8859-1')
            except UnicodeEncodeError:
                cleaned_name = 'FIELD'
            
        new_columns[col] = cleaned_name
    
    # 重命名字段
    gdf = gdf.rename(columns=new_columns)
    
    # 处理重复字段名
    columns = list(gdf.columns)
    if 'geometry' in columns:
        columns.remove('geometry')
        
    unique_columns = []
    for i, col in enumerate(columns):
        counter = 1
        new_col = col
        while new_col in unique_columns:
            # 如果字段名重复，添加数字后缀
            suffix = str(counter)
            if len(col) + len(suffix) <= 10:
                new_col = col[:-len(suffix)] + suffix
            else:
                new_col = col[:10-len(suffix)] + suffix
            counter += 1
        unique_columns.append(new_col)
    
    # 重新构建列名映射
    if 'geometry' in gdf.columns:
        unique_columns.append('geometry')
        
    # 如果列数不匹配，保持原样
    if len(unique_columns) == len(gdf.columns):
        column_mapping = dict(zip(gdf.columns, unique_columns))
        gdf = gdf.rename(columns=column_mapping)
    
    return gdf
