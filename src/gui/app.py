from __future__ import annotations
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

import customtkinter as ctk

if sys.platform == "win32":
    import ctypes
    # Garante que o Windows use o ícone da aplicação na barra de tarefas
    # em vez do ícone do interpretador Python
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "CATEC.ConferenciaXMLIBSCBS.1"
    )

from ..conciliacao import validar_diretorio
from ..exporter import exportar_csv
from ..models import ResultadoArquivo
from .result_table import TabelaResultados

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_LARGURA_SIDEBAR = 270
_COR_OK      = "#4caf87"
_COR_ERRO    = "#e05252"
_COR_AVISO   = "#d4a017"
_COR_NEUTRO  = "#888888"


def _resource_path(relativo: str) -> Path:
    """Retorna o caminho absoluto do recurso, compatível com PyInstaller."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent.parent))
    return base / relativo


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Validador IBS/CBS — NF-e  |  NT 2025.002 v1.30")
        self.geometry("1150x720")
        self.minsize(960, 620)
        self._aplicar_icone()

        self._resultados: list[ResultadoArquivo] = []
        self._construir_layout()
        # after() garante que o ícone é aplicado DEPOIS do CTk terminar
        # sua própria inicialização, evitando que ele sobrescreva o ícone
        self.after(0, self._aplicar_icone)

    def _aplicar_icone(self) -> None:
        if sys.platform == "win32":
            icone = _resource_path("icon.ico")
            if icone.exists():
                self.iconbitmap(str(icone))

    # ------------------------------------------------------------------ layout

    def _construir_layout(self) -> None:
        self._sidebar = self._criar_sidebar()
        self._sidebar.pack(side="left", fill="y")

        separador = ctk.CTkFrame(self, width=1, fg_color="#3a3a3a", corner_radius=0)
        separador.pack(side="left", fill="y")

        self._area = self._criar_area_conteudo()
        self._area.pack(side="left", fill="both", expand=True)

    def _criar_sidebar(self) -> ctk.CTkFrame:
        sb = ctk.CTkFrame(self, width=_LARGURA_SIDEBAR, corner_radius=0)
        sb.pack_propagate(False)

        ctk.CTkLabel(
            sb,
            text="Validador\nIBS / CBS",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(pady=(32, 4))

        ctk.CTkLabel(
            sb,
            text="NF-e · NT 2025.002 v1.30",
            font=ctk.CTkFont(size=11),
            text_color=_COR_NEUTRO,
        ).pack(pady=(0, 24))

        # --- diretório ---
        ctk.CTkLabel(sb, text="Diretório dos XMLs:", anchor="w").pack(padx=20, fill="x")

        frame_dir = ctk.CTkFrame(sb, fg_color="transparent")
        frame_dir.pack(padx=20, fill="x", pady=(4, 0))

        self._var_diretorio = tk.StringVar()
        self._entry_dir = ctk.CTkEntry(
            frame_dir,
            textvariable=self._var_diretorio,
            placeholder_text="Selecione uma pasta...",
        )
        self._entry_dir.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            frame_dir,
            text="…",
            width=36,
            command=self._selecionar_diretorio,
        ).pack(side="left", padx=(6, 0))

        # --- botões ---
        self._btn_processar = ctk.CTkButton(
            sb,
            text="▶  Processar XMLs",
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._iniciar_processamento,
        )
        self._btn_processar.pack(padx=20, pady=(20, 8), fill="x")

        self._btn_exportar = ctk.CTkButton(
            sb,
            text="⬇  Exportar CSV",
            height=36,
            fg_color="transparent",
            border_width=1,
            state="disabled",
            command=self._exportar_csv,
        )
        self._btn_exportar.pack(padx=20, pady=(0, 24), fill="x")

        # --- resumo ---
        frame_stats = ctk.CTkFrame(sb)
        frame_stats.pack(padx=20, fill="x")

        ctk.CTkLabel(
            frame_stats,
            text="Resumo",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=(10, 6))

        self._lbl_total  = ctk.CTkLabel(frame_stats, text="Arquivos: —", anchor="w")
        self._lbl_ok     = ctk.CTkLabel(frame_stats, text="OK: —", anchor="w", text_color=_COR_OK)
        self._lbl_erro   = ctk.CTkLabel(frame_stats, text="Erro: —", anchor="w", text_color=_COR_ERRO)
        self._lbl_aviso  = ctk.CTkLabel(frame_stats, text="Aviso/Inválido: —", anchor="w", text_color=_COR_AVISO)

        for lbl in (self._lbl_total, self._lbl_ok, self._lbl_erro, self._lbl_aviso):
            lbl.pack(padx=14, anchor="w")

        ctk.CTkLabel(frame_stats, text="").pack(pady=4)

        # --- status ---
        self._lbl_status = ctk.CTkLabel(
            sb,
            text="Selecione um diretório e clique em Processar.",
            wraplength=_LARGURA_SIDEBAR - 30,
            font=ctk.CTkFont(size=11),
            text_color=_COR_NEUTRO,
            justify="left",
        )
        self._lbl_status.pack(padx=18, pady=14, anchor="w")

        return sb

    def _criar_area_conteudo(self) -> ctk.CTkFrame:
        area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        # cabeçalho da tabela
        frame_header = ctk.CTkFrame(area, fg_color="transparent")
        frame_header.pack(fill="x", padx=14, pady=(12, 0))

        ctk.CTkLabel(
            frame_header,
            text="Resultados da Validação",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left")

        # tabela
        frame_tabela = ctk.CTkFrame(area)
        frame_tabela.pack(fill="both", expand=True, padx=14, pady=(8, 0))

        self._tabela = TabelaResultados(
            frame_tabela,
            ao_selecionar=self._ao_selecionar_linha,
            bg="#2b2b2b",
        )
        self._tabela.pack(fill="both", expand=True, padx=8, pady=8)

        # painel de detalhes
        frame_det = ctk.CTkFrame(area, height=170)
        frame_det.pack(fill="x", padx=14, pady=(6, 12))
        frame_det.pack_propagate(False)

        ctk.CTkLabel(
            frame_det,
            text="Detalhes do arquivo selecionado",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self._txt_detalhe = ctk.CTkTextbox(
            frame_det,
            state="disabled",
            font=ctk.CTkFont(family="Courier New", size=11),
            wrap="none",
        )
        self._txt_detalhe.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        return area

    # -------------------------------------------------------------- callbacks

    def _selecionar_diretorio(self) -> None:
        pasta = filedialog.askdirectory(title="Selecione o diretório com arquivos XML")
        if pasta:
            self._var_diretorio.set(pasta)

    def _iniciar_processamento(self) -> None:
        dir_str = self._var_diretorio.get().strip()
        if not dir_str:
            messagebox.showwarning("Atenção", "Selecione um diretório primeiro.")
            return

        caminho = Path(dir_str)
        if not caminho.is_dir():
            messagebox.showerror("Erro", "Caminho inválido ou não é um diretório.")
            return

        self._btn_processar.configure(state="disabled", text="⏳  Processando...")
        self._btn_exportar.configure(state="disabled")
        self._tabela.limpar()
        self._set_detalhe("Processando arquivos...")
        self._set_status("Processando arquivos XML...", "neutro")

        threading.Thread(
            target=self._processar_em_thread,
            args=(caminho,),
            daemon=True,
        ).start()

    def _processar_em_thread(self, caminho: Path) -> None:
        try:
            resultados = validar_diretorio(caminho)
        except Exception as exc:  # noqa: BLE001
            self.after(0, lambda: self._ao_erro(str(exc)))
            return
        self.after(0, lambda: self._ao_concluir(resultados))

    def _ao_concluir(self, resultados: list[ResultadoArquivo]) -> None:
        self._resultados = resultados
        self._btn_processar.configure(state="normal", text="▶  Processar XMLs")

        if not resultados:
            self._set_status("Nenhum arquivo XML encontrado no diretório.", "aviso")
            self._set_detalhe("Nenhum arquivo .xml encontrado.")
            return

        self._tabela.carregar(resultados)
        self._btn_exportar.configure(state="normal")
        self._atualizar_resumo(resultados)
        self._set_status(f"{len(resultados)} arquivo(s) processado(s).", "ok")
        self._set_detalhe("Clique em uma linha para ver os detalhes.")

    def _ao_erro(self, msg: str) -> None:
        self._btn_processar.configure(state="normal", text="▶  Processar XMLs")
        self._set_status(f"Erro: {msg}", "erro")
        messagebox.showerror("Erro inesperado", f"Falha ao processar arquivos:\n\n{msg}")

    def _atualizar_resumo(self, resultados: list[ResultadoArquivo]) -> None:
        total  = len(resultados)
        ok     = sum(1 for r in resultados if r.status == "OK")
        erro   = sum(1 for r in resultados if r.status == "ERRO")
        outros = total - ok - erro

        self._lbl_total.configure(text=f"Arquivos: {total}")
        self._lbl_ok.configure(text=f"OK: {ok}")
        self._lbl_erro.configure(text=f"Erro: {erro}")
        self._lbl_aviso.configure(text=f"Aviso/Inválido: {outros}")

    def _set_status(self, texto: str, tipo: str = "neutro") -> None:
        cores = {"ok": _COR_OK, "erro": _COR_ERRO, "aviso": _COR_AVISO, "neutro": _COR_NEUTRO}
        self._lbl_status.configure(text=texto, text_color=cores.get(tipo, _COR_NEUTRO))

    def _ao_selecionar_linha(self, resultado: ResultadoArquivo) -> None:
        linhas: list[str] = [
            f"Arquivo  : {resultado.nome_arquivo}",
            f"Status   : {resultado.status}  —  {resultado.mensagem}",
        ]

        if resultado.total_itens > 0:
            linhas += [
                f"Itens    : {resultado.total_itens} total  |  "
                f"{resultado.itens_com_ibscbs} com IBS/CBS  |  "
                f"{resultado.itens_sem_ibscbs} sem IBS/CBS",
            ]

        linhas.append("")

        if resultado.tags_ausentes_totais:
            linhas.append("Tags ausentes em <total>:")
            for t in resultado.tags_ausentes_totais:
                linhas.append(f"  ✗  {t.caminho}")
                linhas.append(f"       → {t.descricao}")

        itens_erro = [i for i in resultado.itens if i.tags_ausentes]
        if itens_erro:
            linhas.append("Tags ausentes por item:")
            for item in itens_erro:
                linhas.append(f"  Item {item.numero_item}:")
                for t in item.tags_ausentes:
                    linhas.append(f"    ✗  {t.caminho}")
                    linhas.append(f"         → {t.descricao}")

        if resultado.status == "INVALIDO":
            linhas.append(f"Erro de parsing: {resultado.mensagem}")

        if (
            resultado.status in ("OK", "AVISO")
            and not resultado.tags_ausentes_totais
            and not itens_erro
        ):
            linhas.append("Nenhuma tag obrigatória ausente detectada.")

        self._set_detalhe("\n".join(linhas))

    def _set_detalhe(self, texto: str) -> None:
        self._txt_detalhe.configure(state="normal")
        self._txt_detalhe.delete("1.0", "end")
        self._txt_detalhe.insert("1.0", texto)
        self._txt_detalhe.configure(state="disabled")

    def _exportar_csv(self) -> None:
        if not self._resultados:
            return
        destino = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")],
            initialfile="resultado_validacao_ibscbs.csv",
            title="Salvar resultado como...",
        )
        if not destino:
            return
        try:
            exportar_csv(self._resultados, Path(destino))
            messagebox.showinfo("Exportado", f"Arquivo salvo em:\n{destino}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erro ao exportar", str(exc))
