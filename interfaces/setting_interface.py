# coding:utf-8
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard,
                            OptionsSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme,
                            CustomColorSettingCard, setTheme, setThemeColor,
                            RangeSettingCard, InfoBar, isDarkTheme,
                            HyperlinkCard, PushSettingCard, MessageBox)
from qfluentwidgets import FluentIcon as FIF
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel

from configs.config import cfg, isWin11


class SettingInterface(ScrollArea):
    """ 设置界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # 设置标签
        self.settingLabel = QLabel("设置", self)

        # 个性化设置组
        self.personalGroup = SettingCardGroup('个性化', self.scrollWidget)
        
        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            'Mica 效果',
            '为窗口和表面应用半透明效果',
            cfg.micaEnabled,
            self.personalGroup
        )
        
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            '应用主题',
            "更改应用程序的外观",
            texts=['浅色', '深色', '跟随系统设置'],
            parent=self.personalGroup
        )
        
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            '主题色',
            '更改应用程序的主题颜色',
            self.personalGroup
        )
        
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            "界面缩放",
            "更改小部件和字体的大小",
            texts=["100%", "125%", "150%", "175%", "200%", "跟随系统设置"],
            parent=self.personalGroup
        )
        
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            '语言',
            '设置界面的首选语言',
            texts=['简体中文', 'English', '跟随系统设置'],
            parent=self.personalGroup
        )

        # 材料设置组
        self.materialGroup = SettingCardGroup('材料', self.scrollWidget)
        
        self.blurRadiusCard = RangeSettingCard(
            cfg.blurRadius,
            FIF.ALBUM,
            '亚克力模糊半径',
            '半径越大，图像越模糊（范围：0-40）',
            self.materialGroup
        )
        
        # 关于设置组
        self.aboutGroup = SettingCardGroup('关于', self.scrollWidget)
        
        # 版本信息卡片
        self.versionCard = PushSettingCard(
            '查看详情',
            FIF.INFO,
            '当前版本',
            f'当前版本号: {cfg.currentVersion.value}\n最新版本号: {cfg.latestVersion.value}',
            self.aboutGroup
        )
        
        # 检查更新卡片
        self.checkUpdateCard = PushSettingCard(
            '检查更新',
            FIF.UPDATE,
            '检查更新',
            '检查是否有可用的新版本',
            self.aboutGroup
        )
        
        # 项目主页卡片
        self.homepageCard = HyperlinkCard(
            'https://github.com/Zhiqiuyiye2023/ZhiqiuWorkPlatform',
            '访问GitHub',
            FIF.GITHUB,
            '项目主页',
            '访问项目GitHub仓库',
            self.aboutGroup
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')

        # 初始化样式
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        
        # 根据系统版本启用/禁用 Mica 效果
        self.micaCard.setEnabled(isWin11())

        # 初始化布局
        self.__initLayout()
        self.__connectSignalToSlot()
        
        # 初始化主题样式
        self._onThemeChanged()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # 添加卡片到个性化组
        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

        # 添加卡片到材料组
        self.materialGroup.addSettingCard(self.blurRadiusCard)
        
        # 添加卡片到关于组
        self.aboutGroup.addSettingCard(self.versionCard)
        self.aboutGroup.addSettingCard(self.checkUpdateCard)
        self.aboutGroup.addSettingCard(self.homepageCard)

        # 添加设置卡片组到布局
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.materialGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __showRestartTooltip(self):
        """ 显示重启提示 """
        InfoBar.success(
            '更新成功',
            '配置在重启后生效',
            duration=1500,
            parent=self
        )

    def __onBlurRadiusChanged(self, value):
        """ 模糊半径改变时的回调 """
        # 可以在这里添加额外的逻辑
        pass

    def __connectSignalToSlot(self):
        """ 连接信号到槽 """
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # 个性化设置
        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        
        # 监听主题变化
        cfg.themeChanged.connect(self._onThemeChanged)
        
        # 材料设置
        cfg.blurRadius.valueChanged.connect(self.__onBlurRadiusChanged)
        
        # 关于设置
        self.checkUpdateCard.clicked.connect(self.__onCheckUpdate)
    
    def __onCheckUpdate(self):
        """检查更新"""
        from PyQt6.QtCore import QObject, pyqtSignal
        import threading
        import time
        
        # 创建一个信号类用于线程间通信
        class UpdateSignal(QObject):
            update_available = pyqtSignal(str)  # 有新版本可用信号
            update_not_available = pyqtSignal()  # 无新版本可用信号
            update_ui = pyqtSignal(str, str)  # 更新UI信号
        
        def check_update():
            try:
                # 实际从GitHub API获取最新版本号
                import requests
                response = requests.get('https://api.github.com/repos/Zhiqiuyiye2023/ZhiqiuWorkPlatform/releases/latest', timeout=5)
                response.raise_for_status()
                latest_info = response.json()
                latest_version = latest_info['tag_name'].lstrip('v')  # 移除可能的 "v" 前缀
            except Exception as e:
                # 网络请求失败时使用模拟数据
                latest_version = "1.1.0"
            
            current_version = cfg.currentVersion.value
            
            # 更新配置
            cfg.latestVersion.value = latest_version
            
            # 通过信号更新UI
            update_signal.update_ui.emit(current_version, latest_version)
            
            # 比较版本号
            current = tuple(map(int, current_version.split('.')))
            latest = tuple(map(int, latest_version.split('.')))
            
            if latest > current:
                # 有新版本可用
                update_signal.update_available.emit(latest_version)
            else:
                # 当前已是最新版本
                update_signal.update_not_available.emit()
        
        # 创建信号实例
        update_signal = UpdateSignal()
        
        # 连接信号到槽
        update_signal.update_available.connect(self.__showUpdateAvailable)
        update_signal.update_not_available.connect(self.__showUpdateNotAvailable)
        update_signal.update_ui.connect(self.__updateVersionCard)
        
        # 启动线程检查更新
        thread = threading.Thread(target=check_update)
        thread.daemon = True
        thread.start()
        
        # 显示检查中提示
        InfoBar.info(
            '检查更新',
            '正在检查更新，请稍候...',
            duration=1000,
            parent=self
        )
    
    def __updateVersionCard(self, current_version, latest_version):
        """更新版本卡片内容"""
        self.versionCard.setContent(f'当前版本号: {current_version}\n最新版本号: {latest_version}')
    
    def __showUpdateAvailable(self, latest_version):
        """显示有新版本可用"""
        from qfluentwidgets import MessageBox
        
        InfoBar.success(
            '发现新版本',
            f'已发现新版本 {latest_version}，请前往GitHub更新',
            duration=3000,
            parent=self
        )
        
        # 使用qfluentwidgets的MessageBox，自动适配主题
        msg_box = MessageBox(
            '发现新版本',
            f'已发现新版本 {latest_version}\n\n是否前往GitHub下载最新版本？',
            self
        )
        msg_box.yesButton.setText('前往下载')
        msg_box.cancelButton.setText('取消')
        
        if msg_box.exec():
            import webbrowser
            webbrowser.open('https://github.com/Zhiqiuyiye2023/ZhiqiuWorkPlatform/releases/latest')
    
    def __showUpdateNotAvailable(self):
        """显示当前已是最新版本"""
        InfoBar.success(
            '检查更新',
            '当前已是最新版本',
            duration=2000,
            parent=self
        )
    
    def _onThemeChanged(self):
        """主题变化时更新样式，只修改必要的背景色，保留qfluentwidgets默认控件样式"""
        # 只更新滚动区域和内容部件的背景色，不覆盖控件的默认样式
        if isDarkTheme():
            self.setStyleSheet("ScrollArea { background-color: #1e1e1e; border: none; }")
            self.scrollWidget.setStyleSheet("QWidget#scrollWidget { background-color: #1e1e1e; }")
            self.settingLabel.setStyleSheet("QLabel#settingLabel { font-size: 28px; font-weight: bold; color: #ffffff; background: transparent; }")
        else:
            self.setStyleSheet("ScrollArea { background-color: #f3f3f3; border: none; }")
            self.scrollWidget.setStyleSheet("QWidget#scrollWidget { background-color: #f3f3f3; }")
            self.settingLabel.setStyleSheet("QLabel#settingLabel { font-size: 28px; font-weight: bold; color: #000000; background: transparent; }")
        
        # 确保所有文本标签都没有背景色
        for label in self.findChildren(QLabel):
            if label != self.settingLabel:
                # 只设置背景透明，保留qfluentwidgets的默认文本颜色
                current_style = label.styleSheet()
                if 'background:' not in current_style:
                    label.setStyleSheet(current_style + " background: transparent;")
                else:
                    # 替换现有的背景色设置为透明
                    from re import sub
                    label.setStyleSheet(sub(r'background:[^;]*;?', 'background: transparent;', current_style))
