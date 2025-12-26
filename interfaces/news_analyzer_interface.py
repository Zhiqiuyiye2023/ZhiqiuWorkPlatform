# coding:utf-8
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                            QGridLayout, QSplitter, QTreeWidget, QTreeWidgetItem, 
                            QTableWidgetItem, QTableWidget)
from PyQt6.QtGui import QFont, QColor
from qfluentwidgets import (ScrollArea, CardWidget, IconWidget, BodyLabel, 
                            CaptionLabel, TitleLabel, PrimaryPushButton, 
                            PushButton, FlowLayout, isDarkTheme, themeColor,
                            StrongBodyLabel, SubtitleLabel, ComboBox, 
                            SwitchButton, TextEdit, LineEdit, ToolButton, 
                            TableWidget, TableItemDelegate, MessageBox)
from qfluentwidgets import FluentIcon as FIF
from configs.config import cfg
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入新闻分析器核心模块
from news_analyzer import RSSCollector, LLMClient


class NewsRefreshThread(QThread):
    """新闻刷新线程"""
    # 定义信号，用于通知主线程新闻刷新完成
    refreshFinished = pyqtSignal(list)  # 传递新闻列表
    refreshError = pyqtSignal(str)      # 传递错误信息
    
    def __init__(self, rss_collector):
        """初始化新闻刷新线程"""
        super().__init__()
        self.rss_collector = rss_collector
    
    def run(self):
        """线程运行函数"""
        try:
            # 从所有RSS源获取新闻
            all_news = self.rss_collector.fetch_all()
            # 发送成功信号
            self.refreshFinished.emit(all_news)
        except Exception as e:
            # 发送错误信号
            self.refreshError.emit(str(e))


class NewsAnalyzeThread(QThread):
    """新闻分析线程"""
    # 定义信号，用于通知主线程新闻分析完成
    analyzeFinished = pyqtSignal(str)  # 传递分析结果
    analyzeError = pyqtSignal(str)      # 传递错误信息
    
    def __init__(self, llm_client, news_data, analysis_type):
        """初始化新闻分析线程"""
        super().__init__()
        self.llm_client = llm_client
        self.news_data = news_data
        self.analysis_type = analysis_type
    
    def run(self):
        """线程运行函数"""
        try:
            # 分析新闻
            result = self.llm_client.analyze_news(self.news_data, self.analysis_type)
            # 发送成功信号
            self.analyzeFinished.emit(result)
        except Exception as e:
            # 发送错误信号
            self.analyzeError.emit(str(e))


