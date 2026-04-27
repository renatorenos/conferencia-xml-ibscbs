from __future__ import annotations
import csv
from pathlib import Path

from .models import ResultadoArquivo, TagAusente


def _coletar_tags(resultado: ResultadoArquivo) -> list[str]:
    tags: list[str] = []
    for t in resultado.tags_ausentes_totais:
        tags.append(f"[total] {t.caminho}")
    for item in resultado.itens:
        for t in item.tags_ausentes:
            tags.append(f"[item {item.numero_item}] {t.caminho}")
    return tags


def exportar_csv(resultados: list[ResultadoArquivo], destino: Path) -> None:
    with destino.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Arquivo",
            "Status",
            "Mensagem",
            "Total Itens",
            "Itens com IBS/CBS",
            "Itens sem IBS/CBS",
            "Tags Ausentes",
        ])
        for r in resultados:
            tags = _coletar_tags(r)
            writer.writerow([
                r.nome_arquivo,
                r.status,
                r.mensagem,
                r.total_itens,
                r.itens_com_ibscbs,
                r.itens_sem_ibscbs,
                " | ".join(tags) if tags else "",
            ])
