# coding:utf-8
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard,
                            OptionsSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme,
                            CustomColorSettingCard, setTheme, setThemeColor,
                            RangeSettingCard, InfoBar, isDarkTheme)
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

        # 添加设置卡片组到布局
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.materialGroup)

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
