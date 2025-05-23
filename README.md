# easy-tunnel-connector

## 项目目的

本项目为用户提供一个本地 SOCKS5 代理工具，通过 SSH 隧道安全转发本地流量到远程服务器。适用于科学上网、安全代理、开发调试等场景。

- 本地监听 SOCKS5 端口（如 1080），可配置多个 SSH 隧道。
- 所有通过本地 SOCKS5 端口的流量将通过 SSH 动态端口转发到远程主机。
- 支持图形界面管理、托盘最小化、配置多隧道、流量统计等。

## 项目结构

```
README.md
requirements.txt
setup.py
main.py
src/
    dialogs.py
    settings.json
    ssh_tunnel_config.json
    traffic.py
    tunnel_manager.py
    utils/
        ssh_tunnel.py
```

## 使用说明

### 依赖安装

请先安装依赖：

```sh
pip install -r requirements.txt
```

### 启动程序

```sh
python main.py
```

### 配置说明

- 启动后可通过“新增”按钮添加 SSH 隧道配置。
- 每条隧道需填写本地端口、远程主机、端口、用户名、密码等信息。
- 启动隧道后，本地 SOCKS5 端口（如 1080）即可作为代理服务器使用。
- 可在浏览器、v2ray 等工具中设置 SOCKS5 代理为 127.0.0.1:1080（或你配置的端口）。
- 支持多隧道并发，支持流量实时统计。
- 支持最小化到托盘、托盘通知等。

### 注意事项

- 本工具仅作为本地 SOCKS5 代理入口，所有流量通过 SSH 隧道转发，安全可靠。
- 请确保远程主机 SSH 账号密码正确，且服务器允许端口转发。
- 若遇到端口占用、依赖缺失等问题，请检查配置和环境。

如有问题欢迎反馈与贡献！

## 贡献

欢迎任何形式的贡献！请提交 issue 或拉取请求。