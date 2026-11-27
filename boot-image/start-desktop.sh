#!/bin/sh

# startx runs this client in the active text-console session.
openbox-session >/tmp/calculanatoros-openbox.log 2>&1 &
window_manager_pid=$!
python3 "$HOME/CalculanatorOS_Desktop.py"
desktop_status=$?
kill "$window_manager_pid" 2>/dev/null || true
wait "$window_manager_pid" 2>/dev/null || true
exit "$desktop_status"
