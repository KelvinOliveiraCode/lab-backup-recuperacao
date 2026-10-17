# lab-backup-recuperacao

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/tests-48%20passing-brightgreen?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/coverage-90%25-green?style=flat-square" alt="Coverage">
  <img src="https://img.shields.io/badge/deps-zero%20deps-brightgreen?style=flat-square" alt="Dependencies">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
</p>

Local backup with full tested cycle: SHA-256 incremental detection, zip/lzma compression, GFS routine (7-4-12), and restore with byte-by-byte verification.

## Problem / Why it exists

A file copied to another folder is an inventory, not a backup. A backup only counts if the restore has been tested, and a backup that restores differently from the original is worse than no backup: it occupies disk space and gives a false sense of security. This project demonstrates the full cycle with proof: run the backup, restore it, and check the hash of each file against the source.

## What it does

The `backuplab` package exposes two commands via the CLI.

`executar` runs the incremental backup:
- scans the source recursively and computes SHA-256 for each file in 64 KiB blocks
- compares with the saved manifest: new files (missing path) and modified files (same path, different hash) enter the copy; date and size are not used to decide
- compresses each file into ZIP (DEFLATE) or LZMA and writes to `<destino>/arquivos/<caminho>.<metodo>`
- rewrites the manifest to `<destino>/manifesto.json`
- prints file count and compression ratio

`restaurar` brings files back:
- decompresses `.zip` and `.lzma` back to the name without extension
- ignores `manifesto.json` (it is backup metadata, not source data)
- copies corrupted packages as-is so verification flags the divergence later, instead of interrupting the restore halfway
- with `--verificar --origem`, compares the SHA-256 of each restored file against the source and exits with code 1 if there is a divergence

On a second run with no changes, nothing is copied: real incremental, not a full backup under another name.

## Stack

- Python 3.10+
- Standard library only: `hashlib`, `zipfile`, `lzma`, `json`, `pathlib`, `shutil`, `argparse`, `dataclasses`. Zero runtime dependencies (`dependencies = []` in `pyproject.toml`).
- Development: `pytest>=7.4`, `pytest-cov>=4.1`
- Formats: ZIP/DEFLATE and LZMA, one package per file, no deduplication between files

## How it works

1. **Scan**: `incremental.varrer` reads all source files, sorts by relative path, and computes SHA-256 for each.
2. **Compare**: `Manifesto.mudancas` returns new, modified, and removed files comparing the current state with the saved manifest. The hash changes if and only if content changes.
3. **Copy and compress**: each new or modified file is read, compressed with the chosen method (`zip` by default, `lzma` optional via `--metodo`), and written to `<destino>/arquivos/<caminho>.<metodo>`.
4. **Manifest**: the full state is saved to `<destino>/manifesto.json`.
5. **Restore**: `restauracao.restaurar` decompresses each package back to the original name; corrupted packages are copied intact.
6. **Verify**: `verificacao.comparar` checks the hash catalogs of source and restore; a different or missing file in the restore fails the verdict.

## How to run

Editable install, with development dependencies:

```
pip install -e ".[dev]"
```

After installing, the `backuplab` command is also available (`backuplab = "backuplab.cli:main"`).

First backup:

```
python -m backuplab executar --origem dados/arquivos-originais --destino saida/
```

Typical output of the first run:

```
arquivos na origem: 500
novos: 500  modificados: 0
copiados: 500  taxa: 0.55
```

The ratio value depends on the interpreter's zlib version (text compresses well, binary does not).

Second run, no changes in the source:

```
python -m backuplab executar --origem dados/arquivos-originais --destino saida/
```

```
arquivos na origem: 500
novos: 0  modificados: 0
copiados: 0  taxa: 0.00
```

Restore with verification against the source:

```
python -m backuplab restaurar --backup saida/arquivos --destino restaurado/ --verificar --origem dados/arquivos-originais
```

```
restaurados e conferidos
todos os arquivos conferem com a origem
```

CLI exit codes: 0 ok, 1 restore divergence, 2 error (source or backup missing).

Tests:

```
python -m pytest -v
```

Result: 48 passing tests, coverage 90% (requires 70%).

Support tools:

```
python tools/verificar_aceite.py     # 500 identical + GFS + incremental
python tools/verificar_encoding.py   # no corrupted character
python tools/gerar_exemplo.py        # regenerates the deterministic example
```

## Project structure

```
lab-backup-recuperacao/
  src/backuplab/        package: cli, incremental, compressao, restauracao, verificacao, politica
  tests/                48 tests: cli, compressao, incremental, restauracao, verificacao
  docs/                 politica-de-retencao.md, teste-de-restauracao.md
  exemplos/             relatorio-backup.md (real output copied by gerar_exemplo.py)
  tools/                gerar_exemplo.py, gerar_arquivos.py, verificar_aceite.py, verificar_encoding.py
  dados/arquivos-originais/  500 fictitious files (doc, data, bin) used in tests
  pyproject.toml        build, entry point, pytest, coverage
  requirements.txt      development dependencies
  LICENSE               MIT
```

## Trade-offs and decisions

- Hash instead of date: modification date is filesystem metadata and changes without changing a byte (copy between disks, time zone, restore). SHA-256 changes if and only if content changes. The cost is reading the whole file at each scan.
- One package per file: simple and isolates corruption (one bad package does not invalidate others), no deduplication or delta between files.
- Corrupted package does not interrupt restore: it is copied as-is and verification flags it later. Stopping halfway leaves the destination incomplete without saying what is missing.
- Manifest is not data: it is not restored together, otherwise it would create a file that never existed in the source and verification would flag the measuring instrument itself.
- Compression per file: each file is an independent package; restoring one does not require reading the others.
- GFS by name, not by date: the type comes from the directory prefix (`diario-`, `semanal-`, `mensal-`). A name outside the pattern becomes daily, the shortest window, so unknown backups expire quickly instead of occupying space forever.
- GFS retention 7-4-12: 7 dailies cover the week, 4 weeklies cover the month, 12 monthlies cover the year; each window expires on its own.

## Known limitations

- Reads everything, every time: the hash requires reading each file in full; for terabytes another strategy would be needed. The module says this instead of pretending to scale.
- No remote backup: local folders only; no sending, encryption in transit, or authentication.
- No open-file backup: a file in use may be copied halfway; there is no snapshot or lock.
- No deduplication between files: compression is per file, no delta.
- GFS by name: classification reads the backup name; the real date is not used.
- Fictitious data: the 500 files in `dados/` are invented for lab testing; no system path is touched.

## License

MIT.

## Author

Kelvin
