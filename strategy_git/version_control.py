"""
Strategy Version Control - 策略Git版本控制
"""
import os, hashlib, json
from datetime import datetime
from typing import Optional, List, Dict

class StrategyCommit:
    """策略提交"""
    def __init__(self, commit_id, strategy_name, version, code, message, author):
        self.commit_id = commit_id
        self.strategy_name = strategy_name
        self.version = version
        self.code = code
        self.message = message
        self.author = author
        self.timestamp = datetime.now().isoformat()
        self.code_hash = hashlib.sha256(code.encode()).hexdigest()
        self.parent_id = None
        self.branch = 'main'

class StrategyRepository:
    """策略仓库"""
    def __init__(self, repo_path='/tmp/strategy_repos'):
        self.repo_path = repo_path
        self.commits = {}  # {commit_id: StrategyCommit}
        self.branches = {'main': []}  # {branch: [commit_ids]}
        self.strategy_versions = {}  # {strategy_name: {version: commit_id}}
        self.current_branch = 'main'
        os.makedirs(repo_path, exist_ok=True)
    
    def init_repo(self, strategy_name):
        """初始化仓库"""
        strategy_dir = f"{self.repo_path}/{strategy_name}"
        os.makedirs(strategy_dir, exist_ok=True)
        
        # 初始化Git-like结构
        meta_file = f"{strategy_dir}/meta.json"
        if not os.path.exists(meta_file):
            with open(meta_file, 'w') as f:
                json.dump({
                    'name': strategy_name,
                    'created': datetime.now().isoformat(),
                    'branches': ['main']
                }, f)
    
    def commit(self, strategy_name, code, message, author, version=None):
        """提交策略"""
        # 生成commit ID
        commit_id = hashlib.sha256(f"{strategy_name}{code}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # 确定版本号
        if version is None:
            versions = self.strategy_versions.get(strategy_name, {})
            version = f"v{len(versions) + 1}.0"
        
        commit = StrategyCommit(
            commit_id=commit_id,
            strategy_name=strategy_name,
            version=version,
            code=code,
            message=message,
            author=author
        )
        
        # 设置父提交
        branch_commits = self.branches[self.current_branch]
        if branch_commits:
            commit.parent_id = branch_commits[-1]
        
        # 保存
        self.commits[commit_id] = commit
        
        # 更新分支
        self.branches[self.current_branch].append(commit_id)
        
        # 更新版本映射
        if strategy_name not in self.strategy_versions:
            self.strategy_versions[strategy_name] = {}
        self.strategy_versions[strategy_name][version] = commit_id
        
        # 保存代码文件
        strategy_dir = f"{self.repo_path}/{strategy_name}"
        code_file = f"{strategy_dir}/{commit_id}.py"
        with open(code_file, 'w') as f:
            f.write(code)
        
        print(f"[Git] {strategy_name} {version} committed: {commit_id}")
        return commit_id
    
    def checkout(self, strategy_name, version):
        """检出版本"""
        commit_id = self.strategy_versions.get(strategy_name, {}).get(version)
        if not commit_id:
            return None
        
        commit = self.commits.get(commit_id)
        return commit
    
    def get_history(self, strategy_name, limit=10):
        """获取提交历史"""
        history = []
        for commit_id in reversed(self.branches[self.current_branch]):
            commit = self.commits.get(commit_id)
            if commit and commit.strategy_name == strategy_name:
                history.append({
                    'commit_id': commit.commit_id,
                    'version': commit.version,
                    'message': commit.message,
                    'author': commit.author,
                    'timestamp': commit.timestamp,
                    'code_hash': commit.code_hash[:8]
                })
            if len(history) >= limit:
                break
        
        return history
    
    def get_diff(self, commit_id1, commit_id2):
        """比较差异"""
        c1 = self.commits.get(commit_id1)
        c2 = self.commits.get(commit_id2)
        
        if not c1 or not c2:
            return None
        
        # 简化: 简单比较
        lines1 = c1.code.split('\n')
        lines2 = c2.code.split('\n')
        
        added = len([l for l in lines2 if l not in lines1])
        removed = len([l for l in lines1 if l not in lines2])
        
        return {
            'from': commit_id1,
            'to': commit_id2,
            'added': added,
            'removed': removed
        }
    
    def create_branch(self, branch_name):
        """创建分支"""
        if branch_name not in self.branches:
            self.branches[branch_name] = list(self.branches[self.current_branch])
            print(f"[Git] Created branch: {branch_name}")
    
    def merge_branch(self, source_branch, target_branch='main'):
        """合并分支"""
        if source_branch not in self.branches:
            return False
        
        self.branches[target_branch].extend(self.branches[source_branch])
        print(f"[Git] Merged {source_branch} into {target_branch}")
        return True
    
    def tag_version(self, strategy_name, version, commit_id):
        """标记版本"""
        if strategy_name not in self.strategy_versions:
            self.strategy_versions[strategy_name] = {}
        self.strategy_versions[strategy_name][version] = commit_id
        print(f"[Git] Tagged {strategy_name} {version}")
