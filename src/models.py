from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TagAusente:
    caminho: str
    descricao: str


@dataclass
class ResultadoItem:
    numero_item: str
    possui_ibscbs: bool
    tags_ausentes: list[TagAusente] = field(default_factory=list)


@dataclass
class ResultadoArquivo:
    nome_arquivo: str
    caminho_completo: str
    status: str  # "OK" | "ERRO" | "AVISO" | "INVALIDO"
    mensagem: str = ""
    total_itens: int = 0
    itens_com_ibscbs: int = 0
    itens_sem_ibscbs: int = 0
    tags_ausentes_totais: list[TagAusente] = field(default_factory=list)
    itens: list[ResultadoItem] = field(default_factory=list)
