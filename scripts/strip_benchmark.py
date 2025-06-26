#!/usr/bin/env python3
"""
strip_benchmark.py - Strip压缩效果基准测试工具

对不同Strip策略进行基准测试，评估压缩效果、性能影响和安全性。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

@dataclass
class BenchmarkResult:
    """基准测试结果"""
    method: str
    description: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    size_reduction_bytes: int
    time_taken: float
    success: bool
    functionality_passed: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    platform_specific_notes: List[str] = None


@dataclass
class PerformanceMetrics:
    """性能指标"""
    startup_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    test_duration: float
    success: bool
    error_message: Optional[str] = None


class StripBenchmark:
    """Strip压缩基准测试器"""
    
    def __init__(self, binary_path: Path):
        self.binary_path = Path(binary_path)
        self.original_size = self.binary_path.stat().st_size
        self.platform = sys.platform
        self.temp_dir = Path(tempfile.mkdtemp(prefix="strip_benchmark_"))
        self.results: List[BenchmarkResult] = []
        
        print(f"🎯 Strip基准测试初始化")
        print(f"   目标文件: {self.binary_path}")
        print(f"   原始大小: {self.original_size:,} bytes ({self.original_size/1024/1024:.2f} MB)")
        print(f"   平台: {self.platform}")
        print(f"   临时目录: {self.temp_dir}")
    
    def __del__(self):
        """清理临时目录"""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def run_all_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """运行所有Strip方法的基准测试"""
        print(f"\n🚀 开始Strip基准测试...")
        
        # 定义测试方法
        test_methods = [
            ('conservative_strip', '保守Strip', self._test_conservative_strip),
            ('moderate_strip', '中等Strip', self._test_moderate_strip),
            ('aggressive_strip', '激进Strip', self._test_aggressive_strip),
            ('no_strip_baseline', '无Strip基线', self._test_no_strip_baseline),
        ]
        
        # 如果是Linux平台，添加更多选项
        if self.platform.startswith('linux'):
            test_methods.extend([
                ('strip_unneeded', 'Strip Unneeded', self._test_strip_unneeded),
                ('strip_debug_only', '仅Strip调试', self._test_strip_debug_only),
            ])
        
        results = {}
        
        for method_name, description, method_func in test_methods:
            print(f"\n📊 测试方法: {description}")
            print("-" * 50)
            
            try:
                result = method_func()
                results[method_name] = result
                self.results.append(result)
                
                if result.success:
                    print(f"✅ {description}: {result.compression_ratio:.1f}% 压缩")
                    print(f"   大小: {result.original_size:,} → {result.compressed_size:,} bytes")
                    print(f"   耗时: {result.time_taken:.2f}s")
                    if result.functionality_passed:
                        print(f"   功能: ✅ 通过")
                    else:
                        print(f"   功能: ❌ 失败")
                else:
                    print(f"❌ {description}: {result.error_message}")
                    
            except Exception as e:
                print(f"❌ {description}: 测试过程出错 - {e}")
                results[method_name] = BenchmarkResult(
                    method=method_name,
                    description=description,
                    original_size=self.original_size,
                    compressed_size=self.original_size,
                    compression_ratio=0.0,
                    size_reduction_bytes=0,
                    time_taken=0.0,
                    success=False,
                    functionality_passed=False,
                    error_message=str(e)
                )
        
        return results
    
    def _create_test_copy(self, suffix: str) -> Path:
        """创建测试用的二进制副本"""
        test_binary = self.temp_dir / f"{self.binary_path.name}.{suffix}"
        shutil.copy2(self.binary_path, test_binary)
        return test_binary
    
    def _test_conservative_strip(self) -> BenchmarkResult:
        """测试保守Strip策略"""
        return self._execute_strip_test(
            method="conservative_strip",
            description="保守Strip (仅移除调试符号)",
            strip_args=["--strip-debug", "--preserve-dates"]
        )
    
    def _test_moderate_strip(self) -> BenchmarkResult:
        """测试中等Strip策略"""
        return self._execute_strip_test(
            method="moderate_strip",
            description="中等Strip (移除非必需符号)",
            strip_args=["--strip-unneeded", "--preserve-dates"]
        )
    
    def _test_aggressive_strip(self) -> BenchmarkResult:
        """测试激进Strip策略"""
        return self._execute_strip_test(
            method="aggressive_strip",
            description="激进Strip (移除所有符号)",
            strip_args=["--strip-all", "--preserve-dates"]
        )
    
    def _test_strip_unneeded(self) -> BenchmarkResult:
        """测试Strip Unneeded"""
        return self._execute_strip_test(
            method="strip_unneeded",
            description="Strip Unneeded",
            strip_args=["--strip-unneeded"]
        )
    
    def _test_strip_debug_only(self) -> BenchmarkResult:
        """测试仅Strip调试信息"""
        return self._execute_strip_test(
            method="strip_debug_only",
            description="仅Strip调试信息",
            strip_args=["--strip-debug"]
        )
    
    def _test_no_strip_baseline(self) -> BenchmarkResult:
        """无Strip基线测试"""
        test_binary = self._create_test_copy("baseline")
        
        start_time = time.time()
        functionality_passed = self._verify_functionality(test_binary)
        time_taken = time.time() - start_time
        
        return BenchmarkResult(
            method="no_strip_baseline",
            description="无Strip基线",
            original_size=self.original_size,
            compressed_size=self.original_size,
            compression_ratio=0.0,
            size_reduction_bytes=0,
            time_taken=time_taken,
            success=True,
            functionality_passed=functionality_passed,
            warnings=["基线测试，无压缩效果"]
        )
    
    def _execute_strip_test(self, method: str, description: str, strip_args: List[str]) -> BenchmarkResult:
        """执行Strip测试的通用方法"""
        test_binary = self._create_test_copy(method)
        warnings = []
        platform_notes = []
        
        start_time = time.time()
        
        try:
            # 检查平台兼容性
            if self.platform == 'win32':
                return BenchmarkResult(
                    method=method,
                    description=description,
                    original_size=self.original_size,
                    compressed_size=self.original_size,
                    compression_ratio=0.0,
                    size_reduction_bytes=0,
                    time_taken=0.0,
                    success=False,
                    functionality_passed=False,
                    error_message="Windows平台不支持strip命令"
                )
            
            # macOS平台调整参数
            if self.platform == 'darwin':
                # macOS的strip命令参数不同
                if '--strip-debug' in strip_args:
                    strip_args = ['-S']
                elif '--strip-unneeded' in strip_args:
                    strip_args = ['-x']
                elif '--strip-all' in strip_args:
                    strip_args = ['-x']
                
                # 移除macOS不支持的选项
                strip_args = [arg for arg in strip_args if arg != '--preserve-dates']
                platform_notes.append("macOS平台Strip参数已调整")
            
            # 执行Strip命令
            cmd = ['strip'] + strip_args + [str(test_binary)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return BenchmarkResult(
                    method=method,
                    description=description,
                    original_size=self.original_size,
                    compressed_size=self.original_size,
                    compression_ratio=0.0,
                    size_reduction_bytes=0,
                    time_taken=time.time() - start_time,
                    success=False,
                    functionality_passed=False,
                    error_message=f"Strip命令失败: {result.stderr}"
                )
            
            # 计算压缩效果
            compressed_size = test_binary.stat().st_size
            size_reduction = self.original_size - compressed_size
            compression_ratio = (size_reduction / self.original_size) * 100 if self.original_size > 0 else 0
            
            # 验证功能性
            functionality_passed = self._verify_functionality(test_binary)
            
            # 性能测试
            performance_metrics = self._measure_performance(test_binary)
            if performance_metrics:
                platform_notes.append(f"启动时间: {performance_metrics.startup_time:.2f}s")
                platform_notes.append(f"内存使用: {performance_metrics.memory_usage_mb:.1f}MB")
            
            time_taken = time.time() - start_time
            
            # 生成警告
            if compression_ratio < 1.0:
                warnings.append("压缩效果很小，可能不值得Strip")
            if not functionality_passed:
                warnings.append("功能测试失败，可能存在兼容性问题")
            if self._is_pyside6_binary(test_binary) and method == "aggressive_strip":
                warnings.append("PySide6应用使用激进Strip存在高风险")
            
            return BenchmarkResult(
                method=method,
                description=description,
                original_size=self.original_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                size_reduction_bytes=size_reduction,
                time_taken=time_taken,
                success=True,
                functionality_passed=functionality_passed,
                warnings=warnings if warnings else None,
                platform_specific_notes=platform_notes if platform_notes else None
            )
            
        except subprocess.TimeoutExpired:
            return BenchmarkResult(
                method=method,
                description=description,
                original_size=self.original_size,
                compressed_size=self.original_size,
                compression_ratio=0.0,
                size_reduction_bytes=0,
                time_taken=time.time() - start_time,
                success=False,
                functionality_passed=False,
                error_message="Strip命令超时"
            )
        
        except Exception as e:
            return BenchmarkResult(
                method=method,
                description=description,
                original_size=self.original_size,
                compressed_size=self.original_size,
                compression_ratio=0.0,
                size_reduction_bytes=0,
                time_taken=time.time() - start_time,
                success=False,
                functionality_passed=False,
                error_message=f"Strip测试失败: {e}"
            )
    
    def _verify_functionality(self, binary: Path) -> bool:
        """验证二进制文件的基本功能"""
        if not binary.exists() or not os.access(binary, os.X_OK):
            return False
        
        try:
            # 测试版本信息
            result = subprocess.run(
                [str(binary), '--version'],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return True
            
            # 如果版本测试失败，尝试帮助信息
            result = subprocess.run(
                [str(binary), '--help'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _is_pyside6_binary(self, binary: Path) -> bool:
        """检查是否是PySide6应用"""
        try:
            result = subprocess.run(
                ['strings', str(binary)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                content = result.stdout
                return any(keyword in content for keyword in ['PySide6', 'QtCore', 'QtWidgets'])
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return False
    
    def _measure_performance(self, binary: Path) -> Optional[PerformanceMetrics]:
        """测量性能指标"""
        if not os.access(binary, os.X_OK):
            return None
        
        try:
            # 测量启动时间
            start_time = time.time()
            result = subprocess.run(
                [str(binary), '--version'],
                capture_output=True,
                timeout=30
            )
            startup_time = time.time() - start_time
            
            if result.returncode == 0:
                return PerformanceMetrics(
                    startup_time=startup_time,
                    memory_usage_mb=0.0,  # 简化实现，不测量内存
                    cpu_usage_percent=0.0,  # 简化实现，不测量CPU
                    test_duration=startup_time,
                    success=True
                )
            else:
                return PerformanceMetrics(
                    startup_time=startup_time,
                    memory_usage_mb=0.0,
                    cpu_usage_percent=0.0,
                    test_duration=startup_time,
                    success=False,
                    error_message="性能测试失败"
                )
        
        except Exception as e:
            return PerformanceMetrics(
                startup_time=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                test_duration=0.0,
                success=False,
                error_message=str(e)
            )
    
    def generate_report(self, output_file: str = "strip_benchmark_report.json"):
        """生成详细的基准测试报告"""
        print(f"\n📋 生成基准测试报告...")
        
        # 计算统计信息
        successful_results = [r for r in self.results if r.success]
        best_compression = max(successful_results, key=lambda x: x.compression_ratio) if successful_results else None
        safest_option = next((r for r in successful_results if r.functionality_passed and "conservative" in r.method), None)
        
        report = {
            'metadata': {
                'generated_at': time.time(),
                'generated_at_iso': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                'binary_path': str(self.binary_path),
                'original_size': self.original_size,
                'platform': self.platform,
                'temp_directory': str(self.temp_dir)
            },
            'summary': {
                'total_methods_tested': len(self.results),
                'successful_methods': len(successful_results),
                'failed_methods': len(self.results) - len(successful_results),
                'best_compression_method': best_compression.method if best_compression else None,
                'best_compression_ratio': best_compression.compression_ratio if best_compression else 0,
                'safest_recommended_method': safest_option.method if safest_option else None,
                'max_size_reduction_bytes': max((r.size_reduction_bytes for r in successful_results), default=0),
                'max_size_reduction_mb': max((r.size_reduction_bytes for r in successful_results), default=0) / (1024 * 1024)
            },
            'detailed_results': [asdict(result) for result in self.results],
            'recommendations': self._generate_recommendations(successful_results, best_compression, safest_option)
        }
        
        # 保存JSON报告
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # 生成可读摘要
        summary_file = output_file.replace('.json', '_summary.txt')
        self._generate_summary_report(report, summary_file)
        
        print(f"✅ 报告生成完成:")
        print(f"   详细报告: {output_file}")
        print(f"   摘要报告: {summary_file}")
        
        return report
    
    def _generate_recommendations(self, successful_results: List[BenchmarkResult], 
                                best_compression: Optional[BenchmarkResult],
                                safest_option: Optional[BenchmarkResult]) -> Dict:
        """生成建议和推荐"""
        recommendations = {
            'for_production': [],
            'for_testing': [],
            'general_advice': [],
            'platform_specific': []
        }
        
        # 生产环境建议
        if safest_option:
            recommendations['for_production'].append(
                f"推荐使用 {safest_option.method} ({safest_option.description})"
            )
            recommendations['for_production'].append(
                f"预期压缩率: {safest_option.compression_ratio:.1f}%"
            )
        else:
            recommendations['for_production'].append("未找到安全可靠的Strip选项，建议不使用Strip")
        
        # 测试环境建议
        if best_compression and best_compression != safest_option:
            recommendations['for_testing'].append(
                f"最佳压缩效果: {best_compression.method} ({best_compression.compression_ratio:.1f}%)"
            )
            recommendations['for_testing'].append(
                "仅建议在测试环境使用，需要充分验证功能"
            )
        
        # 通用建议
        recommendations['general_advice'].extend([
            "始终在Strip前创建备份文件",
            "生产部署前进行完整功能测试",
            "监控Strip后的应用性能",
            "保留调试版本用于问题排查"
        ])
        
        # 平台特定建议
        if self.platform.startswith('linux'):
            recommendations['platform_specific'].append("Linux平台Strip功能最完善，支持所有级别")
        elif self.platform == 'darwin':
            recommendations['platform_specific'].append("macOS平台Strip选项有限，主要支持调试符号移除")
        elif self.platform == 'win32':
            recommendations['platform_specific'].append("Windows平台不支持Strip，考虑使用其他压缩方案")
        
        # PySide6特定建议
        pyside6_results = [r for r in successful_results if any(
            'pyside6' in note.lower() or 'qt' in note.lower() 
            for note in (r.platform_specific_notes or [])
        )]
        
        if pyside6_results:
            recommendations['platform_specific'].append("检测到PySide6应用，强烈建议仅使用保守Strip")
        
        return recommendations
    
    def _generate_summary_report(self, report: dict, output_file: str):
        """生成人类可读的摘要报告"""
        with open(output_file, 'w') as f:
            f.write("📊 Strip压缩基准测试摘要报告\n")
            f.write("=" * 60 + "\n\n")
            
            # 基本信息
            f.write(f"🎯 测试目标: {report['metadata']['binary_path']}\n")
            f.write(f"📏 原始大小: {report['metadata']['original_size']:,} bytes ")
            f.write(f"({report['metadata']['original_size']/1024/1024:.2f} MB)\n")
            f.write(f"🖥️  平台: {report['metadata']['platform']}\n")
            f.write(f"⏰ 测试时间: {report['metadata']['generated_at_iso']}\n\n")
            
            # 测试摘要
            summary = report['summary']
            f.write("📈 测试摘要:\n")
            f.write(f"   总测试方法: {summary['total_methods_tested']}\n")
            f.write(f"   成功方法: {summary['successful_methods']}\n")
            f.write(f"   失败方法: {summary['failed_methods']}\n")
            f.write(f"   最大压缩率: {summary['best_compression_ratio']:.1f}%\n")
            f.write(f"   最大节省空间: {summary['max_size_reduction_mb']:.2f} MB\n\n")
            
            # 详细结果
            f.write("📋 详细测试结果:\n")
            f.write("-" * 60 + "\n")
            
            for result in report['detailed_results']:
                status = "✅" if result['success'] else "❌"
                func_status = "✅" if result['functionality_passed'] else "❌"
                
                f.write(f"{status} {result['description']}:\n")
                
                if result['success']:
                    f.write(f"   压缩率: {result['compression_ratio']:.1f}%\n")
                    f.write(f"   大小变化: {result['original_size']:,} → {result['compressed_size']:,} bytes\n")
                    f.write(f"   节省空间: {result['size_reduction_bytes']:,} bytes\n")
                    f.write(f"   耗时: {result['time_taken']:.2f}s\n")
                    f.write(f"   功能测试: {func_status}\n")
                    
                    if result['warnings']:
                        f.write(f"   ⚠️  警告: {', '.join(result['warnings'])}\n")
                    
                    if result['platform_specific_notes']:
                        f.write(f"   📝 注释: {', '.join(result['platform_specific_notes'])}\n")
                else:
                    f.write(f"   ❌ 错误: {result['error_message']}\n")
                
                f.write("\n")
            
            # 推荐建议
            recommendations = report['recommendations']
            f.write("💡 建议和推荐:\n")
            f.write("-" * 60 + "\n")
            
            if recommendations['for_production']:
                f.write("🏭 生产环境:\n")
                for rec in recommendations['for_production']:
                    f.write(f"   • {rec}\n")
                f.write("\n")
            
            if recommendations['for_testing']:
                f.write("🧪 测试环境:\n")
                for rec in recommendations['for_testing']:
                    f.write(f"   • {rec}\n")
                f.write("\n")
            
            if recommendations['general_advice']:
                f.write("📚 通用建议:\n")
                for rec in recommendations['general_advice']:
                    f.write(f"   • {rec}\n")
                f.write("\n")
            
            if recommendations['platform_specific']:
                f.write("🖥️  平台特定:\n")
                for rec in recommendations['platform_specific']:
                    f.write(f"   • {rec}\n")
                f.write("\n")
            
            # 结论
            f.write("🎯 结论:\n")
            f.write("-" * 60 + "\n")
            
            if summary['best_compression_method']:
                f.write(f"🏆 最佳方案: {summary['best_compression_method']}\n")
                f.write(f"📊 压缩效果: {summary['best_compression_ratio']:.1f}%\n")
            
            if summary['safest_recommended_method']:
                f.write(f"🛡️  安全方案: {summary['safest_recommended_method']}\n")
            
            if summary['max_size_reduction_mb'] > 0:
                f.write(f"💾 最大节省: {summary['max_size_reduction_mb']:.2f} MB\n")
            else:
                f.write("⚠️  建议: 当前二进制文件可能不适合Strip压缩\n")


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Strip压缩基准测试工具")
    parser.add_argument('binary', help='要测试的二进制文件路径')
    parser.add_argument('-o', '--output', default='strip_benchmark_report.json',
                       help='输出报告文件名 (默认: strip_benchmark_report.json)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细输出')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    binary_path = Path(args.binary)
    if not binary_path.exists():
        print(f"❌ 错误: 文件不存在 - {binary_path}")
        sys.exit(1)
    
    if not os.access(binary_path, os.R_OK):
        print(f"❌ 错误: 文件不可读 - {binary_path}")
        sys.exit(1)
    
    print(f"🚀 开始Strip压缩基准测试: {binary_path}")
    
    try:
        # 创建基准测试器
        benchmark = StripBenchmark(binary_path)
        
        # 运行所有测试
        results = benchmark.run_all_benchmarks()
        
        # 生成报告
        report = benchmark.generate_report(args.output)
        
        print(f"\n🎉 基准测试完成!")
        
        # 显示快速摘要
        successful_count = len([r for r in results.values() if r.success])
        if successful_count > 0:
            best_result = max(
                (r for r in results.values() if r.success), 
                key=lambda x: x.compression_ratio
            )
            print(f"🏆 最佳压缩: {best_result.method} ({best_result.compression_ratio:.1f}%)")
        else:
            print(f"⚠️  警告: 没有成功的Strip方法")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 基准测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()