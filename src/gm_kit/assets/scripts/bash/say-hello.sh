#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --greeting \"Hello\" --sequence 01 --templates-dir <path> --output-dir <path>"
}

greeting=""
sequence=""
templates_dir=""
output_dir=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --greeting)
      greeting="$2"
      shift 2
      ;;
    --sequence)
      sequence="$2"
      shift 2
      ;;
    --templates-dir)
      templates_dir="$2"
      shift 2
      ;;
    --output-dir)
      output_dir="$2"
      shift 2
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$greeting" || -z "$sequence" || -z "$templates_dir" || -z "$output_dir" ]]; then
  usage
  exit 1
fi

template_path="${templates_dir%/}/hello-gmkit-template.md"
output_path="${output_dir%/}/greetings/greeting${sequence}.md"

mkdir -p "$(dirname "$output_path")"

rendered_content=$(sed \
  -e "s/{{ *greeting *}}/$greeting/g" \
  -e "s/{{ *sequence *}}/$sequence/g" \
  "$template_path")

echo "$rendered_content" > "$output_path"
echo "$rendered_content"
