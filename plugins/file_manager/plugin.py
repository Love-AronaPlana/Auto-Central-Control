#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
plugins/file_manager/plugin.py - 文件管理插件

该模块提供文件读写操作功能，供执行Agent使用。
"""

import os
import json
import shutil
from typing import Dict, Any, List, Optional

# 插件信息，用于系统识别
PLUGIN_INFO = {
    'name': '文件管理器',
    'description': '提供文件读写、创建、删除等基本操作',
    'version': '1.0.0',
    'author': 'Auto-Central-Control'
}

def read_file(file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        encoding: 文件编码，默认为utf-8
        
    Returns:
        Dict[str, Any]: 操作结果
    """
    try:
        if not os.path.exists(file_path):
            return {
                'status': 'error',
                'message': f'文件不存在: {file_path}'
            }
            
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
            
        return {
            'status': 'success',
            'content': content,
            'file_path': file_path
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'读取文件失败: {str(e)}'
        }

def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码，默认为utf-8
        
    Returns:
        Dict[str, Any]: 操作结果
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
            
        return {
            'status': 'success',
            'message': f'文件写入成功: {file_path}',
            'file_path': file_path
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'写入文件失败: {str(e)}'
        }

def append_file(file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """
    追加文件内容
    
    Args:
        file_path: 文件路径
        content: 追加的内容
        encoding: 文件编码，默认为utf-8
        
    Returns:
        Dict[str, Any]: 操作结果
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'a', encoding=encoding) as f:
            f.write(content)
            
        return {
            'status': 'success',
            'message': f'文件追加成功: {file_path}',
            'file_path': file_path
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'追加文件失败: {str(e)}'
        }

def delete_file(file_path: str) -> Dict[str, Any]:
    """
    删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict[str, Any]: 操作结果
    """
    try:
        if not os.path.exists(file_path):
            return {
                'status': 'error',
                'message': f'文件不存在: {file_path}'
            }
            
        os.remove(file_path)
            
        return {
            'status': 'success',
            'message': f'文件删除成功: {file_path}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'删除文件失败: {str(e)}'
        }

def list_files(directory: str) -> Dict[str, Any]:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        
    Returns:
        Dict[str, Any]: 操作结果
    """
    try:
        if not os.path.exists(directory):
            return {
                'status': 'error',
                'message': f'目录不存在: {directory}'
            }
            
        if not os.path.isdir(directory):
            return {
                'status': 'error',
                'message': f'路径不是目录: {directory}'
            }
            
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            item_type = 'directory' if os.path.isdir(item_path) else 'file'
            files.append({
                'name': item,
                'path': item_path,
                'type': item_type
            })
            
        return {
            'status': 'success',
            'directory': directory,
            'files': files
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'列出文件失败: {str(e)}'
        }