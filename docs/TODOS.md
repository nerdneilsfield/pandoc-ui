‍♂️: 我已根据你改用 **uv** 进行依赖与虚拟环境管理的要求，重新梳理了各阶段 TODO，并把“Poetry → uv”相应操作全部替换。下面是更新后的 **TODOs 文档**。所有要点都用完整句子撰写，并在每一阶段后列出明确产物与验收标准，便于跟踪进度。

🐍:

## 总览表

| 阶段      | 目标      | 关键产物                                                  | 主要验收点                                              |
| ------- | ------- | ----------------------------------------------------- | -------------------------------------------------- |
| Phase 0 | 环境与需求冻结 | `.gitignore`、`pyproject.toml`、`README.md` v0          | `uv pip sync` 后项目可安装并通过 `python -m pytest -q`（空测试） |
| Phase 1 | CLI 核心  | `infra/pandoc_runner.py`、`app/conversion_service.py`  | 在 CLI 下能批量把示例 `.md` 转成 `.html` 并打印日志               |
| Phase 2 | GUI MVP | `gui/main_window.ui`、`gui/main_window.py`             | 选择单文件→输出 PDF 成功；日志实时更新                             |
| Phase 3 | 批量支持    | `app/task_queue.py`、`app/folder_scanner.py`           | 100 个文件批量转换完成且 UI 不卡顿                              |
| Phase 4 | 快照与设置   | `app/profile_repository.py`、`infra/settings_store.py` | 快照保存→重启→加载后能复现参数                                   |
| Phase 5 | 打包发布    | Nuitka one-file 构建脚本、NSIS/PKG 模板                      | Windows/macOS/Linux 安装包均可一键运行                      |
| Phase 6 | 文档与质保   | `docs/`、`CHANGELOG.md` v1.0                           | 截图、FAQ、GitHub Actions 徽章全部就绪                       |

---

## Phase 0 — 环境与需求冻结

1. 你需要先在本机全局安装 **uv**，然后执行 `uv venv .venv` 创建隔离环境，以保证后续依赖一致性。
2. 你应在根目录运行 `uv pip install --editable .`，这样任何本地代码改动都会立即在 venv 中生效。
3. 你必须编写最小版本的 `pyproject.toml`，只声明运行依赖 `PySide6`、`uvicorn`（如需调试用 http 服务）以及打包依赖 `Nuitka`。
4. 你需要创建 `.gitignore`，并明确排除 `.venv/`、`dist/`、`build/`、`__pycache__/` 与 `*.qm` 临时文件。
5. 你应新建 `README.md`，至少包含一句话说明项目目标、一条 uv 安装指令和一张界面占位图。
6. 当你执行 `uv pip sync` 后，`python -c "import PySide6"` 不应报错，这将作为阶段验收标准。

---

## Phase 1 — CLI 核心

1. 你要实现 `infra/pandoc_detector.py` 中的 `detect()` 方法，它在 `$PATH` 和常见安装目录中定位 Pandoc 并缓存路径。
2. 你必须在 `infra/pandoc_runner.py` 中编写 `build_command(profile, input_path)`，生成最小可行的 Pandoc 命令列表。
3. 你需要实现 `app/conversion_service.py` 的 `convert_async()`，但在此阶段先用同步实现确保 CLI 演示可用。
4. 你应在 `tests/` 添加单元测试，模拟 Pandoc 路径并断言命令行字符串正确。
5. 你必须在根目录提供 `examples/article.md`，并在 `scripts/demo_cli.py` 中调用 Service 把该文件转出 HTML，输出日志到终端。
6. 阶段验收标准是：`python scripts/demo_cli.py examples/article.md -o out` 能成功生成 `article.html` 且返回码为 0。

---

## Phase 2 — GUI MVP

1. 你需要用 Qt Designer 画出 `main_window.ui`，包含文件选择框、目标格式下拉框、输出目录输入框和“开始转换”按钮。
2. 你必须在 `gui/main_window.py` 中加载 `.ui` 并发射 `start_conversion` 信号，携带文件路径与格式信息。
3. 你应在 `src/main.py` 初始化 `QApplication`、`ConversionService` 和 UI，然后把信号连接到 `convert_async`。
4. 为避免 GUI 卡顿，你可以暂时用 `QThread` 包装 Service 的同步实现，并用信号回传日志。
5. 当用户完成一次 Markdown→PDF 转换后，进度条应到 100 %，日志窗打印 “✔ completed”。
6. 阶段验收以“GUI 单文件转换成功且窗口可关闭无崩溃”为准。

---

## Phase 3 — 批量支持

1. 你必须实现 `app/task_queue.py`，基于 `QThreadPool` 限制并发数并维护 `active_jobs` 计数。
2. 你需要开发 `app/folder_scanner.py`，它递归枚举匹配扩展名的文件并返回列表给 Service。
3. 在 GUI 中，你应额外增加“文件夹模式”单选框与扩展名过滤输入框，切换模式后自动启用/禁用控件。
4. 你必须确保批量任务失败时只影响单个条目，并在日志窗用红色前景色高亮失败条目。
5. 阶段验收是：在示例 `examples/` 复制 100 份 Markdown 后，点击“批量转换”能全部输出 HTML，总用时相对 Pandoc 原生批量调用增加不超过 10 %。

---

## Phase 4 — 配置快照与设置

1. 你需要实现 `app/profile_repository.py`，它序列化所有 UI 参数为 JSON 并存储在用户目录下 `~/.pandoc_gui/profiles/`。
2. 你应实现 `infra/settings_store.py`，集中存储语言、默认输出路径与线程并发数；采用 `pydantic` 校验 schema。
3. GUI 必须新增“保存快照”与“加载快照”两个按钮，并在列表中显示已有快照名称与修改时间。
4. 你要在 UI 底部增加语言切换框，并在切换后即时刷新界面文本。
5. 阶段验收标准为：保存当前配置→关闭应用→重新打开→加载快照→所有表单字段与上次一致。

---

## Phase 5 — 打包发布

1. 你应编写 `scripts/build_windows.ps1`、`build_macos.sh` 和 `build_linux.sh`，它们执行 `uv pip sync --production` 后调用 Nuitka `--onefile` 打包。
2. 你必须在 Windows 使用 NSIS 创建安装器，并在安装阶段检测 Pandoc 是否存在；若无则弹出下载链接。
3. 你需要在 macOS 使用 `codesign`、`productbuild` 及 notarization 流程生成 `.pkg`。
4. `CI.yml` 中应新增三个 job：`build-win`、`build-macos`、`build-linux`，全部上传产物到 Release。
5. 阶段验收是：三个平台的安装包在干净虚拟机中双击即可运行 GUI 并通过单文件转换测试。

---

## Phase 6 — 文档与质量保障

1. 你必须在 `docs/` 下用 MkDocs 或 Sphinx 写完整安装指南、FAQ、命令行与 GUI 功能对照表。
2. 你需要在 `examples/quickstart_profile.json` 加入注释，供用户一键导入体验批量转换。
3. 你应更新 `CHANGELOG.md` 并添加 v1.0 发行笔记，列出主要功能、依赖与已知问题。
4. CI 中应增加 `uv pip audit` 步骤，自动检查依赖 CVE；同时拉取 `flake8`、`black`、`mypy` 质量门禁。
5. 阶段验收指标：GitHub README 显示构建通过徽章、文档截图、用户下载跳转链接全部可点击。
