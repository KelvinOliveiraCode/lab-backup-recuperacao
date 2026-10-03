"""Rotina GFS com expiracao automatica.

GFS schedule with automatic expiry.

Sete diarios, quatro semanais, doze mensais: a rotina guarda o recente com
densidade e o antigo com esparsidade, porque recuperar "ontem" e comum e
recuperar "ha oito meses" e raro mas critico.

## Classificacao por nome

O backup carrega a data no nome (`diario-2026-10-01`, `semanal-2026-W40`,
`mensal-2026-10`), e o tipo vem do prefixo. Nome fora do padrao cai em
diario: e a janela mais curta, entao um backup desconhecido expira rapido em
vez de ocupar espaco para sempre.
"""

from __future__ import annotations

from dataclasses import dataclass

DIARIO = "diario"
SEMANAL = "semanal"
MENSAL = "mensal"
TIPOS = (DIARIO, SEMANAL, MENSAL)


@dataclass(frozen=True)
class Janela:
    """Quanto reter de cada tipo.

    How much to retain of each type.

    Attributes:
        tipo: `diario`, `semanal` ou `mensal`.
        reter: Quantos backups manter.
    """

    tipo: str
    reter: int


PADRAO: tuple[Janela, ...] = (
    Janela(tipo=DIARIO, reter=7),
    Janela(tipo=SEMANAL, reter=4),
    Janela(tipo=MENSAL, reter=12),
)


def classificar(nome_do_backup: str) -> str:
    """O tipo de um backup pelo nome.

    A backup's type by name.

    Args:
        nome_do_backup: O nome do diretorio ou arquivo.

    Returns:
        `diario`, `semanal` ou `mensal`. Nome fora do padrao e diario.
    """
    base = nome_do_backup.strip().lower()
    if base.startswith(SEMANAL):
        return SEMANAL
    if base.startswith(MENSAL):
        return MENSAL
    return DIARIO


def expirar(
    backups: list[str], janelas: tuple[Janela, ...] = PADRAO
) -> tuple[list[str], list[str]]:
    """Separa o que fica do que sai.

    Split what stays from what goes.

    Mantem os N mais recentes de cada tipo (ordem alfabetica inversa, que
    coincide com a cronologica no padrao `tipo-AAAA-MM-DD`). O resto sai.

    Args:
        backups: Os nomes existentes.
        janelas: As janelas de retencao.

    Returns:
        O par `(manter, remover)`, ambos ordenados.
    """
    limites = {janela.tipo: janela.reter for janela in janelas}
    por_tipo: dict[str, list[str]] = {}
    for nome in backups:
        por_tipo.setdefault(classificar(nome), []).append(nome)
    manter: list[str] = []
    remover: list[str] = []
    for tipo, nomes in por_tipo.items():
        recentes = sorted(nomes, reverse=True)[:limites.get(tipo, 0)]
        manter.extend(recentes)
        remover.extend(n for n in nomes if n not in recentes)
    return sorted(manter), sorted(remover)