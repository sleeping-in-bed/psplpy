import other_util


def set_clash_for_windows_network_proxy():
    host = '127.0.0.1'
    port = 7890
    other_util.run_command(f"gsettings set org.gnome.system.proxy mode 'manual'", show_output=True)
    for protocol in ['http', 'https', 'ftp', 'socks']:
        other_util.run_command(f"gsettings set org.gnome.system.proxy.{protocol} host '{host}'", show_output=True)
        other_util.run_command(f"gsettings set org.gnome.system.proxy.{protocol} port '{port}'", show_output=True)


def automatic_screen_lock(time: int = 0) -> str:
    command = f'gsettings set org.gnome.desktop.session idle-delay {time}'
    return other_util.run_command(command, show_output=True)



def apt_get(name: str) -> str:
    command = f"apt-get install {name}"
    return other_util.run_command(command, show_output=True)


def dpkg(file_path: str) -> str:
    command = f"dpkg -i {file_path}"
    return other_util.run_command(command, show_output=True)


if __name__ == '__main__':
    automatic_screen_lock()