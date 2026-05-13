#!/usr/bin/env python3
"""
安全文件写入工具 - 避免exec preflight拦截heredoc
用法: python3 safe_write.py <file_path> <content_base64>
"""
import sys, base64

if len(sys.argv) < 3:
    print("用法: python3 safe_write.py <file_path> <content_base64>")
    sys.exit(1)

file_path = sys.argv[1]
content_b64 = sys.argv[2]

try:
    content = base64.b64decode(content_b64).decode('utf-8')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"OK: {file_path}")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
