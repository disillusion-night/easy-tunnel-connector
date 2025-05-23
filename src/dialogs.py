from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QLineEdit, QFormLayout, QFileDialog, QMessageBox, QComboBox, QPushButton, QHBoxLayout
import paramiko
import os

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
        self.resize(400, 300)
        layout = QFormLayout()
        self.name = QLineEdit()
        self.local_bind_port = QLineEdit('1080')
        self.ssh_host = QLineEdit()
        self.ssh_port = QLineEdit('22')
        self.ssh_username = QLineEdit()
        self.ssh_password = QLineEdit()
        self.ssh_password.setEchoMode(QLineEdit.Password)
        self.ssh_key_path = QLineEdit()
        # 新增：密钥类型选择和生成按钮
        key_layout = QHBoxLayout()
        self.key_type = QComboBox()
        self.key_type.addItems(['ed25519', 'rsa'])
        self.btn_gen_key = QPushButton('生成密钥对')
        self.btn_gen_key.clicked.connect(self.generate_keypair)
        key_layout.addWidget(self.ssh_key_path)
        key_layout.addWidget(self.key_type)
        key_layout.addWidget(self.btn_gen_key)
        layout.addRow('隧道名称', self.name)
        layout.addRow('本地端口', self.local_bind_port)
        layout.addRow('远程主机地址', self.ssh_host)
        layout.addRow('远程主机端口', self.ssh_port)
        layout.addRow('用户名', self.ssh_username)
        layout.addRow('密码', self.ssh_password)
        layout.addRow('私钥路径(可选)', key_layout)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        self.setLayout(layout)

    def generate_keypair(self):
        key_type = self.key_type.currentText()
        save_path, _ = QFileDialog.getSaveFileName(self, '保存私钥', '', '私钥文件 (*)')
        if not save_path:
            return
        try:
            if key_type == 'ed25519':
                # paramiko.Ed25519Key 没有 generate 方法，需用 cryptography 生成
                from cryptography.hazmat.primitives.asymmetric import ed25519
                from cryptography.hazmat.primitives import serialization
                private_key = ed25519.Ed25519PrivateKey.generate()
                # 保存私钥
                with open(save_path, 'wb') as f:
                    f.write(private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
                # 保存公钥
                pub_path = save_path + '.pub'
                with open(pub_path, 'wb') as f:
                    f.write(private_key.public_key().public_bytes(
                        encoding=serialization.Encoding.OpenSSH,
                        format=serialization.PublicFormat.OpenSSH
                    ))
                self.ssh_key_path.setText(save_path)
                QMessageBox.information(self, '成功', f'密钥对已生成!\n私钥: {save_path}\n公钥: {pub_path}\n\n请勿泄露私钥，并将公钥提供给你的管理员。')
                return
            elif key_type == 'rsa':
                key = paramiko.RSAKey.generate(2048)
                key.write_private_key_file(save_path)
                pub_path = save_path + '.pub'
                with open(pub_path, 'w') as f:
                    f.write(f'{key.get_name()} {key.get_base64()}\n')
                self.ssh_key_path.setText(save_path)
                QMessageBox.information(self, '成功', f'密钥对已生成!\n私钥: {save_path}\n公钥: {pub_path}\n\n请勿泄露私钥，并将公钥提供给你的管理员。')
                return
        except Exception as e:
            QMessageBox.critical(self, '错误', f'密钥生成失败: {e}')

    def get_config(self):
        return {
            'name': self.name.text().strip(),
            'local_bind_port': int(self.local_bind_port.text().strip()),
            'ssh_host': self.ssh_host.text().strip(),
            'ssh_port': int(self.ssh_port.text().strip()),
            'ssh_username': self.ssh_username.text().strip(),
            'ssh_password': self.ssh_password.text(),
            'ssh_key_path': self.ssh_key_path.text().strip(),
        }
