import sys
import os
from PyQt5.QtWidgets import QApplication
from tunnel_manager import TunnelManager

if __name__ == '__main__':
    app = QApplication(sys.argv)
    config_path = os.path.join(os.path.dirname(__file__), 'ssh_tunnel_config.json')
    win = TunnelManager(config_path)
    win.show()
    sys.exit(app.exec_())