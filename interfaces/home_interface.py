# coding:utf-8
# coding:utf-8
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                            QGraphicsOpacityEffect, QGridLayout)
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient, QPainterPath
from qfluentwidgets import (ScrollArea, CardWidget, IconWidget, BodyLabel, 
                            CaptionLabel, TitleLabel, PrimaryPushButton, 
                            PushButton, FlowLayout, isDarkTheme, themeColor,
                            StrongBodyLabel, SubtitleLabel, TransparentToolButton)
from qfluentwidgets import FluentIcon as FIF
from configs.config import cfg
from datetime import datetime
import json
import os


class MatrixColumn:
    """动态字符列"""
    
    def __init__(self, x, delay, duration, parent_width, parent_height):
        self.x = x
        self.delay = delay
        self.duration = duration
        self.parent_width = parent_width
        self.parent_height = parent_height
        self.y = -100  # 初始位置
        self.opacity = 1.0
        
        # 论语等中华字符
        self.chars = [
            '学而时习之', '不亦说乎', '有朋自远方来', '不亦乐乎', '人不知而不愠', '不亦君子乎',
            '吾日三省吾身', '为人谋而不忠乎', '与朋友交而不信乎', '传不习乎',
            '温故而知新', '可以为师矣', '学而不思则罔', '思而不学则殆',
            '知之为知之', '不知为不知', '是知也', '三人行', '必有我师焉',
            '择其善者而从之', '其不善者而改之', '士不可以不弘毅', '任重而道远',
            '仁以为己任', '不亦重乎', '死而后已', '不亦远乎',
            '岁寒', '然后知松柏之后凋也', '有一言而可以终身行之者乎', '其恕乎',
            '己所不欲', '勿施于人', '人无远虑', '必有近忧', '躬自厚而薄责于人', '则远怨矣',
            '君子喻于义', '小人喻于利', '见贤思齐焉', '见不贤而内自省也',
            '君子欲讷于言', '而敏于行', '巧言令色', '鲜矣仁', '道不同', '不相为谋',
            '听其言而观其行', '敏而好学', '不耻下问', '默而识之', '学而不厌', '诲人不倦',
            '吾十有五而志于学', '三十而立', '四十而不惑', '五十而知天命',
            '六十而耳顺', '七十而从心所欲', '不逾矩', '知之者不如好之者',
            '好之者不如乐之者', '逝者如斯夫', '不舍昼夜', '三军可夺帅也', '匹夫不可夺志也',
            '博学而笃志', '切问而近思', '仁在其中矣', '君子坦荡荡', '小人长戚戚',
            '士志于道', '而耻恶衣恶食者', '未足与议也', '饭疏食饮水', '曲肱而枕之', '乐亦在其中矣',
            '不义而富且贵', '于我如浮云', '发愤忘食', '乐以忘忧', '不知老之将至云尔',
            '我非生而知之者', '好古', '敏以求之者也', '三人行必有我师',
            '知者乐水', '仁者乐山', '知者动', '仁者静', '知者乐', '仁者寿',
            '君子成人之美', '不成人之恶', '小人反是', '其身正', '不令而行',
            '其身不正', '虽令不从', '言必信', '行必果', '硁硁然小人哉',
            '工欲善其事', '必先利其器', '人而无信', '不知其可也', '大车无輗', '小车无軏',
            '其何以行之哉', '岁寒然后知松柏之后凋', '知者不惑', '仁者不忧', '勇者不惧',
            '不患人之不己知', '患不知人也', '君子求诸己', '小人求诸人',
            '己欲立而立人', '己欲达而达人', '能近取譬', '可谓仁之方也已',
            '欲速则不达', '见小利则大事不成', '过而不改', '是谓过矣',
            '君子和而不同', '小人同而不和', '君子泰而不骄', '小人骄而不泰',
            '有德者必有言', '有言者不必有德', '仁者必有勇', '勇者不必有仁',
            '贫而无怨难', '富而无骄易', '不以言举人', '不以人废言',
            '巧言乱德', '小不忍则乱大谋', '众恶之', '必察焉', '众好之', '必察焉',
            '人能弘道', '非道弘人', '过而能改', '善莫大焉', '道听而涂说', '德之弃也',
            '三人成虎', '众口铄金', '积毁销骨', '言者无罪', '闻者足戒', '有则改之', '无则加勉',
            '尺有所短', '寸有所长', '金无足赤', '人无完人', '良药苦口利于病', '忠言逆耳利于行',
            '海纳百川', '有容乃大', '壁立千仞', '无欲则刚', '己所不欲', '勿施于人',
            '己欲立而立人', '己欲达而达人', '老吾老以及人之老', '幼吾幼以及人之幼',
            '得道多助', '失道寡助', '天时不如地利', '地利不如人和',
            '生于忧患', '死于安乐', '富贵不能淫', '贫贱不能移', '威武不能屈',
            '不以物喜', '不以己悲', '先天下之忧而忧', '后天下之乐而乐',
            '天下兴亡', '匹夫有责', '人生自古谁无死', '留取丹心照汗青',
            '苟利国家生死以', '岂因祸福避趋之', '一寸丹心图报国', '两行清泪为思亲',
            '位卑未敢忘忧国', '事定犹须待阖棺', '春蚕到死丝方尽', '蜡炬成灰泪始干',
            '落红不是无情物', '化作春泥更护花', '横眉冷对千夫指', '俯首甘为孺子牛',
            '捐躯赴国难', '视死忽如归', '鞠躬尽瘁', '死而后已', '宁为玉碎', '不为瓦全',
            '人固有一死', '或重于泰山', '或轻于鸿毛', '生当作人杰', '死亦为鬼雄',
            '士为知己者死', '女为悦己者容', '君子之交淡如水', '小人之交甘若醴',
            '近朱者赤', '近墨者黑', '路遥知马力', '日久见人心', '疾风知劲草', '板荡识诚臣',
            '言必行', '行必果', '一言既出', '驷马难追', '言而无信', '不知其可',
            '人而无信', '不知其可也', '君子一言', '快马一鞭',
            '海内存知己', '天涯若比邻', '海上生明月', '天涯共此时',
            '但愿人长久', '千里共婵娟', '独在异乡为异客', '每逢佳节倍思亲',
            '慈母手中线', '游子身上衣', '临行密密缝', '意恐迟迟归', '谁言寸草心', '报得三春晖',
            '劝君更尽一杯酒', '西出阳关无故人', '莫愁前路无知己', '天下谁人不识君',
            '桃花潭水深千尺', '不及汪伦送我情', '洛阳亲友如相问', '一片冰心在玉壶',
            '寒雨连江夜入吴', '平明送客楚山孤', '孤帆远影碧空尽', '唯见长江天际流',
            '山回路转不见君', '雪上空留马行处', '相见时难别亦难', '东风无力百花残',
            '蜡烛有心还惜别', '替人垂泪到天明', '别时容易见时难', '流水落花春去也', '天上人间',
            '多情自古伤离别', '更那堪冷落清秋节', '今宵酒醒何处', '杨柳岸晓风残月',
            '此去经年', '应是良辰好景虚设', '便纵有千种风情', '更与何人说',
            '十年生死两茫茫', '不思量', '自难忘', '千里孤坟', '无处话凄凉',
            '纵使相逢应不识', '尘满面', '鬓如霜', '夜来幽梦忽还乡', '小轩窗', '正梳妆',
            '相顾无言', '惟有泪千行', '料得年年肠断处', '明月夜', '短松冈',
            '曾经沧海难为水', '除却巫山不是云', '取次花丛懒回顾', '半缘修道半缘君',
            '问世间情为何物', '直教生死相许', '天南地北双飞客', '老翅几回寒暑',
            '欢乐趣', '离别苦', '就中更有痴儿女', '君应有语', '渺万里层云',
            '千山暮雪', '只影向谁去', '横汾路', '寂寞当年箫鼓', '荒烟依旧平楚',
            '招魂楚些何嗟及', '山鬼暗啼风雨', '天也妒', '未信与', '莺儿燕子俱黄土',
            '千秋万古', '为留待骚人', '狂歌痛饮', '来访雁丘处',
            '在天愿作比翼鸟', '在地愿为连理枝', '天长地久有时尽', '此恨绵绵无绝期',
            '相见时难别亦难', '东风无力百花残', '春蚕到死丝方尽', '蜡炬成灰泪始干',
            '晓镜但愁云鬓改', '夜吟应觉月光寒', '蓬山此去无多路', '青鸟殷勤为探看',
            '庄生晓梦迷蝴蝶', '望帝春心托杜鹃', '沧海月明珠有泪', '蓝田日暖玉生烟',
            '此情可待成追忆', '只是当时已惘然', '锦瑟无端五十弦', '一弦一柱思华年',
            '去年今日此门中', '人面桃花相映红', '人面不知何处去', '桃花依旧笑春风',
            '众里寻他千百度', '蓦然回首', '那人却在', '灯火阑珊处',
            '昨夜西风凋碧树', '独上高楼', '望尽天涯路', '衣带渐宽终不悔',
            '为伊消得人憔悴', '两情若是久长时', '又岂在朝朝暮暮',
            '曾经沧海难为水', '除却巫山不是云', '取次花丛懒回顾', '半缘修道半缘君',
            '问君能有几多愁', '恰似一江春水向东流', '剪不断', '理还乱', '是离愁', '别是一般滋味在心头',
            '寻寻觅觅', '冷冷清清', '凄凄惨惨戚戚', '乍暖还寒时候', '最难将息',
            '三杯两盏淡酒', '怎敌他', '晚来风急', '雁过也', '正伤心', '却是旧时相识',
            '满地黄花堆积', '憔悴损', '如今有谁堪摘', '守着窗儿', '独自怎生得黑',
            '梧桐更兼细雨', '到黄昏', '点点滴滴', '这次第', '怎一个愁字了得',
            '花自飘零水自流', '一种相思', '两处闲愁', '此情无计可消除',
            '才下眉头', '却上心头', '莫道不消魂', '帘卷西风', '人比黄花瘦',
            '少年不识愁滋味', '爱上层楼', '爱上层楼', '为赋新词强说愁',
            '而今识尽愁滋味', '欲说还休', '欲说还休', '却道天凉好个秋',
            '醉里挑灯看剑', '梦回吹角连营', '八百里分麾下炙', '五十弦翻塞外声',
            '沙场秋点兵', '马作的卢飞快', '弓如霹雳弦惊', '了却君王天下事',
            '赢得生前身后名', '可怜白发生', '千古江山', '英雄无觅孙仲谋处',
            '舞榭歌台', '风流总被雨打风吹去', '斜阳草树', '寻常巷陌',
            '人道寄奴曾住', '想当年', '金戈铁马', '气吞万里如虎',
            '元嘉草草', '封狼居胥', '赢得仓皇北顾', '四十三年', '望中犹记',
            '烽火扬州路', '可堪回首', '佛狸祠下', '一片神鸦社鼓', '凭谁问',
            '廉颇老矣', '尚能饭否', '大江东去', '浪淘尽', '千古风流人物',
            '故垒西边', '人道是', '三国周郎赤壁', '乱石穿空', '惊涛拍岸',
            '卷起千堆雪', '江山如画', '一时多少豪杰', '遥想公瑾当年',
            '小乔初嫁了', '雄姿英发', '羽扇纶巾', '谈笑间', '樯橹灰飞烟灭',
            '故国神游', '多情应笑我', '早生华发', '人生如梦', '一尊还酹江月',
            '明月几时有', '把酒问青天', '不知天上宫阙', '今夕是何年',
            '我欲乘风归去', '又恐琼楼玉宇', '高处不胜寒', '起舞弄清影',
            '何似在人间', '转朱阁', '低绮户', '照无眠', '不应有恨',
            '何事长向别时圆', '人有悲欢离合', '月有阴晴圆缺', '此事古难全',
            '但愿人长久', '千里共婵娟',
        ]
        
        # 随机选择一个字符组合
        import random
        self.char_sequence = random.choice(self.chars)
    
    def update(self, delta_time):
        """更新字符列位置和透明度"""
        # 计算下落距离 - 增加速度系数从100到150
        self.y += delta_time * 150 / self.duration
        
        # 计算透明度
        progress = (self.y + 100) / (self.parent_height + 100)
        self.opacity = 1.0 - progress
        
        # 如果超出屏幕，重置位置
        if self.y > self.parent_height + 100:
            self.y = -100
            self.opacity = 1.0
            import random
            self.char_sequence = random.choice(self.chars)


