from __future__ import annotations
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

NS_NFE = "http://www.portalfiscal.inf.br/nfe"


@dataclass
class DadosNFe:
    itens_det: list[ET.Element] = field(default_factory=list)
    total: Optional[ET.Element] = None
    namespace: str = NS_NFE
    valido: bool = True
    erro: str = ""


def detectar_namespace(raiz: ET.Element) -> str:
    tag = raiz.tag
    if tag.startswith("{"):
        return tag[1 : tag.index("}")]
    return ""


def extrair_dados_nfe(caminho: Path) -> DadosNFe:
    try:
        tree = ET.parse(str(caminho))
    except ET.ParseError as e:
        return DadosNFe(valido=False, erro=f"XML malformado: {e}")

    raiz = tree.getroot()
    ns = detectar_namespace(raiz)

    def q(local: str) -> str:
        return f"{{{ns}}}{local}" if ns else local

    inf_nfe = raiz.find(f".//{q('infNFe')}")
    if inf_nfe is None:
        return DadosNFe(
            namespace=ns or NS_NFE,
            valido=False,
            erro="Elemento <infNFe> não encontrado — não é um XML de NF-e válido",
        )

    itens = inf_nfe.findall(q("det"))
    total = inf_nfe.find(q("total"))

    return DadosNFe(
        itens_det=itens,
        total=total,
        namespace=ns or NS_NFE,
    )
