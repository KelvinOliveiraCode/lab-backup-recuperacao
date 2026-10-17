# lab-backup-recuperacao

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/testes-48%20passing-brightgreen?style=flat-square" alt="Testes">
  <img src="https://img.shields.io/badge/cobertura-90%25-green?style=flat-square" alt="Cobertura">
  <img src="https://img.shields.io/badge/deps-zero%20deps-brightgreen?style=flat-square" alt="Dependencias">
  <img src="https://img.shields.io/badge/licenca-MIT-yellow?style=flat-square" alt="Licenca">
</p>

Backup local com ciclo completo testado: detecção incremental por SHA-256, compressão zip/lzma, rotina GFS (7-4-12) e restauração com verificação byte a byte.

## Problema / Por que existe

Um arquivo copiado para outra pasta é um inventário, não um backup. Backup só vale se a restauração foi testada, e um backup que restaura diferente do original é pior que nenhum backup: ocupa disco e dá falsa sensação de segurança. Este projeto demonstra o ciclo completo com a prova: executa o backup, restaura e confere o hash de cada arquivo contra a origem.

## O que faz

O pacote `backuplab` expõe dois comandos pela CLI.

`executar` faz o backup incremental:
- varre a origem recursivamente e calcula o SHA-256 de cada arquivo em blocos de 64 KiB
- compara com o manifesto salvo: arquivos novos (caminho ausente) e modificados (mesmo caminho, hash diferente) entram na cópia; data e tamanho não são usados para decidir
- comprime cada arquivo em ZIP (DEFLATE) ou LZMA e grava em `<destino>/arquivos/<caminho>.<metodo>`
- regrava o manifesto em `<destino>/manifesto.json`
- imprime contagem de arquivos e taxa de compressão

`restaurar` traz os arquivos de volta:
- descomprime `.zip` e `.lzma` de volta ao nome sem extensão
- ignora o `manifesto.json` (é metadado do backup, não dado da origem)
- copia pacotes corrompidos como estão para a verificação acusar a divergência depois, em vez de interromper a restauração na metade
- com `--verificar --origem`, compara o SHA-256 de cada arquivo restaurado com a origem e sai com código 1 se houver divergência

Na segunda execução sem mudanças, nada é copiado: incremental de verdade, não backup completo com outro nome.

## Stack

- Python 3.10+
- Biblioteca padrão apenas: `hashlib`, `zipfile`, `lzma`, `json`, `pathlib`, `shutil`, `argparse`, `dataclasses`. Zero dependências de execução (`dependencies = []` em `pyproject.toml`).
- Desenvolvimento: `pytest>=7.4`, `pytest-cov>=4.1`
- Formatos: ZIP/DEFLATE e LZMA, um pacote por arquivo, sem deduplicação entre arquivos

## Como funciona

1. **Varrer**: `incremental.varrer` lê todos os arquivos da origem, ordena por caminho relativo e calcula o SHA-256 de cada um.
2. **Comparar**: `Manifesto.mudancas` retorna novos, modificados e removidos comparando o estado atual com o manifesto salvo. O hash muda se e somente se o conteúdo mudar.
3. **Copiar e comprimir**: cada arquivo novo ou modificado é lido, comprimido com o método escolhido (`zip` padrão, `lzma` opcional via `--metodo`) e gravado em `<destino>/arquivos/<caminho>.<metodo>`.
4. **Manifesto**: o estado completo é salvo em `<destino>/manifesto.json`.
5. **Restaurar**: `restauracao.restaurar` descomprime cada pacote de volta ao nome original; pacotes corrompidos são copiados intactos.
6. **Verificar**: `verificacao.comparar` confere os catálogos de hash de origem e restauração; arquivo diferente ou ausente na restauração derruba o veredicto.

## Como rodar

Instalação em modo editável, com dependências de desenvolvimento:

```
pip install -e ".[dev]"
```

Após instalar, o comando `backuplab` também fica disponível (`backuplab = "backuplab.cli:main"`).

Primeiro backup:

```
python -m backuplab executar --origem dados/arquivos-originais --destino saida/
```

