# Launch CalculanatorOS automatically on the first text console.
if [[ "$(tty 2>/dev/null)" == "/dev/tty1" ]] && [[ -f "$HOME/CalculanatorOS.py" ]]; then
    exec python3 "$HOME/CalculanatorOS.py"
fi
