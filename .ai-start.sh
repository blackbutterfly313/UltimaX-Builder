#!/data/data/com.termux/files/usr/bin/env bash
# Start local AI stack (llama.cpp server + web_termux.py) and drop into zsh

# Start llama server (if binary at ~/llama.cpp/server and model exists)
LLAMA_BIN="$HOME/llama.cpp/server"
LLAMA_MODEL="${HOME}/models/qwen1.5/qwen1_5-1_8b-chat.Q4_K_M.gguf"
if [ -f "$LLAMA_BIN" ] && [ -f "$LLAMA_MODEL" ]; then
  (cd ~/llama.cpp && nohup "$LLAMA_BIN" --model "$LLAMA_MODEL" --host 127.0.0.1 --port 8081 --threads 4 --ctx-size 2048 >/tmp/llama_server.log 2>&1 &)
  echo "llama server started on http://127.0.0.1:8081 (logs: /tmp/llama_server.log)"
else
  echo "llama binary or model not found; build llama.cpp first."
fi

# Start CoPilot web UI (Flask app). Expects ~/copilot/web_termux.py
if [ -f "$HOME/copilot/web_termux.py" ]; then
  (cd "$HOME/copilot" && nohup python web_termux.py >/tmp/copilot_ui.log 2>&1 &)
  echo "CoPilot Web UI started on http://127.0.0.1:8082 (logs: /tmp/copilot_ui.log)"
else
  echo "copilot web_termux.py not found in ~/copilot"
fi

# Start code-server if installed
if [ -x "$HOME/bin/code-server-start" ]; then
  "$HOME/bin/code-server-start"
  echo "code-server started (127.0.0.1:8080)"
fi

# Finally, open interactive zsh
exec zsh
