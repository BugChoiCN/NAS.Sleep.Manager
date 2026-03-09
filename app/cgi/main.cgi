#!/bin/bash
# NAS智能休眠管理CGI后端
# 保存到: NAS.Sleep.Manager/app/cgi/main.cgi

APP_DIR="$TRIM_APPDEST"
CONFIG_FILE="$TRIM_PKGETC/nas-suspend.conf"
LOG_FILE="$TRIM_PKGVAR/nas-suspend.log"
PID_FILE="$TRIM_PKGVAR/nas-sleep-manager.pid"

# 设置响应头
echo "Content-Type: application/json"
echo ""

# 解析请求
REQUEST_METHOD="$REQUEST_METHOD"
REQUEST_URI="$REQUEST_URI"
QUERY_STRING="$QUERY_STRING"

# 读取POST数据
if [ "$REQUEST_METHOD" = "POST" ]; then
    read -r -d '' POST_DATA <&0
fi

# 路由处理
case "$REQUEST_URI" in
    /|/main.cgi)
        # 返回主页面
        if [ -f "$TRIM_APPDEST/app/ui/index.html" ]; then
            cat "$TRIM_APPDEST/app/ui/index.html"
        else
            echo '{"error": "index.html not found"}'
        fi
        ;;

    /api/status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE" 2>/dev/null)
            if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
                # 获取连接数（统一使用netstat）
                if command -v ss >/dev/null 2>&1; then
                    CONNECTIONS=$(ss -tn state established 2>/dev/null | awk '!/127\.0\.0\.1|::1/ && NR>1' | wc -l 2>/dev/null || echo 0)
                elif command -v netstat >/dev/null 2>&1; then
                    CONNECTIONS=$(netstat -tn 2>/dev/null | grep 'ESTABLISHED' | grep -v '127.0.0.1' | grep -v '::1' | wc -l 2>/dev/null || echo 0)
                else
                    CONNECTIONS=0
                fi
                cat << EOF
{
    "running": true,
    "pid": $PID,
    "connections": $CONNECTIONS,
    "lastCheckTime": "$(date '+%Y-%m-%d %H:%M:%S')",
    "systemStatus": "运行中"
}
EOF
            else
                echo '{"running": false}'
            fi
        else
            echo '{"running": false}'
        fi
        ;;
        
    /api/settings)
        if [ "$REQUEST_METHOD" = "GET" ]; then
            # 读取当前设置
            if [ -f "$CONFIG_FILE" ]; then
                source "$CONFIG_FILE" 2>/dev/null
                cat << EOF
{
    "enabled": true,
    "inactivityTimeout": ${INACTIVITY_TIMEOUT:-1800},
    "checkInterval": ${CHECK_INTERVAL:-60},
    "maxConnections": ${MAX_ALLOWED_CONNECTIONS:-3},
    "networkThreshold": ${MIN_NETWORK_CHANGE:-1048576},
    "wakeOnLAN": true,
    "verboseLogging": true
}
EOF
            else
                # 默认设置
                cat << EOF
{
    "enabled": true,
    "inactivityTimeout": 1800,
    "checkInterval": 60,
    "maxConnections": 3,
    "networkThreshold": 1048576,
    "wakeOnLAN": true,
    "verboseLogging": true
}
EOF
            fi
        elif [ "$REQUEST_METHOD" = "POST" ]; then
            # 保存设置（不依赖jq，使用纯bash解析）
            if command -v jq >/dev/null 2>&1; then
                echo "$POST_DATA" | jq -r '
                    "INACTIVITY_TIMEOUT=" + (.inactivityTimeout|tostring) + "\n" +
                    "CHECK_INTERVAL=" + (.checkInterval|tostring) + "\n" +
                    "MAX_ALLOWED_CONNECTIONS=" + (.maxConnections|tostring) + "\n" +
                    "MIN_NETWORK_CHANGE=" + (.networkThreshold|tostring) + "\n" +
                    "VERBOSE_LOG=" + (if .verboseLogging then "true" else "false" end) + "\n" +
                    "# 自动生成配置文件\n" +
                    "# 更新时间: " + (now|strftime("%Y-%m-%d %H:%M:%S"))
                ' > "$CONFIG_FILE"
            else
                # 不依赖jq的备用方案
                echo "# ============================================
