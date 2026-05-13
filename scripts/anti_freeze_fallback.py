#!/usr/bin/env python3
"""
紧急防僵死脚本 - 当heredoc和直接python都失败时的备用方案
使用base64编码方式安全写入文件
"""
import base64, os, sys

WORKSPACE = '/home/goose/.openclaw/workspace'

def b64_write(path, content):
    """使用base64安全写入文件"""
    encoded = base64.b64encode(content.encode()).decode()
    script = f'''python3 -c "
import base64
content = base64.b64decode('{encoded}').decode()
with open('{path}', 'w') as f:
    f.write(content)
print('OK')
"'''
    os.system(script)

# 示例：写入一个简单的测试文件
test_content = '''#!/usr/bin/env python3
print("Hello from anti-freeze!")
'''

test_path = f'{WORKSPACE}/scripts/test_anti_freeze.py'
b64_write(test_path, test_content)
print(f"测试文件已写入: {test_path}")
