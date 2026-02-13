# Quickstart: PDF Code Pipeline (E4-07a)

## Run full pipeline

```bash
gmkit pdf-convert <pdf-path> --output <output-dir>
```

## Run a specific phase

```bash
gmkit pdf-convert --phase <phase-number> <output-dir>
```

## Resume a conversion

```bash
gmkit pdf-convert --resume <output-dir>
```

## Check status

```bash
gmkit pdf-convert --status <output-dir>
```

## Diagnostics bundle

```bash
gmkit pdf-convert <pdf-path> --output <output-dir> --diagnostics
```

## Custom callout detection

Provide a callout config file to identify GM callout regions by text boundaries:

```bash
gmkit pdf-convert <pdf-path> --output <output-dir> --gm-callout-config-file callout_config.json
```

If omitted, an empty `callout_config.json` is created in the output directory during pre-flight. You can edit it before proceeding (choose "R" at the confirmation prompt).

Example `callout_config.json`:
```json
[
  {"start_text": "Keeper's Note:", "end_text": "End of Note", "label": "callout_gm"}
]
```

## Custom GM keywords

Add custom keywords for GM callout detection (in addition to built-in defaults):

```bash
gmkit pdf-convert <pdf-path> --output <output-dir> --gm-keyword "Keeper" --gm-keyword "Referee"
```
