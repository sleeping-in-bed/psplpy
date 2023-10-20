import other_util


def set_clash_for_windows_network_proxy():
    host = '127.0.0.1'
    port = 7890
    other_util.run_command(f"gsettings set org.gnome.system.proxy mode 'manual'")
    for protocol in ['http', 'https', 'ftp', 'socks']:
        other_util.run_command(f"gsettings set org.gnome.system.proxy.{protocol} host '{host}'")
        other_util.run_command(f"gsettings set org.gnome.system.proxy.{protocol} port '{port}'")


def touch(file_path: str):
    other_util.run_command(f'touch {file_path}')


def echo(s: str):
    other_util.run_command(f'echo {s}')


def create_desktop_shortcut(name: str, exec_path: str, icon_path: str = None):
    file_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={name}
Exec="{exec_path}"
"""
    if icon_path:
        file_content += f'Icon="{icon_path}"'
    echo(fr'{file_content} >> ~/Desktop/{name}.desktop')

def automatic_screen_lock(time: int = 0) -> str:
    command = f'gsettings set org.gnome.desktop.session idle-delay {time}'
    return other_util.run_command(command)


def apt_get(name: str) -> str:
    command = f"apt-get install {name}"
    return other_util.run_command(command)


def dpkg(file_path: str) -> str:
    command = f"dpkg -i {file_path}"
    return other_util.run_command(command)


if __name__ == '__main__':
    automatic_screen_lock()