class CustomTableItemDelegate(TableItemDelegate):
    """自定义表格项委托"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.column() != 1:  # 只处理来源列
            return

        if isDarkTheme():
            option.palette.setColor(option.palette.ColorRole.Text, Qt.GlobalColor.white)
            option.palette.setColor(option.palette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        else:
            option.palette.setColor(option.palette.ColorRole.Text, Qt.GlobalColor.red)
            option.palette.setColor(option.palette.ColorRole.HighlightedText, Qt.GlobalColor.red)


class NewsAnalyzerInterface(ScrollArea):
    """新闻分析器界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.mainLayout = QHBoxLayout(self.view)  # 主布局改为水平布局
        self.parent_window = parent  # 保存父窗口引用
        
        # 设置滚动区域
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setObjectName('newsAnalyzerInterface')
        
        # 设置样式
        self.view.setStyleSheet("QWidget{background:transparent}")
        self.mainLayout.setContentsMargins(12, 10, 12, 12)
        self.mainLayout.setSpacing(12)
        
        # 初始化新闻收集器和LLM客户端
        self.rss_collector = RSSCollector()
        self.llm_client = LLMClient()
        
        # 创建左侧区域（控制面板和新闻列表）
        self.leftLayout = QVBoxLayout()
        self.leftLayout.setSpacing(12)
        
        # 1. 创建顶部控制面板
        self._addControlPanel()
        
        # 2. 创建新闻列表
        self._addNewsList()
        
        # 创建右侧区域（新闻内容和分析结果）
        self.rightLayout = QVBoxLayout()
        self.rightLayout.setSpacing(12)
        
        # 3. 创建新闻内容区域
        self._addNewsContent()
        
        # 4. 创建分析设置区域
        self._addAnalysisSettings()
        
        # 5. 创建分析结果区域
        self._addAnalysisResults()
        
        # 添加到主布局
        self.mainLayout.addLayout(self.leftLayout, 1)  # 左侧占1份
        self.mainLayout.addLayout(self.rightLayout, 2)  # 右侧占2份
        
        # 监听主题变化
        cfg.themeChanged.connect(self._onThemeChanged)
        # 应用初始主题
        self._onThemeChanged()
    
    def _addControlPanel(self):
        """添加顶部控制面板"""
        # 创建控制面板卡片
        controlCard = CardWidget(self.view)
        controlCardLayout = QGridLayout(controlCard)
        controlCardLayout.setContentsMargins(15, 12, 15, 12)
        controlCardLayout.setSpacing(10)
        
        # 标题
        titleLabel = SubtitleLabel('控制面板', controlCard)
        titleLabel.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Bold))
        controlCardLayout.addWidget(titleLabel, 0, 0, 1, 3)
        
        # 刷新按钮
        refreshBtn = PrimaryPushButton('刷新新闻', controlCard)
        refreshBtn.setIcon(FIF.SYNC)
        refreshBtn.clicked.connect(self._refreshNews)
        controlCardLayout.addWidget(refreshBtn, 1, 0)
        
        # 新闻源设置按钮
        sourceSettingsBtn = PushButton('新闻源设置', controlCard)
        sourceSettingsBtn.setIcon(FIF.SETTING)
        sourceSettingsBtn.clicked.connect(self._showSourceSettings)
        controlCardLayout.addWidget(sourceSettingsBtn, 1, 1)
        
        # 分类选择
        categoryLabel = BodyLabel('新闻分类:', controlCard)
        controlCardLayout.addWidget(categoryLabel, 2, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.categoryComboBox = ComboBox(controlCard)
        self.categoryComboBox.addItem('所有', '所有')
        controlCardLayout.addWidget(self.categoryComboBox, 2, 1, 1, 2)
        
        # 加载分类
        self._loadCategories()
        
        # 延迟连接信号，确保newsList已经初始化
        self.categoryComboBox.currentIndexChanged.connect(self._onCategoryChanged)
        
        self.leftLayout.addWidget(controlCard)
    
    def _addNewsList(self):
        """添加新闻列表"""
        # 创建新闻列表卡片
        listCard = CardWidget(self.view)
        listCardLayout = QVBoxLayout(listCard)
        listCardLayout.setContentsMargins(15, 12, 15, 12)
        listCardLayout.setSpacing(10)
        
        # 标题
        titleLabel = SubtitleLabel('新闻列表', listCard)
        titleLabel.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Bold))
        listCardLayout.addWidget(titleLabel)
        
        # 新闻列表
        self.newsList = TableWidget(listCard)
        
        # 设置样式
        self.newsList.setBorderVisible(True)
        self.newsList.setBorderRadius(8)
        self.newsList.setWordWrap(False)
        
        # 设置列数和表头
        self.newsList.setColumnCount(3)
        self.newsList.setHorizontalHeaderLabels(['标题', '来源', '日期'])
        
        # 设置列宽
        self.newsList.setColumnWidth(0, 250)
        self.newsList.setColumnWidth(1, 100)
        self.newsList.setColumnWidth(2, 120)
        
        # 隐藏垂直表头
        self.newsList.verticalHeader().hide()
        
        # 应用自定义委托
        self.newsList.setItemDelegate(CustomTableItemDelegate(self.newsList))
        
        # 连接点击信号
        self.newsList.cellClicked.connect(self._onNewsItemClicked)
        
        listCardLayout.addWidget(self.newsList)
        
        self.leftLayout.addWidget(listCard, 1)  # 占1份权重
    
    def _addNewsContent(self):
        """添加新闻内容区域"""
        # 创建新闻内容卡片
        contentCard = CardWidget(self.view)
        contentCardLayout = QVBoxLayout(contentCard)
        contentCardLayout.setContentsMargins(15, 12, 15, 12)
        contentCardLayout.setSpacing(10)
        
        # 标题
        titleLabel = SubtitleLabel('新闻内容', contentCard)
        titleLabel.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Bold))
        contentCardLayout.addWidget(titleLabel)
        
        # 新闻标题
        self.newsTitleLabel = TitleLabel('请选择一条新闻', contentCard)
        self.newsTitleLabel.setFont(QFont('Microsoft YaHei', 12, QFont.Weight.Bold))
        contentCardLayout.addWidget(self.newsTitleLabel)
        
        # 新闻元信息
        self.newsMetaLabel = BodyLabel('', contentCard)
        self.newsMetaLabel.setFont(QFont('Microsoft YaHei', 10))
        contentCardLayout.addWidget(self.newsMetaLabel)
        
        # 新闻内容
        self.newsContentText = TextEdit(contentCard)
        self.newsContentText.setReadOnly(True)
        contentCardLayout.addWidget(self.newsContentText)
        
        self.rightLayout.addWidget(contentCard)
    
    def _addAnalysisSettings(self):
        """添加分析设置区域"""
        # 创建分析设置卡片
        settingsCard = CardWidget(self.view)
        settingsCardLayout = QVBoxLayout(settingsCard)
        settingsCardLayout.setContentsMargins(15, 12, 15, 12)
        settingsCardLayout.setSpacing(10)
        
        # 标题
        titleLabel = SubtitleLabel('分析设置', settingsCard)
        titleLabel.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Bold))
        settingsCardLayout.addWidget(titleLabel)
        
        # 分析类型选择
        analysisTypeLayout = QHBoxLayout()
        analysisTypeLabel = BodyLabel('分析类型:', settingsCard)
        analysisTypeLayout.addWidget(analysisTypeLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.analysisTypeComboBox = ComboBox(settingsCard)
        self.analysisTypeComboBox.addItems(['摘要', '深度分析', '关键观点', '事实核查'])
        self.analysisTypeComboBox.setCurrentIndex(0)
        analysisTypeLayout.addWidget(self.analysisTypeComboBox)
        
        # 分析按钮
        self.analyzeBtn = PrimaryPushButton('分析新闻', settingsCard)
        self.analyzeBtn.setIcon(FIF.APPLICATION)
        self.analyzeBtn.clicked.connect(self._analyzeNews)
        analysisTypeLayout.addWidget(self.analyzeBtn)
        
        # LLM设置按钮
        self.llmSettingsBtn = PushButton('LLM设置', settingsCard)
        self.llmSettingsBtn.setIcon(FIF.SETTING)
        self.llmSettingsBtn.clicked.connect(self._showLLMSettings)
        analysisTypeLayout.addWidget(self.llmSettingsBtn)
        
        settingsCardLayout.addLayout(analysisTypeLayout)
        
        self.rightLayout.addWidget(settingsCard)
    
    def _addAnalysisResults(self):
        """添加分析结果区域"""
        # 创建分析结果卡片
        resultCard = CardWidget(self.view)
        resultCardLayout = QVBoxLayout(resultCard)
        resultCardLayout.setContentsMargins(15, 12, 15, 12)
        resultCardLayout.setSpacing(10)
        
        # 标题
        titleLabel = SubtitleLabel('分析结果', resultCard)
        titleLabel.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Bold))
        resultCardLayout.addWidget(titleLabel)
        
        # 分析结果
        self.analysisResultText = TextEdit(resultCard)
        self.analysisResultText.setReadOnly(True)
        resultCardLayout.addWidget(self.analysisResultText)
        
        self.rightLayout.addWidget(resultCard, 1)  # 占1份权重
    
    def _loadCategories(self):
        """加载新闻分类"""
        # 获取所有分类
        categories = self.rss_collector.get_categories()
        
        # 清空现有分类（保留"所有"选项）
        self.categoryComboBox.clear()
        self.categoryComboBox.addItem('所有', '所有')
        
        # 添加分类
        for category in categories:
            self.categoryComboBox.addItem(category, category)
    
    def _refreshNews(self):
        """刷新新闻"""
        # 清空新闻列表
        self.newsList.setRowCount(0)
        
        # 创建并启动新闻刷新线程
        self.refresh_thread = NewsRefreshThread(self.rss_collector)
        # 连接信号
        self.refresh_thread.refreshFinished.connect(self._onNewsRefreshFinished)
        self.refresh_thread.refreshError.connect(self._onNewsRefreshError)
        # 启动线程
        self.refresh_thread.start()
    
    def _onNewsRefreshFinished(self, all_news):
        """新闻刷新完成处理"""
        # 添加到新闻列表
        self.newsList.setRowCount(len(all_news))
        for i, news in enumerate(all_news):
            # 设置新闻标题
            title_item = QTableWidgetItem(news.get('title', ''))
            title_item.setData(Qt.ItemDataRole.UserRole, news)
            self.newsList.setItem(i, 0, title_item)
            
            # 设置新闻来源
            source_item = QTableWidgetItem(news.get('source_name', ''))
            source_item.setData(Qt.ItemDataRole.UserRole, news)
            self.newsList.setItem(i, 1, source_item)
            
            # 设置发布日期
            date_item = QTableWidgetItem(news.get('pub_date', ''))
            date_item.setData(Qt.ItemDataRole.UserRole, news)
            self.newsList.setItem(i, 2, date_item)
    
    def _onNewsRefreshError(self, error_msg):
        """新闻刷新错误处理"""
        # 显示错误消息
        msg_box = MessageBox('刷新失败', f'无法刷新新闻: {error_msg}', self.view)
        msg_box.exec()
    
    def _onCategoryChanged(self):
        """分类变化事件"""
        # 获取选中的分类
        category = self.categoryComboBox.currentData()
        
        # 清空新闻列表
        self.newsList.setRowCount(0)
        
        # 获取对应分类的新闻
        if category == '所有':
            news_list = self.rss_collector.get_all_news()
        else:
            news_list = self.rss_collector.get_news_by_category(category)
        
        # 添加到新闻列表
        self.newsList.setRowCount(len(news_list))
        for i, news in enumerate(news_list):
            # 设置新闻标题
            title_item = QTableWidgetItem(news.get('title', ''))
            title_item.setData(Qt.ItemDataRole.UserRole, news)
            self.newsList.setItem(i, 0, title_item)
            
            # 设置新闻来源
            source_item = QTableWidgetItem(news.get('source_name', ''))
            source_item.setData(Qt.ItemDataRole.UserRole, news)
            self.newsList.setItem(i, 1, source_item)
            
            # 设置发布日期
            date_item = QTableWidgetItem(news.get('pub_date', ''))
            date_item.setData(Qt.ItemDataRole.UserRole, news)
            self.newsList.setItem(i, 2, date_item)
    
    def _onNewsItemClicked(self, row, column):
        """新闻项点击事件"""
        # 获取新闻数据
        item = self.newsList.item(row, 0)
        news_data = item.data(Qt.ItemDataRole.UserRole)
        
        if news_data:
            # 更新新闻标题
            self.newsTitleLabel.setText(news_data.get('title', ''))
            
            # 更新新闻元信息
            meta_text = f"来源: {news_data.get('source_name', '')} | 分类: {news_data.get('category', '')} | 发布日期: {news_data.get('pub_date', '')}"
            self.newsMetaLabel.setText(meta_text)
            
            # 更新新闻内容
            self.newsContentText.setText(news_data.get('description', ''))
            
            # 保存当前选中的新闻
            self.currentNews = news_data
    
    def _analyzeNews(self):
        """分析新闻"""
        if not hasattr(self, 'currentNews'):
            # 显示提示消息
            msg_box = MessageBox('提示', '请先选择一条新闻进行分析', self.view)
            msg_box.exec()
            return
        
        # 获取分析类型
        analysis_type = self.analysisTypeComboBox.currentText()
        
        # 显示加载中
        self.analysisResultText.setText('正在分析...')
        
        # 创建并启动新闻分析线程
        self.analyze_thread = NewsAnalyzeThread(self.llm_client, self.currentNews, analysis_type)
        # 连接信号
        self.analyze_thread.analyzeFinished.connect(self._onNewsAnalyzeFinished)
        self.analyze_thread.analyzeError.connect(self._onNewsAnalyzeError)
        # 启动线程
        self.analyze_thread.start()
    
    def _onNewsAnalyzeFinished(self, result):
        """新闻分析完成处理"""
        self.analysisResultText.setText(result)
    
    def _onNewsAnalyzeError(self, error_msg):
        """新闻分析错误处理"""
        # 更新分析结果文本
        self.analysisResultText.setText(f'分析失败: {error_msg}')
        # 显示错误消息
        msg_box = MessageBox('分析失败', f'无法分析新闻: {error_msg}', self.view)
        msg_box.exec()
    
    def updateTheme(self):
        """主题变化时更新样式"""
        if isDarkTheme():
            # 深色主题
            self.setStyleSheet("NewsAnalyzerInterface { background-color: #1e1e1e; border: none; }")
            # 更新表格样式
            if hasattr(self, 'newsList'):
                # 设置表格背景色和文字颜色
                self.newsList.setStyleSheet("""
                    QTableWidget {
                        background-color: #2d2d2d;
                        color: #ffffff;
                        border: 1px solid #404040;
                    }
                    QHeaderView::section {
                        background-color: #333333;
                        color: #ffffff;
                        border: 1px solid #404040;
                        padding: 8px;
                    }
                    QTableWidget::item {
                        background-color: #2d2d2d;
                        color: #ffffff;
                        border-bottom: 1px solid #404040;
                    }
                    QTableWidget::item:selected {
                        background-color: #0078D4;
                        color: #ffffff;
                    }
                """)
                # 刷新表格委托样式
                self.newsList.reset()
        else:
            # 浅色主题
            self.setStyleSheet("NewsAnalyzerInterface { background-color: #f3f3f3; border: none; }")
            # 更新表格样式
            if hasattr(self, 'newsList'):
                # 设置表格背景色和文字颜色
                self.newsList.setStyleSheet("""
                    QTableWidget {
                        background-color: #ffffff;
                        color: #000000;
                        border: 1px solid #e0e0e0;
                    }
                    QHeaderView::section {
                        background-color: #f0f0f0;
                        color: #000000;
                        border: 1px solid #e0e0e0;
                        padding: 8px;
                    }
                    QTableWidget::item {
                        background-color: #ffffff;
                        color: #000000;
                        border-bottom: 1px solid #e0e0e0;
                    }
                    QTableWidget::item:selected {
                        background-color: #0078D4;
                        color: #ffffff;
                    }
                """)
                # 刷新表格委托样式
                self.newsList.reset()
    
    def _onThemeChanged(self):
        """主题变化时更新样式（兼容旧的调用）"""
        self.updateTheme()
    

    
    def adjustLayout(self, is_maximized):
        """根据窗口状态调整布局"""
        # 调整内容边距
        if is_maximized:
            self.mainLayout.setContentsMargins(50, 20, 50, 20)
        else:
            self.mainLayout.setContentsMargins(12, 10, 12, 12)
        
        # 触发重绘和布局更新
        self.update()
        self.view.updateGeometry()
    
    def _showLLMSettings(self):
        """显示LLM设置对话框"""
        from qfluentwidgets import (
            Dialog, FluentIcon as FIF, BodyLabel, PrimaryPushButton,
            LineEdit
        )
        from PyQt6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout
        )
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import Qt
        
        # 创建对话框
        dialog = Dialog('LLM设置', '配置LLM模型参数')
        dialog.setFixedSize(700, 400)
        
        # 主内容部件
        content_widget = QWidget(dialog)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)
        
        # 功能说明
        desc_label = BodyLabel(
            "📢 <b>功能说明：</b><br>" \
            "配置LLM模型参数，用于新闻分析功能", content_widget
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                padding: 12px;
                font-size: 13px;
                background-color: rgba(0, 120, 212, 0.1);
                border-left: 3px solid #0078D4;
                border-radius: 4px;
            }
        """)
        content_layout.addWidget(desc_label)
        
        # API URL设置
        hbox_api_url = QHBoxLayout()
        hbox_api_url.setSpacing(10)
        
        api_url_label = BodyLabel('API URL:', content_widget)
        api_url_label.setFixedWidth(100)
        
        self.apiUrlEdit = LineEdit(content_widget)
        self.apiUrlEdit.setText(self.llm_client.api_url)
        self.apiUrlEdit.setPlaceholderText('输入LLM API地址')
        
        hbox_api_url.addWidget(api_url_label)
        hbox_api_url.addWidget(self.apiUrlEdit)
        content_layout.addLayout(hbox_api_url)
        
        # API Key设置
        hbox_api_key = QHBoxLayout()
        hbox_api_key.setSpacing(10)
        
        api_key_label = BodyLabel('API Key:', content_widget)
        api_key_label.setFixedWidth(100)
        
        self.apiKeyEdit = LineEdit(content_widget)
        self.apiKeyEdit.setText(self.llm_client.api_key)
        self.apiKeyEdit.setPlaceholderText('输入LLM API密钥')
        
        hbox_api_key.addWidget(api_key_label)
        hbox_api_key.addWidget(self.apiKeyEdit)
        content_layout.addLayout(hbox_api_key)
        
        # 模型名称设置
        hbox_model = QHBoxLayout()
        hbox_model.setSpacing(10)
        
        model_label = BodyLabel('模型名称:', content_widget)
        model_label.setFixedWidth(100)
        
        self.modelEdit = LineEdit(content_widget)
        self.modelEdit.setText(self.llm_client.model)
        self.modelEdit.setPlaceholderText('输入模型名称，如gpt-3.5-turbo')
        
        hbox_model.addWidget(model_label)
        hbox_model.addWidget(self.modelEdit)
        content_layout.addLayout(hbox_model)
        
        # 添加弹性空间
        content_layout.addStretch(1)
        
        # 添加到对话框
        dialog.textLayout.addWidget(content_widget)
        
        # 连接信号
        dialog.yesSignal.connect(self._saveLLMSettings)
        
        # 显示对话框
        dialog.exec()
    
    def _saveLLMSettings(self):
        """保存LLM设置"""
        self.llm_client.api_url = self.apiUrlEdit.text()
        self.llm_client.api_key = self.apiKeyEdit.text()
        self.llm_client.model = self.modelEdit.text()
        self.llm_client.api_type = self.llm_client._determine_api_type()
    
    def _applyThemeToWindow(self, window):
        """应用主题到窗口"""
        from qfluentwidgets import isDarkTheme
        
        # 主题已由FluentWindow自动处理，这里确保部件样式正确
        pass
    
    def _showSourceSettings(self):
        """显示新闻源设置对话框"""
        from qfluentwidgets import (
            Dialog, TableWidget, FluentIcon as FIF, BodyLabel, 
            PrimaryPushButton, PushButton, ComboBox
        )
        from PyQt6.QtWidgets import (QTreeWidget, QTreeWidgetItem, 
                                   QHBoxLayout, QVBoxLayout, QWidget, QTableWidgetItem)
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import Qt
        
        # 创建对话框
        dialog = Dialog('新闻源设置', '管理和配置新闻源')
        dialog.setFixedSize(850, 650)  # 增加对话框高度
        
        # 主内容部件
        content_widget = QWidget(dialog)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(15)
        
        # 功能说明
        desc_label = BodyLabel(
            "📢 <b>功能说明：</b><br>" \
            "管理和配置新闻源，支持按分类过滤和批量操作", content_widget
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                padding: 12px;
                font-size: 13px;
                background-color: rgba(0, 120, 212, 0.1);
                border-left: 3px solid #0078D4;
                border-radius: 4px;
            }
        """)
        content_layout.addWidget(desc_label)
        
        # 分类过滤
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        
        filter_label = BodyLabel('分类过滤:', content_widget)
        filter_label.setFixedWidth(100)
        filter_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # 使用FluentUI的ComboBox
        self.categoryFilterCombo = ComboBox(content_widget)
        self.categoryFilterCombo.addItems(['全部'] + self.rss_collector.get_categories())
        self.categoryFilterCombo.setCurrentIndex(0)
        self.categoryFilterCombo.setFixedHeight(36)
        
        # 按钮组
        btn_group = QHBoxLayout()
        btn_group.setSpacing(8)
        btn_group.setContentsMargins(0, 0, 0, 0)
        
        refresh_btn = PrimaryPushButton('刷新', content_widget)
        refresh_btn.setIcon(FIF.SYNC)
        refresh_btn.setFixedHeight(36)
        refresh_btn.setFixedWidth(80)
        
        select_all_btn = PrimaryPushButton('全选', content_widget)
        select_all_btn.setIcon(FIF.ACCEPT)
        select_all_btn.setFixedHeight(36)
        select_all_btn.setFixedWidth(80)
        
        unselect_all_btn = PrimaryPushButton('取消全选', content_widget)
        unselect_all_btn.setIcon(FIF.CANCEL)
        unselect_all_btn.setFixedHeight(36)
        unselect_all_btn.setFixedWidth(120)
        
        btn_group.addWidget(refresh_btn)
        btn_group.addWidget(select_all_btn)
        btn_group.addWidget(unselect_all_btn)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.categoryFilterCombo)
        filter_layout.addLayout(btn_group)
        filter_layout.addStretch(1)
        
        content_layout.addLayout(filter_layout)
        
        # 新闻源列表
        list_title = BodyLabel('新闻源列表', content_widget)
        list_title.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Bold))
        content_layout.addWidget(list_title)
        
        # 使用TableWidget替代QTreeWidget
        self.sourceTree = TableWidget(content_widget)
        
        # 设置样式
        self.sourceTree.setBorderVisible(True)
        self.sourceTree.setBorderRadius(8)
        self.sourceTree.setWordWrap(False)
        
        # 设置列数和表头
        self.sourceTree.setColumnCount(4)
        self.sourceTree.setHorizontalHeaderLabels(['名称', 'URL', '分类', '启用'])
        
        # 设置列宽
        self.sourceTree.setColumnWidth(0, 180)
        self.sourceTree.setColumnWidth(1, 350)
        self.sourceTree.setColumnWidth(2, 120)
        self.sourceTree.setColumnWidth(3, 100)
        
        # 设置合适的高度，避免压盖
        self.sourceTree.setFixedHeight(300)
        
        # 隐藏垂直表头
        self.sourceTree.verticalHeader().hide()
        
        # 应用自定义委托
        self.sourceTree.setItemDelegate(CustomTableItemDelegate(self.sourceTree))
        
        # 绑定双击事件，允许用户切换启用状态
        self.sourceTree.cellDoubleClicked.connect(self._onSourceItemDoubleClicked)
        
        # 添加到布局
        content_layout.addWidget(self.sourceTree)
        
        # 连接信号
        refresh_btn.clicked.connect(self._refreshSourceList)
        select_all_btn.clicked.connect(lambda: self._toggleAllSources(True))
        unselect_all_btn.clicked.connect(lambda: self._toggleAllSources(False))
        self.categoryFilterCombo.currentIndexChanged.connect(self._refreshSourceList)
        
        # 连接对话框的确定按钮信号，用于保存设置
        dialog.yesSignal.connect(self._saveSourceSettings)
        
        # 刷新新闻源列表
        self._refreshSourceList()
        
        # 添加到对话框
        dialog.textLayout.addWidget(content_widget)
        
        # 显示对话框
        dialog.exec()
    
    def _saveSourceSettings(self):
        """保存新闻源设置"""
        # 保存到文件
        self.rss_collector.save_sources()
        # 更新分类选择器
        self._loadCategories()
    
    def _onSourceItemDoubleClicked(self, row, column):
        """双击新闻源项，切换启用状态"""
        if column == 3:  # 只处理启用列
            current_item = self.sourceTree.item(row, 3)
            current_text = current_item.text()
            new_enabled = current_text == '否'
            current_item.setText('是' if new_enabled else '否')
            # 更新内部数据
            source_item = self.sourceTree.item(row, 0)
            source = source_item.data(Qt.ItemDataRole.UserRole)
            if source:
                for s in self.rss_collector.sources:
                    if s['url'] == source['url']:
                        s['enabled'] = new_enabled
                        break
    
    def _toggleAllSources(self, enabled):
        """全选或取消全选所有新闻源"""
        for i in range(self.sourceTree.rowCount()):
            enabled_item = self.sourceTree.item(i, 3)
            enabled_item.setText('是' if enabled else '否')
            # 更新内部数据
            source_item = self.sourceTree.item(i, 0)
            source = source_item.data(Qt.ItemDataRole.UserRole)
            if source:
                for s in self.rss_collector.sources:
                    if s['url'] == source['url']:
                        s['enabled'] = enabled
                        break
    
    def _refreshSourceList(self):
        """刷新新闻源列表"""
        # 清空现有项目
        self.sourceTree.setRowCount(0)
        
        # 获取所有新闻源
        sources = self.rss_collector.get_sources()
        
        # 根据分类过滤
        selectedCategory = self.categoryFilterCombo.currentText()
        if selectedCategory != '全部':
            sources = [source for source in sources if source['category'] == selectedCategory]
        
        # 添加到TableWidget
        self.sourceTree.setRowCount(len(sources))
        for i, source in enumerate(sources):
            enabled = '是' if source.get('enabled', True) else '否'
            
            # 设置名称
            name_item = QTableWidgetItem(source['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, source)
            self.sourceTree.setItem(i, 0, name_item)
            
            # 设置URL
            url_item = QTableWidgetItem(source['url'])
            self.sourceTree.setItem(i, 1, url_item)
            
            # 设置分类
            category_item = QTableWidgetItem(source['category'])
            self.sourceTree.setItem(i, 2, category_item)
            
            # 设置启用状态
            enabled_item = QTableWidgetItem(enabled)
            self.sourceTree.setItem(i, 3, enabled_item)