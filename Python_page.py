import json
import os
import platform
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class PythonInterpreter:
    """保存 Python 解释器信息的数据结构。"""
    executable: str
    display_name: str


class CommandWorker(QThread):
    """通用后台任务线程，用于执行耗时命令并回传结果。"""
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, runner, *args, **kwargs):
        """初始化任务执行器及其参数。"""
        super().__init__()
        self._runner = runner
        self._args = args
        self._kwargs = kwargs

    def run(self):
        """在线程中执行目标任务并通过信号上报成功或失败。"""
        try:
            result = self._runner(*self._args, **self._kwargs)
            self.succeeded.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class PackageInstallConfirmDialog(QDialog):
    """安装前确认弹窗，展示名称、版本、描述，避免误装。"""
    def __init__(self, name: str, version: str, summary: str, parent=None):
        """构建安装确认对话框。"""
        super().__init__(parent)
        self.setWindowTitle('确认安装库')
        self.setModal(True)

        layout = QFormLayout(self)
        layout.addRow('名称：', QLabel(name))
        layout.addRow('版本：', QLabel(version or '未指定'))

        summary_label = QLabel(summary or '暂无描述')
        summary_label.setWordWrap(True)
        layout.addRow('描述：', summary_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class PackageDetailsDialog(QDialog):
    """第三方库详情弹窗，用于展示完整元信息。"""
    def __init__(self, name: str, version: str, summary: str, home_page: str, parent=None):
        """构建详情对话框并填充核心字段。"""
        super().__init__(parent)
        self.setWindowTitle(f'库详情：{name}')
        self.setModal(True)

        layout = QFormLayout(self)
        layout.addRow('名称：', QLabel(name))
        layout.addRow('版本：', QLabel(version))

        summary_label = QLabel(summary or '暂无描述')
        summary_label.setWordWrap(True)
        layout.addRow('描述：', summary_label)

        homepage_label = QLabel(home_page or '暂无主页信息')
        homepage_label.setWordWrap(True)
        layout.addRow('主页：', homepage_label)

        button = QDialogButtonBox(QDialogButtonBox.Close)
        button.rejected.connect(self.reject)
        button.accepted.connect(self.accept)
        layout.addRow(button)


class PythonPage(QWidget):
    """Python 版本与第三方库管理页面。"""
    def __init__(self, parent=None):
        """初始化页面状态、UI 结构与解释器列表。"""
        super().__init__(parent=parent)
        self.interpreters: list[PythonInterpreter] = []
        self.packages_cache: dict[str, list[dict]] = {}
        self.current_worker: CommandWorker | None = None

        self._build_ui()
        self._load_interpreters()

    def _build_ui(self):
        """创建页面控件并绑定交互信号。"""
        main_layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.python_combo = QComboBox()
        self.python_combo.currentIndexChanged.connect(self.on_python_changed)
        self.refresh_button = QPushButton('刷新库列表')
        self.refresh_button.clicked.connect(self.refresh_current_packages)

        top_layout.addWidget(QLabel('Python 版本：'))
        top_layout.addWidget(self.python_combo, 1)
        top_layout.addWidget(self.refresh_button)
        main_layout.addLayout(top_layout)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索已安装库，或输入库名后点击“搜索/安装库”')
        self.search_input.textChanged.connect(self._filter_table)
        self.search_install_button = QPushButton('搜索/安装库')
        self.search_install_button.clicked.connect(self.on_search_install)

        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.search_install_button)
        main_layout.addLayout(search_layout)

        self.package_table = QTableWidget(0, 3)
        self.package_table.setHorizontalHeaderLabels(['名称', '版本', '描述'])
        self.package_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.package_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.package_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.package_table.customContextMenuRequested.connect(self.on_context_menu)
        self.package_table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.package_table)

        self.status_label = QLabel('正在初始化...')
        main_layout.addWidget(self.status_label)

    def _set_busy(self, busy: bool, text: str | None = None):
        """统一切换页面忙碌状态，避免并发操作造成冲突。"""
        self.refresh_button.setEnabled(not busy)
        self.search_install_button.setEnabled(not busy)
        self.python_combo.setEnabled(not busy)
        if text:
            self.status_label.setText(text)

    def _load_interpreters(self):
        """加载解释器列表并刷新当前选中解释器的包数据。"""
        self.interpreters = self._detect_python_interpreters()
        self.python_combo.clear()

        for interpreter in self.interpreters:
            self.python_combo.addItem(interpreter.display_name, interpreter.executable)

        if not self.interpreters:
            self.status_label.setText('未检测到 Python 解释器')
            return

        self.status_label.setText(f'已检测到 {len(self.interpreters)} 个 Python 解释器')
        self.on_python_changed(self.python_combo.currentIndex())

    def _detect_python_interpreters(self) -> list[PythonInterpreter]:
        """探测系统中可用的 Python 解释器并去重。"""
        candidates = set()

        # 常见命令名优先检测，避免全盘扫描带来性能问题
        command_names = [
            'python', 'python3', 'python3.12', 'python3.11', 'python3.10', 'python3.9', 'python3.8',
            'python3.7', 'python3.6', 'py'
        ]

        for cmd in command_names:
            found = shutil.which(cmd)
            if found:
                candidates.add(found)

        if platform.system().lower().startswith('win'):
            py_launcher = shutil.which('py')
            if py_launcher:
                try:
                    out = subprocess.check_output([py_launcher, '-0p'], text=True, stderr=subprocess.STDOUT)
                    for line in out.splitlines():
                        m = re.search(r'([A-Za-z]:\\[^\s]+python\.exe)', line)
                        if m:
                            candidates.add(m.group(1))
                except Exception:
                    pass
        else:
            for folder in ['/usr/bin', '/usr/local/bin', str(Path.home() / '.pyenv' / 'versions')]:
                if not os.path.isdir(folder):
                    continue
                try:
                    for name in os.listdir(folder):
                        if re.fullmatch(r'python(\d+(\.\d+)*)?', name):
                            candidate = os.path.join(folder, name)
                            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                                candidates.add(candidate)
                except OSError:
                    continue

        interpreters: list[PythonInterpreter] = []
        for exe in sorted(candidates):
            try:
                version = subprocess.check_output([exe, '--version'], text=True, stderr=subprocess.STDOUT).strip()
                interpreters.append(PythonInterpreter(executable=exe, display_name=f'{version} ({exe})'))
            except Exception:
                continue

        # 使用解释器路径去重，防止软链接重复
        unique = {}
        for item in interpreters:
            unique[os.path.realpath(item.executable)] = item
        return list(unique.values())

    def on_python_changed(self, index: int):
        """切换解释器时优先读取缓存，否则重新查询包列表。"""
        if index < 0 or index >= len(self.interpreters):
            return
        exe = self.interpreters[index].executable
        if exe in self.packages_cache:
            self._render_packages(self.packages_cache[exe])
            self.status_label.setText('已加载缓存的库列表')
            return
        self._query_packages(exe)

    def refresh_current_packages(self):
        """手动刷新当前解释器的第三方库列表。"""
        index = self.python_combo.currentIndex()
        if index < 0:
            return
        exe = self.interpreters[index].executable
        self.packages_cache.pop(exe, None)
        self._query_packages(exe)

    def _query_packages(self, exe: str):
        """异步触发包列表查询。"""
        self._start_worker(self._list_packages, exe, busy_text='正在读取已安装库...')

    def _list_packages(self, exe: str) -> list[dict]:
        """在目标解释器中批量读取安装包信息（名称/版本/描述）。"""
        script = (
            "import json\n"
            "from importlib import metadata as m\n"
            "rows=[]\n"
            "for d in m.distributions():\n"
            "    name=d.metadata.get('Name') or ''\n"
            "    if not name:\n"
            "        continue\n"
            "    rows.append({\n"
            "        'name': name,\n"
            "        'version': d.version or '',\n"
            "        'summary': d.metadata.get('Summary') or '暂无描述'\n"
            "    })\n"
            "rows.sort(key=lambda x: x['name'].lower())\n"
            "print(json.dumps(rows, ensure_ascii=False))\n"
        )
        output = subprocess.check_output([exe, '-c', script], text=True, stderr=subprocess.STDOUT, timeout=120)
        return json.loads(output)

    def _render_packages(self, packages: list[dict]):
        """将包列表渲染到表格控件。"""
        self.package_table.setRowCount(len(packages))
        for row, pkg in enumerate(packages):
            self.package_table.setItem(row, 0, QTableWidgetItem(pkg.get('name', '')))
            self.package_table.setItem(row, 1, QTableWidgetItem(pkg.get('version', '')))
            self.package_table.setItem(row, 2, QTableWidgetItem(pkg.get('summary', '')))
        self.package_table.resizeColumnsToContents()
        self._filter_table(self.search_input.text())

    def _filter_table(self, keyword: str):
        """根据关键词过滤表格行，支持名称和描述匹配。"""
        keyword = keyword.strip().lower()
        for row in range(self.package_table.rowCount()):
            name_item = self.package_table.item(row, 0)
            summary_item = self.package_table.item(row, 2)
            content = f"{name_item.text() if name_item else ''} {summary_item.text() if summary_item else ''}".lower()
            self.package_table.setRowHidden(row, bool(keyword) and keyword not in content)

    def on_context_menu(self, pos):
        """处理右键菜单，支持更新、卸载、查看详情。"""
        item = self.package_table.itemAt(pos)
        if not item:
            return
        row = item.row()
        name = self.package_table.item(row, 0).text()

        menu = QMenu(self)
        act_update = menu.addAction('更新库')
        act_uninstall = menu.addAction('卸载库')
        act_detail = menu.addAction('查看详情')

        selected = menu.exec_(self.package_table.viewport().mapToGlobal(pos))
        if selected == act_update:
            self._update_package(name)
        elif selected == act_uninstall:
            self._uninstall_package(name)
        elif selected == act_detail:
            self._show_package_details(name)

    def _current_exe(self) -> str | None:
        """获取当前选中的解释器可执行路径。"""
        idx = self.python_combo.currentIndex()
        if idx < 0 or idx >= len(self.interpreters):
            return None
        return self.interpreters[idx].executable

    def _update_package(self, name: str):
        """更新指定第三方库到最新版本。"""
        exe = self._current_exe()
        if not exe:
            return
        self._start_worker(self._run_pip_command, exe, ['install', '--upgrade', name], busy_text=f'正在更新 {name}...')

    def _uninstall_package(self, name: str):
        """卸载指定第三方库，并进行二次确认。"""
        exe = self._current_exe()
        if not exe:
            return
        reply = QMessageBox.question(self, '确认卸载', f'确认卸载 {name} 吗？')
        if reply != QMessageBox.Yes:
            return
        self._start_worker(self._run_pip_command, exe, ['uninstall', '-y', name], busy_text=f'正在卸载 {name}...')

    def _show_package_details(self, name: str):
        """查询并弹窗展示第三方库详情。"""
        exe = self._current_exe()
        if not exe:
            return
        try:
            out = subprocess.check_output([exe, '-m', 'pip', 'show', name], text=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            QMessageBox.critical(self, '查看详情失败', exc.output)
            return

        info = {'Name': name, 'Version': '', 'Summary': '', 'Home-page': ''}
        for line in out.splitlines():
            if ':' not in line:
                continue
            k, v = line.split(':', 1)
            info[k.strip()] = v.strip()

        dialog = PackageDetailsDialog(
            info.get('Name', name),
            info.get('Version', ''),
            info.get('Summary', ''),
            info.get('Home-page', ''),
            self,
        )
        dialog.exec_()

    def on_search_install(self):
        """根据输入库名查询安装候选信息并进入确认流程。"""
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.information(self, '提示', '请输入库名')
            return

        exe = self._current_exe()
        if not exe:
            return

        self._start_worker(self._query_and_install_candidate, exe, keyword, busy_text='正在搜索库信息...')

    def _query_and_install_candidate(self, exe: str, name: str) -> dict:
        """从 PyPI 查询安装候选的名称、版本和描述信息。"""
        del exe  # 保留参数以便后续扩展离线索引查询
        safe_name = urllib.parse.quote(name)
        url = f'https://pypi.org/pypi/{safe_name}/json'

        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                payload = json.loads(resp.read().decode('utf-8'))
            info = payload.get('info', {})
            return {
                'name': info.get('name') or name,
                'version': info.get('version') or '',
                'summary': info.get('summary') or '暂无描述',
            }
        except urllib.error.HTTPError:
            raise RuntimeError('未在 PyPI 中找到该库，请检查拼写')
        except Exception:
            return {'name': name, 'version': '', 'summary': '网络异常，仍可继续安装，请确认库名无误。'}

    def _run_pip_command(self, exe: str, pip_args: list[str]) -> str:
        """在目标解释器中执行 pip 命令并返回输出。"""
        result = subprocess.check_output([exe, '-m', 'pip', *pip_args], text=True, stderr=subprocess.STDOUT, timeout=300)
        return result

    def _start_worker(self, runner, *args, busy_text: str = '处理中...'):
        """启动后台任务线程，统一处理并发保护与状态控制。"""
        if self.current_worker is not None and self.current_worker.isRunning():
            QMessageBox.warning(self, '提示', '当前已有任务在执行，请稍后')
            return

        self._set_busy(True, busy_text)
        worker = CommandWorker(runner, *args)
        self.current_worker = worker
        worker.succeeded.connect(self._on_worker_success)
        worker.failed.connect(self._on_worker_failed)
        worker.start()

    def _on_worker_success(self, result):
        """处理后台任务成功结果，并按结果类型分发后续动作。"""
        self._set_busy(False)
        self.current_worker = None

        if isinstance(result, list):
            exe = self._current_exe()
            if exe:
                self.packages_cache[exe] = result
            self._render_packages(result)
            self.status_label.setText(f'已加载 {len(result)} 个第三方库')
            return

        if isinstance(result, dict) and {'name', 'version', 'summary'}.issubset(result.keys()):
            dialog = PackageInstallConfirmDialog(result['name'], result['version'], result['summary'], self)
            if dialog.exec_() == QDialog.Accepted:
                exe = self._current_exe()
                if exe:
                    self._start_worker(
                        self._run_pip_command,
                        exe,
                        ['install', f"{result['name']}=={result['version']}"] if result['version'] else ['install', result['name']],
                        busy_text=f"正在安装 {result['name']}...",
                    )
                    return
            self.status_label.setText('已取消安装')
            return

        self.status_label.setText('操作完成，正在刷新库列表')
        self.refresh_current_packages()

    def _on_worker_failed(self, error: str):
        """处理后台任务失败结果并提示用户。"""
        self._set_busy(False, '操作失败')
        self.current_worker = None
        QMessageBox.critical(self, '操作失败', error)
