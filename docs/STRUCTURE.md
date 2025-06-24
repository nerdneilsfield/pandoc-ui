# 程序架构与目录规划文档

## 1 总体架构概览

* 整个系统分为 **UI 层、应用层（Application）与基础设施层（Infrastructure）**，它们以事件-信号方式耦合，从而保持清晰的依赖方向。
* UI 层只负责界面呈现与信号发射，因此它不直接调用 Pandoc，而是通过应用层公开的服务接口请求转换任务。
* 应用层聚焦业务逻辑：它调度任务、管理配置并将进度回传给 UI；同时它利用基础设施层封装的 Pandoc 执行器与文件系统工具。
* 基础设施层包装外部进程、下载器和本地缓存，因此 UI 与业务逻辑可以完全独立于具体实现细节而演进。

```text
         ┌─────── UI (PySide6 Widgets / QML) ────────┐
         │ MainWindow  SettingsDialog  SnapshotView │
         └───────────────▲───────────────▲──────────┘
                         │ signals/slots
         ┌───────────────┴───────────────┴──────────┐
         │          Application  Layer              │
         │  ConversionService   ProfileRepository   │
         │  FolderScanner       TaskQueue           │
         └───────────────▲───────────────▲──────────┘
                         │ import/use
         ┌───────────────┴───────────────┴──────────┐
         │         Infrastructure  Layer            │
         │  PandocRunner  PandocDetector  Downloader│
         │  PathUtils     SettingsStore             │
         └──────────────────────────────────────────┘
```

---

## 2 目录结构与文件职责

```text
pandoc-gui/
├─ pyproject.toml         # Poetry & build metadata
├─ README.md              # 项目说明
├─ pandoc-gui/
│  ├─ gui/                # UI 层
│  │   ├─ __init__.py
│  │   ├─ main_window.py  # 信号→Application
│  │   ├─ main_window.ui  # Qt Designer 文件
│  │   └─ dialogs/
│  │       └─ settings_dialog.ui
│  ├─ app/                # Application 层
│  │   ├─ __init__.py
│  │   ├─ conversion_service.py
│  │   ├─ profile_repository.py
│  │   ├─ folder_scanner.py
│  │   └─ task_queue.py
│  ├─ infra/              # Infrastructure 层
│  │   ├─ __init__.py
│  │   ├─ pandoc_runner.py
│  │   ├─ pandoc_detector.py
│  │   ├─ downloader.py
│  │   ├─ path_utils.py
│  │   └─ settings_store.py
│  └─ main.py             # 程序入口，初始化依赖注入
├─ resources/             # 图标、翻译 qm 文件、模板示例
├─ tests/                 # pytest 单元与集成测试
│  ├─ test_runner.py
│  ├─ test_service.py
│  └─ data/
├─ scripts/               # 辅助脚本（CI、打包）
│  ├─ build_windows.ps1
│  ├─ build_macos.sh
│  └─ build_linux.sh
└─ packaging/             # NSIS 与 productbuild 配置
    ├─ windows_installer.nsi
    └─ macos_pkgbuild.plist
```

### 说明

| 目录 / 文件     | 职责说明                                                        |
| ----------- | ----------------------------------------------------------- |
| `src/gui`   | 存放所有 Qt Designer `.ui` 文件与对应的 Python 类；每个对话框或窗口一个文件，保持粒度清晰。 |
| `src/app`   | 定义“无 UI 业务逻辑”，如任务调度、配置管理与并行队列；对外提供干净的服务接口以便测试与复用。           |
| `src/infra` | 包含 Pandoc 检测与执行、文件系统与下载工具；任何可能导致 IO 或外部进程调用的代码都集中在此层。       |
| `resources` | 放置多语言翻译文件（`*.qm`）、图标与示例模板，以支持国际化与 UI 资源独立管理。                |
| `tests`     | 提供高覆盖率的单元与端到端测试；`tests/data` 保留示例 Markdown 以保证转换流程可预测。      |
| `scripts`   | 存放跨平台打包与 CI 辅助脚本，避免在 CI 配置文件中写复杂 shell。                     |
| `packaging` | 归档 NSIS、pkgbuild 等打包器的模板，以便版本控制。                            |

