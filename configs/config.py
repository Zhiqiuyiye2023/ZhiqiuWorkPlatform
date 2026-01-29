# coding:utf-8
import sys
import os
from enum import Enum

from PyQt6.QtCore import QLocale
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            Theme, ConfigSerializer)


class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
    ENGLISH = QLocale(QLocale.Language.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


# 从version.json文件中读取版本号
def get_current_version():
    import json
    import os
    try:
        version_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'version.json')
        with open(version_file_path, 'r', encoding='utf-8') as f:
            version_info = json.load(f)
        return version_info['version']
    except Exception as e:
        # 如果读取失败，使用默认值
        return "1.0.3"

class Config(QConfig):
    """ Config of application """

    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # Material
    blurRadius = RangeConfigItem("Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40))
    
    # Version
    currentVersion = ConfigItem("Version", "CurrentVersion", get_current_version(), None)
    latestVersion = ConfigItem("Version", "LatestVersion", get_current_version(), None)
    
    # Server
    serverType = OptionsConfigItem(
        "Server", "ServerType", "public", OptionsValidator(["local", "public"]), restart=False)
    localServerUrl = ConfigItem("Server", "LocalServerUrl", "http://127.0.0.1:5000", None)
    publicServerUrl = ConfigItem("Server", "PublicServerUrl", "https://bream-guided-poodle.ngrok-free.app", None)


# 创建全局配置对象
cfg = Config()

# 加载配置文件
# 获取用户目录
user_dir = os.path.expanduser('~')
# 配置文件路径
config_dir = os.path.join(user_dir, '知秋工作平台', 'configs')
config_file = os.path.join(config_dir, 'config.json')

# 确保配置目录存在
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

try:
    qconfig.load(config_file, cfg)
except:
    pass  # 如果配置文件不存在，使用默认值

# 不硬编码主题，使用qfluentwidgets的默认主题设置
# 默认情况下，qfluentwidgets会跟随系统主题设置
# 如果需要修改默认主题，可以取消下面的注释并设置为Theme.DARK或Theme.LIGHT
# cfg.themeMode.value = Theme.LIGHT