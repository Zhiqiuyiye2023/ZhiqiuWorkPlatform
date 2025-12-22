# coding:utf-8
import os
import sys
import json
import shutil
import threading
import tempfile
import subprocess
from typing import Optional, Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtGui import QDesktopServices

class UpdateManager(QObject):
    """GitHub Releases自动更新管理器"""
    
    # 信号定义
    updateAvailable = pyqtSignal(str, str)  # 有更新可用，参数：新版本号，更新说明
    updateNotAvailable = pyqtSignal()       # 已是最新版本
    updateProgress = pyqtSignal(int)        # 更新进度，参数：百分比
    updateCompleted = pyqtSignal()          # 更新完成
    updateFailed = pyqtSignal(str)          # 更新失败，参数：错误信息
    
    def __init__(self, github_repo: str = "your_username/your_repo", current_version: str = "1.0.0"):
        """
        初始化更新管理器
        
        Args:
            github_repo: GitHub仓库地址，格式：username/repo
            current_version: 当前应用版本
        """
        super().__init__()
        
        self.github_repo = github_repo
        self.current_version = current_version
        self.latest_version = None
        self.latest_download_url = None
        self.latest_release_notes = None
        
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._onNetworkReply)
        
        # 存储正在进行的请求
        self.current_reply = None
    
    def checkForUpdates(self):
        """检查GitHub Releases是否有新版本"""
        self._is_checking = True
        
        # 构建GitHub API URL
        api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        
        # 发送网络请求
        request = QNetworkRequest(QUrl(api_url))
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "GitHub Update Checker")
        self.current_reply = self.network_manager.get(request)
    
    def _onNetworkReply(self, reply: QNetworkReply):
        """网络请求完成回调"""
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.updateFailed.emit(f"网络请求失败: {reply.errorString()}")
            return
        
        try:
            # 解析JSON响应
            data = json.loads(reply.readAll().data().decode("utf-8"))
            
            # 提取版本信息
            self.latest_version = data["tag_name"].lstrip("v")  # 移除可能的v前缀
            self.latest_release_notes = data["body"]
            
            # 查找Windows可执行文件下载链接
            for asset in data["assets"]:
                if asset["name"].endswith(".exe") and "Windows" in asset["name"]:
                    self.latest_download_url = asset["browser_download_url"]
                    break
            
            # 如果没有找到Windows可执行文件，尝试查找任何.exe文件
            if not self.latest_download_url:
                for asset in data["assets"]:
                    if asset["name"].endswith(".exe"):
                        self.latest_download_url = asset["browser_download_url"]
                        break
            
            # 比较版本号
            if self._isNewerVersion(self.latest_version, self.current_version):
                self.updateAvailable.emit(self.latest_version, self.latest_release_notes)
            else:
                self.updateNotAvailable.emit()
                
        except Exception as e:
            self.updateFailed.emit(f"解析GitHub响应失败: {str(e)}")
        finally:
            reply.deleteLater()
    
    def _isNewerVersion(self, version1: str, version2: str) -> bool:
        """比较两个版本号，判断version1是否比version2新"""
        # 简单的版本号比较逻辑，适用于x.y.z格式
        v1_parts = list(map(int, version1.split(".")))
        v2_parts = list(map(int, version2.split(".")))
        
        # 补齐版本号长度
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_len - len(v1_parts))
        v2_parts += [0] * (max_len - len(v2_parts))
        
        # 比较每个部分
        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 > v2:
                return True
            if v1 < v2:
                return False
        
        return False
    
    def downloadAndUpdate(self):
        """下载并安装更新"""
        if not self.latest_download_url:
            self.updateFailed.emit("没有找到可用的下载链接")
            return
        
        # 创建临时文件来保存下载的更新包
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".exe", delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        
        # 发送下载请求
        request = QNetworkRequest(QUrl(self.latest_download_url))
        self.current_reply = self.network_manager.get(request)
        self.current_reply.downloadProgress.connect(self._onDownloadProgress)
        self.current_reply.finished.connect(self._onDownloadFinished)
    
    def _onDownloadProgress(self, bytes_received: int, bytes_total: int):
        """下载进度回调"""
        if bytes_total > 0:
            progress = int((bytes_received / bytes_total) * 100)
            self.updateProgress.emit(progress)
    
    def _onDownloadFinished(self):
        """下载完成回调"""
        if self.current_reply.error() != QNetworkReply.NetworkError.NoError:
            self.updateFailed.emit(f"下载失败: {self.current_reply.errorString()}")
            return
        
        try:
            # 将下载的数据写入临时文件
            with open(self.temp_file_path, "wb") as f:
                f.write(self.current_reply.readAll().data())
            
            # 关闭当前请求
            self.current_reply.deleteLater()
            
            # 安装更新
            self._installUpdate()
            
        except Exception as e:
            self.updateFailed.emit(f"保存下载文件失败: {str(e)}")
    
    def _installUpdate(self):
        """安装更新"""
        try:
            # 获取当前应用的可执行文件路径
            current_exe_path = sys.executable
            
            # 构建更新命令
            # 使用cmd.exe启动新的更新程序，并退出当前程序
            update_cmd = f'start "" "{self.temp_file_path}" "--update" "{current_exe_path}"'
            
            # 执行更新命令
            subprocess.Popen(update_cmd, shell=True)
            
            # 退出当前应用
            QApplication.quit()
            
        except Exception as e:
            self.updateFailed.emit(f"启动更新程序失败: {str(e)}")
    
    def checkForUpdatesOnStartup(self, auto_check: bool = True):
        """启动时检查更新"""
        if auto_check:
            self.checkForUpdates()
    
    def openGitHubReleases(self):
        """打开GitHub Releases页面"""
        releases_url = f"https://github.com/{self.github_repo}/releases"
        QDesktopServices.openUrl(QUrl(releases_url))
    
    def setCurrentVersion(self, version: str):
        """设置当前应用版本"""
        self.current_version = version
    
    def setGitHubRepo(self, repo: str):
        """设置GitHub仓库地址"""
        self.github_repo = repo


