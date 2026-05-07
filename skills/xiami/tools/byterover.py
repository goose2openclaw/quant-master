#!/usr/bin/env python3
"""
XIAMI ByteRover Alternative - 知识管理系统
AI Agent 知识管理工具
"""

import json
import os
from datetime import datetime
from pathlib import Path

class KnowledgeBase:
    """知识库管理"""
    
    def __init__(self, base_dir="~/.xiami-kb"):
        self.base_dir = os.path.expanduser(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        
        self.index_file = os.path.join(self.base_dir, "index.json")
        self.load_index()
    
    def load_index(self):
        """加载索引"""
        if os.path.exists(self.index_file):
            with open(self.index_file) as f:
                self.index = json.load(f)
        else:
            self.index = {'entries': [], 'tags': {}}
    
    def save_index(self):
        """保存索引"""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def add(self, key, value, tags=None):
        """添加知识条目"""
        entry = {
            'key': key,
            'value': value,
            'tags': tags or [],
            'created': datetime.now().isoformat(),
            'updated': datetime.now().isoformat()
        }
        
        self.index['entries'].append(entry)
        
        # 更新标签索引
        for tag in entry['tags']:
            if tag not in self.index['tags']:
                self.index['tags'][tag] = []
            self.index['tags'][tag].append(key)
        
        self.save_index()
        
        return {'status': 'added', 'key': key}
    
    def get(self, key):
        """获取知识条目"""
        for entry in self.index['entries']:
            if entry['key'] == key:
                return entry
        return None
    
    def search(self, query):
        """搜索知识"""
        results = []
        query = query.lower()
        
        for entry in self.index['entries']:
            if query in entry['key'].lower() or query in str(entry['value']).lower():
                results.append(entry)
        
        return results
    
    def list_by_tag(self, tag):
        """按标签列出"""
        keys = self.index['tags'].get(tag, [])
        return [self.get(k) for k in keys if self.get(k)]
    
    def delete(self, key):
        """删除条目"""
        self.index['entries'] = [e for e in self.index['entries'] if e['key'] != key]
        
        # 清理标签
        for tag in self.index['tags']:
            self.index['tags'][tag] = [k for k in self.index['tags'][tag] if k != key]
        
        self.save_index()
        return {'status': 'deleted', 'key': key}


def main():
    import sys
    
    kb = KnowledgeBase()
    
    if len(sys.argv) < 2:
        print("""
🧠 XIAMI Knowledge Base (ByteRover Alternative)

用法:
  python byterover.py add <key> <value> [tags...]
  python byterover.py get <key>
  python byterover.py search <query>
  python byterover.py tag <tag>
  python byterover.py list
  python byterover.py delete <key>

示例:
  python byterover.py add "BTC策略" "逢低买入" trading
  python byterover.py search "买入"
  python byterover.py tag trading
""")
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'add':
        if len(sys.argv) < 4:
            print("用法: python byterover.py add <key> <value> [tags...]")
            return
        key = sys.argv[2]
        value = sys.argv[3]
        tags = sys.argv[4:] if len(sys.argv) > 4 else []
        result = kb.add(key, value, tags)
        print(f"✅ 已添加: {key}")
        
    elif cmd == 'get':
        key = sys.argv[2]
        entry = kb.get(key)
        if entry:
            print(f"\n🔍 {entry['key']}")
            print(f"   内容: {entry['value']}")
            print(f"   标签: {', '.join(entry['tags'])}")
            print(f"   创建: {entry['created']}")
        else:
            print(f"未找到: {key}")
    
    elif cmd == 'search':
        query = sys.argv[2]
        results = kb.search(query)
        print(f"\n🔍 搜索 '{query}' ({len(results)} 结果)")
        for r in results:
            print(f"  - {r['key']}: {r['value'][:50]}...")
    
    elif cmd == 'tag':
        tag = sys.argv[2]
        results = kb.list_by_tag(tag)
        print(f"\n🏷️ 标签 '{tag}' ({len(results)} 条)")
        for r in results:
            print(f"  - {r['key']}")
    
    elif cmd == 'list':
        print(f"\n📚 知识库 ({len(kb.index['entries'])} 条)")
        for e in kb.index['entries']:
            print(f"  - {e['key']}")
    
    elif cmd == 'delete':
        key = sys.argv[2]
        result = kb.delete(key)
        print(f"✅ 已删除: {key}")


if __name__ == '__main__':
    main()
