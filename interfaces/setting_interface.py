# coding:utf-8
import sys
import os
import time
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard,
                            OptionsSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme,
                            CustomColorSettingCard, setTheme, setThemeColor,
                            RangeSettingCard, InfoBar, isDarkTheme,
                            HyperlinkCard, PushSettingCard, MessageBox)
from qfluentwidgets import FluentIcon as FIF
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import QWidget, QLabel, QProgressDialog, QApplication

from configs.config import cfg, isWin11


class SettingInterface(ScrollArea):
    """ 设置界面 """
    
    # 定义信号
    files_update_available = pyqtSignal(list)  # 有文件需要更新信号
    files_update_not_available = pyqtSignal()  # 无需更新信号
    files_update_error = pyqtSignal(str)  # 文件更新错误信号
    update_progress = pyqtSignal(int)  # 更新进度信号
    update_error = pyqtSignal(str)  # 更新错误信号
    update_completed = pyqtSignal()  # 更新完成信号

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
        import requests
        import os
        import json
        import hashlib
        from PyQt6.QtCore import QThread, pyqtSignal
        
        # 创建统一的进度对话框，用于整个更新过程
        self.update_progress_dialog = QProgressDialog(
            '正在验证服务器连接...',
            '取消',
            0, 100,
            self
        )
        self.update_progress_dialog.setWindowTitle('检查更新')
        self.update_progress_dialog.setCancelButton(None)
        self.update_progress_dialog.setMinimumDuration(0)
        # 设置固定宽度
        self.update_progress_dialog.setFixedWidth(400)
        
        # 设置进度条样式，跟随主题
        if isDarkTheme():
            self.update_progress_dialog.setStyleSheet(
                """QProgressDialog {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #333333;
                }
                QProgressBar {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #007acc;
                    border-radius: 4px;
                }
                QLabel {
                    color: #ffffff;
                }"""
            )
        else:
            self.update_progress_dialog.setStyleSheet(
                """QProgressDialog {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #e0e0e0;
                }
                QProgressBar {
                    background-color: #f0f0f0;
                    color: #000000;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 4px;
                }
                QLabel {
                    color: #000000;
                }"""
            )
        
        self.update_progress_dialog.show()
        
        # 创建检查更新线程类
        class CheckUpdateThread(QThread):
            update_available = pyqtSignal(dict)  # 有新版本可用信号，传递项目信息
            update_not_available = pyqtSignal()  # 无新版本可用信号
            update_ui = pyqtSignal(str, str)  # 更新UI信号
            update_error = pyqtSignal(str)  # 更新错误信号
            files_update_available = pyqtSignal(list)  # 有文件需要更新信号
            files_update_not_available = pyqtSignal()  # 无需更新信号
            files_update_error = pyqtSignal(str)  # 文件更新错误信号
            progress_updated = pyqtSignal(str, int)  # 进度更新信号
            
            def run(self):
                try:
                    import os
                    import glob
                    import hashlib
                    import requests
                    from configs.config import cfg
                    
                    # 安全的信号发射函数
                    def safe_emit(signal, *args, **kwargs):
                        try:
                            signal.emit(*args, **kwargs)
                        except RuntimeError:
                            # 信号已断开连接，跳过
                            pass
                    
                    # 获取所有可用服务器地址，确保URL格式正确（去除可能的引号或反引号）
                    local_url = cfg.localServerUrl.value.strip('`\'"')
                    public_url = cfg.publicServerUrl.value.strip('`\'"')
                    
                    server_url = None
                    
                    # 获取用户选择的服务器类型
                    server_type = cfg.serverType.value
                    print(f"[检查更新] 用户选择的服务器类型: {server_type}")
                    
                    # 根据用户选择的服务器类型，确定服务器连接顺序
                    if server_type == '本地服务器':
                        # 优先使用本地服务器
                        server_order = [(local_url, '本地服务器'), (public_url, '公网服务器')]
                    else:
                        # 优先使用公网服务器
                        server_order = [(public_url, '公网服务器'), (local_url, '本地服务器')]
                    
                    # 尝试连接服务器
                    for url, server_name in server_order:
                        safe_emit(self.progress_updated, f'正在验证{server_name}连接...', 10)
                        try:
                            print(f"[检查更新] 尝试连接{server_name}: {url}")
                            response = requests.get(f'{url}/api/v1/healthcheck', timeout=3)
                            if response.status_code == 200:
                                try:
                                    # 尝试解析JSON响应
                                    data = response.json()
                                    # 检查是否包含预期的字段
                                    if 'status' in data and data['status'] == 'ok':
                                        server_url = url
                                        print(f"[检查更新] 成功连接{server_name}: {server_url}")
                                        break
                                    else:
                                        print(f"[检查更新] {server_name}返回无效响应: {data}")
                                except ValueError:
                                    # 无法解析为JSON，可能是错误页面
                                    print(f"[检查更新] {server_name}返回非JSON响应: {response.text[:100]}...")
                        except requests.exceptions.RequestException as e:
                            print(f"[检查更新] {server_name}连接失败: {str(e)}")
                    
                    # 第三步：如果两个服务器都无法连接，提示错误
                    if not server_url:
                        safe_emit(self.update_error, '无法连接到服务器，请联系研发人员开启服务器')
                        return
                    
                    # 第三步：验证服务器是否正常响应
                    response = requests.get(f'{server_url}/api/v1/healthcheck', timeout=2)
                    response.raise_for_status()
                    # 再次验证响应内容是否符合预期
                    try:
                        data = response.json()
                        if 'status' not in data or data['status'] != 'ok':
                            raise Exception(f"服务器返回无效响应: {data}")
                    except ValueError:
                        raise Exception(f"服务器返回非JSON响应")
                    
                    # 第五步：检查服务器是否能监测到dist目录下的数据
                    safe_emit(self.progress_updated, '正在检查服务器文件目录...', 30)
                    
                    response = requests.get(f'{server_url}/api/v1/server_files_info', timeout=10)
                    response.raise_for_status()
                    server_files_info = response.json()
                    # 检查响应是否包含预期的files字段
                    if 'files' not in server_files_info:
                        raise Exception(f"服务器返回无效的文件信息响应")
                    server_files = server_files_info['files']
                    
                    # 检查是否有文件
                    if not server_files:
                        safe_emit(self.update_error, '服务器未检测到dist目录下的数据，请确保服务器已正确配置')
                        return
                    
                    # 第三步：获取服务器版本信息
                    safe_emit(self.progress_updated, '正在获取服务器版本信息...', 30)
                    
                    response = requests.get(f'{server_url}/api/v1/project_info', timeout=5)
                    response.raise_for_status()
                    latest_info = response.json()
                    # 检查响应是否包含预期的version字段
                    if 'version' not in latest_info:
                        raise Exception(f"服务器返回无效的版本信息响应")
                    latest_version = latest_info['version']
                    
                    current_version = cfg.currentVersion.value
                    
                    # 更新配置
                    cfg.latestVersion.value = latest_version
                    
                    # 通过信号更新UI
                    safe_emit(self.update_ui, current_version, latest_version)
                    
                    # 比较版本号
                    current = tuple(map(int, current_version.split('.')))
                    latest = tuple(map(int, latest_version.split('.')))
                    
                    if latest > current:
                        # 有新版本可用
                        safe_emit(self.update_available, latest_info)
                    else:
                        # 当前已是最新版本
                        safe_emit(self.update_not_available)
                    
                    # 第四步：获取本地安装目录并检查
                    safe_emit(self.progress_updated, '正在获取本地安装目录...', 40)
                    
                    # 获取本地安装目录
                    local_install_dir = "C:\Program Files (x86)\知秋工作平台"
                    
                    # 如果本地目录不存在，提示用户
                    if not os.path.exists(local_install_dir):
                        # 通过信号发送错误信息到主线程
                        safe_emit(self.files_update_error, f'本地安装目录不存在: {local_install_dir}')
                        return
                    
                    # 第五步：计算本地文件信息
                    safe_emit(self.progress_updated, '正在获取本地文件列表...', 50)
                    
                    local_files = {}
                    total_local_files = 0
                    
                    # 先计算总文件数，添加异常处理
                    try:
                        for root, dirs, files in os.walk(local_install_dir):
                            total_local_files += len(files)
                    except Exception as e:
                        print(f"获取本地文件总数失败: {str(e)}")
                        # 如果无法获取文件总数，跳过本地文件检查
                        safe_emit(self.files_update_not_available)
                        return
                    
                    current_file = 0
                    safe_emit(self.progress_updated, f'正在计算本地文件MD5 ({current_file}/{total_local_files})...', 60)
                    
                    try:
                        for root, dirs, files in os.walk(local_install_dir):
                            for file in files:
                                local_file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(local_file_path, local_install_dir)
                                
                                try:
                                    # 计算文件MD5，添加异常处理
                                    with open(local_file_path, 'rb') as f:
                                        md5_hash = hashlib.md5()
                                        while True:
                                            chunk = f.read(4096)
                                            if not chunk:
                                                break
                                            md5_hash.update(chunk)
                                        md5 = md5_hash.hexdigest()
                                    
                                    # 获取文件大小和时间，添加异常处理
                                    try:
                                        file_size = os.path.getsize(local_file_path)
                                        file_mtime = os.path.getmtime(local_file_path)
                                    except Exception as e:
                                        print(f"获取文件属性失败: {local_file_path} - {str(e)}")
                                        file_size = 0
                                        file_mtime = 0
                                    
                                    local_files[rel_path] = {
                                        "md5": md5,
                                        "size": file_size,
                                        "modify_time": file_mtime
                                    }
                                except Exception as e:
                                    print(f"计算本地文件MD5失败: {local_file_path} - {str(e)}")
                                    # 跳过无法处理的文件，继续处理其他文件
                                    continue
                                
                                # 更新进度
                                current_file += 1
                                progress = 60 + int((current_file / total_local_files) * 25)
                                safe_emit(self.progress_updated, f'正在计算本地文件MD5 ({current_file}/{total_local_files})...', progress)
                    except Exception as e:
                        print(f"遍历本地文件失败: {str(e)}")
                        # 如果无法遍历文件，跳过本地文件检查
                        safe_emit(self.files_update_not_available)
                        return
                    
                    # 第六步：比较服务器文件和本地文件
                    safe_emit(self.progress_updated, '正在比较文件差异...', 85)
                    
                    files_to_update = []
                    
                    # 遍历所有服务器文件
                    for server_file in server_files:
                        # 服务器返回的完整相对路径（相对于dist目录）
                        server_file_path = server_file['file_path']
                        server_md5 = server_file['md5']
                        
                        # 获取文件名
                        file_name = os.path.basename(server_file_path)
                        
                        # 判断是否是知秋工作平台exe文件
                        is_zhiqiu_exe = '知秋工作平台' in file_name and file_name.endswith('.exe')
                        
                        if is_zhiqiu_exe:
                            # 对于知秋工作平台exe文件，使用文件名作为相对路径
                            relative_path = file_name
                        else:
                            # 对于普通文件，去掉路径中的"知秋工作平台"前缀和可能的分隔符
                            if server_file_path.startswith('知秋工作平台'):
                                # 去掉"知秋工作平台"前缀
                                relative_path = server_file_path[len('知秋工作平台'):]
                                # 去掉可能的前导斜杠或反斜杠
                                if relative_path.startswith('/') or relative_path.startswith('\\'):
                                    relative_path = relative_path[1:]
                            else:
                                relative_path = server_file_path
                        
                        # 构建本地完整路径
                        local_file_path = os.path.join(local_install_dir, relative_path)
                        
                        # 如果是exe文件，特殊处理
                        if is_zhiqiu_exe:
                            # 检查本地是否存在任何知秋工作平台exe文件，添加异常处理
                            try:
                                local_zhiqiu_exes = glob.glob(os.path.join(local_install_dir, '知秋工作平台*.exe'))
                            except Exception as e:
                                print(f"查找本地知秋工作平台exe文件失败: {str(e)}")
                                local_zhiqiu_exes = []
                            
                            # 检查是否需要更新
                            need_update = False
                            
                            # 从文件名中提取版本号字符串
                            def extract_version_str(file_name):
                                # 从形如 "知秋工作平台v1.1.1.exe" 的文件名中提取版本号
                                if file_name.startswith('知秋工作平台v') and file_name.endswith('.exe'):
                                    # 提取版本号部分，例如 "知秋工作平台v1.1.1.exe" -> "v1.1.1"
                                    version_str = file_name[len('知秋工作平台'):-4]  # 去掉前缀和后缀
                                    return version_str
                                return ""  # 默认空版本号
                            
                            # 从服务器文件名中提取版本号字符串
                            server_version_str = extract_version_str(file_name)
                            print(f"服务器知秋工作平台版本: {server_version_str}")
                            
                            if local_zhiqiu_exes:
                                # 从本地文件名中提取版本号字符串
                                local_exe_name = os.path.basename(local_zhiqiu_exes[0])
                                local_version_str = extract_version_str(local_exe_name)
                                print(f"本地知秋工作平台版本: {local_version_str}")
                                
                                # 构建本地exe文件路径
                                local_exe_path = os.path.join(local_install_dir, local_exe_name)
                                
                                # 比较版本号字符串是否一致
                                if local_version_str != server_version_str:
                                    need_update = True
                                    print(f"知秋工作平台exe需要更新: 本地版本 {local_version_str} 与服务器版本 {server_version_str} 不一致")
                                else:
                                        # 版本号字符串一致，再比较文件大小和MD5值
                                        # 获取本地文件大小
                                        try:
                                            local_size = os.path.getsize(local_exe_path)
                                        except Exception as e:
                                            print(f"获取本地文件大小失败: {local_exe_path} - {str(e)}")
                                            need_update = True
                                            print(f"知秋工作平台exe需要更新: 无法获取本地文件大小")
                                        else:
                                            server_size = server_file.get('size', 0)
                                            
                                            # 先比较文件大小
                                            if local_size != server_size:
                                                need_update = True
                                                print(f"知秋工作平台exe需要更新: 本地大小 {local_size} 与服务器大小 {server_size} 不一致")
                                            else:
                                                # 文件大小一致，再比较MD5值
                                                try:
                                                    with open(local_exe_path, 'rb') as f:
                                                        md5_hash = hashlib.md5()
                                                        while True:
                                                            chunk = f.read(4096)
                                                            if not chunk:
                                                                break
                                                            md5_hash.update(chunk)
                                                        local_md5 = md5_hash.hexdigest()
                                                    
                                                    # 比较MD5
                                                    if server_md5 != local_md5:
                                                        need_update = True
                                                        print(f"知秋工作平台exe需要更新: 本地MD5 {local_md5} 与服务器MD5 {server_md5} 不一致")
                                                    else:
                                                        print(f"知秋工作平台exe无需更新: 版本号、大小和MD5均一致")
                                                except Exception as e:
                                                    print(f"计算本地文件MD5失败: {local_exe_path} - {str(e)}")
                                                    need_update = True
                            else:
                                # 本地不存在，需要下载
                                need_update = True
                                print(f"知秋工作平台exe不存在，需要下载")
                            
                            if need_update:
                                # 更新server_file的file_path为处理后的相对路径
                                updated_server_file = server_file.copy()
                                updated_server_file['file_path'] = relative_path
                                files_to_update.append(updated_server_file)
                        else:
                            # 普通文件处理
                            # 检查本地文件是否存在
                            if os.path.exists(local_file_path):
                                # 获取本地文件大小，添加异常处理
                                try:
                                    local_size = os.path.getsize(local_file_path)
                                except Exception as e:
                                    print(f"获取本地文件大小失败: {local_file_path} - {str(e)}")
                                    # 跳过无法处理的文件
                                    continue
                                
                                server_size = server_file.get('size', 0)
                                
                                # 先比较文件大小，如果不一致直接更新
                                if local_size != server_size:
                                    # 文件大小不一致，需要更新
                                    print(f"文件需要更新: {relative_path}, 服务器大小: {server_size}, 本地大小: {local_size}")
                                    # 更新server_file的file_path为处理后的相对路径
                                    updated_server_file = server_file.copy()
                                    updated_server_file['file_path'] = relative_path
                                    files_to_update.append(updated_server_file)
                                else:
                                    # 文件大小一致，再比较MD5
                                    try:
                                        with open(local_file_path, 'rb') as f:
                                            md5_hash = hashlib.md5()
                                            while True:
                                                chunk = f.read(4096)
                                                if not chunk:
                                                    break
                                                md5_hash.update(chunk)
                                            local_md5 = md5_hash.hexdigest()
                                        
                                        # 比较MD5
                                        if server_md5 != local_md5:
                                            # MD5不一致，需要更新
                                            print(f"文件需要更新: {relative_path}, 服务器MD5: {server_md5}, 本地MD5: {local_md5}")
                                            # 更新server_file的file_path为处理后的相对路径
                                            updated_server_file = server_file.copy()
                                            updated_server_file['file_path'] = relative_path
                                            files_to_update.append(updated_server_file)
                                        else:
                                            print(f"文件无需更新: {relative_path}")
                                    except Exception as e:
                                        print(f"计算本地文件MD5失败: {local_file_path} - {str(e)}")
                                        # 跳过无法处理的文件
                            else:
                                # 本地文件不存在，需要下载
                                print(f"文件不存在，需要下载: {relative_path}")
                                # 更新server_file的file_path为处理后的相对路径
                                updated_server_file = server_file.copy()
                                updated_server_file['file_path'] = relative_path
                                files_to_update.append(updated_server_file)
                    
                    # 更新进度
                    safe_emit(self.progress_updated, '检查完成', 100)
                    
                    # 发送文件更新信号
                    if files_to_update:
                        safe_emit(self.files_update_available, files_to_update)
                    else:
                        safe_emit(self.files_update_not_available)
                except requests.exceptions.RequestException:
                    # 网络请求失败，立即停止并提示用户
                    safe_emit(self.update_error, '无法连接到服务器，请联系研发人员开启服务器')
                except Exception as e:
                    # 其他错误，立即停止并提示用户
                    safe_emit(self.update_error, f'检查更新失败: {str(e)}')
        
        # 连接信号到槽
        def on_progress_updated(label, value):
            try:
                if hasattr(self, 'update_progress_dialog') and self.update_progress_dialog:
                    self.update_progress_dialog.setLabelText(label)
                    self.update_progress_dialog.setValue(value)
            except RuntimeError:
                # 对话框已被销毁，跳过更新
                pass
        
        def on_update_available(info):
            # 不立即关闭进度对话框，让文件检查继续
            self.latest_version_info = info
        
        def on_update_not_available():
            # 当前已是最新版本
            self.latest_version_info = None
        
        def on_update_error(error_msg):
            self.update_progress_dialog.close()
            self.__showUpdateError(error_msg)
        
        def on_files_update_available(files_to_update):
            self.update_progress_dialog.close()
            # 显示文件更新提示
            self.__showFilesUpdateAvailable(files_to_update)
        
        def on_files_update_not_available():
            self.update_progress_dialog.close()
            # 如果没有文件需要更新，显示版本更新提示（如果有）
            if hasattr(self, 'latest_version_info') and self.latest_version_info:
                self.__showUpdateAvailable(self.latest_version_info)
            else:
                self.__showUpdateNotAvailable()
        
        def on_files_update_error(error_msg):
            self.update_progress_dialog.close()
            self.__showFilesUpdateError(error_msg)
        
        # 创建线程实例
        self.check_update_thread = CheckUpdateThread()
        self.check_update_thread.progress_updated.connect(on_progress_updated)
        self.check_update_thread.update_available.connect(on_update_available)
        self.check_update_thread.update_not_available.connect(on_update_not_available)
        self.check_update_thread.update_error.connect(on_update_error)
        self.check_update_thread.files_update_available.connect(on_files_update_available)
        self.check_update_thread.files_update_not_available.connect(on_files_update_not_available)
        self.check_update_thread.files_update_error.connect(on_files_update_error)
        self.check_update_thread.update_ui.connect(self.__updateVersionCard)
        
        # 启动线程
        self.check_update_thread.start()
    
    def __showUpdateError(self, error_msg):
        """显示更新错误信息 - 主线程调用"""
        # 如果是无法连接到服务器，显示简洁的错误信息
        if '无法连接到服务器' in error_msg:
            InfoBar.error(
                '检查更新失败',
                '当前无法连接服务器，请联系研发人员开启服务器',
                duration=5000,
                parent=self
            )
        else:
            InfoBar.error(
                '检查更新失败',
                f'检查更新过程中发生错误：{error_msg}',
                duration=5000,
                parent=self
            )
    
    def __showFilesUpdateError(self, error_msg):
        """显示文件更新错误信息 - 主线程调用"""
        InfoBar.error(
            '检查文件更新失败',
            error_msg,
            duration=3000,
            parent=self
        )
    
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
        
        # 服务器设置组
        self.serverGroup = SettingCardGroup('服务器', self.scrollWidget)
        
        # 服务器类型选择卡片
        self.serverTypeCard = ComboBoxSettingCard(
            cfg.serverType,
            FIF.GLOBE,
            '服务器类型',
            '选择检查更新时使用的服务器',
            texts=['本地服务器', '公网服务器'],
            parent=self.serverGroup
        )
        
        # 关于设置组
        self.aboutGroup = SettingCardGroup('关于', self.scrollWidget)
        
        # 版本信息卡片
        self.versionCard = PushSettingCard(
            '查看详情',
            FIF.INFO,
            '当前版本',
            f'当前版本号: {cfg.currentVersion.value}',
            self.aboutGroup
        )
        
        # 检查更新卡片
        self.checkUpdateCard = PushSettingCard(
            '检查更新',
            FIF.UPDATE,
            '检查更新',
            '检查是否有可用的新版本\n\n提示：请以管理员身份运行应用程序以确保更新成功',
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
        
        # 连接信号到槽
        self.files_update_available.connect(self.__showFilesUpdateAvailable)
        self.files_update_not_available.connect(self.__showFilesUpdateNotAvailable)
        self.files_update_error.connect(self.__showFilesUpdateError)
        self.update_completed.connect(self.__onFilesUpdateCompleted)
        self.update_error.connect(self.__onFilesUpdateError)

    def _checkFilesUpdateFromThread(self):
        """从线程中调用检查文件更新 - 已废弃，集成到统一检查更新线程中"""
        pass
    
    def __checkFilesUpdate(self):
        """检查文件更新 - 已废弃，集成到统一检查更新线程中"""
        pass
    
    def __showFilesUpdateAvailable(self, files_to_update):
        """显示有文件需要更新"""
        from qfluentwidgets import MessageBox
        
        file_count = len(files_to_update)
        
        InfoBar.success(
            '发现需要更新的文件',
            f'已发现 {file_count} 个文件需要更新',
            duration=3000,
            parent=self
        )
        
        # 使用qfluentwidgets的MessageBox，自动适配主题
        msg_box = MessageBox(
            '发现需要更新的文件',
            f'已发现 {file_count} 个文件需要更新\n\n是否立即更新？',
            self
        )
        msg_box.yesButton.setText('立即更新')
        msg_box.cancelButton.setText('稍后更新')
        
        if msg_box.exec():
            # 开始更新文件
            self.__startFilesUpdate(files_to_update)
    
    def __showFilesUpdateNotAvailable(self):
        """显示无需更新文件"""
        InfoBar.success(
            '检查文件更新',
            '所有文件均为最新版本，无需更新',
            duration=2000,
            parent=self
        )
    
    def __startFilesUpdate(self, files_to_update):
        """开始更新文件"""
        import os
        import shutil
        import tempfile
        import requests
        from PyQt6.QtCore import QThread, pyqtSignal
        
        # 创建进度对话框
        self.progress_dialog = QProgressDialog(
            f'准备更新 {len(files_to_update)} 个文件...',
            '取消',
            0, 100,
            self
        )
        self.progress_dialog.setWindowTitle('正在更新文件')
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setMinimumDuration(0)
        # 设置固定宽度
        self.progress_dialog.setFixedWidth(400)
        
        # 设置进度条样式，跟随主题
        if isDarkTheme():
            self.progress_dialog.setStyleSheet(
                """QProgressDialog {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #333333;
                }
                QProgressBar {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #007acc;
                    border-radius: 4px;
                }
                QLabel {
                    color: #ffffff;
                }"""
            )
        else:
            self.progress_dialog.setStyleSheet(
                """QProgressDialog {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #e0e0e0;
                }
                QProgressBar {
                    background-color: #f0f0f0;
                    color: #000000;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 4px;
                }
                QLabel {
                    color: #000000;
                }"""
            )
        
        # 定义更新文件线程类
        class UpdateFilesThread(QThread):
            label_updated = pyqtSignal(str)  # 标签更新信号
            progress_updated = pyqtSignal(int)  # 进度更新信号
            update_completed = pyqtSignal()  # 更新完成信号
            update_error = pyqtSignal(str)  # 更新错误信号
            
            def __init__(self, files_to_update):
                super().__init__()
                self.files_to_update = files_to_update
                self.updated_exe_path = None  # 保存更新后的exe文件路径
            
            def run(self):
                try:
                    import os
                    total_files = len(self.files_to_update)
                    updated_files = 0
                    
                    # 获取本地安装目录
                    local_install_dir = "C:\Program Files (x86)\知秋工作平台"
                    
                    # 从配置中获取所有服务器地址
                    from configs.config import cfg
                    local_server_url = cfg.localServerUrl.value.strip('`\'"')
                    public_server_url = cfg.publicServerUrl.value.strip('`\'"')
                    
                    # 初始化下载基础URL
                    download_base_url = None
                    
                    # 第一步：验证服务器连接并获取正确的下载URL
                    self.label_updated.emit('正在验证服务器连接...')
                    
                    # 使用局域网地址优先，公网地址作为备选
                    server_priority = [local_server_url, public_server_url]
                    
                    # 构建所有可能的服务器地址列表（包括http/https变体）
                    possible_servers = []
                    for server_url in server_priority:
                        possible_servers.append(server_url)  # 添加原始URL
                        # 添加http/https变体
                        if 'https://' in server_url:
                            possible_servers.append(server_url.replace('https://', 'http://'))
                        else:
                            possible_servers.append(server_url.replace('http://', 'https://'))
                    
                    working_server = None
                    
                    for server_candidate in possible_servers:
                        try:
                            # 先测试healthcheck
                            response = requests.get(f'{server_candidate}/api/v1/healthcheck', timeout=5)
                            if response.status_code == 200:
                                response.raise_for_status()
                                data = response.json()
                                if 'status' in data and data['status'] == 'ok':
                                    working_server = server_candidate
                                    print(f"[文件更新] 成功连接服务器: {working_server}")
                                    break
                        except Exception as e:
                            print(f"[文件更新] 服务器测试失败 {server_candidate}: {str(e)}")
                            continue
                    
                    if not working_server:
                        self.update_error.emit('无法连接到服务器，请联系研发人员开启服务器')
                        return
                    
                    # 使用工作服务器获取项目信息
                    self.label_updated.emit('正在获取更新信息...')
                    try:
                        response = requests.get(f'{working_server}/api/v1/project_info', timeout=10)
                        response.raise_for_status()
                        project_info = response.json()
                        # 从项目信息中获取正确的下载基础URL
                        if 'download_url' in project_info:
                            download_url_from_server = project_info['download_url']
                            # 去掉URL末尾的/api/v1/download_update部分，得到基础URL
                            if '/api/v1/download_update' in download_url_from_server:
                                candidate_base_url = download_url_from_server.replace('/api/v1/download_update', '')
                                # 验证这个URL是否可用
                                try:
                                    test_response = requests.get(f'{candidate_base_url}/api/v1/healthcheck', timeout=5)
                                    if test_response.status_code == 200:
                                        download_base_url = candidate_base_url
                                except Exception as e:
                                    print(f"测试download_url失败，继续使用工作服务器: {str(e)}")
                    except Exception as e:
                        print(f"获取项目信息失败，使用工作服务器: {str(e)}")
                        download_base_url = working_server
                    
                    # 确保download_base_url没有末尾的斜杠
                    if download_base_url.endswith('/'):
                        download_base_url = download_base_url[:-1]
                    
                    # 确认服务器可用后，开始更新文件
                    for file_info in self.files_to_update:
                        # 更新进度对话框文本
                        self.label_updated.emit(f'正在更新文件: {file_info["file_path"]}')
                        
                        # 构建文件下载URL
                        file_path = file_info['file_path']
                        file_path_normalized = file_path.replace('\\', '/')
                        # 确保路径正确，避免双斜杠
                        download_url = f'{download_base_url}/dist/知秋工作平台/{file_path_normalized}'
                        
                        # 获取文件名
                        file_name = os.path.basename(file_path)
                        
                        # 构建完整本地文件路径，包括子目录
                        local_file_path = os.path.join(local_install_dir, file_path)
                        
                        # 特殊处理：知秋工作平台exe文件
                        if '知秋工作平台' in file_name and file_name.endswith('.exe'):
                            # 先删除本地所有的知秋工作平台exe文件
                            import glob
                            local_zhiqiu_exes = glob.glob(os.path.join(local_install_dir, '知秋工作平台*.exe'))
                            print(f"找到 {len(local_zhiqiu_exes)} 个旧的知秋工作平台exe文件")
                            for old_exe in local_zhiqiu_exes:
                                try:
                                    print(f"正在删除旧的知秋工作平台exe: {old_exe}")
                                    os.remove(old_exe)
                                    print(f"已删除旧的知秋工作平台exe: {os.path.basename(old_exe)}")
                                    self.label_updated.emit(f'已删除旧的知秋工作平台exe: {os.path.basename(old_exe)}')
                                except Exception as e:
                                    print(f"无法删除旧的知秋工作平台exe: {os.path.basename(old_exe)} ({str(e)})")
                                    self.label_updated.emit(f'无法删除旧的知秋工作平台exe: {os.path.basename(old_exe)} ({str(e)})')
                                    # 继续执行，不中断更新过程
                        
                        # 检查是否是普通可执行文件且正在运行
                        elif file_name.lower().endswith('.exe'):
                            # 普通可执行文件正在运行时无法直接替换，跳过更新
                            print(f"跳过更新正在运行的可执行文件: {file_name}")
                            self.label_updated.emit(f'跳过更新正在运行的可执行文件: {file_name}')
                            updated_files += 1
                            progress = int((updated_files / total_files) * 100)
                            self.progress_updated.emit(progress)
                            continue
                        
                        # 下载文件到临时目录
                        temp_dir = tempfile.mkdtemp()
                        temp_file_path = os.path.join(temp_dir, file_name)
                        
                        try:
                            # 下载文件，增加超时时间
                            response = requests.get(download_url, stream=True, timeout=10)
                            response.raise_for_status()
                            
                            # 确保父目录存在
                            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                            
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded_size = 0
                            start_time = time.time()
                            
                            # 转换文件大小为可读格式
                            def format_size(size_bytes):
                                if size_bytes >= 1024 * 1024 * 1024:
                                    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
                                elif size_bytes >= 1024 * 1024:
                                    return f"{size_bytes / (1024 * 1024):.2f} MB"
                                elif size_bytes >= 1024:
                                    return f"{size_bytes / 1024:.2f} KB"
                                else:
                                    return f"{size_bytes} B"
                            
                            total_size_str = format_size(total_size)
                            
                            with open(temp_file_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded_size += len(chunk)
                                        # 计算下载速度
                                        elapsed_time = time.time() - start_time
                                        if elapsed_time > 0:
                                            download_speed = downloaded_size / elapsed_time
                                            # 转换速度单位
                                            if download_speed > 1024 * 1024:
                                                speed_str = f"{download_speed / (1024 * 1024):.2f} MB/s"
                                            elif download_speed > 1024:
                                                speed_str = f"{download_speed / 1024:.2f} KB/s"
                                            else:
                                                speed_str = f"{download_speed:.2f} B/s"
                                            # 更新进度对话框文本，包含下载速度、已下载大小和总大小
                                            downloaded_size_str = format_size(downloaded_size)
                                            self.label_updated.emit(f'正在更新文件: {file_info["file_path"]}\n速度: {speed_str}\n已下载: {downloaded_size_str}/{total_size_str}')
                        except requests.exceptions.RequestException as e:
                            self.update_error.emit(f'文件下载失败：{str(e)}')
                            return
                        
                        # 确保本地文件的父目录存在
                        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                        
                        # 替换本地文件 - 增强权限处理
                        try:
                            # 尝试直接复制文件
                            print(f"正在复制文件: {temp_file_path} -> {local_file_path}")
                            shutil.copy2(temp_file_path, local_file_path)
                            print(f"文件复制成功: {local_file_path}")
                            
                            # 如果是知秋工作平台exe文件，保存其路径
                            if '知秋工作平台' in file_name and file_name.endswith('.exe'):
                                self.updated_exe_path = local_file_path
                        except PermissionError:
                            # 权限错误，尝试多种解决方案
                            backup_path = f"{local_file_path}.bak"
                            try:
                                # 方案1：使用备份方式
                                # 先删除旧的备份文件（如果存在）
                                if os.path.exists(backup_path):
                                    os.remove(backup_path)
                                # 重命名原文件为备份
                                os.rename(local_file_path, backup_path)
                                # 复制新文件
                                shutil.copy2(temp_file_path, local_file_path)
                                # 删除备份文件
                                os.remove(backup_path)
                            except Exception as e:
                                try:
                                    # 方案2：尝试设置文件可写权限
                                    import stat
                                    if os.path.exists(local_file_path):
                                        # 设置文件可写权限
                                        os.chmod(local_file_path, stat.S_IWRITE | stat.S_IRREAD | stat.S_IEXEC)
                                        # 再次尝试复制
                                        shutil.copy2(temp_file_path, local_file_path)
                                    else:
                                        # 文件不存在，直接复制（这应该不会触发权限错误，但为了保险起见）
                                        # 确保父目录存在
                                        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                                        # 直接复制
                                        shutil.copy2(temp_file_path, local_file_path)
                                except Exception as e:
                                    try:
                                        # 方案3：使用管理员权限复制文件（通过PowerShell命令）
                                        import subprocess
                                        # 构建PowerShell命令，使用Copy-Item命令和-Force参数
                                        powershell_cmd = f"Copy-Item -Path '{temp_file_path}' -Destination '{local_file_path}' -Force"
                                        # 执行PowerShell命令
                                        subprocess.run(["powershell", "-Command", powershell_cmd], check=True, capture_output=True, text=True)
                                    except Exception as e:
                                            # 所有方案都失败，记录错误
                                            error_msg = f"无法更新文件: {file_name} (权限错误: {str(e)})"
                                            print(error_msg)
                                            # 发送详细的错误信息，提示用户需要管理员权限
                                            self.update_error.emit(f'无法更新文件 {file_name}，权限不足。请以管理员身份运行应用程序后重试。')
                                            return
                        
                        # 清理临时文件
                        shutil.rmtree(temp_dir)
                        
                        # 如果是知秋工作平台exe文件，生成桌面快捷方式
                        if '知秋工作平台' in file_name and file_name.endswith('.exe'):
                            self.label_updated.emit(f'正在生成桌面快捷方式...')
                            try:
                                import win32com.client
                                import os
                                
                                # 获取桌面路径
                                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                                
                                # 快捷方式名称（不带版本号）
                                shortcut_name = "知秋工作平台.lnk"
                                shortcut_path = os.path.join(desktop_path, shortcut_name)
                                
                                # 如果快捷方式已存在，先删除
                                if os.path.exists(shortcut_path):
                                    os.remove(shortcut_path)
                                
                                # 创建快捷方式
                                shell = win32com.client.Dispatch("WScript.Shell")
                                shortcut = shell.CreateShortCut(shortcut_path)
                                shortcut.Targetpath = local_file_path
                                shortcut.WorkingDirectory = os.path.dirname(local_file_path)
                                shortcut.IconLocation = local_file_path  # 使用exe文件的图标
                                shortcut.save()
                                
                                self.label_updated.emit(f'桌面快捷方式已生成')
                            except Exception as e:
                                # 生成快捷方式失败，不影响更新结果，仅记录日志
                                print(f"生成桌面快捷方式失败: {str(e)}")
                        
                        # 更新进度
                        updated_files += 1
                        progress = int((updated_files / total_files) * 100)
                        self.progress_updated.emit(progress)
                    
                    # 更新完成
                    print(f"所有文件更新完成，共更新了 {updated_files} 个文件")
                    self.label_updated.emit('文件更新完成')
                    self.progress_updated.emit(100)
                    self.update_completed.emit()
                except requests.exceptions.RequestException:
                    # 网络请求失败
                    self.update_error.emit('无法连接到服务器，请联系研发人员开启服务器')
                except Exception as e:
                    # 发送错误信号
                    self.update_error.emit(str(e))
        
        # 连接进度信号
        def on_progress_updated(value):
            self.progress_dialog.setValue(value)
            QApplication.processEvents()
        
        def on_label_updated(text):
            self.progress_dialog.setLabelText(text)
            QApplication.processEvents()
        
        def on_update_completed():
            """更新完成"""
            self.progress_dialog.close()
            self.__onFilesUpdateCompleted()
        
        def on_update_error(error_message):
            """更新错误"""
            self.progress_dialog.close()
            self.__onFilesUpdateError(error_message)
        
        # 连接完成和错误信号
        self.update_completed.connect(on_update_completed)
        self.update_error.connect(on_update_error)
        
        # 创建并启动线程
        self.update_files_thread = UpdateFilesThread(files_to_update)
        self.update_files_thread.progress_updated.connect(on_progress_updated)
        self.update_files_thread.label_updated.connect(on_label_updated)
        self.update_files_thread.update_completed.connect(self.update_completed)
        self.update_files_thread.update_error.connect(self.update_error)
        
        # 显示进度对话框
        self.progress_dialog.show()
        
        # 启动线程执行更新
        self.update_files_thread.start()
    
    def __onFilesUpdateCompleted(self):
        """文件更新完成"""
        InfoBar.success(
            '文件更新完成',
            '所有文件已成功更新',
            duration=3000,
            parent=self
        )
        
        # 询问用户是否立即重启应用
        from qfluentwidgets import MessageBox
        msg_box = MessageBox(
            '文件更新完成',
            '所有文件已成功更新，请重启应用以生效。是否立即重启？',
            self
        )
        msg_box.yesButton.setText('立即重启')
        msg_box.cancelButton.setText('稍后重启')
        
        if msg_box.exec():
            # 重启应用
            import sys
            import os
            import glob
            
            # 获取本地安装目录
            local_install_dir = "C:\Program Files (x86)\知秋工作平台"
            
            # 如果更新了知秋工作平台的exe文件
            if hasattr(self, 'update_files_thread') and hasattr(self.update_files_thread, 'updated_exe_path') and self.update_files_thread.updated_exe_path:
                updated_exe_path = self.update_files_thread.updated_exe_path
                
                # 获取所有旧版exe文件路径（不包括刚更新的）
                local_zhiqiu_exes = glob.glob(os.path.join(local_install_dir, '知秋工作平台*.exe'))
                old_exes = [exe for exe in local_zhiqiu_exes if exe != updated_exe_path]
                
                # 启动新的exe进程
                print(f"正在启动新版本exe: {updated_exe_path}")
                os.startfile(updated_exe_path)
                
                # 关闭当前应用
                QApplication.quit()
                
                # 延迟删除旧版exe文件（因为可能还在使用）
                def delete_old_exes():
                    import time
                    time.sleep(2)  # 等待2秒，确保当前进程已关闭
                    for old_exe in old_exes:
                        try:
                            if os.path.exists(old_exe):
                                print(f"正在删除旧版exe: {old_exe}")
                                os.remove(old_exe)
                                print(f"已删除旧版exe: {old_exe}")
                        except Exception as e:
                            print(f"无法删除旧版exe {old_exe}: {str(e)}")
                
                # 在后台线程中删除旧版exe文件
                import threading
                delete_thread = threading.Thread(target=delete_old_exes)
                delete_thread.daemon = True
                delete_thread.start()
            else:
                # 没有更新exe文件，使用原来的逻辑
                os.execl(sys.executable, sys.executable, *sys.argv)
    
    def __onFilesUpdateError(self, error_message):
        """文件更新错误"""
        InfoBar.error(
            '文件更新失败',
            f'文件更新过程中发生错误：{error_message}',
            duration=3000,
            parent=self
        )
    
    def __updateVersionCard(self, current_version, latest_version):
        """更新版本卡片内容"""
        self.versionCard.setContent(f'当前版本号: {current_version}')
    
    def __showUpdateAvailable(self, project_info):
        """显示有新版本可用"""
        from qfluentwidgets import MessageBox
        
        latest_version = project_info['version']
        update_log = project_info['update_log']
        download_url = project_info['download_url']
        
        InfoBar.success(
            '发现新版本',
            f'已发现新版本 {latest_version}，可以立即更新',
            duration=3000,
            parent=self
        )
        
        # 使用qfluentwidgets的MessageBox，自动适配主题
        msg_box = MessageBox(
            '发现新版本',
            f'已发现新版本 {latest_version}\n\n更新日志：\n{update_log}',
            self
        )
        msg_box.yesButton.setText('立即更新')
        msg_box.cancelButton.setText('稍后更新')
        
        if msg_box.exec():
            # 开始更新流程
            self.__startUpdate(project_info)
    
    def __startUpdate(self, project_info):
        """开始更新流程"""
        from PyQt6.QtCore import QObject, pyqtSignal
        import threading
        import os
        import shutil
        import tempfile
        import requests
        
        # 创建一个信号类用于线程间通信
        class UpdateProcessSignal(QObject):
            update_progress = pyqtSignal(int)  # 更新进度信号
            update_error = pyqtSignal(str)  # 更新错误信号
            update_completed = pyqtSignal()  # 更新完成信号
        
        def update_process():
            try:
                # 显示更新中提示
                InfoBar.info(
                    '正在更新',
                    '正在下载更新包，请稍候...',
                    duration=0,  # 不自动关闭
                    parent=self
                )
                
                # 下载更新包
                download_url = project_info['download_url']
                temp_dir = tempfile.mkdtemp()
                update_file_path = os.path.join(temp_dir, 'update.zip')
                
                # 发送请求下载文件
                response = requests.get(download_url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                start_time = time.time()
                
                # 转换文件大小为可读格式
                def format_size(size_bytes):
                    if size_bytes >= 1024 * 1024 * 1024:
                        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
                    elif size_bytes >= 1024 * 1024:
                        return f"{size_bytes / (1024 * 1024):.2f} MB"
                    elif size_bytes >= 1024:
                        return f"{size_bytes / 1024:.2f} KB"
                    else:
                        return f"{size_bytes} B"
                
                total_size_str = format_size(total_size)
                
                with open(update_file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            # 计算进度百分比
                            if total_size > 0:
                                progress = int((downloaded_size / total_size) * 100)
                            else:
                                progress = 0
                            # 计算下载速度
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                download_speed = downloaded_size / elapsed_time
                                # 转换速度单位
                                if download_speed > 1024 * 1024:
                                    speed_str = f"{download_speed / (1024 * 1024):.2f} MB/s"
                                elif download_speed > 1024:
                                    speed_str = f"{download_speed / 1024:.2f} KB/s"
                                else:
                                    speed_str = f"{download_speed:.2f} B/s"
                                # 转换已下载大小为可读格式
                                downloaded_size_str = format_size(downloaded_size)
                                # 更新提示信息
                                InfoBar.info(
                                    '正在更新',
                                    f'正在下载更新包，请稍候...\n进度: {progress}%\n速度: {speed_str}\n已下载: {downloaded_size_str}/{total_size_str}',
                                    duration=0,  # 不自动关闭
                                    parent=self
                                )
                
                # 更新完成后显示提示
                InfoBar.success(
                    '更新完成',
                    '更新包下载完成，准备安装...',
                    duration=2000,
                    parent=self
                )
                
                # 解压更新包
                import zipfile
                import tempfile
                
                extract_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(update_file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # 获取应用程序的安装目录
                app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                
                # 复制更新文件到应用目录
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        # 计算相对路径
                        rel_path = os.path.relpath(src_path, extract_dir)
                        dst_path = os.path.join(app_dir, rel_path)
                        
                        # 确保目标目录存在
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        
                        # 替换旧文件
                        shutil.copy2(src_path, dst_path)
                
                # 清理临时文件
                shutil.rmtree(temp_dir)
                shutil.rmtree(extract_dir)
                
                # 发送更新完成信号
                update_signal.update_completed.emit()
                
            except Exception as e:
                # 发送错误信号
                update_signal.update_error.emit(str(e))
        
        # 创建信号实例
        update_signal = UpdateProcessSignal()
        
        # 连接信号到槽
        update_signal.update_completed.connect(self.__onUpdateCompleted)
        update_signal.update_error.connect(self.__onUpdateError)
        
        # 启动线程执行更新
        thread = threading.Thread(target=update_process)
        thread.daemon = True
        thread.start()
    
    def __onUpdateCompleted(self):
        """更新完成"""
        InfoBar.success(
            '更新成功',
            '应用已成功更新，请重启应用以生效',
            duration=3000,
            parent=self
        )
        
        # 询问用户是否立即重启
        from qfluentwidgets import MessageBox
        msg_box = MessageBox(
            '更新完成',
            '应用已成功更新，请重启应用以生效。是否立即重启？',
            self
        )
        msg_box.yesButton.setText('立即重启')
        msg_box.cancelButton.setText('稍后重启')
        
        if msg_box.exec():
            # 重启应用
            import sys
            import os
            os.execl(sys.executable, sys.executable, *sys.argv)
    
    def __onUpdateError(self, error_message):
        """更新错误"""
        InfoBar.error(
            '更新失败',
            f'更新过程中发生错误：{error_message}',
            duration=3000,
            parent=self
        )
    
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
