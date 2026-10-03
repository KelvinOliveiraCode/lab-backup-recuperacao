# Relatorio de backup

Saida real dos comandos, copiada sem edicao por
`tools/gerar_exemplo.py`. Por isso o exemplo serve como prova do
comportamento em vez de descricao dele.

```powershell
python -m backuplab executar --origem dados/arquivos-originais --destino saida/
```

```
[codigo de saida: 0]
arquivos na origem: 500
novos: 500  modificados: 0
copiados: 500  taxa: 55.38%
```

```powershell
python -m backuplab restaurar --backup saida/arquivos --destino restaurado/ --verificar --origem dados/arquivos-originais
```

```
[codigo de saida: 0]
restaurados e conferidos
todos os arquivos conferem com a origem
```
