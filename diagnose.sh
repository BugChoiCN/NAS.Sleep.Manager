#!/bin/bash

# 诊断脚本 - 检查应用安装状态

echo "========================================"
echo "NAS智能休眠管理 - 诊断工具"
echo "========================================"
echo ""

# 1. 检查文件结构
echo "1. 检查文件结构..."
FILES=(
    "$TRIM_APPDEST/app/cgi/main.cgi"
    "$TRIM_APPDEST/app/ui/index.html"
    "$TRIM_APPDEST/app/ui/config"
    "$TRIM_APPDEST/app/ui/NAS.Sleep.Manager.Application.desktop"
    "$TRIM_APPDEST/app/ui/images/icon-64.png"
    "$TRIM_APPDEST/app/ui/images/icon-256.png"
    "$TRIM_APPDEST/cmd/main"
    "$TRIM_APPDEST/cmd/config_init"
    "$TRIM_APPDEST/cmd/config_callback"
    "$TRIM_APPDEST/manifest"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (不存在)"
    fi
done

echo ""

# 2. 检查权限
echo "2. 检查文件权限..."
if [ -x "$TRIM_APPDEST/app/cgi/main.cgi" ]; then
    echo "  ✓ main.cgi 可执行"
else
    echo "  ✗ main.cgi 不可执行"
    echo "    尝试修复: chmod +x $TRIM_APPDEST/app/cgi/main.cgi"
fi

echo ""

# 3. 检查配置
echo "3. 检查配置..."
if [ -f "$TRIM_PKGETC/nas-suspend.conf" ]; then
    echo "  ✓ 配置文件存在: $TRIM_PKGETC/nas-suspend.conf"
    echo "  内容:"
    cat "$TRIM_PKGETC/nas-suspend.conf" | head -20
else
    echo "  ✗ 配置文件不存在"
fi

echo ""

# 4. 检查服务状态
echo "4. 检查服务状态..."
if [ -f "$TRIM_PKGVAR/nas-sleep-manager.pid" ]; then
    PID=$(cat "$TRIM_PKGVAR/nas-sleep-manager.pid" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "  ✓ 服务正在运行 (PID: $PID)"
    else
        echo "  ✗ 服务未运行"
    fi
else
    echo "  ℹ 服务未启动"
fi

echo ""

# 5. 测试CGI
echo "5. 测试CGI访问..."
if [ -f "$TRIM_APPDEST/app/cgi/main.cgi" ]; then
    echo "  CGI文件路径: $TRIM_APPDEST/app/cgi/main.cgi"
    echo "  文件大小: $(wc -c < "$TRIM_APPDEST/app/cgi/main.cgi" 2>/dev/null) 字节"
    echo "  第一行: $(head -1 "$TRIM_APPDEST/app/cgi/main.cgi" 2>/dev/null)"
fi

echo ""
echo "========================================"
echo "诊断完成"
echo "========================================"
