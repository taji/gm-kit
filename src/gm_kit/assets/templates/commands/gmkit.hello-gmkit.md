---
title: "GM-Kit Hello Command"
description: "Generate a greeting file using the hello-gmkit template and say-hello script."
---

## Goal
- Accept a user-provided greeting message.
- Determine the next greeting sequence number (e.g., greeting01.md).
- Invoke the generated script with `--greeting` and `--sequence` arguments.
- Write the rendered greeting to `greetings/greetingXX.md` and echo it to stdout.

## Steps for the Agent
1. Read existing files in `greetings/` to find the highest `greetingNN.md` number; default to `01` if none exist.
2. Increment the sequence number for the next file.
3. Call the platform-specific script:
   - Bash: `.gmkit/scripts/bash/say-hello.sh --greeting "<message>" --sequence <NN>`
   - PowerShell: `.gmkit/scripts/powershell/say-hello.ps1 -Greeting "<message>" -Sequence <NN>`
4. Confirm the script output and the file `greetings/greetingNN.md` were created.
5. Reply with the greeting content and the file path.

## Arguments
- `greeting` (required): The user’s greeting text.
- `sequence` (auto): Computed by scanning `greetings/`.

## Output
- File: `greetings/greetingNN.md`
- Content: Rendered from `templates/hello-gmkit-template.md` with greeting + sequence number.
