# GitHub Releases 发布指南

## 1. 概述

本指南将介绍如何将您的项目部署到GitHub上，并通过GitHub Releases实现EXE文件的自动更新功能。

## 2. 准备工作

### 2.1 创建GitHub仓库

1. 登录GitHub账号
2. 创建一个新的仓库
3. 将您的项目代码推送到GitHub仓库

### 2.2 配置自动更新模块

在`update_manager.py`文件中，修改以下配置：

```python
# 将 your_username/your_repo 替换为您的GitHub仓库地址
self.updateManager = UpdateManager("your_username/your_repo", "1.0.0")
```

在`demo.py`和`setting_interface.py`文件中，同样修改GitHub仓库地址。

## 3. 打包应用

使用项目中的`build_exe.bat`脚本打包应用：

1. 双击运行`build_exe.bat`
2. 输入版本号（例如：1.0.0）
3. 等待打包完成
4. 在`dist`目录中会生成打包好的EXE文件

## 4. 发布新版本到GitHub Releases

### 4.1 创建Release

1. 进入GitHub仓库页面
2. 点击"Releases"标签
3. 点击"Draft a new release"

### 4.2 填写Release信息

1. **Tag version**：输入版本号（例如：v1.0.0）
2. **Target**：选择要发布的分支
3. **Release title**：输入发布标题（例如：v1.0.0 发布）
4. **Describe this release**：输入更新说明

### 4.3 上传EXE文件

1. 点击"Attach binaries by dropping them here or selecting them"
2. 选择`dist`目录中打包好的EXE文件
3. 等待上传完成

### 4.4 发布Release

1. 点击"Publish release"
2. 新版本发布成功

## 5. 自动更新功能

### 5.1 启动时自动检查

- 应用启动时会自动检查GitHub Releases是否有新版本
- 如果有新版本，会在右上角显示提示信息

### 5.2 手动检查更新

- 进入应用的"设置"页面
- 点击"检查更新"按钮
- 如果有新版本，会弹出更新提示

### 5.3 更新流程

1. 检查到新版本后，点击"立即更新"
2. 应用会下载最新的EXE文件
3. 下载完成后，应用会自动重启并安装更新
4. 安装完成后，应用会启动新版本

## 6. 版本号规范

建议使用语义化版本号规范：

- **主版本号**：当您做了不兼容的API修改
- **次版本号**：当您做了向下兼容的功能性新增
- **修订号**：当您做了向下兼容的问题修正

例如：1.0.0、1.1.0、1.1.1

## 7. 注意事项

1. 确保打包的EXE文件名称中包含版本号
2. 每次发布新版本时，Tag version必须唯一
3. 发布说明要清晰明了，说明本次更新的内容
4. 确保GitHub仓库地址配置正确
5. 确保自动更新模块中的版本号与实际版本一致

## 8. 常见问题

### 8.1 自动更新失败

- 检查网络连接是否正常
- 检查GitHub仓库地址是否正确
- 检查Release中是否上传了EXE文件

### 8.2 版本检测不准确

- 确保Tag version格式正确（例如：v1.0.0）
- 确保自动更新模块中的版本号与实际版本一致

### 8.3 更新后应用无法启动

- 检查打包过程是否有错误
- 检查Release中上传的EXE文件是否完整
- 检查应用依赖是否正确

## 9. 总结

通过GitHub Releases和自动更新模块，您可以轻松实现应用的自动更新功能。用户只需要保持应用开启，就可以收到新版本的更新提示，并一键更新到最新版本。

这种方式不仅方便了用户，也方便了开发者，可以快速将新功能和 bug 修复推送给用户。