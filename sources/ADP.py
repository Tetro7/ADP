import re
import shlex
import subprocess
import sys
import threading

import sublime
import sublime_plugin

SETTINGS_FILE = "ADP.sublime-settings"
PANEL_NAME = "ADP"


def plugin_loaded():
    print("ADP: plugin loaded OK (Python 3.8)")


class AdpDeployCommand(sublime_plugin.WindowCommand):

    def run(self, device_index=None):
        if device_index is None:
            return

        devices = sublime.load_settings(SETTINGS_FILE).get("devices", [])

        if not devices:
            sublime.error_message(
                "ADP: Нет настроенных устройств.\n\n"
                "Выполните команду «ADP: Edit Settings» и добавьте устройства."
            )
            return

        if not 0 <= device_index < len(devices):
            return

        output_path = self._project_output_path()
        if not output_path:
            sublime.error_message(
                "ADP: output_path не задан в .sublime-project.\n\n"
                'Добавьте в секцию "settings" вашего .sublime-project:\n'
                '  "adp": {\n'
                '    "output_path": "\\\\\\\\wsl.localhost\\\\Distro\\\\path\\\\to\\\\build"\n'
                '  }'
            )
            return

        self._deploy(devices[device_index], output_path)

    def input(self, args):
        if "device_index" not in args:
            return DeviceListInputHandler()
        return None

    def _project_output_path(self):
        data = self.window.project_data() or {}
        return data.get("settings", {}).get("adp", {}).get("output_path")

    def _deploy(self, device, output_path):
        panel = self.window.create_output_panel(PANEL_NAME)
        self.window.run_command("show_panel", {"panel": f"output.{PANEL_NAME}"})

        address = device.get("address", "")
        username = device.get("username", "")
        remote_path = device.get("remote_path", "")
        extra_opts = sublime.load_settings(SETTINGS_FILE).get("scp_options", [])

        cmd = _build_scp_cmd(output_path, username, address, remote_path, extra_opts)

        def log(text):
            sublime.set_timeout(
                lambda: panel.run_command("append", {"characters": text, "scroll_to_end": True}),
                0,
            )

        log(f"ADP: Деплой на {username}@{address}\n")
        log(f"Источник : {output_path}\n")
        log(f"Команда  : {' '.join(cmd)}\n\n")

        threading.Thread(target=_run_scp, args=(cmd, address, log), daemon=True).start()


def _build_scp_cmd(output_path, username, address, remote_path, extra_opts):
    norm = output_path.replace("\\", "/")
    destination = f"{username}@{address}:{remote_path}"

    m = re.match(r"^//wsl(?:\.localhost|\$)/([^/]+)/(.+)$", norm, re.IGNORECASE)
    if m:
        distro = m.group(1)
        linux_path = "/" + m.group(2).rstrip("/")
        opts_str = " ".join(shlex.quote(o) for o in extra_opts)
        bash_cmd = "scp -r {} {}/* {}".format(opts_str, shlex.quote(linux_path), shlex.quote(destination))
        return ["wsl", "-d", distro, "bash", "-c", bash_cmd]

    source = norm.rstrip("/") + "/*"
    return ["scp", "-r"] + extra_opts + [source, destination]


def _run_scp(cmd, address, log):
    try:
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kwargs
        )
        for line in proc.stdout:
            log(line)
        proc.wait()

        if proc.returncode == 0:
            log(f"\nADP: Деплой на {address} завершён успешно.\n")
            sublime.set_timeout(
                lambda: sublime.status_message(f"ADP: Deploy to {address} OK"), 0
            )
        else:
            log(f"\nADP: Ошибка деплоя на {address} (код выхода {proc.returncode}).\n")
    except FileNotFoundError:
        log("\nADP: Команда 'scp' или 'wsl' не найдена в PATH.\n"
            "Убедитесь, что установлен OpenSSH-клиент и/или WSL.\n")
    except Exception as ex:
        log(f"\nADP: Неожиданная ошибка: {ex}\n")


class DeviceListInputHandler(sublime_plugin.ListInputHandler):

    def name(self):
        return "device_index"

    def placeholder(self):
        return "Выберите целевое устройство"

    def list_items(self):
        devices = sublime.load_settings(SETTINGS_FILE).get("devices", [])
        items = []
        for i, dev in enumerate(devices):
            address = dev.get("address", "?")
            username = dev.get("username", "")
            name = dev.get("name", "")
            label = f"ADP: {address}" + (f"  —  {name}" if name else "")
            annotation = f"{username}@{address}"
            items.append(sublime.ListInputItem(
                text=label,
                value=i,
                annotation=annotation,
                kind=(sublime.KIND_ID_AMBIGUOUS, "D", "Device"),
            ))
        return items


class AdpEditSettingsCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        sublime.run_command(
            "edit_settings",
            {
                "base_file": "${packages}/ADP/ADP.sublime-settings",
                "default": (
                    "// ADP — Another Deploy Plugin — User Settings\n"
                    "{\n"
                    "\t\"devices\": [\n"
                    "\t\t{\n"
                    "\t\t\t\"name\": \"My Device\",\n"
                    "\t\t\t\"address\": \"192.168.1.100\",\n"
                    "\t\t\t\"username\": \"user\",\n"
                    "\t\t\t\"remote_path\": \"/home/user/deploy/\"\n"
                    "\t\t}\n"
                    "\t]\n"
                    "}\n"
                ),
            },
        )