---

## 3 模块划分与接口定义

| 模块                      | 关键类 / 方法                                 | 简述                                                             | 依赖方向                                               |
| ----------------------- | ---------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------- |
| `conversion_service.py` | `ConversionService`、`convert_async()`    | 负责接收来自 UI 的批量转换请求，拆分为任务并交由 `TaskQueue` 执行，再把进度信号发回 UI。         | 调用 `TaskQueue`、`ProfileRepository`、`FolderScanner` |
| `task_queue.py`         | `TaskQueue`、`submit()`、`join()`          | 基于 `QThreadPool` 实现有限并发的任务调度，确保 UI 线程不被阻塞。                     | 使用 `PandocRunner`                                  |
| `pandoc_runner.py`      | `PandocRunner`、`build_command()`、`run()` | 负责生成 Pandoc 命令行并捕获 stdout/stderr；对外通过回调或 asyncio queue 抛出日志片段。 | 依赖 `pandoc_detector.py`                            |
| `pandoc_detector.py`    | `detect()`                               | 在首轮启动时定位 Pandoc，可回退到下载对话框；支持缓存并热更新版本。                          | 仅依赖标准库                                             |
| `profile_repository.py` | `ProfileRepository`                      | 读写 JSON 快照文件并提供 CRUD；将文件路径统一相对化。                               | 依赖 `settings_store.py`                             |
| `settings_store.py`     | `SettingsStore`                          | 把应用级设置序列化到 `settings.json`，支持 schema 验证与版本迁移。                  | 仅依赖标准库                                             |
| `folder_scanner.py`     | `FolderScanner`                          | 根据扩展名与递归深度枚举文件，生成 `InputItem` 列表交给队列。                          | 使用 `path_utils.py`                                 |

---

## 4 关键类骨架示例（节选）

```python
# src/app/conversion_service.py
from typing import Iterable
from PySide6.QtCore import QObject, Signal, QRunnable, Slot
from infra.pandoc_runner import PandocRunner
from infra.path_utils import ensure_output_dir

class ConversionProgress(QObject):
    updated = Signal(str, int)   # 文件名, 百分比
    finished = Signal(str, bool, str)  # 文件名, 成功?, 日志

class ConversionService(QObject):
    def __init__(self, runner: PandocRunner, thread_pool):
        super().__init__()
        self.runner = runner
        self.pool = thread_pool
        self.progress = ConversionProgress()

    @Slot(object, list)
    def convert_async(self, profile, input_items: Iterable[str]):
        for file_path in input_items:
            job = _ConversionJob(self.runner, profile, file_path, self.progress)
            self.pool.start(job)

class _ConversionJob(QRunnable):
    def __init__(self, runner, profile, file_path, progress):
        super().__init__()
        self.runner = runner
        self.profile = profile
        self.file_path = file_path
        self.progress = progress

    def run(self):
        cmd = self.runner.build_command(self.profile, self.file_path)
        success, log = self.runner.run(cmd, self.progress)
        self.progress.finished.emit(self.file_path, success, log)
```

---

## 5 依赖管理与测试策略

* 所有核心模块必须保持 **UI 无感知**，从而允许在无图形环境下通过 pytest 运行单元测试并在 CI 中覆盖率度量。
* 使用 **依赖注入**（简单参数传递即可）将 `PandocRunner`、`ProfileRepository` 等注入到 `ConversionService`，避免硬编码单例。
* 对外 shell 执行需用 `subprocess` 的 `check_output` 封装，并在测试中用 `pytest-mock` 模拟 Pandoc，可避免 CI 机器安装 Pandoc。

---

## 6 后续工作分解

1. **落地目录骨架**：在 Git 仓库初始化上述目录，并用 `__init__.py` 与空类占位。
2. **实现 `PandocRunner`**：优先保证 CLI 端到端转换成功，再接入 UI。
3. **建立首批单元测试**：覆盖 `pandoc_detector.detect()`、`pandoc_runner.build_command()` 等纯函数。
4. **搭建 CI**：用 GitHub Actions 配置三平台测试与构建；先跳过 Nuitka，确保语法与测试通过。