#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
tools/text_analyzer/analyzer.py - 文本分析工具

该模块提供文本分析功能，包括关键词提取、情感分析等。
"""

import re
import json
from typing import Dict, Any, List, Tuple
from collections import Counter

# 工具信息
TOOL_INFO = {
    'name': '文本分析器',
    'description': '提供文本分析功能，包括关键词提取、情感分析等',
    'version': '1.0.0',
    'author': 'Auto-Central-Control'
}

def extract_keywords(text: str, top_n: int = 10) -> Dict[str, Any]:
    """
    从文本中提取关键词
    
    Args:
        text: 待分析的文本
        top_n: 返回的关键词数量
        
    Returns:
        Dict[str, Any]: 分析结果
    """
    try:
        # 简单的关键词提取实现，实际应用中可以使用更复杂的算法
        # 移除标点符号和特殊字符
        text = re.sub(r'[^\w\s]', '', text)
        
        # 分词
        words = text.lower().split()
        
        # 过滤停用词（简化版）
        stop_words = {'的', '了', '和', '是', '在', '我', '有', '这', '个', '你', '们', 'to', 'the', 'a', 'of', 'and', 'in', 'is', 'it', 'that'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 统计词频
        word_counts = Counter(filtered_words)
        
        # 获取前N个高频词
        top_keywords = word_counts.most_common(top_n)
        
        return {
            'status': 'success',
            'keywords': [{'word': word, 'count': count} for word, count in top_keywords],
            'total_words': len(words)
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'关键词提取失败: {str(e)}'
        }

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    对文本进行情感分析
    
    Args:
        text: 待分析的文本
        
    Returns:
        Dict[str, Any]: 分析结果
    """
    try:
        # 简单的情感分析实现，实际应用中可以使用机器学习模型
        positive_words = {'好', '喜欢', '优秀', '棒', '赞', '爱', '满意', '开心', '高兴', '快乐',
                         'good', 'great', 'excellent', 'awesome', 'nice', 'love', 'happy', 'positive'}
        negative_words = {'差', '糟糕', '讨厌', '坏', '失望', '不满', '生气', '悲伤', '痛苦',
                         'bad', 'terrible', 'hate', 'awful', 'disappointed', 'negative', 'sad', 'angry'}
        
        # 分词并计数
        words = re.sub(r'[^\w\s]', '', text.lower()).split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # 计算情感得分 (-1 到 1)
        total = positive_count + negative_count
        if total == 0:
            sentiment_score = 0
        else:
            sentiment_score = (positive_count - negative_count) / total
        
        # 确定情感类别
        if sentiment_score > 0.2:
            sentiment = 'positive'
        elif sentiment_score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'status': 'success',
            'sentiment': sentiment,
            'score': sentiment_score,
            'positive_words': positive_count,
            'negative_words': negative_count
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'情感分析失败: {str(e)}'
        }

def count_statistics(text: str) -> Dict[str, Any]:
    """
    统计文本的基本信息
    
    Args:
        text: 待分析的文本
        
    Returns:
        Dict[str, Any]: 统计结果
    """
    try:
        # 计算字符数
        char_count = len(text)
        
        # 计算单词数
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        
        # 计算句子数
        sentences = re.split(r'[.!?。！？]', text)
        sentence_count = sum(1 for s in sentences if s.strip())
        
        # 计算段落数
        paragraphs = text.split('\n\n')
        paragraph_count = sum(1 for p in paragraphs if p.strip())
        
        return {
            'status': 'success',
            'char_count': char_count,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'统计分析失败: {str(e)}'
        }