# agents.registry.sh
# Record format (TAB-delimited):
# name<TAB>detect_cmd<TAB>install_cmd<TAB>verify_cmd<TAB>verify_args<TAB>uninstall_cmd<TAB>purge_paths_csv

AGENTS=(
  $'claude\tclaude\tnpm install -g @anthropic-ai/claude-code\tclaude\t--version\tnpm uninstall -g @anthropic-ai/claude-code\t'"$HOME"$'/.claude,'"${HOME}"$'/.config/claude,'"${HOME}"$'/.cache/claude,'"${HOME}"$'/.local/share/claude'

  $'codex-cli\tcodex\tnpm install -g @openai/codex\tcodex\t--version\tnpm uninstall -g @openai/codex\t'"$HOME"$'/.config/codex,'"${HOME}"$'/.cache/codex,'"${HOME}"$'/.local/share/codex'

  $'gemini\tgemini\tnpm install -g @google/gemini-cli\tgemini\t--version\tnpm uninstall -g @google/gemini-cli\t'"$HOME"$'/.config/gemini,'"${HOME}"$'/.cache/gemini,'"${HOME}"$'/.local/share/gemini'

  $'qwen\tqwen\tnpm install -g @qwen-code/qwen-code\tqwen\t--version\tnpm uninstall -g @qwen-code/qwen-code\t'"$HOME"$'/.config/qwen,'"${HOME}"$'/.cache/qwen,'"${HOME}"$'/.local/share/qwen'
)
