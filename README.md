# ADP
ADP is another deploy plugin for sublime text 4

Настройка

  1. Устройства — Preferences > Package Settings > ADP > Settings

  {
      "devices": [
          {
              "name": "Taquasar Dev",
              "address": "172.17.42.213",
              "username": "taquasar",
              "remote_path": "/home/taquasar/upd/"
          }
      ]
  }

  2. Путь к сборке — в .sublime-project

  {
      "folders": [...],
      "settings": {
          "adp": {
              "output_path": "\\\\wsl.localhost\\Debian9-13\\tmp\\abs\\_snmp_\\snmp\\linux-main"
          }
      }
  }

  3. Использование

  Ctrl+Shift+P → введите adp → выберите ADP: Deploy → выберите устройство из списка.

  Результат деплоя выводится в нижнюю панель ADP.

  ---
  Как работает

  - WSL-пути (\\wsl.localhost\Distro\...) — плагин автоматически определяет дистрибутив и запускает wsl
   -d Distro scp -r /linux/path/. user@host:/remote/, чтобы SCP работал с нативными Linux-путями и
  SSH-ключами внутри WSL.
  - Обычные пути — вызывает системный scp -r напрямую (требует OpenSSH).
  - Деплой выполняется в фоновом потоке, не блокируя редактор.
  - Дополнительные опции scp (например ["-o", "StrictHostKeyChecking=no"]) задаются в scp_options.
