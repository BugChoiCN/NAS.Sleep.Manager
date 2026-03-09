# 修复说明

## 问题诊断

### 问题1: 桌面没有图标
**原因**: 缺少桌面快捷方式文件
**修复**:
- 创建了 `app/ui/NAS.Sleep.Manager.Application.desktop`
- 修改了 `manifest` 中的 `desktop_uidir` 为 `app/ui`

### 问题2: 应用中心点击打开没响应
**原因**: CGI路由配置不正确,根路径没有返回HTML
**修复**:
- 修改了 `app/ui/config` 中的URL为 `/cgi/ThirdParty/NAS.Sleep.Manager/main.cgi/`
- 在 `app/cgi/main.cgi` 中添加了根路径 `/` 和 `/main.cgi` 的处理
- 移除了URL参数 `openConfig=true` 的处理

### 问题3: 配置界面为空
**原因**: wizard配置没有提示信息,初始化脚本不存在
**修复**:
- 在 `wizard/config` 中添加了 `tips` 提示
- 创建了 `cmd/config_init` 初始化脚本
- 所有字段都有 `initValue` 默认值

## 文件变更

### 新增文件
- `app/ui/NAS.Sleep.Manager.Application.desktop` - 桌面快捷方式
- `app/ui/config.html` - 配置页面
- `cmd/config_init` - 配置初始化脚本
- `diagnose.sh` - 诊断脚本

### 修改文件
- `manifest` - 修改 `desktop_uidir` 为 `app/ui`
- `app/ui/config` - 修改URL指向CGI
- `app/ui/index.html` - 移除URL参数处理,添加健康检查
- `app/cgi/main.cgi` - 添加根路径处理,添加健康检查API
- `cmd/install_callback` - 添加权限设置
- `wizard/config` - 添加提示信息

## 测试步骤

### 1. 重新打包插件
将所有文件打包为 .tar.gz 格式

### 2. 卸载旧版本
在飞牛应用中心卸载旧版本插件

### 3. 完全重启飞牛
重启飞牛系统以清除缓存

### 4. 重新安装
上传并安装新版本插件

### 5. 验证图标
检查桌面是否出现图标:
- 桌面应该有 "NAS智能休眠管理" 图标
- 图标应该显示在应用中心

### 6. 测试打开
- 点击桌面图标应该打开Web UI
- 在应用中心点击"打开"应该也能打开

### 7. 测试配置
- 点击"打开配置向导"按钮
- 应该能看到配置界面和默认值

### 8. 运行诊断
如果还有问题,运行诊断脚本:
```bash
bash /path/to/NAS.Sleep.Manager/diagnose.sh
```

## 配置说明

配置界面包含以下字段:
- 启用自动休眠功能 (默认: 开启)
- 空闲休眠时间（分钟）(默认: 30, 范围: 5-240)
- 检查间隔（秒）(默认: 60, 范围: 10-300)
- 最大允许连接数 (默认: 5, 范围: 0-50)
- 启用网络唤醒（WOL）(默认: 开启)
- 启用详细日志记录 (默认: 开启)

## 健康检查

Web UI 现在包含健康检查功能:
- 服务运行状态
- 进程运行时间
- 最后检查时间
- 配置文件状态
- 日志文件状态
- 刷新检测按钮
- 测试休眠按钮

## 注意事项

1. **文件权限**: 安装后会自动设置脚本可执行权限
2. **图标路径**: 确保图标文件存在于 `app/ui/images/` 目录
3. **CGI访问**: CGI脚本需要web服务器支持
4. **环境变量**: 需要 `TRIM_APPDEST`, `TRIM_PKGETC`, `TRIM_PKGVAR` 环境变量
5. **配置文件**: 配置文件位于 `$TRIM_PKGETC/nas-suspend.conf`

## 故障排查

如果点击打开没响应:
1. 检查日志: `tail -f /var/log/nginx/error.log` (或对应的web服务器日志)
2. 检查权限: 确保 `app/cgi/main.cgi` 有执行权限
3. 运行诊断: `bash /path/to/diagnose.sh`
4. 查看进程: `ps aux | grep nas-sleep`
5. 测试CGI: `curl http://localhost:8085/cgi/ThirdParty/NAS.Sleep.Manager/main.cgi/`