class GradientBannerCard(CardWidget):
    """动态背景横幅卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(180)
        self.timer = None  # 初始化定时器引用
        self.fadeAnimation = None  # 初始化动画引用
        
        # 创建动态字符列
        self.matrix_columns = []
        self._initMatrixColumns()
        
        # 创建布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 20, 30, 20)
        self.vBoxLayout.setSpacing(10)
        
        # 欢迎标题
        self.titleLabel = TitleLabel(self)
        self.titleLabel.setFont(QFont('Microsoft YaHei', 24, QFont.Weight.Bold))
        self._updateGreeting()
        
        # 副标题
        self.subTitleLabel = BodyLabel('欢迎使用知秋工作平台，让工作更高效！', self)
        self.subTitleLabel.setFont(QFont('Microsoft YaHei', 12))
        
        # 时间显示
        self.timeLabel = CaptionLabel(self)
        self.timeLabel.setFont(QFont('Microsoft YaHei', 10))
        self._updateTime()
        
        # 添加到布局
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.subTitleLabel)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.timeLabel)
        
        # 启动淡入动画
        self._startFadeInAnimation()
        
        # 定时更新时间
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._updateTime)
        self.timer.start(1000)  # 每秒更新
        
        # 动态背景定时器
        self.matrix_timer = QTimer(self)
        self.matrix_timer.timeout.connect(self._updateMatrix)
        self.matrix_timer.start(30)  # 约33fps
        
        # 监听主题变化
        cfg.themeChanged.connect(self._updateGreeting)
    
    def _initMatrixColumns(self):
        """初始化动态字符列"""
        self.matrix_columns.clear()
        width = self.width()
        height = self.height()
        
        # 根据窗口宽度计算需要的字符列数量，确保覆盖整个宽度
        column_spacing = 20  # 减小字符列间隔
        column_count = width // column_spacing + 5  # 增加5个额外的字符列以确保覆盖
        
        # 创建足够的字符列以覆盖整个宽度
        for i in range(column_count):
            x = i * column_spacing  # 每个字符列间隔20px
            # 随机延迟和持续时间
            import random
            delay = -random.uniform(0, 5)
            duration = random.uniform(2, 5)
            column = MatrixColumn(x, delay, duration, width, height)
            self.matrix_columns.append(column)
    
    def _updateMatrix(self):
        """更新动态字符列"""
        # 更新所有字符列
        for column in self.matrix_columns:
            column.update(0.03)  # 30ms
        
        # 重绘
        self.update()
    
    def _updateGreeting(self):
        """根据时间更新问候语"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = "早上好！☀️"
        elif 12 <= hour < 14:
            greeting = "中午好！🌤️"
        elif 14 <= hour < 18:
            greeting = "下午好！⛅"
        elif 18 <= hour < 22:
            greeting = "晚上好！🌙"
        else:
            greeting = "夜深了！✨"
        
        self.titleLabel.setText(greeting)
        
        # 美化标题字体颜色
        if isDarkTheme():
            # 深色主题下使用渐变色彩
            self.titleLabel.setStyleSheet("""
                TitleLabel {
                    color: white;
                    font-weight: bold;
                    background: linear-gradient(90deg, #00B4FF, #0078D4);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
            """)
        else:
            # 浅色主题下使用渐变色彩
            self.titleLabel.setStyleSheet("""
                TitleLabel {
                    color: black;
                    font-weight: bold;
                    background: linear-gradient(90deg, #0078D4, #00B4FF);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
            """)
    
    def _updateTime(self):
        """更新时间显示"""
        now = datetime.now()
        time_str = now.strftime('%Y年%m月%d日 %H:%M:%S  %A')
        # 星期中文转换
        weekdays = {
            'Monday': '星期一', 'Tuesday': '星期二', 'Wednesday': '星期三',
            'Thursday': '星期四', 'Friday': '星期五', 
            'Saturday': '星期六', 'Sunday': '星期日'
        }
        for en, zh in weekdays.items():
            time_str = time_str.replace(en, zh)
        self.timeLabel.setText(time_str)
    
    def _startFadeInAnimation(self):
        """淡入动画"""
        self.opacityEffect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacityEffect)
        
        self.fadeAnimation = QPropertyAnimation(self.opacityEffect, b"opacity")
        self.fadeAnimation.setDuration(800)
        self.fadeAnimation.setStartValue(0)
        self.fadeAnimation.setEndValue(1)
        self.fadeAnimation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fadeAnimation.start()
    
    def cleanup(self):
        """清理资源"""
        # 停止并删除定时器
        if self.timer:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None
        
        # 停止并删除动态背景定时器
        if hasattr(self, 'matrix_timer') and self.matrix_timer:
            self.matrix_timer.stop()
            self.matrix_timer.deleteLater()
            self.matrix_timer = None
        
        # 停止并删除动画
        if self.fadeAnimation:
            self.fadeAnimation.stop()
            self.fadeAnimation.deleteLater()
            self.fadeAnimation = None
        
        # 断开主题变化连接
        try:
            cfg.themeChanged.disconnect(self._updateGreeting)
        except:
            pass
    
    def paintEvent(self, e):
        """绘制动态背景"""
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 设置圆角半径
        radius = 10
        rect = self.rect()
        
        # 创建圆角矩形路径
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), radius, radius)
        
        # 设置裁剪路径，确保所有内容都在圆角内
        painter.setClipPath(path)
        
        # 设置背景色 - 使用圆角矩形绘制
        if isDarkTheme():
            painter.fillPath(path, QColor(0, 0, 0))
        else:
            painter.fillPath(path, QColor(240, 240, 240))
        
        # 绘制动态字符列
        for column in self.matrix_columns:
            # 设置透明度
            painter.setOpacity(column.opacity)
            
            # 设置字体 - 改为楷体，减小字体大小从16到12
            font = QFont('KaiTi', 12, QFont.Weight.Bold)
            painter.setFont(font)
            
            # 绘制字符
            for i, char in enumerate(column.char_sequence):
                # 计算字符位置 - 减小字符间距从30到24px
                char_y = column.y + i * 24  # 字符间距24px
                
                # 为字符设置直接颜色，提高对比度
                if isDarkTheme():
                    # 深色主题下使用明亮的绿色
                    painter.setPen(QColor(0, 255, 65))
                else:
                    # 浅色主题下使用深绿色
                    painter.setPen(QColor(0, 150, 38))
                
                # 绘制字符
                painter.drawText(column.x, char_y, char)
        
        # 绘制圆角矩形边框
        painter.setOpacity(1.0)
        pen = painter.pen()
        if isDarkTheme():
            pen.setColor(QColor(50, 50, 50))
        else:
            pen.setColor(QColor(200, 200, 200))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)
    
    def resizeEvent(self, event):
        """窗口大小变化时重新初始化字符列"""
        super().resizeEvent(event)
        self._initMatrixColumns()