Saída típica da primeira execução:

```
arquivos na origem: 500
novos: 500  modificados: 0
copiados: 500  taxa: 0.55
```

O valor da taxa depende da versão do zlib do interpretador (texto comprime bem, binário não).

Segunda execução, sem mudanças na origem:

```
python -m backuplab executar --origem dados/arquivos-originais --destino saida/
```

```
arquivos na origem: 500
novos: 0  modificados: 0
copiados: 0  taxa: 0.00
```

Restaurar com verificação contra a origem:

```
python -m backuplab restaurar --backup saida/arquivos --destino restaurado/ --verificar --origem dados/arquivos-originais
```

```
restaurados e conferidos
todos os arquivos conferem com a origem
```

Códigos de saída da CLI: 0 ok, 1 divergência na restauração, 2 erro (origem ou backup ausente).

Testes:

```
python -m pytest -v
```

Resultado: 48 testes passando, cobertura 90% (exige 70%).

Ferramentas de apoio:

```
python tools/verificar_aceite.py     # 500 identicos + GFS + incremental
python tools/verificar_encoding.py   # nenhum caractere corrompido
python tools/gerar_exemplo.py        # regenera o exemplo deterministico
```

## Estrutura do projeto

```
lab-backup-recuperacao/
  src/backuplab/        pacote: cli, incremental, compressao, restauracao, verificacao, politica
  tests/                48 testes: cli, compressao, incremental, restauracao, verificacao
  docs/                 politica-de-retencao.md, teste-de-restauracao.md
  exemplos/             relatorio-backup.md (saida real copiada por gerar_exemplo.py)
  tools/                gerar_exemplo.py, gerar_arquivos.py, verificar_aceite.py, verificar_encoding.py
  dados/arquivos-originais/  500 arquivos ficticios (doc, dado, bin) usados nos testes
  pyproject.toml        build, ponto de entrada, pytest, coverage
  requirements.txt      dependencias de desenvolvimento
  LICENSE               MIT
```

## Trade-offs e decisões

- Hash em vez de data: a data de modificação é metadado do sistema de arquivos e muda sem mudar um byte (cópia entre discos, fuso horário, restauração). O SHA-256 muda se e somente se o conteúdo mudar. O custo é ler o arquivo inteiro a cada varredura.
- Um pacote por arquivo: simples e isola corrupção (um pacote ruim não invalida os outros), sem deduplicação nem delta entre arquivos.
- Pacote corrompido não interrompe a restauração: é copiado como está e a verificação acusa depois. Parar na metade deixa o destino incompleto sem dizer o que falta.
- Manifesto não é dado: não é restaurado junto, senão criaria um arquivo que nunca existiu na origem e a verificação acusaria o próprio instrumento de medida.
- Compressão por arquivo: cada arquivo é um pacote independente; restaurar um não exige ler os outros.
- GFS por nome, não por data: o tipo vem do prefixo do diretório (`diario-`, `semanal-`, `mensal-`). Nome fora do padrão vira diário, a janela mais curta, para backups desconhecidos expirarem rápido em vez de ocupar espaço para sempre.
- Retenção GFS 7-4-12: 7 diários cobrem a semana, 4 semanais cobrem o mês, 12 mensais cobrem o ano; cada janela expira sozinha.

## Limitações conhecidas

- Lê tudo, toda vez: o hash exige leitura completa de cada arquivo; para terabytes seria precisa outra estratégia. O módulo diz isso em vez de fingir que escala.
- Sem backup remoto: apenas pastas locais; não há envio, criptografia em trânsito nem autenticação.
- Sem backup aberto: arquivo em uso pode ser copiado pela metade; não há snapshot nem trava.
- Sem deduplicação entre arquivos: compressão é por arquivo, sem delta.
- GFS por nome: a classificação lê o nome do backup; a data real não entra.
- Dados fictícios: os 500 arquivos de `dados/` são inventados para teste de laboratório; nenhum caminho do sistema é tocado.

## Licença

MIT.

## Autor

Kelvin
