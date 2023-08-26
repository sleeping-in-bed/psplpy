import os
import subprocess
import other_util


def set_clash_for_windows_network_proxy():
    host = '127.0.0.1'
    port = 7890
    other_util.run_command(f"gsettings set org.gnome.system.proxy mode 'manual'", show_output=True)
    for protocol in ['http', 'https', 'ftp', 'socks']:
        other_util.run_command(f"gsettings set org.gnome.system.proxy.{protocol} host '{host}'", show_output=True)
        other_util.run_command(f"gsettings set org.gnome.system.proxy.{protocol} port '{port}'", show_output=True)