class StatCard(CardWidget):
    """数据统计卡片"""
    
    def __init__(self, icon, title: str, value: str, change: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 85)  # 再次减小宽度和高度
        
        # 创建主布局
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(5)
        
        # 创建顶部水平布局（图标和标题）
        self.topLayout = QHBoxLayout()
        self.topLayout.setSpacing(5)
        
        # 图标
        self.iconWidget = IconWidget(icon, self)
        self.iconWidget.setFixedSize(20, 20)
        
        # 标题
        self.titleLabel = CaptionLabel(title, self)
        self.titleLabel.setWordWrap(True)  # 允许换行，避免遮挡
        
        # 添加到顶部布局
        self.topLayout.addWidget(self.iconWidget)
        self.topLayout.addWidget(self.titleLabel)
        self.topLayout.addStretch(1)
        
        # 数值
        self.valueLabel = SubtitleLabel(value, self)
        self.valueLabel.setFont(QFont('Microsoft YaHei', 12, QFont.Weight.Bold))
        self.valueLabel.setWordWrap(True)  # 允许换行，避免遮挡
        
        # 变化值
        if change:
            self.changeLabel = CaptionLabel(change, self)
            self.changeLabel.setStyleSheet('color: #10B981')  # 绿色
            self.changeLabel.setWordWrap(True)  # 允许换行，避免遮挡
        else:
            self.changeLabel = None
        
        # 添加到主布局
        self.mainLayout.addLayout(self.topLayout)
        self.mainLayout.addWidget(self.valueLabel)
        if self.changeLabel:
            self.mainLayout.addWidget(self.changeLabel)
        self.mainLayout.addStretch(1)
        
        # 悬停效果
        self.setStyleSheet("""
            StatCard:hover {
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)


class QuickActionCard(CardWidget):
    """快速操作卡片"""
    clicked = pyqtSignal(str)  # 发送应用ID
    
    def __init__(self, app_id: str, icon, title: str, description: str, parent=None):
        super().__init__(parent)
        self.app_id = app_id
        self.setFixedSize(160, 80)  # 再次调小尺寸
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 创建布局
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(10, 10, 10, 10)  # 进一步减小边距
        self.hBoxLayout.setSpacing(6)  # 进一步减小间距
        
        # 图标
        self.iconWidget = IconWidget(icon, self)
        self.iconWidget.setFixedSize(20, 20)
        
        # 文字容器
        self.textLayout = QVBoxLayout()
        self.textLayout.setSpacing(3)
        
        # 标题
        self.titleLabel = StrongBodyLabel(title, self)
        
        # 描述
        self.descLabel = CaptionLabel(description, self)
        self.descLabel.setWordWrap(True)
        
        # 添加到布局
        self.textLayout.addWidget(self.titleLabel)
        self.textLayout.addWidget(self.descLabel)
        self.textLayout.addStretch(1)
        
        self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.textLayout)
    
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
    
    def mouseReleaseEvent(self, e):
        # 不再调用父类的mouseReleaseEvent，避免信号冲突
        # 直接发出带有app_id参数的信号
        self.clicked.emit(self.app_id)


class RecentItemCard(CardWidget):
    """最近使用项卡片"""
    clicked = pyqtSignal(str)  # 发送应用ID
    
    def __init__(self, app_id: str, icon, title: str, time: str, parent=None):
        super().__init__(parent)
        self.app_id = app_id
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 创建布局（与TipCard保持一致）
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(15, 12, 15, 12)
        self.vBoxLayout.setSpacing(6)
        
        # 标题栏
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setSpacing(8)
        self.iconWidget = IconWidget(icon, self)
        self.iconWidget.setFixedSize(16, 16)
        self.titleLabel = StrongBodyLabel(title, self)
        
        self.headerLayout.addWidget(self.iconWidget)
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch(1)
        
        # 时间
        self.timeLabel = CaptionLabel(time, self)
        
        # 添加到布局
        self.vBoxLayout.addLayout(self.headerLayout)
        self.vBoxLayout.addWidget(self.timeLabel)
    
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.clicked.emit(self.app_id)


class TipCard(CardWidget):
    """提示卡片"""
    
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)
        
        # 创建布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(15, 12, 15, 12)
        self.vBoxLayout.setSpacing(6)
        
        # 标题栏
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setSpacing(8)
        self.iconWidget = IconWidget(FIF.INFO, self)
        self.iconWidget.setFixedSize(16, 16)
        self.titleLabel = StrongBodyLabel(title, self)
        
        self.headerLayout.addWidget(self.iconWidget)
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch(1)
        
        # 内容
        self.contentLabel = BodyLabel(content, self)
        self.contentLabel.setWordWrap(True)
        
        # 添加到布局
        self.vBoxLayout.addLayout(self.headerLayout)
        self.vBoxLayout.addWidget(self.contentLabel)


class HomeInterface(ScrollArea):
    """炒酷的首页界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)
        self.parent_window = parent  # 保存父窗口引用
        
        # 使用全局管理器
        from recent_manager import recent_manager
        self.recent_manager = recent_manager
        
        # 设置滚动区域
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setObjectName('homeInterface')
        
        # 设置样式
        self.view.setStyleSheet("QWidget{background:transparent}")
        self.vBoxLayout.setContentsMargins(12, 10, 12, 12)  # 进一步减小边距
        self.vBoxLayout.setSpacing(12)  # 进一步减小间距
        
        # 1. 欢迎横幅
        self.bannerCard = GradientBannerCard(self.view)
        self.vBoxLayout.addWidget(self.bannerCard)
        
        # 2. 数据统计区域
        self._addStatsSection()
        
        # 3. 快速访问区域
        self._addQuickActionsSection()
        
        # 4. 最近使用和提示区域（左右布局）
        self._addBottomSection()
        
        self.vBoxLayout.addStretch(1)
        
        # 监听主题变化
        cfg.themeChanged.connect(self._onThemeChanged)
        # 应用初始主题
        self._onThemeChanged()
    
    def _addStatsSection(self):
        """添加数据统计区域"""
        # 区域标题
        titleLabel = SubtitleLabel('📊 数据概览', self.view)
        titleLabel.setFont(QFont('Microsoft YaHei', 16, QFont.Weight.Bold))
        self.vBoxLayout.addWidget(titleLabel)
        
        # 统计卡片容器
        statsLayout = QHBoxLayout()
        statsLayout.setSpacing(6)  # 进一步减小间距
        
        # 创建统计卡片
        stats = [
            (FIF.APPLICATION, '总功能数', '13', '+2 本月'),
            (FIF.HISTORY, '使用次数', '128', '+24 本周'),
            (FIF.FOLDER, '处理文件', '1,024', '+156 本周'),
            (FIF.SAVE, '节省时间', '48h', '+6h 本周'),
        ]
        
        for icon, title, value, change in stats:
            card = StatCard(icon, title, value, change, self.view)
            statsLayout.addWidget(card)
        
        statsLayout.addStretch(1)
        self.vBoxLayout.addLayout(statsLayout)
    
    def _addQuickActionsSection(self):
        """添加快速访问区域"""
        # 区域标题
        titleLabel = SubtitleLabel('🚀 快速访问', self.view)
        titleLabel.setFont(QFont('Microsoft YaHei', 16, QFont.Weight.Bold))
        self.vBoxLayout.addWidget(titleLabel)
        
        # 快速操作卡片容器
        quickLayout = FlowLayout(needAni=True)
        quickLayout.setContentsMargins(0, 0, 0, 0)
        quickLayout.setHorizontalSpacing(6)  # 进一步减小水平间距
        quickLayout.setVerticalSpacing(6)  # 进一步减小垂直间距
        
        # 创建快速操作卡片（app_id, icon, title, desc）
        actions = [
            ('data_overlay', FIF.TILES, '数据叠加', '计算矢量套合占比'),
            ('field_split', FIF.CUT, '字段分离', '按字段分离要素'),
            ('pdf_tools', FIF.DOCUMENT, 'PDF工具', 'PDF合并、分离、转换'),
            ('shp_to_kmz', FIF.FOLDER, 'SHP转KMZ', '转换为奥维格式'),
            ('image_mosaic', FIF.PHOTO, '影像拼接', '多影像拼接处理'),
            ('batch_copy_move', FIF.COPY, '按列表批量操作', '批量按表格操作文件与文件夹'),
        ]
        
        for app_id, icon, title, desc in actions:
            card = QuickActionCard(app_id, icon, title, desc, self.view)
            card.clicked.connect(self._onQuickActionClicked)
            quickLayout.addWidget(card)
        
        self.vBoxLayout.addLayout(quickLayout)
    
    def _addBottomSection(self):
        """添加底部区域（最近使用和提示）"""
        bottomLayout = QHBoxLayout()
        bottomLayout.setSpacing(10)  # 进一步减小间距
        
        # 左侧：最近使用
        self.recentWidget = QWidget(self.view)
        self.recentLayout = QVBoxLayout(self.recentWidget)
        self.recentLayout.setContentsMargins(0, 0, 0, 0)
        self.recentLayout.setSpacing(6)  # 进一步减小间距
        
        recentTitleLabel = SubtitleLabel('📝 最近使用', self.recentWidget)
        recentTitleLabel.setFont(QFont('Microsoft YaHei', 16, QFont.Weight.Bold))
        self.recentLayout.addWidget(recentTitleLabel)
        
        # 初始加载最近使用项
        self._refreshRecentApps()
        
        # 右侧：使用提示
        tipsWidget = QWidget(self.view)
        tipsLayout = QVBoxLayout(tipsWidget)
        tipsLayout.setContentsMargins(0, 0, 0, 0)
        tipsLayout.setSpacing(6)  # 进一步减小间距
        
        tipsTitleLabel = SubtitleLabel('💡 使用提示', tipsWidget)
        tipsTitleLabel.setFont(QFont('Microsoft YaHei', 16, QFont.Weight.Bold))
        tipsLayout.addWidget(tipsTitleLabel)
        
        # 提示卡片
        tips = [
            ('快捷搜索', '使用顶部搜索框快速查找功能，支持拼音搜索'),
            ('批量处理', '大部分工具支持批量处理，可一次性处理多个文件'),
            ('最新更新', 'v1.5版本新增影像拼接和影像裁剪功能'),
        ]
        
        for title, content in tips:
            card = TipCard(title, content, tipsWidget)
            tipsLayout.addWidget(card)
        
        tipsLayout.addStretch(1)
        
        # 添加到主布局
        bottomLayout.addWidget(self.recentWidget, 1)
        bottomLayout.addWidget(tipsWidget, 1)
        
        self.vBoxLayout.addLayout(bottomLayout)
    
    def _refreshRecentApps(self):
        """刷新最近使用项"""
        # 清除现有的最近使用项
        while self.recentLayout.count() > 1:  # 保留标题标签
            item = self.recentLayout.itemAt(1)  # 从第二个项开始删除
            widget = item.widget()
            if widget:
                widget.deleteLater()
            self.recentLayout.removeItem(item)
        
        # 加载最近使用的应用
        recent_items = self._loadRecentApps()
        
        # 只显示最多3条记录
        displayed_count = 0
        for app_id, icon_name, title, time_str in recent_items:
            # 根据icon_name获取图标
            icon = getattr(FIF, icon_name, FIF.APPLICATION)
            card = RecentItemCard(app_id, icon, title, time_str, self.recentWidget)
            card.clicked.connect(self._onRecentItemClicked)
            self.recentLayout.addWidget(card)
            displayed_count += 1
            if displayed_count >= 3:  # 限制显示3条记录
                break
        
        # 添加弹性空间以保持对称
        self.recentLayout.addStretch(1)
    
    def _loadRecentApps(self):
        """加载最近使用的应用"""
        return self.recent_manager.load_recent_apps()
    
    def _saveRecentApp(self, app_id: str, icon_name: str, title: str):
        """保存最近使用的应用（已废弃，使用 recent_manager 代替）"""
        # 直接使用管理器
        self.recent_manager.add_recent_app(app_id)
    
    def _onQuickActionClicked(self, app_id: str):
        """快速访问卡片点击事件"""
        from app_functions import AppFunctionManager
        
        # 打开应用（AppFunctionManager.openApp 会自动记录到最近使用）
        AppFunctionManager.openApp(app_id, self)
        
        # 刷新最近使用面板
        self._refreshRecentApps()
    
    def _onRecentItemClicked(self, app_id: str):
        """最近使用项点击事件"""
        # 复用快速访问的逻辑
        self._onQuickActionClicked(app_id)
        
        # 刷新最近使用面板
        self._refreshRecentApps()
    
    def hideEvent(self, a0):
        """页面隐藏时清理资源"""
        if self.bannerCard:
            self.bannerCard.cleanup()
        super().hideEvent(a0)
    
    def showEvent(self, a0):
        """页面显示时重启资源"""
        super().showEvent(a0)
        if self.bannerCard:
            # 如果定时器不存在或已被删除，则重新创建
            if not hasattr(self.bannerCard, 'timer') or self.bannerCard.timer is None:
                from PyQt6.QtCore import QTimer
                self.bannerCard.timer = QTimer(self.bannerCard)
                self.bannerCard.timer.timeout.connect(self.bannerCard._updateTime)
                self.bannerCard.timer.start(1000)
            # 如果定时器存在但未激活，则启动它
            elif not self.bannerCard.timer.isActive():
                self.bannerCard.timer.start(1000)
            
            # 重启动态背景定时器
            if not hasattr(self.bannerCard, 'matrix_timer') or self.bannerCard.matrix_timer is None:
                from PyQt6.QtCore import QTimer
                self.bannerCard.matrix_timer = QTimer(self.bannerCard)
                self.bannerCard.matrix_timer.timeout.connect(self.bannerCard._updateMatrix)
                self.bannerCard.matrix_timer.start(30)
            elif not self.bannerCard.matrix_timer.isActive():
                self.bannerCard.matrix_timer.start(30)
        
        # 刷新最近使用面板
        self._refreshRecentApps()
    
    def _onThemeChanged(self):
        """主题变化时更新背景色"""
        if isDarkTheme():
            self.setStyleSheet("HomeInterface { background-color: #1e1e1e; border: none; }")
        else:
            self.setStyleSheet("HomeInterface { background-color: #f3f3f3; border: none; }")
    
    def adjustLayout(self, is_maximized):
        """根据窗口状态调整布局（仅调整宽度相关适配）
        
        Args:
            is_maximized: 窗口是否处于最大化状态
        """
        # 调整内容边距（仅调整左右边距，保持上下边距不变）
        if is_maximized:
            # 最大化状态下增加左右边距
            margin_top, _, margin_bottom, _ = self.vBoxLayout.getContentsMargins()
            self.vBoxLayout.setContentsMargins(50, margin_top, 50, margin_bottom)
        else:
            # 还原状态下减少左右边距
            margin_top, _, margin_bottom, _ = self.vBoxLayout.getContentsMargins()
            self.vBoxLayout.setContentsMargins(20, margin_top, 20, margin_bottom)
        
        # 调整统计卡片大小（仅调整宽度）
        # 统计卡片在self.vBoxLayout中的第三个位置（索引2）是统计区域布局
        if len(self.vBoxLayout.children()) > 2:
            stats_layout_item = self.vBoxLayout.itemAt(2)
            if stats_layout_item and stats_layout_item.layout():
                stats_layout = stats_layout_item.layout()
                
                # 调整统计卡片的宽度，保持高度不变
                for i in range(stats_layout.count()):
                    item = stats_layout.itemAt(i)
                    if item and item.widget() and isinstance(item.widget(), StatCard):
                        card = item.widget()
                        current_height = card.height()
                        if is_maximized:
                            card.setFixedSize(240, current_height)
                        else:
                            card.setFixedSize(200, current_height)
        
        # 调整快速操作卡片布局（仅调整水平间距）
        # 快速操作区域在self.vBoxLayout中的第五个位置（索引4）是FlowLayout
        if len(self.vBoxLayout.children()) > 4:
            quick_layout_item = self.vBoxLayout.itemAt(4)
            if quick_layout_item and quick_layout_item.layout():
                quick_layout = quick_layout_item.layout()
                
                # 调整水平间距
                if is_maximized:
                    quick_layout.setHorizontalSpacing(20)
                else:
                    quick_layout.setHorizontalSpacing(10)
        
        # 触发重绘和布局更新
        self.update()
        self.view.updateGeometry()
