import sys
import os
import socket
import threading
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from src.tunnel_manager import TunnelManager

SINGLE_INSTANCE_PORT = 54321  # 可自定义端口

def is_another_instance_running():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
        s.listen(1)
        return False, s  # 没有其他实例，返回socket对象用于后续保持
    except OSError:
        return True, None

def start_wakeup_listener(app, win, instance_socket):
    # 在主实例中启动线程监听唤醒消息
    def listener():
        while True:
            try:
                conn, _ = instance_socket.accept()
                msg = conn.recv(1024)
                if msg == b'WAKEUP':
                    # 在主线程前置窗口
                    def bring_to_front():
                        try:
                            # 先用PyQt5 API恢复窗口
                            win.showNormal()
                            win.raise_()
                            win.activateWindow()
                            # 再用win32gui补充（如有需要）
                            try:
                                import win32gui, win32con
                                hwnd = int(win.winId())
                                win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
                                win32gui.SetForegroundWindow(hwnd)
                                win32gui.BringWindowToTop(hwnd)
                                win32gui.SetActiveWindow(hwnd)
                            except Exception as e:
                                print(f'win32gui唤醒补充失败: {e}')
                        except Exception as e:
                            print(f'窗口唤醒失败: {e}')
                    # 用QTimer.singleShot保证主线程安全
                    QTimer.singleShot(0, bring_to_front)
                conn.close()
            except Exception as e:
                print(f'唤醒监听异常: {e}')
                break
    t = threading.Thread(target=listener, daemon=True)
    t.start()

if __name__ == '__main__':
    running, instance_socket = is_another_instance_running()
    if running:
        # 尝试激活已运行的窗口（仅限Windows，需pywin32支持，否则只弹提示）
        try:
            import win32gui, win32con, win32api
            import time
            def enumHandler(hwnd, lParam):
                if win32gui.IsWindow(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if 'SSH Tunnel 管理器' in title:
                        # 先还原窗口（包括托盘/最小化/隐藏）
                        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
                        # 多次尝试前置，兼容托盘和最小化
                        for _ in range(3):
                            win32gui.SetForegroundWindow(hwnd)
                            time.sleep(0.1)
                        # 额外激活窗口
                        win32gui.BringWindowToTop(hwnd)
                        win32gui.SetActiveWindow(hwnd)
            win32gui.EnumWindows(enumHandler, None)
        except Exception as e:
            print(f'窗口唤醒失败: {e}')
        # 修正：先创建 QApplication 实例再弹窗，防止卡死
        app = QApplication(sys.argv)
        QMessageBox.information(None, '已在运行', '已有一个SSH Tunnel 管理器正在运行，本窗口将退出。')
        sys.exit(0)
    app = QApplication(sys.argv)
    config_path = os.path.join(os.path.dirname(__file__), 'src', 'ssh_tunnel_config.json')
    win = TunnelManager(config_path)
    win.show()
    # 启动唤醒监听线程
    start_wakeup_listener(app, win, instance_socket)
    sys.exit(app.exec_())