def main():
    """主函数，用于测试更新功能"""
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QProgressBar
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = QWidget()
    window.setWindowTitle("自动更新测试")
    window.resize(500, 400)
    
    # 创建布局
    layout = QVBoxLayout(window)
    
    # 创建文本编辑框
    text_edit = QTextEdit()
    text_edit.setReadOnly(True)
    layout.addWidget(text_edit)
    
    # 创建进度条
    progress_bar = QProgressBar()
    progress_bar.setValue(0)
    layout.addWidget(progress_bar)
    
    # 创建更新管理器
    update_manager = UpdateManager("your_username/your_repo", "1.0.0")
    
    # 连接信号
    def on_update_available(version, notes):
        text_edit.append(f"发现新版本: {version}")
        text_edit.append(f"更新说明: {notes}")
        
    def on_update_not_available():
        text_edit.append("已是最新版本")
        
    def on_update_progress(progress):
        progress_bar.setValue(progress)
        
    def on_update_completed():
        text_edit.append("更新完成")
        
    def on_update_failed(error):
        text_edit.append(f"更新失败: {error}")
        
    update_manager.updateAvailable.connect(on_update_available)
    update_manager.updateNotAvailable.connect(on_update_not_available)
    update_manager.updateProgress.connect(on_update_progress)
    update_manager.updateCompleted.connect(on_update_completed)
    update_manager.updateFailed.connect(on_update_failed)
    
    # 创建检查更新按钮
    check_btn = QPushButton("检查更新")
    check_btn.clicked.connect(update_manager.checkForUpdates)
    layout.addWidget(check_btn)
    
    # 创建下载更新按钮
    download_btn = QPushButton("下载更新")
    download_btn.clicked.connect(update_manager.downloadAndUpdate)
    layout.addWidget(download_btn)
    
    # 显示窗口
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
