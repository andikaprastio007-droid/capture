#!/data/data/com.termux/files/usr/bin/bash
# Multi Tunnel Manager
# Usage:
#   ./multi_tunnel.sh start <name> <provider> [port]
#   ./multi_tunnel.sh stop <name>
#   ./multi_tunnel.sh list
#   ./multi_tunnel.sh url <name>
#   ./multi_tunnel.sh status

TUNNEL_DIR="$HOME/capture-pro/tunnels"
mkdir -p "$TUNNEL_DIR"

start_tunnel() {
    local name="$1"
    local provider="$2"
    local port="${3:-8000}"
    
    if [ -z "$name" ] || [ -z "$provider" ]; then
        echo "Usage: $0 start <name> <provider> [port]"
        return 1
    fi
    
    local pid_file="$TUNNEL_DIR/$name.pid"
    local log_file="$TUNNEL_DIR/$name.log"
    local url_file="$TUNNEL_DIR/$name.url"
    
    # Cek sudah jalan
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "⚠️  Tunnel '$name' sudah jalan (PID: $old_pid)"
            [ -f "$url_file" ] && echo "   URL: $(cat $url_file)"
            return 1
        fi
        rm -f "$pid_file"
    fi
    
    echo "🚀 Starting tunnel '$name' with provider '$provider' on port $port..."
    
    case "$provider" in
        cloudflare)
            if ! command -v cloudflared >/dev/null 2>&1; then
                echo "❌ cloudflared tidak ada. Install: pkg install cloudflared"
                return 1
            fi
            nohup cloudflared tunnel --url "http://localhost:$port" > "$log_file" 2>&1 &
            echo $! > "$pid_file"
            ;;
        
        localhost.run|localhostrun|lhr)
            if ! command -v ssh >/dev/null 2>&1; then
                echo "❌ ssh tidak ada. Install: pkg install openssh"
                return 1
            fi
            nohup ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
                -R 80:localhost:$port nokey@localhost.run > "$log_file" 2>&1 &
            echo $! > "$pid_file"
            ;;
        
        serveo)
            if ! command -v ssh >/dev/null 2>&1; then
                echo "❌ ssh tidak ada. Install: pkg install openssh"
                return 1
            fi
            nohup ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
                -R 80:localhost:$port serveo.net > "$log_file" 2>&1 &
            echo $! > "$pid_file"
            ;;
        
        *)
            echo "❌ Provider tidak dikenal: $provider"
            echo "   Pilih: cloudflare | localhost.run | serveo"
            return 1
            ;;
    esac
    
    echo "   Tunggu URL muncul (max 20 detik)..."
    
    local url=""
    for i in $(seq 1 20); do
        sleep 1
        case "$provider" in
            cloudflare)
                url=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$log_file" 2>/dev/null | head -1)
                ;;
            localhost.run|localhostrun|lhr)
                url=$(grep -o 'https://[a-z0-9]*\.lhr\.life' "$log_file" 2>/dev/null | head -1)
                ;;
            serveo)
                url=$(grep -o 'https://[a-z0-9-]*\.serveo\.net' "$log_file" 2>/dev/null | head -1)
                ;;
        esac
        [ -n "$url" ] && break
    done
    
    if [ -n "$url" ]; then
        echo "$url" > "$url_file"
        echo "✅ Tunnel '$name' started"
        echo "   URL: $url"
    else
        echo "⚠️  Tunnel jalan tapi URL belum muncul — cek log"
        echo "   Log: $log_file"
    fi
}

stop_tunnel() {
    local name="$1"
    if [ -z "$name" ]; then
        echo "Usage: $0 stop <name>"
        return 1
    fi
    
    local pid_file="$TUNNEL_DIR/$name.pid"
    if [ ! -f "$pid_file" ]; then
        echo "⚠️  Tunnel '$name' tidak jalan"
        return 1
    fi
    
    local pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null
        sleep 2
        kill -9 "$pid" 2>/dev/null
    fi
    
    rm -f "$pid_file" "$TUNNEL_DIR/$name.url"
    echo "✅ Tunnel '$name' stopped"
}

list_tunnels() {
    echo "🌐 Active tunnels:"
    echo ""
    
    local count=0
    for pid_file in "$TUNNEL_DIR"/*.pid; do
        [ -f "$pid_file" ] || continue
        local name=$(basename "$pid_file" .pid)
        local pid=$(cat "$pid_file")
        local url_file="$TUNNEL_DIR/$name.url"
        local url=""
        [ -f "$url_file" ] && url=$(cat "$url_file")
        
        if kill -0 "$pid" 2>/dev/null; then
            echo "  ✅ $name (PID: $pid)"
            [ -n "$url" ] && echo "     🔗 $url"
        else
            echo "  ❌ $name (dead)"
        fi
        count=$((count + 1))
    done
    
    if [ $count -eq 0 ]; then
        echo "  (tidak ada tunnel aktif)"
    fi
}

show_url() {
    local name="$1"
    if [ -z "$name" ]; then
        echo "Usage: $0 url <name>"
        return 1
    fi
    
    local url_file="$TUNNEL_DIR/$name.url"
    if [ -f "$url_file" ]; then
        cat "$url_file"
    else
        echo "❌ Tunnel '$name' tidak ada"
        return 1
    fi
}

show_status() {
    echo "=== Tunnel Status ==="
    echo ""
    list_tunnels
    echo ""
    echo "=== Directory ==="
    ls -la "$TUNNEL_DIR" 2>/dev/null | head -20
}

case "$1" in
    start) start_tunnel "$2" "$3" "$4" ;;
    stop) stop_tunnel "$2" ;;
    list|ls) list_tunnels ;;
    url) show_url "$2" ;;
    status) show_status ;;
    *)
        echo "Multi Tunnel Manager"
        echo ""
        echo "Usage:"
        echo "  $0 start <name> <provider> [port]"
        echo "  $0 stop <name>"
        echo "  $0 list"
        echo "  $0 url <name>"
        echo ""
        echo "Provider: cloudflare | localhost.run | serveo"
        ;;
esac
