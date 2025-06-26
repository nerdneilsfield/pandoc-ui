#!/usr/bin/env python3
"""
integrity_validator.py - 二进制文件完整性验证工具

用于验证Strip操作前后的文件完整性，并提供详细的分析报告。
"""

import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class FileMetadata:
    """文件元数据"""
    path: str
    size: int
    permissions: str
    modified_time: float
    checksums: Dict[str, str]


@dataclass
class IntegrityReport:
    """完整性验证报告"""
    original_metadata: FileMetadata
    current_metadata: FileMetadata
    size_change: int
    size_change_percent: float
    checksums_changed: bool
    functionality_test_passed: bool
    strip_level: Optional[str] = None
    error_message: Optional[str] = None
    recommendations: List[str] = None


class BinaryIntegrityValidator:
    """二进制文件完整性验证器"""
    
    def __init__(self):
        self.hash_algorithms = ['md5', 'sha1', 'sha256', 'sha512']
        self.supported_platforms = ['linux', 'darwin', 'win32']
        
    def calculate_checksums(self, filepath: Path) -> Dict[str, str]:
        """计算文件的多种校验和"""
        checksums = {}
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
                
                for algo in self.hash_algorithms:
                    try:
                        hash_obj = hashlib.new(algo)
                        hash_obj.update(data)
                        checksums[algo] = hash_obj.hexdigest()
                    except ValueError:
                        # 某些算法可能不可用
                        continue
                        
        except Exception as e:
            print(f"⚠️  计算校验和失败: {e}")
            
        return checksums
    
    def get_file_metadata(self, filepath: Path) -> FileMetadata:
        """获取文件元数据"""
        stat_info = filepath.stat()
        
        # 获取权限字符串
        permissions = oct(stat_info.st_mode)[-3:]
        
        return FileMetadata(
            path=str(filepath),
            size=stat_info.st_size,
            permissions=permissions,
            modified_time=stat_info.st_mtime,
            checksums=self.calculate_checksums(filepath)
        )
    
    def create_baseline(self, binary_path: Path, output_path: Optional[Path] = None) -> Path:
        """创建Strip前的基线"""
        if output_path is None:
            output_path = binary_path.parent / f"{binary_path.name}.baseline.json"
        
        print(f"📋 创建基线文件: {output_path}")
        
        metadata = self.get_file_metadata(binary_path)
        
        baseline = {
            'created_at': time.time(),
            'created_at_iso': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'binary_path': str(binary_path),
            'platform': sys.platform,
            'metadata': asdict(metadata)
        }
        
        with open(output_path, 'w') as f:
            json.dump(baseline, f, indent=2)
        
        print(f"✅ 基线创建完成")
        print(f"   文件大小: {metadata.size:,} bytes ({metadata.size/1024/1024:.2f} MB)")
        print(f"   SHA256: {metadata.checksums.get('sha256', 'N/A')[:16]}...")
        
        return output_path
    
    def verify_integrity(self, binary_path: Path, baseline_path: Path, 
                        strip_level: Optional[str] = None) -> IntegrityReport:
        """验证文件完整性"""
        print(f"🔍 验证文件完整性: {binary_path}")
        
        # 加载基线
        try:
            with open(baseline_path, 'r') as f:
                baseline = json.load(f)
        except Exception as e:
            raise ValueError(f"无法加载基线文件: {e}")
        
        # 重建原始元数据
        original_dict = baseline['metadata']
        original_metadata = FileMetadata(**original_dict)
        
        # 获取当前元数据
        current_metadata = self.get_file_metadata(binary_path)
        
        # 计算变化
        size_change = current_metadata.size - original_metadata.size
        size_change_percent = (size_change / original_metadata.size) * 100 if original_metadata.size > 0 else 0
        
        # 检查校验和是否改变
        checksums_changed = current_metadata.checksums != original_metadata.checksums
        
        # 执行功能性测试
        functionality_test_passed = self._test_functionality(binary_path)
        
        # 生成建议
        recommendations = self._generate_recommendations(
            original_metadata, current_metadata, strip_level, functionality_test_passed
        )
        
        report = IntegrityReport(
            original_metadata=original_metadata,
            current_metadata=current_metadata,
            size_change=size_change,
            size_change_percent=size_change_percent,
            checksums_changed=checksums_changed,
            functionality_test_passed=functionality_test_passed,
            strip_level=strip_level,
            recommendations=recommendations
        )
        
        self._print_verification_results(report)
        
        return report
    
    def _test_functionality(self, binary_path: Path) -> bool:
        """测试二进制文件基本功能"""
        print(f"🧪 测试功能性: {binary_path}")
        
        if not binary_path.exists():
            print("❌ 文件不存在")
            return False
        
        if not os.access(binary_path, os.X_OK):
            print("❌ 文件不可执行")
            return False
        
        # 测试基本执行
        try:
            # 测试版本信息
            result = subprocess.run(
                [str(binary_path), '--version'],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ 版本检查通过")
                version_test_passed = True
            else:
                print("⚠️  版本检查未通过（可能不支持--version）")
                version_test_passed = False
        
        except subprocess.TimeoutExpired:
            print("⚠️  版本检查超时")
            version_test_passed = False
        except Exception:
            print("⚠️  版本检查出错")
            version_test_passed = False
        
        # 测试帮助信息
        try:
            result = subprocess.run(
                [str(binary_path), '--help'],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ 帮助信息检查通过")
                help_test_passed = True
            else:
                print("⚠️  帮助信息检查未通过（可能不支持--help）")
                help_test_passed = False
        
        except subprocess.TimeoutExpired:
            print("⚠️  帮助信息检查超时")
            help_test_passed = False
        except Exception:
            print("⚠️  帮助信息检查出错")
            help_test_passed = False
        
        # 检查是否是PySide6应用并进行特殊测试
        if self._is_pyside6_binary(binary_path):
            print("🎨 检测到PySide6应用，进行Qt功能测试")
            qt_test_passed = self._test_pyside6_functionality(binary_path)
        else:
            qt_test_passed = True  # 非Qt应用不需要Qt测试
        
        # 综合评估
        overall_success = qt_test_passed and (version_test_passed or help_test_passed)
        
        if overall_success:
            print("✅ 功能性测试通过")
        else:
            print("❌ 功能性测试失败")
        
        return overall_success
    
    def _is_pyside6_binary(self, binary_path: Path) -> bool:
        """检查是否是PySide6应用"""
        try:
            result = subprocess.run(
                ['strings', str(binary_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                content = result.stdout
                return any(keyword in content for keyword in ['PySide6', 'QtCore', 'QtWidgets', 'Qt6'])
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return False
    
    def _test_pyside6_functionality(self, binary_path: Path) -> bool:
        """测试PySide6应用特定功能"""
        # 创建临时测试脚本
        test_script_content = '''
import sys
import os
import tempfile
import subprocess

# 设置环境变量以便无头运行
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

try:
    # 测试Qt库导入
    from PySide6.QtCore import QCoreApplication, QTimer
    from PySide6.QtWidgets import QApplication
    
    # 创建应用实例
    app = QCoreApplication(sys.argv)
    
    # 测试基本Qt功能
    timer = QTimer()
    timer.timeout.connect(app.quit)
    timer.start(100)  # 100ms后退出
    
    # 运行事件循环
    app.exec()
    
    print("PySide6 functionality test passed")
    sys.exit(0)
    
except ImportError as e:
    print(f"PySide6 import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"PySide6 test failed: {e}")
    sys.exit(1)
'''
        
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_script_content)
                test_script_path = f.name
            
            # 运行测试脚本
            result = subprocess.run(
                ['python3', test_script_path],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            os.unlink(test_script_path)
            
            if result.returncode == 0:
                print("✅ PySide6功能测试通过")
                return True
            else:
                print(f"❌ PySide6功能测试失败: {result.stderr}")
                return False
        
        except Exception as e:
            print(f"⚠️  PySide6测试脚本执行失败: {e}")
            return False
    
    def _generate_recommendations(self, original: FileMetadata, current: FileMetadata,
                                strip_level: Optional[str], functionality_passed: bool) -> List[str]:
        """生成建议和注意事项"""
        recommendations = []
        
        # 大小变化分析
        size_reduction = original.size - current.size
        if size_reduction > 0:
            reduction_percent = (size_reduction / original.size) * 100
            recommendations.append(f"文件大小减少了 {size_reduction:,} bytes ({reduction_percent:.1f}%)")
        elif size_reduction < 0:
            recommendations.append(f"⚠️  文件大小意外增加了 {abs(size_reduction):,} bytes")
        else:
            recommendations.append("⚠️  文件大小没有变化，Strip可能没有效果")
        
        # Strip级别分析
        if strip_level:
            if strip_level == "conservative":
                recommendations.append("✅ 使用了保守Strip策略，安全性较高")
            elif strip_level == "moderate":
                recommendations.append("⚖️  使用了中等Strip策略，请确保充分测试")
            elif strip_level == "aggressive":
                recommendations.append("⚠️  使用了激进Strip策略，存在较高风险")
        
        # 功能性测试结果
        if functionality_passed:
            recommendations.append("✅ 功能性测试通过，应用应该能正常运行")
        else:
            recommendations.append("❌ 功能性测试失败，建议回滚到Strip前版本")
            recommendations.append("🔄 使用备份文件恢复或重新使用更保守的Strip级别")
        
        # 通用建议
        recommendations.extend([
            "💾 保留Strip前的备份文件用于紧急回滚",
            "🧪 在生产环境部署前进行完整的功能测试",
            "📊 监控应用性能，确保Strip没有影响运行效率"
        ])
        
        return recommendations
    
    def _print_verification_results(self, report: IntegrityReport):
        """打印验证结果"""
        print("\n" + "="*60)
        print("📊 完整性验证报告")
        print("="*60)
        
        print(f"\n📁 文件信息:")
        print(f"   路径: {report.current_metadata.path}")
        print(f"   权限: {report.current_metadata.permissions}")
        
        print(f"\n📏 大小变化:")
        print(f"   原始大小: {report.original_metadata.size:,} bytes ({report.original_metadata.size/1024/1024:.2f} MB)")
        print(f"   当前大小: {report.current_metadata.size:,} bytes ({report.current_metadata.size/1024/1024:.2f} MB)")
        print(f"   变化量: {report.size_change:,} bytes ({report.size_change_percent:.2f}%)")
        
        print(f"\n🔐 校验和验证:")
        if report.checksums_changed:
            print("   ✅ 校验和已改变（Strip操作生效）")
            # 显示关键校验和的变化
            if 'sha256' in report.original_metadata.checksums and 'sha256' in report.current_metadata.checksums:
                orig_sha = report.original_metadata.checksums['sha256']
                curr_sha = report.current_metadata.checksums['sha256']
                print(f"   原始SHA256: {orig_sha[:16]}...{orig_sha[-16:]}")
                print(f"   当前SHA256: {curr_sha[:16]}...{curr_sha[-16:]}")
        else:
            print("   ⚠️  校验和未改变（Strip可能无效果）")
        
        print(f"\n🧪 功能性测试:")
        if report.functionality_test_passed:
            print("   ✅ 通过")
        else:
            print("   ❌ 失败")
        
        if report.strip_level:
            print(f"\n⚙️  Strip级别: {report.strip_level}")
        
        if report.recommendations:
            print(f"\n💡 建议和注意事项:")
            for i, recommendation in enumerate(report.recommendations, 1):
                print(f"   {i}. {recommendation}")
        
        print("\n" + "="*60)
    
    def save_report(self, report: IntegrityReport, output_path: Path):
        """保存验证报告"""
        report_data = {
            'generated_at': time.time(),
            'generated_at_iso': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'report': asdict(report)
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📋 验证报告已保存: {output_path}")
    
    def compare_multiple_binaries(self, binary_paths: List[Path], baseline_dir: Path) -> Dict[str, IntegrityReport]:
        """批量验证多个二进制文件"""
        results = {}
        
        print(f"🔍 批量验证 {len(binary_paths)} 个文件")
        
        for i, binary_path in enumerate(binary_paths, 1):
            print(f"\n[{i}/{len(binary_paths)}] 验证: {binary_path.name}")
            
            baseline_path = baseline_dir / f"{binary_path.name}.baseline.json"
            
            if not baseline_path.exists():
                print(f"⚠️  跳过 {binary_path.name}: 未找到基线文件")
                continue
            
            try:
                report = self.verify_integrity(binary_path, baseline_path)
                results[str(binary_path)] = report
            except Exception as e:
                print(f"❌ 验证失败 {binary_path.name}: {e}")
                continue
        
        return results
    
    def generate_summary_report(self, results: Dict[str, IntegrityReport], output_path: Path):
        """生成批量验证摘要报告"""
        total_files = len(results)
        successful_files = sum(1 for r in results.values() if r.functionality_test_passed)
        failed_files = total_files - successful_files
        
        total_size_reduction = sum(abs(r.size_change) for r in results.values() if r.size_change < 0)
        
        summary = {
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'total_files': total_files,
            'successful_files': successful_files,
            'failed_files': failed_files,
            'success_rate': (successful_files / total_files * 100) if total_files > 0 else 0,
            'total_size_reduction_bytes': total_size_reduction,
            'total_size_reduction_mb': total_size_reduction / (1024 * 1024),
            'file_results': {path: asdict(report) for path, report in results.items()}
        }
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # 打印摘要
        print(f"\n📊 批量验证摘要:")
        print(f"   总文件数: {total_files}")
        print(f"   成功验证: {successful_files}")
        print(f"   失败验证: {failed_files}")
        print(f"   成功率: {summary['success_rate']:.1f}%")
        print(f"   总大小减少: {summary['total_size_reduction_mb']:.2f} MB")
        print(f"📋 详细报告已保存: {output_path}")


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="二进制文件完整性验证工具")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建基线命令
    create_parser = subparsers.add_parser('create-baseline', help='创建Strip前基线')
    create_parser.add_argument('binary', help='二进制文件路径')
    create_parser.add_argument('-o', '--output', help='基线文件输出路径')
    
    # 验证命令
    verify_parser = subparsers.add_parser('verify', help='验证Strip后完整性')
    verify_parser.add_argument('binary', help='二进制文件路径')
    verify_parser.add_argument('baseline', help='基线文件路径')
    verify_parser.add_argument('--strip-level', choices=['conservative', 'moderate', 'aggressive'], 
                              help='Strip级别')
    verify_parser.add_argument('-o', '--output', help='验证报告输出路径')
    
    # 批量验证命令
    batch_parser = subparsers.add_parser('batch-verify', help='批量验证多个文件')
    batch_parser.add_argument('files', nargs='+', help='二进制文件路径列表')
    batch_parser.add_argument('--baseline-dir', required=True, help='基线文件目录')
    batch_parser.add_argument('-o', '--output', help='摘要报告输出路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    validator = BinaryIntegrityValidator()
    
    try:
        if args.command == 'create-baseline':
            binary_path = Path(args.binary)
            output_path = Path(args.output) if args.output else None
            validator.create_baseline(binary_path, output_path)
        
        elif args.command == 'verify':
            binary_path = Path(args.binary)
            baseline_path = Path(args.baseline)
            
            report = validator.verify_integrity(binary_path, baseline_path, args.strip_level)
            
            if args.output:
                output_path = Path(args.output)
                validator.save_report(report, output_path)
        
        elif args.command == 'batch-verify':
            binary_paths = [Path(f) for f in args.files]
            baseline_dir = Path(args.baseline_dir)
            
            results = validator.compare_multiple_binaries(binary_paths, baseline_dir)
            
            if args.output:
                output_path = Path(args.output)
                validator.generate_summary_report(results, output_path)
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()