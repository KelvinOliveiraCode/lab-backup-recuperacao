<div align="center">

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/tests-48%20passing-brightgreen?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/coverage-90%25-green-brightgreen?style=flat-square" alt="Coverage">
  <img src="https://img.shields.io/badge/deps-zero%20deps-brightgreen?style=flat-square" alt="Deps">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows-blue?style=flat-square" alt="Windows">
</p>

</div>

# lab-backup-recuperacao

Backup local com ciclo completo testado: detecta mudança por hash, comprime,
aplica rotina GFS, restaura e confere byte a byte.

Local backup with a tested full cycle: hash-based change detection,
compression, GFS schedule, restore with byte-level verification.

> **Nada aqui é real.** Os 500 arquivos são inventados, e nenhum caminho de
> sistema é tocado. Tudo acontece em pastas do projeto.

## O que é

Quinhentos arquivos fictícios, backup incremental por SHA-256, compressão zip
e lzma, rotina GFS (7 diários, 4 semanais, 12 mensais) com expiração, e
restauração que confere hash contra a origem. O teste do ciclo inteiro roda
num comando.

## Por que foi feito

Backup só vale se a restauração foi testada. Um arquivo salvo em outro lugar
é um inventário, não um backup — e backup não testado é ilusão. Demonstrar o
ciclo completo, com a prova, é raro e valorizado.

## Como rodar

```powershell
python -m backuplab executar --origem dados/arquivos-originais --destino saida/
```

```
arquivos na origem: 500
novos: 500  modificados: 0
copiados: 500  taxa: 55.38%
```

```powershell
python -m backuplab restaurar --backup saida/arquivos --destino restaurado/ --verificar --origem dados/arquivos-originais
```

```
restaurados e conferidos
todos os arquivos conferem com a origem
```

A segunda execução sem mudança não copia nada — incremental de verdade, não
backup completo com outro nome.

Instalação:

```powershell
pip install -e ".[dev]"
```

## Por que hash e não data

Data de modificação é metadado do sistema de arquivos, não do conteúdo. Cópia
entre discos, fuso errado, restauração — qualquer um muda a data sem mudar um
byte. Hash muda se e somente se o conteúdo mudar. O teste `test_toque_sem_
mudanca_nao_copia` prova: data futura, mesmo conteúdo, nada copiado.

## GFS: 7-4-12

O recente com densidade, o antigo com esparsidade: 7 diários cobrem a semana,
4 semanais cobrem o mês, 12 mensais cobrem o ano. Nome fora do padrão cai em
diário — janela curta, para o desconhecido expirar rápido.

## O que aprendi

- **Restaurar comprimido sem descomprimir não é restaurar.** A primeira versão
  guardava `.zip` e devolvia `.zip`. O ciclo só fechou com descompressão na
  volta.
- **Pacote corrompido não pode parar a restauração.** Ele é copiado como está
  e a verificação acusa depois. Parar no meio deixa o destino pela metade sem
  dizer o que falta.
- **Manifesto não é dado.** Restaurá-lo junto criava um arquivo que nunca
  existiu na origem, e a verificação acusava o próprio instrumento.
- **Segunda execução zerada é o teste do incremental.** Se copia sem mudança,
  não é incremental.
- **Taxa de 55% mente.** É a média de texto que comprime bem com binário que
  não comprime. Uma taxa só diz algo por tipo de conteúdo.

## Testes

```powershell
python -m pytest -v
```

48 testes, 90% de cobertura. Cobrem detecção por hash, round-trip nos três
tipos, verificação com 1 byte trocado, restauração com pacote corrompido, GFS,
CLI e o portão de encoding.

```powershell
python tools/verificar_aceite.py     # 500 identicos + GFS + incremental
python tools/verificar_encoding.py   # nenhum caractere corrompido
python tools/gerar_exemplo.py        # regenera o exemplo deterministico
```

## Limitações

- **Lê tudo, toda vez.** Hash exige leitura completa; para terabytes seria
  preciso outra estratégia. O módulo diz isso em vez de fingir que escala.
- **Sem backup remoto.** Tudo é pasta local; não há envio, criptografia em
  trânsito nem autenticação.
- **Sem backup aberto.** Arquivo em uso pode ser copiado pela metade; não há
  snapshot nem trava.
- **GFS por nome, não por data.** A classificação lê o nome do backup; data
  real não entra.
- **Compressão por arquivo.** Sem deduplicação entre arquivos, sem delta.

## Licença

MIT.

---

## English

Local backup with a tested full cycle: 500 fictitious files, SHA-256
incremental detection, zip/lzma compression, GFS schedule (7-4-12) with
expiry, restore with hash verification.

Hash, not mtime: copy preserves dates, timezones lie, content doesn't. A
second run with no changes copies nothing. Corrupt archives don't stop the
restore — verification flags them after.

### Tests

48 tests, 90% coverage.

```powershell
python -m pytest -v
python tools/verificar_aceite.py
python tools/verificar_encoding.py
python tools/gerar_exemplo.py
```

### Limitations

Reads everything every time; no remote backup; no open-file handling; GFS by
name; per-file compression, no dedup.

### License

MIT.