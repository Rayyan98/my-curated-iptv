#!/bin/bash
# Mock download script for testing download functionality

echo "🧪 Mock downloading Pakistani channels..."
cat > main/pk.m3u << 'EOF'
#EXTM3U
#EXTINF:-1 tvg-id="MockPK1" tvg-logo="test1.png" group-title="Test",Mock Pakistani 1
https://httpbin.org/status/200
#EXTINF:-1 tvg-id="MockPK2" tvg-logo="test2.png" group-title="Test",Mock Pakistani 2
https://httpbin.org/delay/1
#EXTINF:-1 tvg-id="MockPK3" tvg-logo="test3.png" group-title="Test",Mock Pakistani 3 (Fail)
https://httpbin.org/status/404
EOF

echo "🧪 Mock downloading Indian channels..."
cat > main/in.m3u << 'EOF'
#EXTM3U
#EXTINF:-1 tvg-id="MockIN1" tvg-logo="test4.png" group-title="Test",Mock Indian 1
https://httpbin.org/status/200
#EXTINF:-1 tvg-id="MockIN2" tvg-logo="test5.png" group-title="Test",Mock Indian 2
https://httpbin.org/status/301
#EXTINF:-1 tvg-id="MockIN3" tvg-logo="test6.png" group-title="Test",Mock Indian 3 (Timeout)
https://httpbin.org/delay/10
EOF

echo "🧪 Mock downloading global channels..."
cat > extended/global.m3u << 'EOF'
#EXTM3U
#EXTINF:-1 tvg-id="MockPK1" tvg-logo="dup1.png" group-title="Test",Duplicate Pakistani 1
https://httpbin.org/status/200
#EXTINF:-1 tvg-id="MockGlobal1" tvg-logo="global1.png" group-title="Test",Mock Global 1
https://httpbin.org/status/200
#EXTINF:-1 tvg-id="MockIN2" tvg-logo="dup2.png" group-title="Test",Duplicate Indian 2
https://httpbin.org/status/200
#EXTINF:-1 tvg-id="MockGlobal2" tvg-logo="global2.png" group-title="Test",Mock Global 2
https://httpbin.org/status/500
#EXTINF:-1 tvg-id="MockGlobal3" tvg-logo="global3.png" group-title="Test",Mock Global 3
https://httpbin.org/status/200
EOF

echo "✅ Mock downloads complete!"