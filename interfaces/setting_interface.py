# coding:utf-8
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard,
                            OptionsSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme,
                            CustomColorSettingCard, setTheme, setThemeColor,
                            RangeSettingCard, InfoBar, isDarkTheme,
                            PrimaryPushSettingCard, MessageBox, ProgressBar)
from qfluentwidgets import FluentIcon as FIF
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout

from configs.config import cfg, isWin11
from update_manager import UpdateManager


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
        
        # 更新设置组
        self.updateGroup = SettingCardGroup('更新', self.scrollWidget)
        
        # 自动更新开关
        self.autoUpdateCard = SwitchSettingCard(
            FIF.SYNC,
            '启动时自动检查更新',
            '应用程序启动时自动检查GitHub上的新版本',
            cfg.autoUpdate,
            self.updateGroup
        )
        
        # 手动检查更新按钮
        self.checkUpdateCard = PrimaryPushSettingCard(
            FIF.UPDATE,
            '检查更新',
            '手动检查GitHub上是否有可用的新版本',
            self.updateGroup
        )
        
        # 版本信息标签
        self.versionLabel = QLabel("当前版本: v1.0.0", self.scrollWidget)
        self.versionLabel.setStyleSheet("font-size: 14px; color: #666666; background: transparent;")
        
        # 初始化更新管理器
        self.updateManager = UpdateManager("your_username/your_repo", "1.0.0")
        
        # 连接更新信号
        self.updateManager.updateAvailable.connect(self._onUpdateAvailable)
        self.updateManager.updateNotAvailable.connect(self._onUpdateNotAvailable)
        self.updateManager.updateProgress.connect(self._onUpdateProgress)
        self.updateManager.updateFailed.connect(self._onUpdateFailed)

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
        
        # 添加卡片到更新组
        self.updateGroup.addSettingCard(self.autoUpdateCard)
        self.updateGroup.addSettingCard(self.checkUpdateCard)

        # 添加设置卡片组到布局
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.materialGroup)
        self.expandLayout.addWidget(self.updateGroup)
        
        # 添加版本信息标签
        from PyQt6.QtWidgets import QVBoxLayout
        versionLayout = QVBoxLayout()
        versionLayout.addSpacing(10)
        versionLayout.addWidget(self.versionLabel)
        versionLayout.addSpacing(20)
        
        # 创建一个容器来容纳版本信息
        versionWidget = QWidget(self.scrollWidget)
        versionWidget.setLayout(versionLayout)
        versionWidget.setStyleSheet("background: transparent;")
        self.expandLayout.addWidget(versionWidget)

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
        
        # 更新设置
        self.checkUpdateCard.clicked.connect(self.updateManager.checkForUpdates)
    
    def _onUpdateAvailable(self, version: str, notes: str):
        """ 发现新版本时的处理 """
        # 显示更新提示对话框
        w = MessageBox(
            '发现新版本',
            f'发现新版本：v{version}\n\n更新说明：\n{notes}',
            self
        )
        w.yesButton.setText('立即更新')
        w.cancelButton.setText('稍后更新')
        
        if w.exec():
            # 用户选择立即更新
            self._showUpdateProgress()
            self.updateManager.downloadAndUpdate()
    
    def _onUpdateNotAvailable(self):
        """ 没有新版本时的处理 """
        InfoBar.success(
            '已是最新版本',
            '当前应用程序已经是最新版本',
            duration=2000,
            parent=self
        )
    
    def _onUpdateProgress(self, progress: int):
        """ 更新进度处理 """
        # 如果进度对话框已关闭，则不更新
        if hasattr(self, '_progressDialog') and self._progressDialog.isVisible():
            self._progressDialog.setValue(progress)
    
    def _onUpdateFailed(self, error: str):
        """ 更新失败处理 """
        InfoBar.error(
            '更新失败',
            f'检查更新失败：{error}',
            duration=3000,
            parent=self
        )
        
        # 关闭进度对话框
        if hasattr(self, '_progressDialog'):
            self._progressDialog.close()
    
    def _showUpdateProgress(self):
        """ 显示更新进度对话框 """
        from qfluentwidgets import ProgressDialog
        
        self._progressDialog = ProgressDialog(
            '正在下载更新',
            '请稍候...',
            self
        )
        self._progressDialog.setMinimum(0)
        self._progressDialog.setMaximum(100)
        self._progressDialog.setValue(0)
        self._progressDialog.show()
    
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
