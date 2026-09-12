"""
Contrato mínimo do CENSOR, replicado do gate.py real do Renato para permitir
testar o C7 isoladamente. NÃO substitui o gate.py — apenas espelha o tipo de
saída que o parser precisa produzir, exatamente como visto na interface:

    @dataclass(frozen=True)
    class CitacaoAlegada:
        numero_processo: str
        relator: str
        trecho_citado: str
        tipo_decisao: Optional[str] = None
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CitacaoAlegada:
    numero_processo: str
    relator: str
    trecho_citado: str
    tipo_decisao: Optional[str] = None
