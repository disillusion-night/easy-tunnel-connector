import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QMessageBox,
    QSystemTrayIcon, QMenu, QAction, QStyle, QDialog, QApplication, QProgressDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QIcon
from src.utils.ssh_tunnel import create_ssh_tunnel
from src.dialogs import ConfigDialog, AddTunnelDialog
from src.traffic import TunnelTraffic
import threading

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'settings.json')

class TunnelManager(QWidget):
    def __init__(self, config_path):
        super().__init__()
        self.setWindowTitle('SSH Tunnel 管理器')
        self.resize(500, 350)
        self.config_path = config_path
        self.tunnels = []
        self.configs = self.load_config()
        self.settings = self.load_settings()
        if 'hide_to_tray_notify' not in self.settings:
            self.settings['hide_to_tray_notify'] = True
        if 'debug_print' not in self.settings:
            self.settings['debug_print'] = False
        self.traffic_stats = []  # 与self.tunnels一一对应
        self.timer = None
        self.init_ui()
        self.installEventFilter(self)

    def load_settings(self):
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'minimize_to_tray': True}

    def save_settings(self):
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def load_config(self):
        if not os.path.exists(self.config_path):
            QMessageBox.warning(self, '错误', f'未找到配置文件: {self.config_path}')
            return []
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_config(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.configs, f, ensure_ascii=False, indent=2)

    def init_ui(self):
        layout = QVBoxLayout()
        self.list = QListWidget()
        for conf in self.configs:
            self.list.addItem(conf.get('name', conf['ssh_host']))
        layout.addWidget(QLabel('可用SSH隧道配置:'))
        layout.addWidget(self.list)
        layout.addWidget(QLabel('本工具仅作为本地 SOCKS5 代理入口，适配 v2ray/浏览器等。'))
        # self.progress_bar = QProgressBar()
        # self.progress_bar.setRange(0, 0)
        # self.progress_bar.setVisible(False)
        # layout.addWidget(self.progress_bar)
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton('启动隧道')
        self.btn_stop = QPushButton('关闭选中隧道')
        self.btn_refresh = QPushButton('刷新配置')
        self.btn_config = QPushButton('配置')
        self.btn_add = QPushButton('+')
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_config)
        btn_layout.addWidget(self.btn_add)
        layout.addLayout(btn_layout)

        self.status_label = QLabel('当前无已连接隧道。')
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.btn_start.clicked.connect(self.start_tunnel)
        self.btn_stop.clicked.connect(self.stop_tunnel)
        self.btn_refresh.clicked.connect(self.refresh_config)
        self.btn_config.clicked.connect(self.open_config_dialog)
        self.btn_add.clicked.connect(self.open_add_dialog)

        # System Tray Icon
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon.fromTheme('network-server')
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        tray_menu = QMenu(self)
        restore_action = QAction('显示主界面', self)
        quit_action = QAction('退出', self)
        tray_menu.addAction(restore_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        restore_action.triggered.connect(self.showNormal)
        quit_action.triggered.connect(self.exit_app)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

        self.setup_list_context_menu()

    def open_config_dialog(self):
        dlg = ConfigDialog(self, self.settings.get('minimize_to_tray', True), self.settings.get('hide_to_tray_notify', True), self.settings.get('debug_print', False))
        if dlg.exec_() == QDialog.Accepted:
            self.settings['minimize_to_tray'] = dlg.get_minimize_to_tray()
            self.settings['hide_to_tray_notify'] = dlg.get_hide_to_tray_notify()
            self.settings['debug_print'] = dlg.get_debug_print()
            self.save_settings()

    def open_add_dialog(self):
        dlg = AddTunnelDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            try:
                conf = dlg.get_config()
                self.configs.append(conf)
                self.save_config()
                self.list.addItem(conf.get('name', conf['ssh_host']))
                QMessageBox.information(self, '成功', '新增配置已保存！')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'保存失败: {e}')

    def open_edit_dialog(self, idx):
        conf = self.configs[idx]
        dlg = AddTunnelDialog(self)
        dlg.name.setText(conf.get('name', ''))
        dlg.local_bind_port.setText(str(conf.get('local_bind_port', 1080)))
        dlg.ssh_host.setText(conf.get('ssh_host', ''))
        dlg.ssh_port.setText(str(conf.get('ssh_port', 22)))
        dlg.ssh_username.setText(conf.get('ssh_username', ''))
        dlg.ssh_password.setText(conf.get('ssh_password', ''))
        if dlg.exec_() == QDialog.Accepted:
            try:
                new_conf = dlg.get_config()
                self.configs[idx] = new_conf
                self.save_config()
                self.list.item(idx).setText(new_conf.get('name', new_conf['ssh_host']))
                QMessageBox.information(self, '成功', '配置已更新！')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'保存失败: {e}')

    def setup_list_context_menu(self):
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_list_context_menu)

    def show_list_context_menu(self, pos):
        idx = self.list.currentRow()
        if idx < 0 or idx >= len(self.configs):
            return
        menu = QMenu(self)
        edit_action = QAction('编辑', self)
        delete_action = QAction('删除', self)
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        edit_action.triggered.connect(lambda: self.open_edit_dialog(idx))
        delete_action.triggered.connect(lambda: self.delete_tunnel(idx))
        menu.exec_(self.list.mapToGlobal(pos))

    def delete_tunnel(self, idx):
        reply = QMessageBox.question(self, '确认删除', f'确定要删除“{self.configs[idx].get("name", self.configs[idx]["ssh_host"])}”吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.configs.pop(idx)
            self.save_config()
            self.list.takeItem(idx)
            QMessageBox.information(self, '成功', '配置已删除！')

    def start_tunnel(self):
        import traceback  # 添加traceback用于详细异常输出
        idx = self.list.currentRow()
        if idx < 0 or idx >= len(self.configs):
            QMessageBox.warning(self, '提示', '请先选择一个配置')
            return
        conf = self.configs[idx]
        def do_connect():
            if self.settings.get('debug_print', False):
                print(f"[DEBUG] 尝试连接: host={conf['ssh_host']} port={conf.get('ssh_port', 22)} user={conf['ssh_username']} 本地端口={conf.get('local_bind_port', 1080)} key={conf.get('ssh_key_path', '')}")
            try:
                print(f"[DEBUG] 连接参数: {conf}")
                server = create_ssh_tunnel(
                    conf['ssh_host'],
                    conf.get('ssh_port', 22),
                    conf['ssh_username'],
                    conf['ssh_password'],
                    local_bind_address=('127.0.0.1', conf.get('local_bind_port', 1080)),
                    ssh_key_path=conf.get('ssh_key_path', None)
                )
                print(f"[DEBUG] create_ssh_tunnel 返回: {server}")
                def on_success():
                    print(f"[DEBUG] 隧道建立成功: {server}")
                    self.tunnels.append({'name': conf.get('name', conf['ssh_host']), 'server': server})
                    self.traffic_stats.append(TunnelTraffic(server))
                    self.update_status()
                    if not self.timer:
                        self.timer = self.startTimer(1000)
                    QMessageBox.information(self, '成功', f"隧道已建立，本地端口: {server.local_bind_port}")
                QApplication.instance().postEvent(self, _FunctionEvent(on_success))
            except Exception as e:
                print(f"[ERROR] 隧道建立失败: {e}")
                print(traceback.format_exc())
                def on_fail():
                    QMessageBox.critical(self, '错误', f'隧道建立失败: {e}\n{traceback.format_exc()[:1000]}')
                QApplication.instance().postEvent(self, _FunctionEvent(on_fail))
        threading.Thread(target=do_connect, daemon=True).start()

    def stop_tunnel(self):
        idx = self.list.currentRow()
        if idx < 0 or idx >= len(self.tunnels):
            QMessageBox.warning(self, '提示', '请先选择一个已连接的隧道')
            return
        try:
            self.tunnels[idx]['server'].stop()
            self.traffic_stats[idx].stop()
            name = self.tunnels[idx]['name']
            self.tunnels.pop(idx)
            self.traffic_stats.pop(idx)
            self.update_status()
            if not self.tunnels and self.timer:
                self.killTimer(self.timer)
                self.timer = None
            QMessageBox.information(self, '成功', f'隧道 {name} 已关闭。')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'关闭失败: {e}')

    def timerEvent(self, event):
        self.update_status()

    def update_status(self):
        if not self.tunnels:
            self.status_label.setText('当前无已连接隧道。')
        else:
            status = '已连接隧道:\n'
            for i, t in enumerate(self.tunnels):
                traffic = self.traffic_stats[i]
                status += (f"{t['name']} 本地端口: {t['server'].local_bind_port} "
                           f"↑{self._format_bytes(traffic.up_speed)}/s ↓{self._format_bytes(traffic.down_speed)}/s "
                           f"总↑{self._format_bytes(traffic.up)} 总↓{self._format_bytes(traffic.down)}\n")
            self.status_label.setText(status)

    def _format_bytes(self, num):
        for unit in ['B','KB','MB','GB']:
            if abs(num) < 1024.0:
                return f"{num:.1f}{unit}"
            num /= 1024.0
        return f"{num:.1f}TB"

    def closeEvent(self, event):
        if self.settings.get('minimize_to_tray', True):
            event.ignore()
            self.hide()
            if self.settings.get('hide_to_tray_notify', True):
                self.tray_icon.showMessage('SSH Tunnel 管理器', '程序已最小化到托盘，可右键托盘图标退出。', QSystemTrayIcon.Information, 2000)
        else:
            self.exit_app()

    def exit_app(self):
        for t in self.tunnels:
            t['server'].stop()
        for traffic in getattr(self, 'traffic_stats', []):
            traffic.stop()
        QApplication.quit()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()

    def refresh_config(self):
        self.configs = self.load_config()
        self.list.clear()
        for conf in self.configs:
            self.list.addItem(conf.get('name', conf['ssh_host']))
        QMessageBox.information(self, '刷新', '配置已刷新！')

    def eventFilter(self, obj, event):
        if event.type() == _FunctionEvent.EVENT_TYPE:
            event.execute()
            return True
        return super().eventFilter(obj, event)

class _FunctionEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    def __init__(self, fn):
        super().__init__(self.EVENT_TYPE)
        self.fn = fn

    def execute(self):
        self.fn()
