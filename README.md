# Validador IBS/CBS — NF-e

Aplicação desktop em Python para validação das TAGs relacionadas aos tributos **IBS** (Imposto sobre Bens e Serviços) e **CBS** (Contribuição sobre Bens e Serviços) em arquivos XML de NF-e, conforme a **Nota Técnica 2025.002 v1.30**.

---

## Funcionalidades

- Seleção de diretório com múltiplos arquivos XML via interface gráfica
- Leitura e parsing de todos os XMLs encontrados no diretório
- Validação das TAGs obrigatórias IBS/CBS por item (`det`) e na seção de totais
- Detecção de TAGs **ausentes**, com **conteúdo vazio** e com **valor zerado** (`vBC`)
- Painel de detalhes com lista completa dos problemas por arquivo
- Exportação dos resultados para CSV
- Interface dark mode responsiva com processamento em thread separada

---

## Regras de Validação

A validação é baseada no schema XSD oficial (`DFeTiposBasicos_v1.00.xsd`) incluso na NT 2025.002 v1.30.

### Por item (`det/imposto/IBSCBS`)

| TAG | Tipo de verificação |
|---|---|
| `IBSCBS/CST` | Ausente ou vazio |
| `IBSCBS/cClassTrib` | Ausente ou vazio |
| `gIBSCBS/vBC` | Ausente, vazio ou **igual a zero** |
| `gIBSCBS/gIBSUF/pIBSUF` | Ausente ou vazio |
| `gIBSCBS/gIBSUF/vIBSUF` | Ausente ou vazio |
| `gIBSCBS/gIBSMun/pIBSMun` | Ausente ou vazio |
| `gIBSCBS/gIBSMun/vIBSMun` | Ausente ou vazio |
| `gIBSCBS/vIBS` | Ausente ou vazio |
| `gIBSCBS/gCBS/pCBS` | Ausente ou vazio |
| `gIBSCBS/gCBS/vCBS` | Ausente ou vazio |

### Seção de totais (`total/IBSCBSTot`)

| TAG | Tipo de verificação |
|---|---|
| `total/IBSCBSTot` | Ausente quando existem itens com `<IBSCBS>` |
| `total/IBSCBSTot/vBCIBSCBS` | Ausente ou vazio |

### Status por arquivo

| Status | Condição |
|---|---|
| `OK` | Todos os itens possuem `<IBSCBS>` válido e completo |
| `ERRO` | Um ou mais problemas encontrados nas TAGs |
| `AVISO` | Nenhum item contém `<IBSCBS>` ou parte dos itens não possui o grupo |
| `INVALIDO` | XML malformado ou sem elemento `<infNFe>` |

---

## Arquitetura

O projeto segue arquitetura em camadas com separação estrita de responsabilidades:

```
main.py                  # Ponto de entrada
│
src/
├── models.py            # Dataclasses compartilhadas entre camadas
├── conciliacao.py       # Regras de validação IBS/CBS (lógica pura, sem I/O)
├── exporter.py          # Exportação de resultados para CSV
├── parsers/
│   └── xml_parser.py    # Parsing XML e detecção de namespace
└── gui/
    ├── app.py           # Janela principal (customtkinter)
    └── result_table.py  # Componente Treeview com estilo dark
```

| Camada | Módulo | Responsabilidade |
|---|---|---|
| **Modelos** | `models.py` | Contrato de dados entre camadas (`TagAusente`, `ResultadoItem`, `ResultadoArquivo`) |
| **Parser** | `parsers/xml_parser.py` | Lê e parseia o XML, detecta namespace, retorna `DadosNFe` |
| **Negócio** | `conciliacao.py` | Aplica as regras de validação — funções puras sem efeitos colaterais |
| **Exportador** | `exporter.py` | Gera arquivo CSV — sem dependência da GUI |
| **Interface** | `gui/` | Orquestra chamadas, gerencia threading e apresenta resultados |

> A GUI nunca acessa o XML diretamente. O processamento ocorre em thread separada; a UI é atualizada exclusivamente via `self.after()`.

---

## Pré-requisitos

- Python 3.9 ou superior
- `customtkinter >= 5.2.0`

---

## Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/conferencia-xml-ibscbs.git
cd conferencia-xml-ibscbs

# Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# Instale as dependências
pip install -r requirements.txt
```

---

## Execução

```bash
python main.py
```

---

## Como usar

1. Clique em **"…"** ao lado do campo de diretório e selecione a pasta com os arquivos XML
2. Clique em **"Processar XMLs"**
3. Aguarde o processamento — os resultados aparecem na tabela com código de cores:
   - 🟢 **Verde** → OK
   - 🔴 **Vermelho** → ERRO
   - 🟡 **Amarelo** → AVISO / INVÁLIDO
4. Clique em qualquer linha para ver os detalhes dos problemas encontrados
5. Clique em **"Exportar CSV"** para salvar os resultados

---

## Documentação de Referência

Os schemas XSD e notas técnicas utilizados na validação estão em `docs/`:

```
docs/
├── notas tecnicas/
│   ├── NT_2025.002_v1.30_RTC_NF-e_IBS_CBS_IS.pdf
│   └── NT2024.003- Altera RVs NF-e - v 1.09.pdf
└── schemas/
    └── PL_010c_NT2022_002v1.30/
        ├── DFeTiposBasicos_v1.00.xsd   ← tipos TTribNFe, TCIBS, TIBSCBSMonoTot
        ├── leiauteNFe_v4.00.xsd
        ├── nfe_v4.00.xsd
        ├── tiposBasico_v4.00.xsd
        └── xmldsig-core-schema_v1.01.xsd
```

---

## Dependências

| Pacote | Versão |
|---|---|
| `customtkinter` | >= 5.2.0 |

> A biblioteca `xml.etree.ElementTree` é nativa do Python — não requer instalação adicional.

---

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
