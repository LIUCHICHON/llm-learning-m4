#!/bin/bash
# 一键重建「AI对话台.app」，让 Finder 里能双击打开。
# 用法：bash AI起步/重建对话台app.sh
#
# 背景：项目按 .gitignore 约定不入库 .app（见 README）。
# 从 GitHub 克隆，或遇到 Finder 里 .app 是空壳、双击没反应时，跑这个脚本即可。
# 真正的启动逻辑在 启动对话台.sh，这里只做一层「双击壳」。
set -eu

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$DIR/AI对话台.app"

echo "重建：$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>AI对话台</string>
    <key>CFBundleDisplayName</key><string>AI对话台</string>
    <key>CFBundleIdentifier</key><string>com.aiqibu.chat</string>
    <key>CFBundleExecutable</key><string>启动</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>1.0</string>
</dict>
</plist>
EOF

cat > "$APP/Contents/MacOS/启动" <<'EOF'
#!/bin/bash
# 双击壳：把活交给源码启动器（Tk 版本选择等逻辑都在那里，只此一份）
set -u
DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
exec "$DIR/启动对话台.sh" "$@"
EOF
chmod +x "$APP/Contents/MacOS/启动"

echo "校验 Info.plist："
plutil -lint "$APP/Contents/Info.plist"
echo "✅ 完成。现在可以在 Finder 里双击 AI对话台.app 了。"
echo "   等价命令：bash AI起步/启动对话台.sh"
