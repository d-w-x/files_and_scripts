#/bin/env bash
systemctl kill --kill-who=main --signal=SIGUSR2 systemd-journald.service
journalctl --vacuum-size=1M
journalctl --vacuum-size=500M
