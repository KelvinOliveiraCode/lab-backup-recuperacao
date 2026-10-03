# Política de retenção

Sete diários, quatro semanais, doze mensais. A rotina guarda o recente com
densidade e o antigo com esparsidade, porque recuperar "ontem" é comum e
recuperar "há oito meses" é raro mas crítico.

## Por que GFS e não "os últimos N"

"Guardar os últimos 30 backups" parece simples e falha no caso que importa:
trinta backups diários cobrem um mês. Um arquivo corrompido há dois meses
está fora de todos os trinta — e ninguém percebe até precisar dele.

A rotina GFS resolve com três janelas independentes. O diário cobre a semana,
o semanal cobre o mês, o mensal cobre o ano. Cada janela expira sozinha, e
nenhuma decisão sobre o diário afeta o mensal.

| Janela | Retém | Cobre |
|---|---|---|
| Diário | 7 | a semana |
| Semanal | 4 | o mês |
| Mensal | 12 | o ano |

## Classificação pelo nome

O backup carrega a data no nome, e o tipo vem do prefixo: `diario-2026-10-01`,
`semanal-2026-W40`, `mensal-2026-10`. Nome fora do padrão cai em diário — a
janela mais curta, para que um backup desconhecido expire rápido em vez de
ocupar espaço para sempre.

## O que expira, e quando

Com 10 diários, 7 ficam e 3 saem — sempre os mais antigos. A expiração não
pergunta se o backup "ainda serve": janela vencida sai. Guardar por apego é
como a rotina vira acumulação, e acumulação sem critério é o oposto de backup.

## O que esta política não resolve

Ela não diz **o quê** guardar, só **quanto tempo**. Decidir que um diretório
entra no backup é decisão de dono de dado, não de rotina. E ela não verifica
conteúdo: um backup corrompido expira no prazo como qualquer outro — por isso
a verificação de integridade é outro módulo, e os dois não se misturam.
