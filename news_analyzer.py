#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
新闻分析器 - TK界面版

该文件实现了新闻分析的核心功能，包括：
- 从RSS源获取新闻数据
- 使用LLM模型分析新闻
- 提供TK图形界面
"""

import sys
import os
import logging
import time
import json
import ssl
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from urllib.request import urlopen, Request
from urllib.error import URLError
import xml.etree.ElementTree as ET
import importlib.util


# 设置日志记录
def setup_logging():
    """设置日志记录"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'news_analyzer_gui.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 创建日志记录器
    logger = logging.getLogger('news_analyzer_gui')
    logger.info('新闻分析器GUI启动')
    
    return logger


# 初始化日志
logger = setup_logging()


class RSSCollector:
    """RSS新闻收集器类"""
    
    def __init__(self):
        """初始化RSS收集器"""
        self.logger = logging.getLogger('news_analyzer_gui.collector')
        self.sources = []
        self.news_cache = []
        
        # 设置保存文件路径
        self.sources_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'news_sources.json')
        
        # 创建SSL上下文以处理HTTPS请求
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # 尝试加载保存的新闻源设置
        if not self.load_sources():
            # 如果没有保存的设置，加载默认新闻源
            self._add_default_sources()
            # 保存默认设置
            self.save_sources()
    
    def save_sources(self):
        """保存新闻源设置到文件"""
        try:
            with open(self.sources_file, 'w', encoding='utf-8') as f:
                json.dump(self.sources, f, ensure_ascii=False, indent=4)
            self.logger.info(f"成功保存 {len(self.sources)} 个新闻源设置")
            return True
        except Exception as e:
            self.logger.error(f"保存新闻源设置失败: {str(e)}")
            return False
    
    def load_sources(self):
        """从文件加载新闻源设置"""
        if not os.path.exists(self.sources_file):
            self.logger.info("新闻源设置文件不存在，使用默认设置")
            return False
        
        try:
            with open(self.sources_file, 'r', encoding='utf-8') as f:
                saved_sources = json.load(f)
            
            if isinstance(saved_sources, list) and len(saved_sources) > 0:
                self.sources = saved_sources
                self.logger.info(f"成功加载 {len(self.sources)} 个新闻源设置")
                return True
            else:
                self.logger.warning("保存的新闻源设置格式不正确，使用默认设置")
                return False
        except Exception as e:
            self.logger.error(f"加载新闻源设置失败: {str(e)}")
            return False
    
    def _add_default_sources(self):
        """添加默认新闻源"""
        # 获取所有新闻源 - 直接从内置数据获取，不再依赖外部文件
        all_sources = self._get_default_sources()
        
        # 添加所有新闻源
        for source in all_sources:
            self.add_source(**source)
            
        self.logger.info(f"成功加载 {len(all_sources)} 个新闻源")
    
    def _get_default_sources(self):
        """
        获取默认的RSS新闻源列表
        
        Returns:
            list: 包含预设新闻源信息的字典列表
        """
        return [
            # 综合新闻 - 中文
            {
                "url": "https://www.thepaper.cn/rss_newslist.jsp",
                "name": "澎湃新闻",
                "category": "综合新闻"
            },
            {
                "url": "https://feedx.net/rss/weixin.xml",
                "name": "微信热门",
                "category": "综合新闻"
            },
            {
                "url": "https://rsshub.app/reuters/cn/china",
                "name": "路透中文网",
                "category": "综合新闻"
            },
            {
                "url": "https://www.zaobao.com/rss/realtime/china",
                "name": "联合早报",
                "category": "综合新闻"
            },
            {
                "url": "https://www.ftchinese.com/rss/feed",
                "name": "FT中文网",
                "category": "综合新闻"
            },
            {
                "url": "https://feedx.net/rss/bbc.xml",
                "name": "BBC中文网",
                "category": "综合新闻"
            },
            
            # 国际新闻
            {
                "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
                "name": "纽约时报国际",
                "category": "国际新闻"
            },
            {
                "url": "https://feeds.washingtonpost.com/rss/world",
                "name": "华盛顿邮报国际",
                "category": "国际新闻"
            },
            {
                "url": "https://www.theguardian.com/world/rss",
                "name": "卫报国际",
                "category": "国际新闻"
            },
            {
                "url": "https://www.aljazeera.com/xml/rss/all.xml",
                "name": "半岛电视台",
                "category": "国际新闻"
            },
            {
                "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
                "name": "BBC国际",
                "category": "国际新闻"
            },
            {
                "url": "https://feedx.net/rss/cnn.xml",
                "name": "CNN国际",
                "category": "国际新闻"
            },
            {
                "url": "https://www.nhk.or.jp/rss/news/cat6.xml",
                "name": "NHK国际",
                "category": "国际新闻"
            },
            
            # 科技新闻
            {
                "url": "https://feedx.net/rss/wired.xml",
                "name": "WIRED",
                "category": "科技新闻"
            },
            {
                "url": "https://www.engadget.com/rss.xml",
                "name": "Engadget",
                "category": "科技新闻"
            },
            {
                "url": "https://www.theverge.com/rss/index.xml",
                "name": "The Verge",
                "category": "科技新闻"
            },
            {
                "url": "https://techcrunch.com/feed/",
                "name": "TechCrunch",
                "category": "科技新闻"
            },
            {
                "url": "https://feeds.arstechnica.com/arstechnica/index",
                "name": "Ars Technica",
                "category": "科技新闻"
            },
            {
                "url": "https://www.solidot.org/index.rss",
                "name": "Solidot",
                "category": "科技新闻"
            },
            {
                "url": "https://rsshub.app/36kr/news/latest",
                "name": "36氪",
                "category": "科技新闻"
            },
            {
                "url": "https://sspai.com/feed",
                "name": "少数派",
                "category": "科技新闻"
            },
            
            # 商业与金融
            {
                "url": "https://www.economist.com/finance-and-economics/rss.xml",
                "name": "经济学人",
                "category": "商业与金融"
            },
            {
                "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
                "name": "华尔街日报市场",
                "category": "商业与金融"
            },
            {
                "url": "https://www.ft.com/rss/home/uk",
                "name": "金融时报",
                "category": "商业与金融"
            },
            {
                "url": "https://www.forbes.com/business/feed/",
                "name": "福布斯商业",
                "category": "商业与金融"
            },
            {
                "url": "https://www.businessinsider.com/rss",
                "name": "商业内幕",
                "category": "商业与金融"
            },
            {
                "url": "https://www.cnbc.com/id/10001147/device/rss/rss.html",
                "name": "CNBC财经",
                "category": "商业与金融"
            },
            {
                "url": "https://rsshub.app/caixin/finance/regulation",
                "name": "财新网",
                "category": "商业与金融"
            },
            
            # 政治新闻
            {
                "url": "https://rss.politico.com/politics.xml",
                "name": "Politico",
                "category": "政治新闻"
            },
            {
                "url": "https://www.realclearpolitics.com/index.xml",
                "name": "RealClearPolitics",
                "category": "政治新闻"
            },
            {
                "url": "https://thehill.com/feed",
                "name": "The Hill",
                "category": "政治新闻"
            },
            {
                "url": "https://feeds.nbcnews.com/nbcnews/public/politics",
                "name": "NBC政治",
                "category": "政治新闻"
            },
            {
                "url": "https://feeds.bbci.co.uk/news/politics/rss.xml",
                "name": "BBC政治",
                "category": "政治新闻"
            },
            
            # 科学新闻
            {
                "url": "https://www.science.org/rss/news_current.xml",
                "name": "Science",
                "category": "科学新闻"
            },
            {
                "url": "https://www.nature.com/nature.rss",
                "name": "Nature",
                "category": "科学新闻"
            },
            {
                "url": "https://feeds.newscientist.com/science-news",
                "name": "New Scientist",
                "category": "科学新闻"
            },
            {
                "url": "https://phys.org/rss-feed/",
                "name": "Phys.org",
                "category": "科学新闻"
            },
            {
                "url": "https://www.scientificamerican.com/rss/feed.rdf?name=sciam",
                "name": "Scientific American",
                "category": "科学新闻"
            },
            {
                "url": "https://www.space.com/feeds/all",
                "name": "Space.com",
                "category": "科学新闻"
            },
            
            # 体育新闻
            {
                "url": "https://www.espn.com/espn/rss/news",
                "name": "ESPN",
                "category": "体育新闻"
            },
            {
                "url": "https://www.skysports.com/rss/12040",
                "name": "Sky Sports",
                "category": "体育新闻"
            },
            {
                "url": "https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml",
                "name": "纽约时报体育",
                "category": "体育新闻"
            },
            {
                "url": "https://api.foxsports.com/v1/rss?partnerKey=zBaFxRyGKCfxBagJG9b8pqLyndmvo7UU",
                "name": "Fox Sports",
                "category": "体育新闻"
            },
            {
                "url": "https://www.cbssports.com/rss/headlines",
                "name": "CBS Sports",
                "category": "体育新闻"
            },
            {
                "url": "https://www.theguardian.com/sport/rss",
                "name": "卫报体育",
                "category": "体育新闻"
            },
            
            # 娱乐新闻
            {
                "url": "https://www.hollywoodreporter.com/feed/",
                "name": "好莱坞记者",
                "category": "娱乐新闻"
            },
            {
                "url": "https://variety.com/feed/",
                "name": "Variety",
                "category": "娱乐新闻"
            },
            {
                "url": "https://www.eonline.com/feeds/topstories.atom",
                "name": "E! Online",
                "category": "娱乐新闻"
            },
            {
                "url": "https://deadline.com/feed/",
                "name": "Deadline",
                "category": "娱乐新闻"
            },
            {
                "url": "https://www.tmz.com/rss.xml",
                "name": "TMZ",
                "category": "娱乐新闻"
            },
            
            # 健康与医疗
            {
                "url": "https://www.medicalnewstoday.com/newsfeeds/rss/medical_all.xml",
                "name": "Medical News Today",
                "category": "健康与医疗"
            },
            {
                "url": "https://rss.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
                "name": "WebMD",
                "category": "健康与医疗"
            },
            {
                "url": "https://tools.cdc.gov/api/v2/resources/media/316422.rss",
                "name": "CDC",
                "category": "健康与医疗"
            },
            {
                "url": "https://www.health.harvard.edu/rss/health",
                "name": "哈佛健康",
                "category": "健康与医疗"
            },
            {
                "url": "https://feeds.feedburner.com/nejm/research",
                "name": "新英格兰医学杂志",
                "category": "健康与医疗"
            },
            
            # 文化与教育
            {
                "url": "https://www.arts.gov/rss-feed",
                "name": "National Endowment for the Arts",
                "category": "文化与教育"
            },
            {
                "url": "https://www.theparisreview.org/feed/",
                "name": "巴黎评论",
                "category": "文化与教育"
            },
            {
                "url": "https://www.chronicle.com/feed",
                "name": "高等教育纪事报",
                "category": "文化与教育"
            },
            {
                "url": "https://www.insidehighered.com/rss/feed/ihe",
                "name": "Inside Higher Ed",
                "category": "文化与教育"
            },
            {
                "url": "https://www.smithsonianmag.com/rss/arts-culture/",
                "name": "史密森尼杂志",
                "category": "文化与教育"
            }
        ]
    
    def add_source(self, url, name=None, category="未分类", enabled=True):
        """添加RSS新闻源
        
        Args:
            url: RSS源URL
            name: 来源名称（可选）
            category: 分类名称（可选）
            enabled: 是否启用该源
        """
        if not url:
            raise ValueError("URL不能为空")
        
        # 如果没有提供名称，使用URL作为默认名称
        if not name:
            name = url.split("//")[-1].split("/")[0]
        
        # 检查是否已存在相同URL的源
        for source in self.sources:
            if source['url'] == url:
                self.logger.warning(f"RSS源已存在: {url}")
                return
        
        # 添加新源
        self.sources.append({
            'url': url,
            'name': name,
            'category': category,
            'enabled': enabled
        })
        
        self.logger.info(f"添加RSS源: {name} ({url}), 分类: {category}, 状态: {'启用' if enabled else '禁用'}")
    
    def toggle_source(self, url, enabled):
        """启用或禁用指定URL的新闻源
        
        Args:
            url: RSS源URL
            enabled: 是否启用
        
        Returns:
            bool: 操作是否成功
        """
        for source in self.sources:
            if source['url'] == url:
                source['enabled'] = enabled
                self.logger.info(f"{'启用' if enabled else '禁用'}RSS源: {source['name']} ({url})")
                return True
        self.logger.warning(f"未找到RSS源: {url}")
        return False
    
    def get_enabled_sources(self):
        """获取所有启用的新闻源
        
        Returns:
            list: 启用的新闻源列表
        """
        return [source for source in self.sources if source.get('enabled', True)]
    
    def fetch_all(self):
        """从所有RSS源获取新闻
        
        Returns:
            list: 新闻条目列表
        """
        all_news = []
        
        # 只从启用的新闻源获取新闻
        for source in self.get_enabled_sources():
            try:
                items = self._fetch_rss(source)
                all_news.extend(items)
                self.logger.info(f"从 {source['name']} 获取了 {len(items)} 条新闻")
            except Exception as e:
                self.logger.error(f"从 {source['name']} 获取新闻失败: {str(e)}")
                # 自动禁用获取失败的新闻源
                self.toggle_source(source['url'], False)
                self.logger.warning(f"已自动禁用新闻源: {source['name']} ({source['url']})")
        
        # 去重
        unique_news = self._remove_duplicates(all_news)
        
        # 更新缓存
        self.news_cache = unique_news
        
        return unique_news
    
    def get_all_news(self):
        """获取所有缓存的新闻
        
        Returns:
            list: 新闻条目列表
        """
        return self.news_cache
    
    def get_news_by_category(self, category):
        """按分类获取新闻
        
        Args:
            category: 分类名称
            
        Returns:
            list: 该分类下的新闻条目列表
        """
        if not category or category == "所有":
            return self.news_cache
        
        return [item for item in self.news_cache if item.get('category') == category]
    
    def fetch_by_category(self, category):
        """按分类从RSS源获取新闻
        
        Args:
            category: 分类名称
            
        Returns:
            list: 该分类下的新闻条目列表
        """
        all_news = []
        
        # 获取该分类下的所有启用新闻源
        category_sources = [source for source in self.get_enabled_sources() 
                          if source.get('category') == category]
        
        # 只从该分类的新闻源获取新闻
        for source in category_sources:
            try:
                items = self._fetch_rss(source)
                all_news.extend(items)
                self.logger.info(f"从 {source['name']} 获取了 {len(items)} 条新闻")
            except Exception as e:
                self.logger.error(f"从 {source['name']} 获取新闻失败: {str(e)}")
                # 自动禁用获取失败的新闻源
                self.toggle_source(source['url'], False)
                self.logger.warning(f"已自动禁用新闻源: {source['name']} ({source['url']})")
        
        # 去重
        unique_news = self._remove_duplicates(all_news)
        
        # 注意：这里不更新缓存，因为只获取部分分类的新闻
        
        return unique_news
    
    def get_sources(self):
        """获取所有RSS源
        
        Returns:
            list: RSS源列表
        """
        return self.sources
    
    def get_categories(self):
        """获取所有分类
        
        Returns:
            list: 分类名称列表
        """
        categories = set()
        for source in self.sources:
            categories.add(source['category'])
        return sorted(list(categories))
    
    def _fetch_rss(self, source):
        """从RSS源获取新闻
        
        Args:
            source: 新闻源信息字典
            
        Returns:
            list: 新闻条目列表
        """
        items = []
        
        try:
            # 创建带User-Agent的请求以避免被屏蔽
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = Request(source['url'], headers=headers)
            
            # 获取RSS内容
            with urlopen(req, context=self.ssl_context, timeout=10) as response:
                rss_content = response.read().decode('utf-8', errors='ignore')
            
            # 解析XML
            root = ET.fromstring(rss_content)
            
            # 处理不同的RSS格式
            if root.tag == 'rss':
                # 标准RSS格式
                channel = root.find('channel')
                if channel is not None:
                    for item in channel.findall('item'):
                        news_item = self._parse_rss_item(item, source)
                        if news_item:
                            items.append(news_item)
            
            elif root.tag.endswith('feed'):
                # Atom格式
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    news_item = self._parse_atom_entry(entry, source)
                    if news_item:
                        items.append(news_item)
            
        except Exception as e:
            self.logger.error(f"获取 {source['name']} 的新闻失败: {str(e)}")
        
        return items
    
    def _parse_rss_item(self, item, source):
        """解析RSS条目
        
        Args:
            item: RSS条目XML元素
            source: 来源信息
            
        Returns:
            dict: 新闻条目字典
        """
        try:
            # 提取标题和链接（必需字段）
            title_elem = item.find('title')
            link_elem = item.find('link')
            
            if title_elem is None or link_elem is None:
                return None
            
            title = title_elem.text or ""
            link = link_elem.text or ""
            
            if not title or not link:
                return None
            
            # 提取描述和发布日期（可选字段）
            description = ""
            desc_elem = item.find('description')
            if desc_elem is not None and desc_elem.text:
                # 简单清理HTML标签
                description = re.sub(r'<[^>]+>', ' ', desc_elem.text)
                description = re.sub(r'\s+', ' ', description).strip()
            
            pub_date = ""
            date_elem = item.find('pubDate')
            if date_elem is not None and date_elem.text:
                pub_date = date_elem.text
            
            # 创建新闻条目
            return {
                'title': title,
                'link': link,
                'description': description,
                'pub_date': pub_date,
                'source_name': source['name'],
                'source_url': source['url'],
                'category': source['category'],
                'collected_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"解析RSS条目失败: {str(e)}")
            return None
    
    def _parse_atom_entry(self, entry, source):
        """解析Atom条目
        
        Args:
            entry: Atom条目XML元素
            source: 来源信息
            
        Returns:
            dict: 新闻条目字典
        """
        try:
            # 提取标题（必需字段）
            title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
            if title_elem is None:
                return None
            
            title = title_elem.text or ""
            
            # 提取链接
            link = ""
            link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
            if link_elem is not None:
                link = link_elem.get('href', '')
            
            if not title or not link:
                return None
            
            # 提取内容和发布日期
            content = ""
            content_elem = entry.find('{http://www.w3.org/2005/Atom}content')
            if content_elem is not None and content_elem.text:
                # 简单清理HTML标签
                content = re.sub(r'<[^>]+>', ' ', content_elem.text)
                content = re.sub(r'\s+', ' ', content).strip()
            
            # 如果没有内容，尝试使用摘要
            if not content:
                summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                if summary_elem is not None and summary_elem.text:
                    content = re.sub(r'<[^>]+>', ' ', summary_elem.text)
                    content = re.sub(r'\s+', ' ', content).strip()
            
            pub_date = ""
            date_elem = entry.find('{http://www.w3.org/2005/Atom}published')
            if date_elem is not None and date_elem.text:
                pub_date = date_elem.text
            
            # 创建新闻条目
            return {
                'title': title,
                'link': link,
                'description': content,
                'pub_date': pub_date,
                'source_name': source['name'],
                'source_url': source['url'],
                'category': source['category'],
                'collected_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"解析Atom条目失败: {str(e)}")
            return None
    
    def _remove_duplicates(self, news_items):
        """移除重复的新闻条目
        
        Args:
            news_items: 新闻条目列表
            
        Returns:
            list: 去重后的新闻条目列表
        """
        unique_items = {}
        
        for item in news_items:
            # 使用标题作为去重键
            key = item.get('title', '')
            if key and key not in unique_items:
                unique_items[key] = item
        
        return list(unique_items.values())


class LLMClient:
    """LLM客户端类"""
    
    def __init__(self, api_key=None, api_url=None, model=None):
        """初始化LLM客户端
        
        Args:
            api_key: API密钥，如果为None则使用本地Ollama模型
            api_url: API URL，如果为None则使用默认值
            model: 模型名称，如果为None则使用默认值
        """
        self.logger = logging.getLogger('news_analyzer_gui.llm.client')
        
        # 设置API密钥（优先使用参数，其次使用环境变量）
        self.api_key = api_key or os.environ.get('LLM_API_KEY', '')
        
        # 优先使用本地Ollama模型
        if not self.api_key:
            # 设置为本地Ollama模型
            self.api_url = "http://localhost:11434/api/generate"
            self.model = "llama3"
        else:
            # 设置API URL
            self.api_url = api_url or os.environ.get(
                'LLM_API_URL', 
                'https://api.openai.com/v1/chat/completions'
            )
            
            # 设置模型
            self.model = model or os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')
        
        # 默认参数
        self.temperature = 0.7
        self.max_tokens = 2048
        self.timeout = 60
        
        # 确定API类型
        self.api_type = self._determine_api_type()
        self.logger.info(f"初始化LLM客户端，API类型: {self.api_type}, 模型: {self.model}")
    
    def _determine_api_type(self):
        """确定API类型"""
        url_lower = self.api_url.lower()
        if "openai.com" in url_lower:
            return "openai"
        elif "anthropic.com" in url_lower:
            return "anthropic"
        elif "localhost" in url_lower or "127.0.0.1" in url_lower:
            return "ollama"
        else:
            return "generic"
    
    def analyze_news(self, news_item, analysis_type='摘要'):
        """分析新闻
        
        Args:
            news_item: 新闻数据字典
            analysis_type: 分析类型，默认为'摘要'
            
        Returns:
            str: 格式化的分析结果
        """
        if not news_item:
            raise ValueError("新闻数据不能为空")
        
        # If API key is not set and not using ollama model, return mock analysis
        if not self.api_key and self.api_type != "ollama":
            return self._mock_analysis(news_item, analysis_type)
        
        # 获取提示词
        prompt = self._get_prompt(analysis_type, news_item)
        
        try:
            # 调用API
            headers = self._get_headers()
            
            # 根据API类型准备请求数据
            if self.api_type == "anthropic":
                data = self._prepare_anthropic_request(prompt)
            elif self.api_type == "ollama":
                data = self._prepare_ollama_request(prompt)
            else:  # OpenAI或通用格式
                data = {
                    'model': self.model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': self.temperature,
                    'max_tokens': self.max_tokens
                }
            
            import requests
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # 处理Ollama API的特殊响应格式（流式响应，每行一个JSON对象）
            if self.api_type == "ollama":
                # 读取响应内容并按行处理，拼接所有response字段
                response_text = response.text
                full_response = ""
                last_result = None
                
                for line in response_text.strip().split('\n'):
                    if line:
                        try:
                            result = json.loads(line)
                            last_result = result
                            # 拼接所有response内容
                            if 'response' in result:
                                full_response += result['response']
                        except json.JSONDecodeError:
                            continue
                
                if not last_result:
                    raise ValueError("API返回的内容为空")
                
                # 使用拼接后的完整响应
                content = full_response
            else:
                # 普通JSON响应
                result = response.json()
                content = self._extract_content_from_response(result)
            
            if not content:
                raise ValueError("API返回的内容为空")
            
            return content
            
        except Exception as e:
            self.logger.error(f"调用LLM API失败: {str(e)}")
            return f"错误：调用LLM API失败 - {str(e)}"
    
    def _prepare_anthropic_request(self, prompt):
        """准备Anthropic API请求
        
        Args:
            prompt: 提示文本
            
        Returns:
            dict: 请求数据
        """
        return {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }
    
    def _prepare_ollama_request(self, prompt):
        """准备Ollama API请求
        
        Args:
            prompt: 提示文本
            
        Returns:
            dict: 请求数据
        """
        # 根据API端点选择请求格式
        if '/api/generate' in self.api_url:
            # /api/generate 端点使用 prompt 参数
            return {
                'model': self.model,
                'prompt': prompt,
                'options': {
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens
                }
            }
        else:
            # /api/chat 端点使用 messages 参数
            return {
                'model': self.model,
                'messages': [{'role': 'user', 'content': prompt}],
                'options': {
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens
                }
            }
    
    def _extract_content_from_response(self, result):
        """从不同API响应中提取内容
        
        Args:
            result: API响应的JSON数据
            
        Returns:
            str: 提取的文本内容
        """
        if self.api_type == "anthropic":
            # 处理各种Claude API格式
            if 'content' in result and isinstance(result['content'], list):
                for item in result['content']:
                    if item.get('type') == 'text':
                        return item.get('text', '')
            return result.get('content', [{}])[0].get('text', '')
        elif self.api_type == "ollama":
            return result.get('response', '')
        else:  # OpenAI或通用格式
            return result.get('choices', [{}])[0].get('message', {}).get('content', '')
    
    def _get_headers(self):
        """获取请求头
        
        Returns:
            dict: 请求头
        """
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 根据API类型设置认证头 - Ollama本地模型不需要认证
        if self.api_type == "anthropic":
            headers['x-api-key'] = self.api_key
            headers['anthropic-version'] = '2023-06-01'  # 使用适当的API版本
        elif self.api_type == "openai":
            headers['Authorization'] = f'Bearer {self.api_key}'
        # Ollama模型不需要认证头，跳过else分支
        
        return headers
    
    def _get_prompt(self, analysis_type, news_item):
        """获取提示词
        
        Args:
            analysis_type: 分析类型
            news_item: 新闻数据
            
        Returns:
            str: 提示词
        """
        title = news_item.get('title', '无标题')
        source = news_item.get('source_name', '未知来源')
        content = news_item.get('description', '无内容')
        pub_date = news_item.get('pub_date', '未知日期')
        
        if analysis_type == '摘要':
            return f"""
            请对以下新闻进行简明扼要的摘要分析，确保所有输出内容均为中文。
            
            新闻标题: {title}
            新闻来源: {source}
            发布日期: {pub_date}
            
            新闻内容:
            {content}
            
            请提供:
            1. 一段200字以内的新闻摘要，包含关键信息点
            2. 3-5个要点列表，提炼新闻中最重要的信息
            
            注意：请确保所有分析结果均为中文，即使新闻内容是英文也需翻译成中文后进行分析。
            """
        elif analysis_type == '深度分析':
            return f"""
            请对以下新闻进行深度分析，确保所有输出内容均为中文。
            
            新闻标题: {title}
            新闻来源: {source}
            新闻内容:
            {content}
            
            请提供背景、影响和发展趋势分析。
            
            注意：请确保所有分析结果均为中文，即使新闻内容是英文也需翻译成中文后进行分析。
            """
        elif analysis_type == '关键观点':
            return f"""
            请提取以下新闻中的关键观点和立场，确保所有输出内容均为中文。
            
            新闻标题: {title}
            新闻来源: {source}
            新闻内容:
            {content}
            
            请分析:
            1. 新闻中表达的主要观点
            2. 各方立场和态度
            3. 潜在的倾向性或偏见
            
            注意：请确保所有分析结果均为中文，即使新闻内容是英文也需翻译成中文后进行分析。
            """
        elif analysis_type == '事实核查':
            return f"""
            请对以下新闻进行事实核查分析，确保所有输出内容均为中文。
            
            新闻标题: {title}
            新闻来源: {source}
            新闻内容:
            {content}
            
            请分析:
            1. 新闻中的主要事实声明
            2. 可能需要核实的关键信息点
            3. 潜在的误导或不准确之处
            
            注意：请确保所有分析结果均为中文，即使新闻内容是英文也需翻译成中文后进行分析。
            """
        else:
            return f"""
            请对以下新闻进行{analysis_type}，确保所有输出内容均为中文。
            
            新闻标题: {title}
            新闻来源: {source}
            新闻内容:
            {content}
            
            注意：请确保所有分析结果均为中文，即使新闻内容是英文也需翻译成中文后进行分析。
            """
    
    def _mock_analysis(self, news_item, analysis_type):
        """模拟分析结果
        
        Args:
            news_item: 新闻数据
            analysis_type: 分析类型
            
        Returns:
            str: 模拟的结果
        """
        title = news_item.get('title', '无标题')
        
        return f"这是对\"{title}\"的{analysis_type}。\n\n由于未设置API密钥，这是一个模拟结果。请在设置中配置有效的LLM API密钥以获取真实分析。"


class NewsAnalyzerGUI:
    """新闻分析器GUI类"""
    
    def __init__(self, root):
        """初始化GUI
        
        Args:
            root: TK根窗口
        """
        self.root = root
        self.root.title("新闻分析器")
        self.root.geometry("1000x700")
        
        # 初始化新闻收集器
        self.rss_collector = RSSCollector()
        
        # 添加默认新闻源（示例）
        self._add_default_sources()
        
        # 初始化LLM客户端
        self.llm_client = LLMClient()
        
        # 当前选中的新闻
        self.selected_news = None
        
        # 创建界面
        self._create_widgets()
        
    def _add_default_sources(self):
        """添加默认新闻源"""
        # 获取所有新闻源 - 直接从内置数据获取，不再依赖外部文件
        all_sources = self._get_default_sources()
        
        # 添加所有新闻源
        for source in all_sources:
            self.rss_collector.add_source(**source)
            
        print(f"成功加载 {len(all_sources)} 个新闻源")
    
    def _get_default_sources(self):
        """
        获取默认的RSS新闻源列表
        
        Returns:
            list: 包含预设新闻源信息的字典列表
        """
        return [
            # 综合新闻 - 中文
            {
                "url": "https://www.thepaper.cn/rss_newslist.jsp",
                "name": "澎湃新闻",
                "category": "综合新闻"
            },
            {
                "url": "https://feedx.net/rss/weixin.xml",
                "name": "微信热门",
                "category": "综合新闻"
            },
            {
                "url": "https://rsshub.app/reuters/cn/china",
                "name": "路透中文网",
                "category": "综合新闻"
            },
            {
                "url": "https://www.zaobao.com/rss/realtime/china",
                "name": "联合早报",
                "category": "综合新闻"
            },
            {
                "url": "https://www.ftchinese.com/rss/feed",
                "name": "FT中文网",
                "category": "综合新闻"
            },
            {
                "url": "https://feedx.net/rss/bbc.xml",
                "name": "BBC中文网",
                "category": "综合新闻"
            },
            
            # 国际新闻
            {
                "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
                "name": "纽约时报国际",
                "category": "国际新闻"
            },
            {
                "url": "https://feeds.washingtonpost.com/rss/world",
                "name": "华盛顿邮报国际",
                "category": "国际新闻"
            },
            {
                "url": "https://www.theguardian.com/world/rss",
                "name": "卫报国际",
                "category": "国际新闻"
            },
            {
                "url": "https://www.aljazeera.com/xml/rss/all.xml",
                "name": "半岛电视台",
                "category": "国际新闻"
            },
            {
                "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
                "name": "BBC国际",
                "category": "国际新闻"
            },
            {
                "url": "https://feedx.net/rss/cnn.xml",
                "name": "CNN国际",
                "category": "国际新闻"
            },
            {
                "url": "https://www.nhk.or.jp/rss/news/cat6.xml",
                "name": "NHK国际",
                "category": "国际新闻"
            },
            
            # 科技新闻
            {
                "url": "https://feedx.net/rss/wired.xml",
                "name": "WIRED",
                "category": "科技新闻"
            },
            {
                "url": "https://www.engadget.com/rss.xml",
                "name": "Engadget",
                "category": "科技新闻"
            },
            {
                "url": "https://www.theverge.com/rss/index.xml",
                "name": "The Verge",
                "category": "科技新闻"
            },
            {
                "url": "https://techcrunch.com/feed/",
                "name": "TechCrunch",
                "category": "科技新闻"
            },
            {
                "url": "https://feeds.arstechnica.com/arstechnica/index",
                "name": "Ars Technica",
                "category": "科技新闻"
            },
            {
                "url": "https://www.solidot.org/index.rss",
                "name": "Solidot",
                "category": "科技新闻"
            },
            {
                "url": "https://rsshub.app/36kr/news/latest",
                "name": "36氪",
                "category": "科技新闻"
            },
            {
                "url": "https://sspai.com/feed",
                "name": "少数派",
                "category": "科技新闻"
            },
            
            # 商业与金融
            {
                "url": "https://www.economist.com/finance-and-economics/rss.xml",
                "name": "经济学人",
                "category": "商业与金融"
            },
            {
                "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
                "name": "华尔街日报市场",
                "category": "商业与金融"
            },
            {
                "url": "https://www.ft.com/rss/home/uk",
                "name": "金融时报",
                "category": "商业与金融"
            },
            {
                "url": "https://www.forbes.com/business/feed/",
                "name": "福布斯商业",
                "category": "商业与金融"
            },
            {
                "url": "https://www.businessinsider.com/rss",
                "name": "商业内幕",
                "category": "商业与金融"
            },
            {
                "url": "https://www.cnbc.com/id/10001147/device/rss/rss.html",
                "name": "CNBC财经",
                "category": "商业与金融"
            },
            {
                "url": "https://rsshub.app/caixin/finance/regulation",
                "name": "财新网",
                "category": "商业与金融"
            },
            
            # 政治新闻
            {
                "url": "https://rss.politico.com/politics.xml",
                "name": "Politico",
                "category": "政治新闻"
            },
            {
                "url": "https://www.realclearpolitics.com/index.xml",
                "name": "RealClearPolitics",
                "category": "政治新闻"
            },
            {
                "url": "https://thehill.com/feed",
                "name": "The Hill",
                "category": "政治新闻"
            },
            {
                "url": "https://feeds.nbcnews.com/nbcnews/public/politics",
                "name": "NBC政治",
                "category": "政治新闻"
            },
            {
                "url": "https://feeds.bbci.co.uk/news/politics/rss.xml",
                "name": "BBC政治",
                "category": "政治新闻"
            },
            
            # 科学新闻
            {
                "url": "https://www.science.org/rss/news_current.xml",
                "name": "Science",
                "category": "科学新闻"
            },
            {
                "url": "https://www.nature.com/nature.rss",
                "name": "Nature",
                "category": "科学新闻"
            },
            {
                "url": "https://feeds.newscientist.com/science-news",
                "name": "New Scientist",
                "category": "科学新闻"
            },
            {
                "url": "https://phys.org/rss-feed/",
                "name": "Phys.org",
                "category": "科学新闻"
            },
            {
                "url": "https://www.scientificamerican.com/rss/feed.rdf?name=sciam",
                "name": "Scientific American",
                "category": "科学新闻"
            },
            {
                "url": "https://www.space.com/feeds/all",
                "name": "Space.com",
                "category": "科学新闻"
            },
            
            # 体育新闻
            {
                "url": "https://www.espn.com/espn/rss/news",
                "name": "ESPN",
                "category": "体育新闻"
            },
            {
                "url": "https://www.skysports.com/rss/12040",
                "name": "Sky Sports",
                "category": "体育新闻"
            },
            {
                "url": "https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml",
                "name": "纽约时报体育",
                "category": "体育新闻"
            },
            {
                "url": "https://api.foxsports.com/v1/rss?partnerKey=zBaFxRyGKCfxBagJG9b8pqLyndmvo7UU",
                "name": "Fox Sports",
                "category": "体育新闻"
            },
            {
                "url": "https://www.cbssports.com/rss/headlines",
                "name": "CBS Sports",
                "category": "体育新闻"
            },
            {
                "url": "https://www.theguardian.com/sport/rss",
                "name": "卫报体育",
                "category": "体育新闻"
            },
            
            # 娱乐新闻
            {
                "url": "https://www.hollywoodreporter.com/feed/",
                "name": "好莱坞记者",
                "category": "娱乐新闻"
            },
            {
                "url": "https://variety.com/feed/",
                "name": "Variety",
                "category": "娱乐新闻"
            },
            {
                "url": "https://www.eonline.com/feeds/topstories.atom",
                "name": "E! Online",
                "category": "娱乐新闻"
            },
            {
                "url": "https://deadline.com/feed/",
                "name": "Deadline",
                "category": "娱乐新闻"
            },
            {
                "url": "https://www.tmz.com/rss.xml",
                "name": "TMZ",
                "category": "娱乐新闻"
            },
            
            # 健康与医疗
            {
                "url": "https://www.medicalnewstoday.com/newsfeeds/rss/medical_all.xml",
                "name": "Medical News Today",
                "category": "健康与医疗"
            },
            {
                "url": "https://rss.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
                "name": "WebMD",
                "category": "健康与医疗"
            },
            {
                "url": "https://tools.cdc.gov/api/v2/resources/media/316422.rss",
                "name": "CDC",
                "category": "健康与医疗"
            },
            {
                "url": "https://www.health.harvard.edu/rss/health",
                "name": "哈佛健康",
                "category": "健康与医疗"
            },
            {
                "url": "https://feeds.feedburner.com/nejm/research",
                "name": "新英格兰医学杂志",
                "category": "健康与医疗"
            },
            
            # 文化与教育
            {
                "url": "https://www.arts.gov/rss-feed",
                "name": "National Endowment for the Arts",
                "category": "文化与教育"
            },
            {
                "url": "https://www.theparisreview.org/feed/",
                "name": "巴黎评论",
                "category": "文化与教育"
            },
            {
                "url": "https://www.chronicle.com/feed",
                "name": "高等教育纪事报",
                "category": "文化与教育"
            },
            {
                "url": "https://www.insidehighered.com/rss/feed/ihe",
                "name": "Inside Higher Ed",
                "category": "文化与教育"
            },
            {
                "url": "https://www.smithsonianmag.com/rss/arts-culture/",
                "name": "史密森尼杂志",
                "category": "文化与教育"
            }
        ]
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置行列权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 创建左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 刷新按钮
        refresh_btn = ttk.Button(control_frame, text="刷新新闻", command=self._refresh_news)
        refresh_btn.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 加载按钮
        load_btn = ttk.Button(control_frame, text="加载新闻", command=self._load_news_from_file)
        load_btn.grid(row=0, column=1, sticky=tk.E, pady=5)
        
        # 新闻源设置按钮
        source_settings_btn = ttk.Button(control_frame, text="新闻源设置", command=self._show_source_settings)
        source_settings_btn.grid(row=0, column=2, sticky=tk.E, pady=5, padx=5)
        
        # 分类选择
        ttk.Label(control_frame, text="新闻分类:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(control_frame, textvariable=self.category_var, state="readonly")
        self.category_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_change)
        
        # 刷新分类按钮
        refresh_category_btn = ttk.Button(control_frame, text="刷新分类", command=self._refresh_categories)
        refresh_category_btn.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 新闻列表
        list_frame = ttk.LabelFrame(main_frame, text="新闻列表", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.news_listbox = tk.Listbox(list_frame, width=40, height=20)
        self.news_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.news_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.news_listbox.config(yscrollcommand=scrollbar.set)
        
        # 绑定列表点击事件
        self.news_listbox.bind("<<ListboxSelect>>", self._on_news_select)
        
        # 创建右侧内容区
        content_frame = ttk.LabelFrame(main_frame, text="新闻内容", padding="10")
        content_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)
        
        # 新闻标题
        self.news_title = tk.Text(content_frame, height=3, wrap=tk.WORD, state=tk.DISABLED)
        self.news_title.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), pady=5)
        
        # 新闻内容
        self.news_content = scrolledtext.ScrolledText(content_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        self.news_content.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 分析控制面板
        analysis_frame = ttk.LabelFrame(content_frame, text="分析设置", padding="10")
        analysis_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N), pady=5)
        
        # 分析类型选择
        ttk.Label(analysis_frame, text="分析类型:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.analysis_type_var = tk.StringVar()
        self.analysis_type_combo = ttk.Combobox(analysis_frame, textvariable=self.analysis_type_var, 
                                             values=["摘要", "深度分析", "关键观点", "事实核查"], 
                                             state="readonly")
        self.analysis_type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.analysis_type_combo.set("摘要")
        
        # 分析按钮
        analyze_btn = ttk.Button(analysis_frame, text="分析新闻", command=self._analyze_news)
        analyze_btn.grid(row=0, column=2, sticky=tk.E, pady=5, padx=5)
        
        # LLM设置按钮
        llm_settings_btn = ttk.Button(analysis_frame, text="LLM设置", command=self._show_llm_settings)
        llm_settings_btn.grid(row=0, column=3, sticky=tk.E, pady=5, padx=5)
        

        
        # 分析结果
        result_frame = ttk.LabelFrame(content_frame, text="分析结果", padding="10")
        result_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        self.analysis_result = scrolledtext.ScrolledText(result_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.analysis_result.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def _refresh_news(self):
        """刷新新闻"""
        # 获取当前选择的分类
        current_category = self.category_var.get()
        
        # 如果没有选择分类或选择的是"所有"，则刷新所有新闻
        if not current_category or current_category == "所有":
            self._refresh_all_news()
        else:
            # 按当前分类刷新新闻
            self._refresh_news_by_category(current_category)
    
    def _refresh_all_news(self):
        """刷新所有新闻"""
        # 显示加载状态
        self._set_status("正在刷新新闻...")
        self.root.update()
        
        # 清空现有列表
        self.news_listbox.delete(0, tk.END)
        
        # 从所有源获取新闻
        news_items = self.rss_collector.fetch_all()
        
        # 更新新闻列表
        self._update_news_list(news_items)
        
        # 更新分类选择
        categories = ["所有"] + self.rss_collector.get_categories()
        self.category_combo['values'] = categories
        
        # 保持当前分类选择，如果当前分类仍然存在，否则设为"所有"
        current_category = self.category_var.get()
        if current_category in categories:
            self.category_combo.set(current_category)
        else:
            self.category_combo.set("所有")
        
        # 显示状态
        self._set_status(f"共获取 {len(news_items)} 条新闻")
    
    def _refresh_categories(self):
        """刷新分类列表"""
        # 获取所有分类
        categories = ["所有"] + self.rss_collector.get_categories()
        self.category_combo['values'] = categories
        
        # 如果当前分类不存在，设置为"所有"
        current_category = self.category_var.get()
        if current_category not in categories:
            self.category_combo.set("所有")
        else:
            self.category_combo.set(current_category)
        
        self._set_status(f"共 {len(categories)-1} 个分类")
    
    def _refresh_news_by_category(self, category):
        """按分类刷新新闻
        
        Args:
            category: 分类名称
        """
        # 显示加载状态
        self._set_status(f"正在刷新 {category} 新闻...")
        self.root.update()
        
        # 清空现有列表
        self.news_listbox.delete(0, tk.END)
        
        # 根据分类获取新闻
        if category == "所有":
            news_items = self.rss_collector.fetch_all()
            # 更新缓存
            self.rss_collector.news_cache = news_items
        else:
            # 只从该分类的新闻源获取新闻
            news_items = self.rss_collector.fetch_by_category(category)
            # 不更新缓存，因为只获取部分分类的新闻
        
        # 更新新闻列表
        self._update_news_list(news_items)
        
        # 更新分类选择
        categories = ["所有"] + self.rss_collector.get_categories()
        self.category_combo['values'] = categories
        self.category_combo.set(category)
        
        # 显示状态
        self._set_status(f"共获取 {len(news_items)} 条{category}新闻")
    
    def _update_news_list(self, news_items):
        """更新新闻列表
        
        Args:
            news_items: 新闻条目列表
        """
        self.news_listbox.delete(0, tk.END)
        
        for i, news in enumerate(news_items):
            # 将新闻对象存储在列表框中
            self.news_listbox.insert(tk.END, f"{i+1}. {news['title'][:50]}...")
            # 使用字典存储新闻对象，通过索引关联
            self.news_listbox.data = getattr(self.news_listbox, 'data', {})
            self.news_listbox.data[i] = news
    
    def _on_category_change(self, event):
        """分类选择变化事件"""
        category = self.category_var.get()
        if category == "所有":
            news_items = self.rss_collector.get_all_news()
        else:
            news_items = self.rss_collector.get_news_by_category(category)
        
        self._update_news_list(news_items)
    
    def _on_news_select(self, event):
        """新闻选择事件"""
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            # 获取选中的新闻
            self.selected_news = getattr(event.widget, 'data', {}).get(index)
            
            if self.selected_news:
                # 显示新闻内容
                self._display_news(self.selected_news)
    
    def _display_news(self, news_item):
        """显示新闻内容
        
        Args:
            news_item: 新闻数据字典
        """
        # 显示标题
        self.news_title.config(state=tk.NORMAL)
        self.news_title.delete(1.0, tk.END)
        self.news_title.insert(tk.END, news_item['title'])
        self.news_title.config(state=tk.DISABLED)
        
        # 显示内容
        self.news_content.config(state=tk.NORMAL)
        self.news_content.delete(1.0, tk.END)
        
        content = f"来源: {news_item['source_name']}\n"
        content += f"分类: {news_item['category']}\n"
        content += f"发布日期: {news_item['pub_date'][:20] if news_item['pub_date'] else '未知'}\n"
        content += f"链接: {news_item['link']}\n\n"
        content += news_item['description']
        
        self.news_content.insert(tk.END, content)
        self.news_content.config(state=tk.DISABLED)
        
        # 清空分析结果
        self.analysis_result.config(state=tk.NORMAL)
        self.analysis_result.delete(1.0, tk.END)
        self.analysis_result.config(state=tk.DISABLED)
    
    def _analyze_news(self):
        """分析当前选中的新闻"""
        if not self.selected_news:
            messagebox.showwarning("警告", "请先选择一条新闻")
            return
        
        analysis_type = self.analysis_type_var.get()
        
        # 显示加载状态
        self._set_status(f"正在进行{analysis_type}...")
        self.root.update()
        
        # 调用LLM分析
        result = self.llm_client.analyze_news(self.selected_news, analysis_type)
        
        # 显示结果
        self.analysis_result.config(state=tk.NORMAL)
        self.analysis_result.delete(1.0, tk.END)
        self.analysis_result.insert(tk.END, result)
        self.analysis_result.config(state=tk.DISABLED)
        
        # 显示状态
        self._set_status(f"{analysis_type}完成")
    
    def _show_llm_settings(self):
        """显示LLM设置对话框"""
        # 创建对话框
        settings_window = tk.Toplevel(self.root)
        settings_window.title("LLM设置")
        settings_window.geometry("500x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 创建设置框架
        settings_frame = ttk.Frame(settings_window, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # API URL
        ttk.Label(settings_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        api_url_var = tk.StringVar(value=self.llm_client.api_url)
        api_url_entry = ttk.Entry(settings_frame, textvariable=api_url_var, width=50)
        api_url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # API Key
        ttk.Label(settings_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        api_key_var = tk.StringVar(value=self.llm_client.api_key)
        api_key_entry = ttk.Entry(settings_frame, textvariable=api_key_var, width=50)
        api_key_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # 模型名称
        ttk.Label(settings_frame, text="模型名称:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        model_var = tk.StringVar(value=self.llm_client.model)
        model_entry = ttk.Entry(settings_frame, textvariable=model_var, width=50)
        model_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # 保存按钮
        def save_settings():
            """保存设置"""
            self.llm_client.api_url = api_url_var.get()
            self.llm_client.api_key = api_key_var.get()
            self.llm_client.model = model_var.get()
            self.llm_client.api_type = self.llm_client._determine_api_type()
            settings_window.destroy()
        
        save_btn = ttk.Button(settings_frame, text="保存", command=save_settings)
        save_btn.grid(row=3, column=1, sticky=tk.E, pady=10, padx=5)
        
        # 取消按钮
        cancel_btn = ttk.Button(settings_frame, text="取消", command=settings_window.destroy)
        cancel_btn.grid(row=3, column=1, sticky=tk.W, pady=10, padx=5)
        
        # 配置列权重
        settings_frame.columnconfigure(1, weight=1)
    
    def _show_source_settings(self):
        """显示新闻源设置对话框"""
        # 创建对话框
        settings_window = tk.Toplevel(self.root)
        settings_window.title("新闻源设置")
        settings_window.geometry("800x600")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 创建主框架
        main_frame = ttk.Frame(settings_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 分类过滤
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="分类过滤:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 分类下拉框
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(filter_frame, textvariable=category_var, state="readonly")
        categories = ["全部"] + self.rss_collector.get_categories()
        category_combo['values'] = categories
        category_combo.set("全部")
        category_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        # 刷新按钮
        refresh_btn = ttk.Button(filter_frame, text="刷新", command=lambda: self._refresh_source_list(tree, category_var.get()))
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 全选/取消全选按钮
        def toggle_all_sources(state):
            for item in tree.get_children():
                tree.set(item, "Enabled", state)
                # 更新内部数据
                url = tree.item(item)['values'][1]  # URL是第二列
                for source in self.rss_collector.sources:
                    if source['url'] == url:
                        source['enabled'] = state
                        break
        
        select_all_btn = ttk.Button(filter_frame, text="全选", command=lambda: toggle_all_sources(True))
        select_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        unselect_all_btn = ttk.Button(filter_frame, text="取消全选", command=lambda: toggle_all_sources(False))
        unselect_all_btn.pack(side=tk.LEFT)
        
        # 创建Treeview来显示新闻源
        columns = ("Name", "URL", "Category", "Enabled")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        
        # 定义列标题
        tree.heading("Name", text="名称")
        tree.heading("URL", text="URL")
        tree.heading("Category", text="分类")
        tree.heading("Enabled", text="启用")
        
        # 设置列宽
        tree.column("Name", width=150)
        tree.column("URL", width=300)
        tree.column("Category", width=100)
        tree.column("Enabled", width=80, anchor="center")
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar_x = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条放在底部
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定点击事件来切换启用状态
        def on_tree_click(event):
            item = tree.identify_row(event.y)
            column = tree.identify_column(event.x)
            
            if item and column == "#4":  # 第4列是启用列
                current_value = tree.item(item, "values")
                new_state = "否" if current_value[3] == "是" else "是"
                tree.set(item, "Enabled", new_state)
                
                # 更新内部数据
                url = current_value[1]  # URL是第二列
                for source in self.rss_collector.sources:
                    if source['url'] == url:
                        source['enabled'] = (new_state == "是")
                        break
        
        tree.bind("<Button-1>", on_tree_click)
        
        # 刷新新闻源列表
        self._refresh_source_list(tree, "全部")
        
        # 更新分类过滤事件
        category_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_source_list(tree, category_var.get()))
        
        # 保存按钮
        def save_settings():
            settings_window.destroy()
        
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        save_btn = ttk.Button(button_frame, text="保存并关闭", command=save_settings)
        save_btn.pack(side=tk.RIGHT)
    
    def _refresh_source_list(self, tree, selected_category):
        """刷新新闻源列表
        
        Args:
            tree: Treeview组件
            selected_category: 选中的分类，'全部'表示显示所有
        """
        # 清空现有项目
        for item in tree.get_children():
            tree.delete(item)
        
        # 获取所有新闻源
        sources = self.rss_collector.get_sources()
        
        # 根据分类过滤
        if selected_category != "全部":
            sources = [source for source in sources if source['category'] == selected_category]
        
        # 添加到Treeview
        for source in sources:
            enabled_text = "是" if source.get('enabled', True) else "否"
            tree.insert("", tk.END, values=(source['name'], source['url'], source['category'], enabled_text))
    
    def _set_status(self, message):
        """设置状态栏消息
        
        Args:
            message: 状态消息
        """
        self.root.title(f"新闻分析器 - {message}")
    
    def _load_news_from_file(self, file_path=None):
        """从JSON文件加载新闻
        
        Args:
            file_path: 新闻文件路径，None则弹出文件选择对话框
        """
        if not file_path:
            # 弹出文件选择对话框
            file_path = filedialog.askopenfilename(
                title="选择新闻文件",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir="c:\\Project\\新闻分析员\\news_analyzer\\data\\news"
            )
            
            if not file_path:
                return
        
        try:
            # 显示加载状态
            self._set_status(f"正在加载新闻文件: {os.path.basename(file_path)}...")
            self.root.update()
            
            # 读取并解析JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                news_items = json.load(f)
            
            if not isinstance(news_items, list):
                messagebox.showerror("错误", "新闻文件格式不正确，应包含一个新闻列表")
                return
            
            # 将新闻加载到缓存
            self.rss_collector.news_cache = news_items
            
            # 更新新闻列表
            self._update_news_list(news_items)
            
            # 更新分类选择
            categories = set()
            for news in news_items:
                categories.add(news['category'])
            self.category_combo['values'] = ["所有"] + sorted(list(categories))
            self.category_combo.set("所有")
            
            # 显示状态
            self._set_status(f"成功加载 {len(news_items)} 条新闻")
            messagebox.showinfo("成功", f"已成功加载 {len(news_items)} 条新闻")
            
        except Exception as e:
            self.logger.error(f"加载新闻文件失败: {str(e)}")
            messagebox.showerror("错误", f"加载新闻文件失败: {str(e)}")
            self._set_status("加载新闻失败")


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 创建并运行GUI
    root = tk.Tk()
    app = NewsAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
