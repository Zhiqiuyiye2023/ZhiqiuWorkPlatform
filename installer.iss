; 安装脚本配置
[Setup]
AppName=知秋工作平台
AppVersion=1.0.5.0129
DefaultDirName={commonpf}\知秋工作平台
DefaultGroupName=知秋工作平台
OutputBaseFilename=知秋工作安装包v1.0.5.0129
SetupIconFile=logo.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

; 安装程序语言设置
[Languages]
Name: "chinese"; MessagesFile: "compiler:Default.isl"

; 安装文件配置
[Files]
Source: "dist\知秋工作平台v1.0.5.0129\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "version.json"; DestDir: "{app}"; Flags: ignoreversion

; 桌面快捷方式
[Icons]
Name: "{autodesktop}\知秋工作平台"; Filename: "{app}\知秋工作平台v1.0.5.0129.exe"; WorkingDir: "{app}"; IconFilename: "{app}\logo.ico"
Name: "{group}\知秋工作平台"; Filename: "{app}\知秋工作平台v1.0.5.0129.exe"; WorkingDir: "{app}"; IconFilename: "{app}\logo.ico"
Name: "{group}\卸载知秋工作平台"; Filename: "{uninstallexe}"

; 安装完成页面
[Run]
Filename: "{app}\知秋工作平台v1.0.5.0129.exe"; Description: "启动知秋工作平台"; Flags: postinstall nowait skipifsilent

; 安装程序界面配置
[Setup]
LicenseFile=LICENSE.txt
InfoBeforeFile=README.txt

; 安装进度页面
[InstallDelete]
Type: files; Name: "{app}\知秋工作平台.exe"
Type: files; Name: "{app}\知秋工作平台v1.0.5.0129.exe"

; 安装日志
[Setup]
SetupLogging=yes