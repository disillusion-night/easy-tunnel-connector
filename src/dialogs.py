from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QLineEdit, QFormLayout

class ConfigDialog(QDialog):
    def __init__(self, parent=None, minimize_to_tray=True, hide_to_tray_notify=True, debug_print=False):
        super().__init__(parent)
        self.setWindowTitle('配置')
        self.resize(300, 140)
        layout = QVBoxLayout()
        self.chk_minimize = QCheckBox('最小化时隐藏到托盘')
        self.chk_minimize.setChecked(minimize_to_tray)
        self.chk_notify = QCheckBox('最小化到托盘时弹出通知')
        self.chk_notify.setChecked(hide_to_tray_notify)
        self.chk_debug = QCheckBox('打印调试信息到控制台')
        self.chk_debug.setChecked(debug_print)
        layout.addWidget(self.chk_minimize)
        layout.addWidget(self.chk_notify)
        layout.addWidget(self.chk_debug)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        self.setLayout(layout)

    def get_minimize_to_tray(self):
        return self.chk_minimize.isChecked()

    def get_hide_to_tray_notify(self):
        return self.chk_notify.isChecked()

    def get_debug_print(self):
        return self.chk_debug.isChecked()

class AddTunnelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('新增SSH隧道配置')
        self.resize(350, 250)
        layout = QFormLayout()
        self.name = QLineEdit()
        self.local_bind_port = QLineEdit('1080')
        self.ssh_host = QLineEdit()
        self.ssh_port = QLineEdit('22')
        self.ssh_username = QLineEdit()
        self.ssh_password = QLineEdit()
        self.ssh_password.setEchoMode(QLineEdit.Password)
        layout.addRow('隧道名称', self.name)
        layout.addRow('本地端口', self.local_bind_port)
        layout.addRow('远程主机地址', self.ssh_host)
        layout.addRow('远程主机端口', self.ssh_port)
        layout.addRow('用户名', self.ssh_username)
        layout.addRow('密码', self.ssh_password)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        self.setLayout(layout)

    def get_config(self):
        return {
            'name': self.name.text().strip(),
            'local_bind_port': int(self.local_bind_port.text().strip()),
            'ssh_host': self.ssh_host.text().strip(),
            'ssh_port': int(self.ssh_port.text().strip()),
            'ssh_username': self.ssh_username.text().strip(),
            'ssh_password': self.ssh_password.text(),
        }
