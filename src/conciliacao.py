from __future__ import annotations
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from .models import ResultadoArquivo, ResultadoItem, TagAusente
from .parsers.xml_parser import extrair_dados_nfe


def _q(local: str, ns: str) -> str:
    return f"{{{ns}}}{local}" if ns else local


def _texto_vazio(elem: Optional[ET.Element]) -> bool:
    """True quando a tag está ausente OU existe mas sem conteúdo textual."""
    if elem is None:
        return True
    return not (elem.text or "").strip()


def _valor_zerado(elem: Optional[ET.Element]) -> bool:
    """True quando a tag está ausente, vazia ou com valor numérico igual a zero."""
    if elem is None:
        return True
    texto = (elem.text or "").strip()
    if not texto:
        return True
    try:
        return float(texto) <= 0
    except ValueError:
        return True  # conteúdo não numérico também é inválido


def _validar_grupo_ibscbs(ibscbs: ET.Element, ns: str) -> list[TagAusente]:
    """Valida sub-elementos obrigatórios de IBSCBS conforme TTribNFe/TCIBS do XSD."""
    q = lambda local: _q(local, ns)
    ausentes: list[TagAusente] = []

    cst = ibscbs.find(q("CST"))
    if _texto_vazio(cst):
        descricao = "Código de Situação Tributária do IBS/CBS ausente ou vazio"
        ausentes.append(TagAusente("IBSCBS/CST", descricao))

    class_trib = ibscbs.find(q("cClassTrib"))
    if _texto_vazio(class_trib):
        descricao = "Classificação Tributária ausente ou vazia"
        ausentes.append(TagAusente("IBSCBS/cClassTrib", descricao))

    g_ibs_cbs = ibscbs.find(q("gIBSCBS"))
    if g_ibs_cbs is not None:
        _validar_tcibs(g_ibs_cbs, ns, ausentes)

    return ausentes


def _validar_tcibs(g: ET.Element, ns: str, ausentes: list[TagAusente]) -> None:
    """Valida estrutura do tipo TCIBS (gIBSCBS)."""
    q = lambda local: _q(local, ns)

    vbc = g.find(q("vBC"))
    if _valor_zerado(vbc):
        ausentes.append(TagAusente("gIBSCBS/vBC", "Base de Cálculo IBS/CBS ausente, vazia ou igual a zero"))

    g_uf = g.find(q("gIBSUF"))
    if g_uf is None:
        ausentes.append(TagAusente("gIBSCBS/gIBSUF", "Grupo IBS da UF ausente"))
    else:
        if _texto_vazio(g_uf.find(q("pIBSUF"))):
            ausentes.append(TagAusente("gIBSCBS/gIBSUF/pIBSUF", "Alíquota IBS da UF ausente ou vazia"))
        if _texto_vazio(g_uf.find(q("vIBSUF"))):
            ausentes.append(TagAusente("gIBSCBS/gIBSUF/vIBSUF", "Valor IBS da UF ausente ou vazio"))

    g_mun = g.find(q("gIBSMun"))
    if g_mun is None:
        ausentes.append(TagAusente("gIBSCBS/gIBSMun", "Grupo IBS do Município ausente"))
    else:
        if _texto_vazio(g_mun.find(q("pIBSMun"))):
            ausentes.append(TagAusente("gIBSCBS/gIBSMun/pIBSMun", "Alíquota IBS Municipal ausente ou vazia"))
        if _texto_vazio(g_mun.find(q("vIBSMun"))):
            ausentes.append(TagAusente("gIBSCBS/gIBSMun/vIBSMun", "Valor IBS Municipal ausente ou vazio"))

    if _texto_vazio(g.find(q("vIBS"))):
        ausentes.append(TagAusente("gIBSCBS/vIBS", "Valor Total IBS ausente ou vazio"))

    g_cbs = g.find(q("gCBS"))
    if g_cbs is None:
        ausentes.append(TagAusente("gIBSCBS/gCBS", "Grupo CBS ausente"))
    else:
        if _texto_vazio(g_cbs.find(q("pCBS"))):
            ausentes.append(TagAusente("gIBSCBS/gCBS/pCBS", "Alíquota CBS ausente ou vazia"))
        if _texto_vazio(g_cbs.find(q("vCBS"))):
            ausentes.append(TagAusente("gIBSCBS/gCBS/vCBS", "Valor CBS ausente ou vazio"))


