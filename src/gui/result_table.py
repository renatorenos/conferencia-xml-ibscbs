from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ..models import ResultadoArquivo

COLUNAS: list[tuple[str, str, int, str]] = [
    ("arquivo",  "Arquivo",       230, "w"),
    ("status",   "Status",         80, "center"),
    ("total",    "Itens",           55, "center"),
    ("com_ibs",  "Com IBS/CBS",    100, "center"),
    ("sem_ibs",  "Sem IBS/CBS",    100, "center"),
    ("mensagem", "Mensagem",       260, "w"),
]

COR_STATUS = {
    "OK":      "#4caf87",
    "ERRO":    "#e05252",
    "AVISO":   "#d4a017",
    "INVALIDO":"#888888",
}

_BG       = "#2b2b2b"
_BG_SEL   = "#1f538d"
_BG_HEAD  = "#333333"
_FG       = "#e0e0e0"


def _aplicar_estilo() -> None:
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "ValidadorIBS.Treeview",
        background=_BG,
        foreground=_FG,
        rowheight=28,
        fieldbackground=_BG,
        borderwidth=0,
        font=("Segoe UI", 10) if tk.TkVersion >= 8.6 else ("TkDefaultFont", 10),
    )
    style.configure(
        "ValidadorIBS.Treeview.Heading",
        background=_BG_HEAD,
        foreground=_FG,
        relief="flat",
        font=("Segoe UI", 10, "bold") if tk.TkVersion >= 8.6 else ("TkDefaultFont", 10, "bold"),
    )
    style.map(
        "ValidadorIBS.Treeview",
        background=[("selected", _BG_SEL)],
        foreground=[("selected", "white")],
    )


class TabelaResultados(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        ao_selecionar: Optional[Callable[[ResultadoArquivo], None]] = None,
        **kwargs: object,
    ) -> None:
        kwargs.setdefault("bg", _BG)
        super().__init__(parent, **kwargs)
        self._ao_selecionar = ao_selecionar
        self._resultados: list[ResultadoArquivo] = []
        self._indices: dict[str, int] = {}
        _aplicar_estilo()
        self._construir()

    def _construir(self) -> None:
        ids = [c[0] for c in COLUNAS]
        self._tree = ttk.Treeview(
            self,
            columns=ids,
            show="headings",
            selectmode="browse",
            style="ValidadorIBS.Treeview",
        )

        for col_id, titulo, largura, ancora in COLUNAS:
            self._tree.heading(col_id, text=titulo, anchor=ancora)  # type: ignore[arg-type]
            self._tree.column(
                col_id,
                width=largura,
                minwidth=40,
                anchor=ancora,  # type: ignore[arg-type]
                stretch=(col_id == "mensagem"),
            )

        for status, cor in COR_STATUS.items():
            self._tree.tag_configure(status, foreground=cor)

        scroll_v = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        scroll_h = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=scroll_v.set, xscrollcommand=scroll_h.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll_v.grid(row=0, column=1, sticky="ns")
        scroll_h.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        if self._ao_selecionar:
            self._tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        sel = self._tree.selection()
        if not sel:
            return
        idx = self._indices.get(sel[0])
        if idx is not None and self._ao_selecionar:
            self._ao_selecionar(self._resultados[idx])

    def carregar(self, resultados: list[ResultadoArquivo]) -> None:
        self._resultados = resultados
        self._indices = {}
        for item in self._tree.get_children():
            self._tree.delete(item)

        for i, r in enumerate(resultados):
            item_id = self._tree.insert(
                "",
                "end",
                values=(
                    r.nome_arquivo,
                    r.status,
                    r.total_itens or "-",
                    r.itens_com_ibscbs if r.total_itens else "-",
                    r.itens_sem_ibscbs if r.total_itens else "-",
                    r.mensagem,
                ),
                tags=(r.status,),
            )
            self._indices[item_id] = i

    def limpar(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._resultados = []
        self._indices = {}
