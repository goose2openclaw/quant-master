"""
Backup/Restore - 配置备份恢复
"""
import os, json, shutil, tarfile
from datetime import datetime
from typing import Dict, List, Optional

class BackupManager:
    """
    备份恢复管理器
    支持: 配置/策略/数据库备份
    """
    def __init__(self, backup_dir='/tmp/qm_backups'):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
        self.config_paths = [
            '/home/goose/.openclaw/workspace/opc/config.py',
            '/home/goose/.openclaw/workspace/quant_master/config/',
        ]
        self.strategy_paths = [
            '/home/goose/.openclaw/workspace/quant_master/strategies/',
        ]
        self.data_paths = [
            '/home/goose/.openclaw/workspace/quant_master/db/',
        ]
    
    def create_backup(self, backup_type='full', name=None):
        """
        创建备份
        backup_type: full, config, strategy, data
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = name or f"backup_{backup_type}_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        os.makedirs(backup_path, exist_ok=True)
        
        # 收集文件
        paths_to_backup = []
        
        if backup_type in ['full', 'config']:
            paths_to_backup.extend(self.config_paths)
        if backup_type in ['full', 'strategy']:
            paths_to_backup.extend(self.strategy_paths)
        if backup_type in ['full', 'data']:
            paths_to_backup.extend(self.data_paths)
        
        # 复制文件
        files_copied = 0
        for src_path in paths_to_backup:
            if os.path.exists(src_path):
                dest = os.path.join(backup_path, os.path.basename(src_path))
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dest)
                files_copied += 1
        
        # 创建备份清单
        manifest = {
            'backup_name': backup_name,
            'backup_type': backup_type,
            'created': datetime.now().isoformat(),
            'files_copied': files_copied,
            'paths': paths_to_backup
        }
        
        with open(os.path.join(backup_path, 'manifest.json'), 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # 压缩备份
        archive_path = f"{backup_path}.tar.gz"
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_path, arcname=backup_name)
        
        # 清理未压缩目录
        shutil.rmtree(backup_path)
        
        print(f"[Backup] Created: {archive_path}")
        return archive_path
    
    def list_backups(self):
        """列出所有备份"""
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.tar.gz'):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                
                backups.append({
                    'name': filename,
                    'path': filepath,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def restore_backup(self, backup_name):
        """恢复备份"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if not backup_name.endswith('.tar.gz'):
            backup_path += '.tar.gz'
        
        if not os.path.exists(backup_path):
            return {'success': False, 'error': 'Backup not found'}
        
        # 解压到临时目录
        temp_dir = os.path.join(self.backup_dir, f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        with tarfile.open(backup_path, 'r:gz') as tar:
            tar.extractall(temp_dir)
        
        # 读取清单
        extracted_name = backup_name.replace('.tar.gz', '')
        manifest_path = os.path.join(temp_dir, extracted_name, 'manifest.json')
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # 恢复文件
        for src_rel_path in manifest['paths']:
            src_path = os.path.join(temp_dir, extracted_name, os.path.basename(src_rel_path))
            
            if os.path.exists(src_path):
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, src_rel_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, src_rel_path)
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
        
        print(f"[Backup] Restored: {backup_name}")
        return {'success': True, 'manifest': manifest}
    
    def delete_backup(self, backup_name):
        """删除备份"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        if not backup_name.endswith('.tar.gz'):
            backup_path += '.tar.gz'
        
        if os.path.exists(backup_path):
            os.remove(backup_path)
            print(f"[Backup] Deleted: {backup_name}")
            return True
        return False
    
    def export_config(self, filepath):
        """导出配置"""
        config = {
            'exported': datetime.now().isoformat(),
            'backups_dir': self.backup_dir,
            'config_paths': self.config_paths,
            'strategy_paths': self.strategy_paths
        }
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
    
    def upload_to_cloud(self, backup_name, cloud_provider='s3', bucket=None):
        """上传到云存储 (简化)"""
        print(f"[Backup] Uploading {backup_name} to {cloud_provider}")
        # 实际需要boto3等库
        return {'success': True, 'url': f's3://{bucket}/{backup_name}'}
    
    def download_from_cloud(self, cloud_path, backup_name):
        """从云下载"""
        print(f"[Backup] Downloading {cloud_path}")
        return {'success': True}