def _validar_totais(
    total: ET.Element,
    ns: str,
    tem_ibscbs_nos_itens: bool,
) -> list[TagAusente]:
    """Valida seção <total> conforme TIBSCBSMonoTot."""
    q = lambda local: _q(local, ns)
    ausentes: list[TagAusente] = []

    ibs_cbs_tot = total.find(q("IBSCBSTot"))

    if tem_ibscbs_nos_itens and ibs_cbs_tot is None:
        ausentes.append(TagAusente(
            "total/IBSCBSTot",
            "Totais IBS/CBS ausentes (existem itens com <IBSCBS>)",
        ))
        return ausentes

    if ibs_cbs_tot is not None:
        if _texto_vazio(ibs_cbs_tot.find(q("vBCIBSCBS"))):
            ausentes.append(TagAusente("total/IBSCBSTot/vBCIBSCBS", "Total Base de Cálculo IBS/CBS ausente ou vazio"))

    return ausentes


def _determinar_status(
    itens: list[ResultadoItem],
    tags_totais: list[TagAusente],
    total_det: int,
    com_ibscbs: int,
) -> tuple[str, str]:
    """Retorna (status, mensagem) para o arquivo."""
    n_tags_item = sum(len(i.tags_ausentes) for i in itens)
    n_tags_total = len(tags_totais)

    if n_tags_item > 0 or n_tags_total > 0:
        return "ERRO", f"{n_tags_item + n_tags_total} problema(s) encontrado(s)"

    if com_ibscbs == 0:
        return "AVISO", "Nenhum item contém <IBSCBS> — verifique se tributação reforma aplica"

    sem = total_det - com_ibscbs
    if sem > 0:
        return "AVISO", f"{sem} item(s) sem <IBSCBS> de {total_det}"

    return "OK", "Estrutura IBS/CBS válida"


def validar_arquivo(caminho: Path) -> ResultadoArquivo:
    dados = extrair_dados_nfe(caminho)

    if not dados.valido:
        return ResultadoArquivo(
            nome_arquivo=caminho.name,
            caminho_completo=str(caminho),
            status="INVALIDO",
            mensagem=dados.erro,
        )

    ns = dados.namespace
    q = lambda local: _q(local, ns)

    itens_resultado: list[ResultadoItem] = []
    itens_com_ibscbs = 0

    for det in dados.itens_det:
        numero = det.get("nItem", "?")
        imposto = det.find(q("imposto"))

        if imposto is None:
            itens_resultado.append(ResultadoItem(
                numero_item=numero,
                possui_ibscbs=False,
                tags_ausentes=[TagAusente("imposto", "Elemento <imposto> ausente no item")],
            ))
            continue

        ibscbs = imposto.find(q("IBSCBS"))

        if ibscbs is None:
            itens_resultado.append(ResultadoItem(numero_item=numero, possui_ibscbs=False))
        else:
            itens_com_ibscbs += 1
            tags_ausentes = _validar_grupo_ibscbs(ibscbs, ns)
            itens_resultado.append(ResultadoItem(
                numero_item=numero,
                possui_ibscbs=True,
                tags_ausentes=tags_ausentes,
            ))

    tags_ausentes_totais: list[TagAusente] = []
    if dados.total is not None:
        tags_ausentes_totais = _validar_totais(dados.total, ns, itens_com_ibscbs > 0)
    elif itens_com_ibscbs > 0:
        tags_ausentes_totais.append(TagAusente("total", "Seção <total> ausente no XML"))

    total_itens = len(dados.itens_det)
    status, mensagem = _determinar_status(
        itens_resultado, tags_ausentes_totais, total_itens, itens_com_ibscbs
    )

    return ResultadoArquivo(
        nome_arquivo=caminho.name,
        caminho_completo=str(caminho),
        status=status,
        mensagem=mensagem,
        total_itens=total_itens,
        itens_com_ibscbs=itens_com_ibscbs,
        itens_sem_ibscbs=total_itens - itens_com_ibscbs,
        tags_ausentes_totais=tags_ausentes_totais,
        itens=itens_resultado,
    )


def validar_diretorio(caminho: Path) -> list[ResultadoArquivo]:
    arquivos = sorted(caminho.glob("*.xml")) + sorted(caminho.glob("*.XML"))
    arquivos_unicos = list(dict.fromkeys(arquivos))
    return [validar_arquivo(arq) for arq in arquivos_unicos]