# NAS自动休眠配置文件
# 更新时间: $(date '+%Y-%m-%d %H:%M:%S')
# ============================================" > "$CONFIG_FILE"
                echo "$POST_DATA" | grep -oP '"inactivityTimeout":\s*\K[0-9]+' | sed 's/^/INACTIVITY_TIMEOUT=/' >> "$CONFIG_FILE"
                echo "$POST_DATA" | grep -oP '"checkInterval":\s*\K[0-9]+' | sed 's/^/CHECK_INTERVAL=/' >> "$CONFIG_FILE"
                echo "$POST_DATA" | grep -oP '"maxConnections":\s*\K[0-9]+' | sed 's/^/MAX_ALLOWED_CONNECTIONS=/' >> "$CONFIG_FILE"
                echo "$POST_DATA" | grep -oP '"networkThreshold":\s*\K[0-9.]+' | sed 's/^/MIN_NETWORK_CHANGE=/' >> "$CONFIG_FILE"
                echo "$POST_DATA" | grep -oP '"verboseLogging":\s*\K(true|false)' | sed 's/^/VERBOSE_LOG=/' >> "$CONFIG_FILE"
            fi
            echo '{"success": true, "message": "设置已保存"}'
        fi
        ;;
        
    /api/restart)
        # 重启服务
        $APP_DIR/cmd/main restart
        echo '{"success": true, "message": "服务已重启"}'
        ;;
        
    /api/logs)
        # 读取日志
        if [ -f "$LOG_FILE" ]; then
            tail -100 "$LOG_FILE"
        else
            echo "暂无日志"
        fi
        ;;
        
    /api/permission-check)
        # 权限检查
        if [ "$EUID" -eq 0 ]; then
            echo '{"permissionLevel": "root"}'
        else
            echo '{"permissionLevel": "limited"}'
        fi
        ;;

    /api/health-check)
        # 健康检查
        local health_status="unknown"
        local last_check_time="从未"
        local uptime_seconds=0

        if [ -f "$PID_FILE" ]; then
            local pid=$(cat "$PID_FILE" 2>/dev/null)
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                # 计算进程运行时间
                local start_time=$(ps -o lstart= -p "$pid" 2>/dev/null | head -1)
                if [ -n "$start_time" ]; then
                    uptime_seconds=$(( ($(date +%s) - $(date -d "$start_time" +%s 2>/dev/null || echo 0)) ))
                    local uptime_hours=$((uptime_seconds / 3600))
                    local uptime_minutes=$(((uptime_seconds % 3600) / 60))

                    if [ $uptime_hours -gt 0 ]; then
                        uptime_str="${uptime_hours}小时${uptime_minutes}分钟"
                    elif [ $uptime_minutes -gt 0 ]; then
                        uptime_str="${uptime_minutes}分钟"
                    else
                        uptime_str="${uptime_seconds}秒"
                    fi
                fi

                # 检查日志文件
                if [ -f "$LOG_FILE" ]; then
                    last_check_time=$(tail -1 "$LOG_FILE" 2>/dev/null | grep -oP '\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}' || echo "未知")

                    # 检查最近5分钟是否有活动
                    local recent_logs=$(tail -20 "$LOG_FILE" 2>/dev/null | grep -c "$(date -d '5 minutes ago' '+%Y-%m-%d %H:%M')" 2>/dev/null || echo 0)
                    if [ "$recent_logs" -gt 0 ]; then
                        health_status="running"
                    else
                        health_status="idle"
                    fi
                else
                    health_status="running"
                fi
            else
                health_status="stopped"
                last_check_time="进程未运行"
            fi
        else
            health_status="not_installed"
            last_check_time="未启动"
        fi

        cat << EOF
{
    "status": "$health_status",
    "pid": "${pid:-0}",
    "uptime": "${uptime_str:-0秒}",
    "uptimeSeconds": ${uptime_seconds:-0},
    "lastCheckTime": "$last_check_time",
    "configFile": "$([ -f "$CONFIG_FILE" ] && echo "exists" || echo "missing")",
    "logFile": "$([ -f "$LOG_FILE" ] && echo "exists" || echo "missing")"
}
EOF
        ;;

    /api/test-suspend)
        # 测试休眠功能(不实际休眠)
        echo '{"success": true, "message": "休眠测试功能已准备，实际休眠将在空闲超时后自动触发"}'
        ;;

    *)
        echo '{"error": "API not found", "path": "'"$REQUEST_URI"'"}'
        ;;
esac

exit 0