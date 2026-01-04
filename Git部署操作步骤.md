# Git部署操作步骤

## 1. Git环境准备

### 1.1 安装Git
- Windows系统：从 [Git官网](https://git-scm.com/download/win) 下载并安装Git
- 安装时建议选择以下配置：
  - 勾选"Git Bash Here"和"Git GUI Here"
  - 默认编辑器选择VS Code或其他你熟悉的编辑器
  - 换行符处理选择"Checkout Windows-style, commit Unix-style line endings"
  - 终端模拟器选择"Use Windows' default console window"

### 1.2 配置Git全局信息
打开Git Bash或命令提示符，执行以下命令配置全局用户名和邮箱：

```bash
git config --global user.name "Zhiqiuyiye2023"
git config --global user.email "527887478@qq.com"
```

## 2. 本地仓库初始化

### 2.1 初始化Git仓库
在项目根目录下执行：

```bash
git init
```

执行成功后，会在项目根目录生成一个隐藏的`.git`文件夹。

### 2.2 查看Git状态

```bash
git status
```

## 3. .gitignore文件配置

### 3.1 创建.gitignore文件
在项目根目录创建`.gitignore`文件，用于指定不需要纳入Git版本控制的文件和目录。

### 3.2 常用.gitignore配置

```gitignore
# Python相关
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Qt相关
*.qm
*.ts

# 配置文件
config.json
*.ini

# 日志文件
*.log
logs/

# 打包文件
*.exe
*.zip
*.rar

# 操作系统文件
.DS_Store
Thumbs.db

# IDE相关
.idea/
.vscode/
*.swp
*.swo
*~

# 临时文件
*.tmp
*.temp
```

## 4. 代码提交

### 4.1 添加文件到暂存区

```bash
# 添加所有文件到暂存区
git add .

# 或添加指定文件
git add 文件名
```

### 4.2 提交代码到本地仓库

```bash
git commit -m "提交描述信息"
```

提交描述信息建议清晰明了，说明本次提交的主要内容。

## 5. 远程仓库关联

### 5.1 创建远程仓库
在GitHub、GitLab或Gitee等平台创建一个新的远程仓库。

### 5.2 关联远程仓库

```bash
git remote add origin https://github.com/Zhiqiuyiye2023/ZhiqiuWorkPlatform.git
```

例如：
```bash
git remote add origin https://github.com/用户名/仓库名.git
```

### 5.3 查看远程仓库信息

```bash
git remote -v
```

## 6. 代码推送

### 6.1 推送代码到远程仓库

```bash
git push -u origin master
```

如果是第一次推送，需要加上`-u`参数，将本地分支与远程分支关联起来。

### 6.2 后续推送

```bash
git push
```

## 7. 分支管理

### 7.1 创建分支

```bash
git branch 分支名
```

### 7.2 切换分支

```bash
git checkout 分支名
```

或使用新语法：
```bash
git switch 分支名
```

### 7.3 创建并切换分支

```bash
git checkout -b 分支名
```

或使用新语法：
```bash
git switch -c 分支名
```

### 7.4 查看所有分支

```bash
git branch -a
```

### 7.5 合并分支
例如，将dev分支合并到master分支：

```bash
git checkout master
git merge dev
```

### 7.6 删除分支

```bash
git branch -d 分支名
```

如果分支未合并，需要使用`-D`强制删除：
```bash
git branch -D 分支名
```

## 8. 拉取代码

### 8.1 拉取远程代码并合并

```bash
git pull
```

### 8.2 仅拉取远程代码不合并

```bash
git fetch
```

## 9. 常见问题及解决方案

### 9.1 推送失败
- 问题：`fatal: Authentication failed for 'https://github.com/用户名/仓库名.git/'`
- 解决方案：检查远程仓库URL是否正确，或重新配置Git凭证

### 9.2 合并冲突
- 问题：合并分支时出现冲突
- 解决方案：手动编辑冲突文件，解决冲突后重新提交

### 9.3 误提交文件
- 问题：将不需要提交的文件提交到了本地仓库
- 解决方案：
  ```bash
  # 从暂存区移除文件但保留本地文件
  git rm --cached 文件名
  # 从本地仓库中删除文件
  git rm 文件名
  ```

## 10. 高级操作

### 10.1 查看提交历史

```bash
git log
```

### 10.2 查看提交差异

```bash
git diff
# 或查看指定文件的差异
git diff 文件名
```

### 10.3 撤销修改

```bash
# 撤销工作区的修改
git checkout -- 文件名
# 撤销暂存区的修改
git reset HEAD 文件名
# 撤销本地仓库的提交
git reset --soft HEAD^  # 保留工作区和暂存区的修改
git reset --mixed HEAD^  # 保留工作区的修改，重置暂存区
git reset --hard HEAD^  # 彻底撤销所有修改，谨慎使用
```

## 11. 标签管理

### 11.1 创建标签

```bash
git tag v1.0.0  # 创建轻量标签
git tag -a v1.0.0 -m "版本1.0.0"  # 创建带注释的标签
```

### 11.2 查看标签

```bash
git tag
```

### 11.3 推送标签到远程仓库

```bash
git push origin v1.0.0  # 推送指定标签
git push origin --tags  # 推送所有标签
```

## 12. 流程建议

1. 每天开始工作前，先执行`git pull`拉取最新代码
2. 完成一个功能或修复一个bug后，执行`git add .`和`git commit`提交代码
3. 每天结束工作前，执行`git push`将本地代码推送到远程仓库
4. 开发新功能时，创建新的分支进行开发，完成后再合并到主分支
5. 定期查看`git status`，确保没有遗漏的文件

以上就是Git部署的基本操作步骤，根据实际项目需求可以灵活调整。