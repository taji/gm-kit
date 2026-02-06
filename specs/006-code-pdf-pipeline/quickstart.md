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
