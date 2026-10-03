# Por que backup não testado é ilusão

A crença mais comum sobre backup é também a mais perigosa: um arquivo salvo em outro lugar é um backup. Isso é uma falácia de confiança. Um backup é uma cópia que nunca foi aberta. Sem restauração testada, o que se tem é um inventário de arquivos cujo conteúdo pode estar truncado, corrompido em bits, incompleto ou mal formatado.

Falhas silenciosas são a regra, não a exceção. Mídia degradada que aceita escrita sem relatar erro. Snapshot capturado no meio de uma transação, consistente no momento do clique mas ilegível depois. Script que supostamente copia e, por falta de permissão no diretório de destino, grava um arquivo vazio e encerra com sucesso. Repasse para fita ou para objeto que perde pacotes sem avisar. Em todos esses casos o log diz "concluído", e é exatamente o caso que importa. O único teste válido de um backup é tentar restaurá-lo, porque backup existe para um evento futuro que ninguém controla, e a única evidência disponível antes desse evento é a restauração já realizada com sucesso.

## Como montar um teste automatizado: ciclo completo com hash antes e depois

O ciclo começa antes de qualquer cópia, estabelecendo uma referência de hash do conjunto original. Em vez de depender de data de modificação ou tamanho — metadados que mudam sem alterar conteúdo e que coincidem por acaso —, calcula-se o SHA-256 de cada arquivo e armazena-se em um manifesto. Esse é exatamente o padrão do módulo `src/backuplab/incremental.py`: suas docstrings explicam que "hash muda se e somente se o conteúdo mudar" e que data "mente", por isso o hash é a única medida honesta de mudança.

O ciclo tem quatro etapas. Primeiro, a referência: varrer a origem, calcular o SHA-256 de cada arquivo e salvar os pares caminho-hash em um manifesto. Segundo, executar o fluxo de backup real, para o destino produtivo, sem pular etapas. Terceiro, restaurar para um local isolado e temporário, nunca sobre a origem, e recalcular o SHA-256 de cada arquivo restaurado com a mesma função usada no backup. Quarto, comparar: a lista de caminhos deve ser idêntica, a contagem de arquivos igual, e cada hash individual deve bater com o registrado no manifesto.

Qualquer arquivo novo, modificado ou removido detectado automaticamente — a rotina devolve três tuplas — deve ser registrado em relatório e tratado. Se o hash de um mesmo caminho mudou, o conteúdo restaurado não é o esperado. Se um caminho falta, houve perda. Se há caminho a mais, há lixo ou restauração parcial. O teste deve rodar como tarefa agendada, seu resultado de falha deve encerrar a pipeline e o relatório deve conter, para cada arquivo, o caminho, o hash esperado e o hash real, de modo que uma discrepância seja imediatamente acionável.

## O que o SHA-256 prova e o que não prova

O SHA-256 prova integridade de bytes: o conteúdo restaurado é bit a bit idêntico ao que existia no instante da referência. Colisão prática é impraticável, o que torna o hash um laço de confiança honesto e barato. Mas o teste não prova que os dados estavam semanticamente corretos antes da cópia — um backup fiel de um dado já corrompido é tecnicamente perfeito e inútil. Também não prova que a aplicação consegue abrir os arquivos, que as permissões e metadados foram preservados, ou que o mesmo software rodará daqui a dez anos em outra plataforma.

Mais importante: o teste não prova que o destino sobreviveu ao longo do tempo. O mesmo teste precisa ser repetido, porque degradação é um processo, não um evento. Um disco que hoje devolve o hash correto pode, meses depois, recuar um bloco silenciosamente. Esse é um ajuste de humildade: o SHA-256 valida a cópia naquele instante, não a garantia perpétua dela.

## Frequência honesta: quanto custa testar e quanto custa não testar

O custo de testar é dominado por I/O: ler cada arquivo para hash, copiar para o destino e restaurar para um local temporário. Para quantidades modestas o custo é irrelevante; para terabytes o próprio módulo `incremental.py` admite que outra estratégia seria necessária e evita fingir que escala. Nesse caso, a rotação GFS 7-4-12 — sete diários, quatro semanais, doze mensais — orienta com que periodicidade cada cópia é testada, e o teste se torna uma política sobre camadas de retenção, não um evento único.

O custo de não testar aparece apenas na recuperação real: tempo de parada estendido além do RTO, dados perdidos além do RPO, reconstrução manual de bancos e logs, e o custo de negócio associado, que cresce com o tempo até o teste. A frequência honesta não é anual nem "quando der". Cada nível da rotação GFS 7-4-12 tem um preço de teste diferente, e a política honesta é testar com a frequência que o custo do teste permite sem comprometer o RPO, sabendo que testar cedo é barato e testar tarde é proibitivamente caro.
