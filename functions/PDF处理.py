# coding:utf-8
"""
PDF文件处理功能模块
"""

import os
import fitz  # PyMuPDF
from PIL import Image
import img2pdf


def PDF合并(文件路径文本, 进度回调=None):
    """
    将多个PDF文件合并为一个
    
    参数:
    文件路径文本: 包含多个PDF文件路径的文本，每行一个路径
    进度回调: 进度回调函数，用于更新进度条
    """
    # 解析文件路径
    file_paths = []
    for f in 文件路径文本.strip().split('\n'):
        path = f.strip()
        # 移除URL前缀
        if path.startswith('file:///'):
            path = path[8:]
        elif path.startswith('file://'):
            path = path[7:]
        if path.lower().endswith('.pdf'):
            file_paths.append(path)
    
    if not file_paths:
        raise ValueError("没有找到有效的PDF文件路径")
    
    # 创建一个新的PDF文档
    new_pdf = fitz.open()
    
    total_files = len(file_paths)
    
    # 遍历所有PDF文件
    for i, file_path in enumerate(file_paths):
        try:
            # 打开PDF文件
            pdf = fitz.open(file_path)
            
            # 将所有页面添加到新PDF中
            for page in pdf:
                new_pdf.insert_pdf(pdf, from_page=page.number, to_page=page.number)
            
            # 关闭当前PDF
            pdf.close()
            
            # 更新进度
            if 进度回调:
                progress = int((i + 1) / total_files * 100)
                进度回调(progress)
        except Exception as e:
            raise Exception(f"处理文件 {file_path} 时出错: {str(e)}")
    
    # 生成输出文件名
    output_path = os.path.join(os.path.dirname(file_paths[0]), "合并结果.pdf")
    
    # 保存新PDF
    new_pdf.save(output_path)
    new_pdf.close()
    
    return output_path


def PDF分离(文件路径文本, 进度回调=None):
    """
    将PDF文件分离为单页
    
    参数:
    文件路径文本: 包含PDF文件路径的文本
    进度回调: 进度回调函数，用于更新进度条
    """
    # 解析文件路径
    file_paths = []
    for f in 文件路径文本.strip().split('\n'):
        path = f.strip()
        # 移除URL前缀
        if path.startswith('file:///'):
            path = path[8:]
        elif path.startswith('file://'):
            path = path[7:]
        if path.lower().endswith('.pdf'):
            file_paths.append(path)
    
    if not file_paths:
        raise ValueError("没有找到有效的PDF文件路径")
    
    for file_path in file_paths:
        try:
            # 打开PDF文件
            pdf = fitz.open(file_path)
            
            # 获取文件目录
            file_dir = os.path.dirname(file_path)
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # 创建输出目录
            output_dir = os.path.join(file_dir, f"{file_name}_分离结果")
            os.makedirs(output_dir, exist_ok=True)
            
            total_pages = len(pdf)
            
            # 分离每一页
            for page_num in range(total_pages):
                # 创建新PDF
                new_pdf = fitz.open()
                new_pdf.insert_pdf(pdf, from_page=page_num, to_page=page_num)
                
                # 生成输出文件名
                output_path = os.path.join(output_dir, f"{file_name}_{page_num + 1}.pdf")
                
                # 保存新PDF
                new_pdf.save(output_path)
                new_pdf.close()
                
                # 更新进度
            if 进度回调:
                progress = int((page_num + 1) / total_pages * 100)
                进度回调(progress)
            
            # 关闭当前PDF
            pdf.close()
        except Exception as e:
            raise Exception(f"处理文件 {file_path} 时出错: {str(e)}")


def PDF转图片(文件路径文本, 进度回调=None):
    """
    将PDF文件转换为图片
    
    参数:
    文件路径文本: 包含PDF文件路径的文本
    进度回调: 进度回调函数，用于更新进度条
    """
    # 解析文件路径
    file_paths = []
    for f in 文件路径文本.strip().split('\n'):
        path = f.strip()
        # 移除URL前缀
        if path.startswith('file:///'):
            path = path[8:]
        elif path.startswith('file://'):
            path = path[7:]
        if path.lower().endswith('.pdf'):
            file_paths.append(path)
    
    if not file_paths:
        raise ValueError("没有找到有效的PDF文件路径")
    
    for file_path in file_paths:
        try:
            # 打开PDF文件
            pdf = fitz.open(file_path)
            
            # 获取文件目录
            file_dir = os.path.dirname(file_path)
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # 创建输出目录
            output_dir = os.path.join(file_dir, f"{file_name}_图片结果")
            os.makedirs(output_dir, exist_ok=True)
            
            total_pages = len(pdf)
            
            # 转换每一页
            for page_num in range(total_pages):
                # 获取页面
                page = pdf[page_num]
                
                # 设置图片分辨率
                pix = page.get_pixmap(dpi=300)
                
                # 生成输出文件名
                output_path = os.path.join(output_dir, f"{file_name}_{page_num + 1}.png")
                
                # 保存图片
                pix.save(output_path)
                
                # 更新进度
            if 进度回调:
                progress = int((page_num + 1) / total_pages * 100)
                进度回调(progress)
            
            # 关闭当前PDF
            pdf.close()
        except Exception as e:
            raise Exception(f"处理文件 {file_path} 时出错: {str(e)}")


def 图片转PDF(文件路径文本, 进度回调=None):
    """
    将多张图片转换为一个PDF文件
    
    参数:
    文件路径文本: 包含图片文件路径的文本，每行一个路径
    进度回调: 进度回调函数，用于更新进度条
    """
    # 解析文件路径
    file_paths = []
    for f in 文件路径文本.strip().split('\n'):
        path = f.strip()
        # 移除URL前缀
        if path.startswith('file:///'):
            path = path[8:]
        elif path.startswith('file://'):
            path = path[7:]
        if path and any(path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']):
            file_paths.append(path)
    
    if not file_paths:
        raise ValueError("没有找到有效的图片文件路径")
    
    # 生成输出文件名
    output_path = os.path.join(os.path.dirname(file_paths[0]), "图片转PDF结果.pdf")
    
    total_files = len(file_paths)
    
    # 转换图片为PDF
    with open(output_path, 'wb') as f:
        # 遍历所有图片文件
        for i, file_path in enumerate(file_paths):
            try:
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    continue
                
                # 更新进度
                if 进度回调:
                    progress = int((i + 1) / total_files * 100)
                    进度回调(progress)
            except Exception as e:
                raise Exception(f"处理文件 {file_path} 时出错: {str(e)}")
        
        # 转换并保存PDF
        f.write(img2pdf.convert(file_paths))

    return output_path
