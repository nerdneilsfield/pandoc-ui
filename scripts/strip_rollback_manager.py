#!/usr/bin/env python3
"""
strip_rollback_manager.py - Strip操作回滚管理器

提供Strip操作的备份、回滚和版本管理功能，确保安全的Strip部署。
"""

import json
import os
import shutil
import sys
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class StripOperation:
    """Strip操作记录"""
    id: str
    timestamp: str
    binary_path: str
    backup_path: str
    strip_method: str
    original_size: int
    stripped_size: int
    original_checksum: str
    stripped_checksum: str
    success: bool
    functionality_verified: bool
    error_message: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class BackupMetadata:
    """备份文件元数据"""
    backup_id: str
    created_at: str
    original_path: str
    backup_path: str
    file_size: int
    checksum: str
    strip_operation_id: Optional[str] = None


class StripRollbackManager:
    """Strip操作回滚管理器"""
    
    def __init__(self, work_dir: str = ".strip_rollback"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        
        # 数据文件
        self.operations_file = self.work_dir / "operations.json"
        self.backups_file = self.work_dir / "backups.json"
        
        # 备份目录
        self.backup_dir = self.work_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 加载历史数据
        self.operations: List[StripOperation] = self._load_operations()
        self.backups: List[BackupMetadata] = self._load_backups()
        
        print(f"🗂️  Strip回滚管理器初始化")
        print(f"   工作目录: {self.work_dir}")
        print(f"   备份目录: {self.backup_dir}")
        print(f"   历史操作: {len(self.operations)} 条")
        print(f"   备份文件: {len(self.backups)} 个")
    
    def _load_operations(self) -> List[StripOperation]:
        """加载操作历史"""
        if self.operations_file.exists():
            try:
                with open(self.operations_file, 'r') as f:
                    data = json.load(f)
                return [StripOperation(**op) for op in data]
            except (json.JSONDecodeError, TypeError) as e:
                print(f"⚠️  加载操作历史失败: {e}")
                return []
        return []
    
    def _load_backups(self) -> List[BackupMetadata]:
        """加载备份元数据"""
        if self.backups_file.exists():
            try:
                with open(self.backups_file, 'r') as f:
                    data = json.load(f)
                return [BackupMetadata(**backup) for backup in data]
            except (json.JSONDecodeError, TypeError) as e:
                print(f"⚠️  加载备份元数据失败: {e}")
                return []
        return []
    
    def _save_operations(self):
        """保存操作历史"""
        with open(self.operations_file, 'w') as f:
            json.dump([asdict(op) for op in self.operations], f, indent=2)
    
    def _save_backups(self):
        """保存备份元数据"""
        with open(self.backups_file, 'w') as f:
            json.dump([asdict(backup) for backup in self.backups], f, indent=2)
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """计算文件SHA256校验和"""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def _generate_operation_id(self) -> str:
        """生成操作ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"strip_{timestamp}_{len(self.operations):03d}"
    
    def _generate_backup_id(self) -> str:
        """生成备份ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}_{len(self.backups):03d}"
    
    def create_backup(self, binary_path: Path, operation_id: Optional[str] = None) -> str:
        """创建备份文件"""
        print(f"💾 创建备份: {binary_path}")
        
        if not binary_path.exists():
            raise FileNotFoundError(f"文件不存在: {binary_path}")
        
        # 生成备份ID和路径
        backup_id = self._generate_backup_id()
        backup_filename = f"{backup_id}_{binary_path.name}"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # 复制文件
            shutil.copy2(binary_path, backup_path)
            
            # 创建备份元数据
            backup_metadata = BackupMetadata(
                backup_id=backup_id,
                created_at=datetime.now().isoformat(),
                original_path=str(binary_path),
                backup_path=str(backup_path),
                file_size=binary_path.stat().st_size,
                checksum=self._calculate_checksum(binary_path),
                strip_operation_id=operation_id
            )
            
            self.backups.append(backup_metadata)
            self._save_backups()
            
            print(f"✅ 备份创建成功: {backup_path}")
            print(f"   备份ID: {backup_id}")
            print(f"   文件大小: {backup_metadata.file_size:,} bytes")
            
            return backup_id
            
        except Exception as e:
            print(f"❌ 备份创建失败: {e}")
            raise
    
    def prepare_strip_operation(self, binary_path: Path, strip_method: str, 
                              create_backup: bool = True) -> str:
        """准备Strip操作"""
        print(f"🚀 准备Strip操作: {binary_path}")
        print(f"   Strip方法: {strip_method}")
        print(f"   自动备份: {create_backup}")
        
        if not binary_path.exists():
            raise FileNotFoundError(f"文件不存在: {binary_path}")
        
        # 生成操作ID
        operation_id = self._generate_operation_id()
        
        # 创建备份
        backup_id = None
        backup_path = ""
        if create_backup:
            backup_id = self.create_backup(binary_path, operation_id)
            backup_metadata = self._find_backup_by_id(backup_id)
            backup_path = backup_metadata.backup_path if backup_metadata else ""
        
        # 记录操作信息
        operation = StripOperation(
            id=operation_id,
            timestamp=datetime.now().isoformat(),
            binary_path=str(binary_path),
            backup_path=backup_path,
            strip_method=strip_method,
            original_size=binary_path.stat().st_size,
            stripped_size=0,  # 待更新
            original_checksum=self._calculate_checksum(binary_path),
            stripped_checksum="",  # 待更新
            success=False,  # 待更新
            functionality_verified=False,  # 待更新
        )
        
        self.operations.append(operation)
        self._save_operations()
        
        print(f"✅ Strip操作准备完成")
        print(f"   操作ID: {operation_id}")
        if backup_id:
            print(f"   备份ID: {backup_id}")
        
        return operation_id
    
    def complete_strip_operation(self, operation_id: str, success: bool, 
                                functionality_verified: bool = False,
                                error_message: Optional[str] = None,
                                notes: Optional[str] = None):
        """完成Strip操作记录"""
        operation = self._find_operation_by_id(operation_id)
        if not operation:
            raise ValueError(f"操作不存在: {operation_id}")
        
        binary_path = Path(operation.binary_path)
        
        # 更新操作记录
        operation.success = success
        operation.functionality_verified = functionality_verified
        operation.error_message = error_message
        operation.notes = notes
        
        if binary_path.exists():
            operation.stripped_size = binary_path.stat().st_size
            operation.stripped_checksum = self._calculate_checksum(binary_path)
        
        self._save_operations()
        
        print(f"📋 Strip操作记录更新: {operation_id}")
        print(f"   成功: {success}")
        print(f"   功能验证: {functionality_verified}")
        
        if success:
            size_reduction = operation.original_size - operation.stripped_size
            reduction_percent = (size_reduction / operation.original_size) * 100
            print(f"   大小减少: {size_reduction:,} bytes ({reduction_percent:.1f}%)")
        
        if error_message:
            print(f"   错误信息: {error_message}")
    
    def rollback_operation(self, operation_id: str) -> bool:
        """回滚Strip操作"""
        print(f"🔄 回滚Strip操作: {operation_id}")
        
        operation = self._find_operation_by_id(operation_id)
        if not operation:
            print(f"❌ 操作不存在: {operation_id}")
            return False
        
        if not operation.backup_path:
            print(f"❌ 没有备份文件，无法回滚")
            return False
        
        backup_path = Path(operation.backup_path)
        binary_path = Path(operation.binary_path)
        
        if not backup_path.exists():
            print(f"❌ 备份文件不存在: {backup_path}")
            return False
        
        try:
            # 验证备份完整性
            backup_checksum = self._calculate_checksum(backup_path)
            if backup_checksum != operation.original_checksum:
                print(f"⚠️  备份文件校验和不匹配，继续回滚...")
            
            # 执行回滚
            shutil.copy2(backup_path, binary_path)
            
            # 验证回滚结果
            restored_checksum = self._calculate_checksum(binary_path)
            if restored_checksum == operation.original_checksum:
                print(f"✅ 回滚成功: {binary_path}")
                
                # 更新操作记录（标记为已回滚）
                operation.notes = f"已回滚于 {datetime.now().isoformat()}"
                self._save_operations()
                
                return True
            else:
                print(f"⚠️  回滚完成，但校验和不匹配")
                return True
                
        except Exception as e:
            print(f"❌ 回滚失败: {e}")
            return False
    
    def rollback_latest_operation(self) -> bool:
        """回滚最近的Strip操作"""
        if not self.operations:
            print("❌ 没有操作记录")
            return False
        
        latest_operation = self.operations[-1]
        return self.rollback_operation(latest_operation.id)
    
    def list_operations(self, limit: int = 10, success_only: bool = False) -> List[StripOperation]:
        """列出Strip操作"""
        operations = self.operations
        
        if success_only:
            operations = [op for op in operations if op.success]
        
        # 按时间倒序排列
        operations.sort(key=lambda x: x.timestamp, reverse=True)
        
        return operations[:limit]
    
    def list_backups(self, limit: int = 10) -> List[BackupMetadata]:
        """列出备份文件"""
        backups = sorted(self.backups, key=lambda x: x.created_at, reverse=True)
        return backups[:limit]
    
    def cleanup_old_backups(self, days_to_keep: int = 30, dry_run: bool = False) -> int:
        """清理旧的备份文件"""
        print(f"🧹 清理 {days_to_keep} 天前的备份文件 {'(模拟运行)' if dry_run else ''}")
        
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        cleaned_size = 0
        
        backups_to_remove = []
        
        for backup in self.backups:
            backup_time = datetime.fromisoformat(backup.created_at)
            
            if backup_time < cutoff_time:
                backup_path = Path(backup.backup_path)
                
                if backup_path.exists():
                    file_size = backup_path.stat().st_size
                    
                    if not dry_run:
                        try:
                            backup_path.unlink()
                            cleaned_count += 1
                            cleaned_size += file_size
                            print(f"   删除: {backup.backup_id} ({file_size:,} bytes)")
                        except Exception as e:
                            print(f"   ⚠️  删除失败 {backup.backup_id}: {e}")
                    else:
                        cleaned_count += 1
                        cleaned_size += file_size
                        print(f"   将删除: {backup.backup_id} ({file_size:,} bytes)")
                
                backups_to_remove.append(backup)
        
        # 从元数据中移除
        if not dry_run and backups_to_remove:
            for backup in backups_to_remove:
                self.backups.remove(backup)
            self._save_backups()
        
        print(f"🧹 清理完成:")
        print(f"   处理文件: {cleaned_count}")
        print(f"   释放空间: {cleaned_size:,} bytes ({cleaned_size/1024/1024:.1f} MB)")
        
        return cleaned_count
    
    def verify_backup_integrity(self, backup_id: str) -> bool:
        """验证备份文件完整性"""
        print(f"🔍 验证备份完整性: {backup_id}")
        
        backup = self._find_backup_by_id(backup_id)
        if not backup:
            print(f"❌ 备份不存在: {backup_id}")
            return False
        
        backup_path = Path(backup.backup_path)
        if not backup_path.exists():
            print(f"❌ 备份文件不存在: {backup_path}")
            return False
        
        try:
            current_checksum = self._calculate_checksum(backup_path)
            current_size = backup_path.stat().st_size
            
            checksum_match = current_checksum == backup.checksum
            size_match = current_size == backup.file_size
            
            if checksum_match and size_match:
                print(f"✅ 备份完整性验证通过")
                return True
            else:
                print(f"❌ 备份完整性验证失败:")
                if not checksum_match:
                    print(f"   校验和不匹配: 期望 {backup.checksum[:16]}..., 实际 {current_checksum[:16]}...")
                if not size_match:
                    print(f"   大小不匹配: 期望 {backup.file_size:,}, 实际 {current_size:,}")
                return False
        
        except Exception as e:
            print(f"❌ 完整性验证失败: {e}")
            return False
    
    def restore_from_backup(self, backup_id: str, target_path: Optional[Path] = None) -> bool:
        """从备份恢复文件"""
        print(f"🔄 从备份恢复: {backup_id}")
        
        backup = self._find_backup_by_id(backup_id)
        if not backup:
            print(f"❌ 备份不存在: {backup_id}")
            return False
        
        backup_path = Path(backup.backup_path)
        if not backup_path.exists():
            print(f"❌ 备份文件不存在: {backup_path}")
            return False
        
        # 确定目标路径
        if target_path is None:
            target_path = Path(backup.original_path)
        
        try:
            # 验证备份完整性
            if not self.verify_backup_integrity(backup_id):
                print(f"⚠️  备份完整性验证失败，但继续恢复...")
            
            # 执行恢复
            shutil.copy2(backup_path, target_path)
            
            print(f"✅ 恢复成功: {target_path}")
            return True
        
        except Exception as e:
            print(f"❌ 恢复失败: {e}")
            return False
    
    def _find_operation_by_id(self, operation_id: str) -> Optional[StripOperation]:
        """根据ID查找操作记录"""
        for operation in self.operations:
            if operation.id == operation_id:
                return operation
        return None
    
    def _find_backup_by_id(self, backup_id: str) -> Optional[BackupMetadata]:
        """根据ID查找备份记录"""
        for backup in self.backups:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total_operations = len(self.operations)
        successful_operations = len([op for op in self.operations if op.success])
        failed_operations = total_operations - successful_operations
        
        total_backups = len(self.backups)
        total_backup_size = sum(backup.file_size for backup in self.backups)
        
        # 计算总节省空间
        total_size_saved = sum(
            op.original_size - op.stripped_size 
            for op in self.operations 
            if op.success and op.stripped_size > 0
        )
        
        return {
            'operations': {
                'total': total_operations,
                'successful': successful_operations,
                'failed': failed_operations,
                'success_rate': (successful_operations / total_operations * 100) if total_operations > 0 else 0
            },
            'backups': {
                'total': total_backups,
                'total_size_bytes': total_backup_size,
                'total_size_mb': total_backup_size / (1024 * 1024)
            },
            'compression': {
                'total_size_saved_bytes': total_size_saved,
                'total_size_saved_mb': total_size_saved / (1024 * 1024)
            }
        }
    
    def generate_report(self, output_file: str = "strip_rollback_report.json"):
        """生成详细报告"""
        print(f"📋 生成回滚管理报告: {output_file}")
        
        stats = self.get_statistics()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': stats,
            'recent_operations': [asdict(op) for op in self.list_operations(20)],
            'recent_backups': [asdict(backup) for backup in self.list_backups(20)],
            'recommendations': self._generate_maintenance_recommendations(stats)
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # 生成摘要
        summary_file = output_file.replace('.json', '_summary.txt')
        self._generate_summary_report(report, summary_file)
        
        print(f"✅ 报告生成完成:")
        print(f"   详细报告: {output_file}")
        print(f"   摘要报告: {summary_file}")
    
    def _generate_maintenance_recommendations(self, stats: Dict) -> List[str]:
        """生成维护建议"""
        recommendations = []
        
        # 备份空间建议
        backup_size_mb = stats['backups']['total_size_mb']
        if backup_size_mb > 1000:  # 1GB
            recommendations.append(f"备份占用空间较大 ({backup_size_mb:.1f} MB)，考虑清理旧备份")
        
        # 成功率建议
        success_rate = stats['operations']['success_rate']
        if success_rate < 80:
            recommendations.append(f"Strip成功率较低 ({success_rate:.1f}%)，检查Strip策略和目标文件兼容性")
        
        # 空间节省建议
        saved_mb = stats['compression']['total_size_saved_mb']
        if saved_mb < 10:
            recommendations.append("Strip压缩效果有限，评估是否继续使用Strip")
        
        # 维护建议
        total_backups = stats['backups']['total']
        if total_backups > 50:
            recommendations.append("备份文件较多，定期清理可释放存储空间")
        
        return recommendations
    
    def _generate_summary_report(self, report: dict, output_file: str):
        """生成摘要报告"""
        with open(output_file, 'w') as f:
            f.write("📋 Strip回滚管理摘要报告\n")
            f.write("=" * 60 + "\n\n")
            
            # 统计信息
            stats = report['statistics']
            f.write("📊 统计信息:\n")
            f.write(f"   Strip操作总数: {stats['operations']['total']}\n")
            f.write(f"   成功操作: {stats['operations']['successful']}\n")
            f.write(f"   失败操作: {stats['operations']['failed']}\n")
            f.write(f"   成功率: {stats['operations']['success_rate']:.1f}%\n")
            f.write(f"   备份文件总数: {stats['backups']['total']}\n")
            f.write(f"   备份占用空间: {stats['backups']['total_size_mb']:.1f} MB\n")
            f.write(f"   总节省空间: {stats['compression']['total_size_saved_mb']:.1f} MB\n\n")
            
            # 最近操作
            if report['recent_operations']:
                f.write("🕒 最近操作:\n")
                for op in report['recent_operations'][:5]:
                    status = "✅" if op['success'] else "❌"
                    f.write(f"   {status} {op['id']}: {op['strip_method']} ({op['timestamp'][:10]})\n")
                f.write("\n")
            
            # 维护建议
            if report['recommendations']:
                f.write("💡 维护建议:\n")
                for rec in report['recommendations']:
                    f.write(f"   • {rec}\n")
                f.write("\n")
            
            f.write(f"报告生成时间: {report['generated_at']}\n")


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Strip回滚管理器")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建备份
    backup_parser = subparsers.add_parser('backup', help='创建备份文件')
    backup_parser.add_argument('binary', help='二进制文件路径')
    
    # 准备Strip操作
    prepare_parser = subparsers.add_parser('prepare', help='准备Strip操作')
    prepare_parser.add_argument('binary', help='二进制文件路径')
    prepare_parser.add_argument('--method', required=True, 
                               choices=['conservative', 'moderate', 'aggressive'],
                               help='Strip方法')
    prepare_parser.add_argument('--no-backup', action='store_true', help='不创建备份')
    
    # 完成操作
    complete_parser = subparsers.add_parser('complete', help='完成Strip操作')
    complete_parser.add_argument('operation_id', help='操作ID')
    complete_parser.add_argument('--success', action='store_true', help='操作成功')
    complete_parser.add_argument('--verified', action='store_true', help='功能已验证')
    complete_parser.add_argument('--error', help='错误信息')
    complete_parser.add_argument('--notes', help='备注信息')
    
    # 回滚操作
    rollback_parser = subparsers.add_parser('rollback', help='回滚Strip操作')
    rollback_parser.add_argument('operation_id', nargs='?', help='操作ID (默认回滚最新操作)')
    
    # 列出操作
    list_ops_parser = subparsers.add_parser('list-operations', help='列出Strip操作')
    list_ops_parser.add_argument('--limit', type=int, default=10, help='显示数量限制')
    list_ops_parser.add_argument('--success-only', action='store_true', help='只显示成功操作')
    
    # 列出备份
    list_backups_parser = subparsers.add_parser('list-backups', help='列出备份文件')
    list_backups_parser.add_argument('--limit', type=int, default=10, help='显示数量限制')
    
    # 清理备份
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧备份')
    cleanup_parser.add_argument('--days', type=int, default=30, help='保留天数')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='模拟运行')
    
    # 验证备份
    verify_parser = subparsers.add_parser('verify', help='验证备份完整性')
    verify_parser.add_argument('backup_id', help='备份ID')
    
    # 恢复备份
    restore_parser = subparsers.add_parser('restore', help='从备份恢复')
    restore_parser.add_argument('backup_id', help='备份ID')
    restore_parser.add_argument('--target', help='目标路径')
    
    # 统计信息
    subparsers.add_parser('stats', help='显示统计信息')
    
    # 生成报告
    report_parser = subparsers.add_parser('report', help='生成详细报告')
    report_parser.add_argument('-o', '--output', default='strip_rollback_report.json',
                              help='输出文件')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        manager = StripRollbackManager()
        
        if args.command == 'backup':
            binary_path = Path(args.binary)
            backup_id = manager.create_backup(binary_path)
            print(f"✅ 备份ID: {backup_id}")
        
        elif args.command == 'prepare':
            binary_path = Path(args.binary)
            operation_id = manager.prepare_strip_operation(
                binary_path, 
                args.method, 
                create_backup=not args.no_backup
            )
            print(f"✅ 操作ID: {operation_id}")
        
        elif args.command == 'complete':
            manager.complete_strip_operation(
                args.operation_id,
                args.success,
                args.verified,
                args.error,
                args.notes
            )
        
        elif args.command == 'rollback':
            if args.operation_id:
                success = manager.rollback_operation(args.operation_id)
            else:
                success = manager.rollback_latest_operation()
            
            if not success:
                sys.exit(1)
        
        elif args.command == 'list-operations':
            operations = manager.list_operations(args.limit, args.success_only)
            if operations:
                print(f"📋 Strip操作列表 (最近 {len(operations)} 条):")
                for op in operations:
                    status = "✅" if op.success else "❌"
                    verified = "🔍" if op.functionality_verified else ""
                    print(f"  {status}{verified} {op.id}: {op.strip_method} ({op.timestamp[:16]})")
                    if op.error_message:
                        print(f"       错误: {op.error_message}")
            else:
                print("📝 暂无操作记录")
        
        elif args.command == 'list-backups':
            backups = manager.list_backups(args.limit)
            if backups:
                print(f"💾 备份文件列表 (最近 {len(backups)} 个):")
                for backup in backups:
                    size_mb = backup.file_size / (1024 * 1024)
                    print(f"  📦 {backup.backup_id}: {Path(backup.original_path).name} ({size_mb:.1f} MB)")
                    print(f"       {backup.created_at[:16]} -> {backup.backup_path}")
            else:
                print("📝 暂无备份文件")
        
        elif args.command == 'cleanup':
            count = manager.cleanup_old_backups(args.days, args.dry_run)
            if count == 0:
                print("✅ 无需清理")
        
        elif args.command == 'verify':
            success = manager.verify_backup_integrity(args.backup_id)
            if not success:
                sys.exit(1)
        
        elif args.command == 'restore':
            target_path = Path(args.target) if args.target else None
            success = manager.restore_from_backup(args.backup_id, target_path)
            if not success:
                sys.exit(1)
        
        elif args.command == 'stats':
            stats = manager.get_statistics()
            print("📊 回滚管理器统计信息:")
            print(f"   Strip操作: {stats['operations']['total']} 次 (成功率 {stats['operations']['success_rate']:.1f}%)")
            print(f"   备份文件: {stats['backups']['total']} 个 ({stats['backups']['total_size_mb']:.1f} MB)")
            print(f"   节省空间: {stats['compression']['total_size_saved_mb']:.1f} MB")
        
        elif args.command == 'report':
            manager.generate_report(args.output)
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()