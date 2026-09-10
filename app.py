# -*- coding: utf-8 -*-
"""
================================================================================
 MATRIZ ÁREA x FUNÇÃO — SANTA CASA DE PORTO ALEGRE
 Cruzamento de 38 Funções (organizadas em 6 Pilares de Sinergia) x
 22 Gerências/Áreas corporativas.
================================================================================

Como rodar:
-----------
1) Terminal local:
       pip install -r requirements.txt
       streamlit run app.py

2) Streamlit Community Cloud:
       Suba este arquivo (app.py) + requirements.txt para um repositório
       GitHub e aponte o deploy para app.py.

Observação sobre os dados:
---------------------------
As relações Função x Gerência abaixo (bloco `carregar_relacoes`) estão
mockadas para fins de demonstração, com base na estrutura organizacional
e nos papéis (Responsável / Apoio) tipicamente observados em hospitais de
grande porte. Em produção, este bloco deve ser substituído por uma consulta
à base real (ex.: planilha/matriz consolidada do Levantamento de Áreas),
mantendo o mesmo formato de saída: uma lista de tuplas
(Função, Gerência, Papel).
================================================================================
"""

import io
import unicodedata

import pandas as pd
import streamlit as st

# ==============================================================================
# 1. CONFIGURAÇÃO GERAL DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Matriz Área x Função | Santa Casa POA",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# 2. ESTILO VISUAL (CSS CUSTOMIZADO)
# ==============================================================================
# Paleta de cores por Macroprocesso — usada tanto no CSS quanto na geração
# das tabelas HTML customizadas.
CORES_MACRO = {
    "Finalístico": {"bg": "#E7F8EE", "text": "#15803D", "forte": "#22C55E"},
    "Meio":        {"bg": "#EAF2FE", "text": "#1D4ED8", "forte": "#3B82F6"},
    "Apoio":       {"bg": "#F1F2F4", "text": "#334155", "forte": "#64748B"},
}

# Paleta de cores por papel de responsabilidade dentro da matriz.
CORES_PAPEL = {
    "R": {"rotulo": "Responsável",       "bg": "#2563EB", "texto": "#FFFFFF", "simbolo": "●"},
    "A": {"rotulo": "Apoio / Interface",  "bg": "#CBD5E1", "texto": "#1E293B", "simbolo": "◐"},
}

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* ---------- Cabeçalho / Hero ---------- */
    .hero-container {
        padding: 1.6rem 1.8rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #0F2A4A 0%, #1B4B7A 55%, #2E6DA4 100%);
        color: white;
        margin-bottom: 1.1rem;
        box-shadow: 0 8px 24px rgba(15, 42, 74, 0.18);
    }
    .hero-title {
        font-size: 1.65rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        opacity: 0.9;
        font-weight: 400;
    }

    /* ---------- Cartões de estatística rápida ---------- */
    .stat-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 0.9rem 1.1rem;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05);
        text-align: left;
    }
    .stat-value {
        font-size: 1.55rem;
        font-weight: 800;
        color: #0F2A4A;
        line-height: 1.1;
    }
    .stat-label {
        font-size: 0.78rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    /* ---------- Legenda ---------- */
    .legenda-card {
        border-radius: 14px;
        border: 1px solid #E5E7EB;
        background: #FAFBFC;
        padding: 1rem 1.2rem;
        margin-bottom: 1.1rem;
    }
    .legenda-titulo {
        font-weight: 700;
        font-size: 0.95rem;
        color: #0F2A4A;
        margin-bottom: 0.55rem;
    }
    .legenda-item {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        margin-right: 1.4rem;
        margin-bottom: 0.35rem;
        font-size: 0.85rem;
        color: #1E293B;
    }
    .legenda-pill {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.78rem;
    }
    .legenda-simbolo {
        font-size: 1rem;
        font-weight: 700;
    }

    /* ---------- Tabela matricial customizada ---------- */
    .tabela-wrapper {
        overflow-x: auto;
        border-radius: 14px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
        max-height: 620px;
        overflow-y: auto;
    }
    table.matriz-tabela {
        border-collapse: collapse;
        width: 100%;
        min-width: 720px;
        font-size: 0.82rem;
    }
    table.matriz-tabela thead th {
        position: sticky;
        top: 0;
        background: #0F2A4A;
        color: white;
        font-weight: 600;
        padding: 0.55rem 0.5rem;
        text-align: center;
        white-space: nowrap;
        z-index: 3;
        border-bottom: 2px solid #0A1F38;
    }
    table.matriz-tabela thead th.col-funcao-header {
        text-align: left;
        left: 0;
        z-index: 4;
        min-width: 230px;
    }
    table.matriz-tabela td {
        padding: 0.5rem 0.5rem;
        text-align: center;
        border-bottom: 1px solid #EEF0F2;
        white-space: nowrap;
    }
    table.matriz-tabela td.col-funcao {
        position: sticky;
        left: 0;
        background: #FFFFFF;
        text-align: left;
        white-space: normal;
        min-width: 230px;
        z-index: 2;
        border-right: 1px solid #E5E7EB;
    }
    table.matriz-tabela tbody tr:nth-child(even) td.col-funcao {
        background: #FAFBFC;
    }
    table.matriz-tabela tbody tr:hover td {
        background: #F0F6FF !important;
    }
    .nome-funcao {
        font-weight: 600;
        color: #0F2A4A;
        display: block;
        margin-top: 0.15rem;
    }
    .badge-macro {
        display: inline-block;
        padding: 0.1rem 0.5rem;
        border-radius: 999px;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .celula-vazia {
        color: #D8DCE1;
        font-size: 0.9rem;
    }
    .celula-papel {
        font-size: 1.05rem;
        font-weight: 700;
        cursor: default;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# 3. CAMADA DE DADOS (MOCK)
# ==============================================================================

def carregar_estrutura() -> dict:
    """Retorna a estrutura dos 6 Pilares de Sinergia, cada um com seu
    Macroprocesso e a lista de Funções que o compõe (38 funções no total)."""
    return {
        "1️⃣ Operações Assistenciais": {
            "macroprocesso": "Finalístico",
            "funcoes": [
                "Pronto Socorro",
                "Unidade de Internação",
                "Serviços Ambulatoriais",
                "Procedimentos Cirúrgicos",
                "Medicina Diagnóstica",
            ],
        },
        "2️⃣ Gestão de Fluxo e Apoio Clínico": {
            "macroprocesso": "Meio",
            "funcoes": [
                "Gestão de Leitos/NIR",
                "Atendimento ao Paciente",
                "Farmácia",
                "Logística de Medicamentos",
                "Nutrição Clínica",
                "Documentação Assistencial",
                "Epidemiologia e Infecção Hospitalar",
            ],
        },
        "3️⃣ Hotelaria, Logística e Infraestrutura": {
            "macroprocesso": "Meio",
            "funcoes": [
                "Higienização",
                "Rouparia",
                "Esterilização",
                "Manutenção Predial",
                "Engenharia Clínica",
                "Obras",
                "Segurança",
                "Suprimentos",
            ],
        },
        "4️⃣ Mercado e Ciclo de Receita": {
            "macroprocesso": "Apoio",
            "funcoes": [
                "Comercial",
                "Produto",
                "Faturamento",
                "Finanças e Controladoria",
                "Marketing",
                "Filantropia",
                "Inovação e Planejamento",
            ],
        },
        "5️⃣ Capital Humano e Governança Clínica": {
            "macroprocesso": "Apoio",
            "funcoes": [
                "Pessoal",
                "Administração de Pessoal",
                "SESMT",
                "Relacionamento Médico",
                "Práticas Médicas",
                "Resultados e Práticas Assistenciais",
            ],
        },
        "6️⃣ Governança Corporativa e Suporte": {
            "macroprocesso": "Apoio",
            "funcoes": [
                "Governança Corporativa",
                "Jurídico",
                "Qualidade",
                "TI",
                "Ensino e Pesquisa",
            ],
        },
    }


def carregar_gerencias() -> list[str]:
    """Lista oficial das 22 Gerências/Áreas existentes hoje na instituição."""
    return [
        "Gerente Corporativo Relacionamento com corpo clinico e clientes",
        "Gerente Ensino e Pesquisa",
        "Gerente de Gestão de Pessoas",
        "Gerente Comunic. e Marketing",
        "Gerente de Infraestrutura",
        "Gerente de Modernização",
        "Gerente de Relações Institucionais",
        "Gerente de Suprimentos",
        "Gerente PMO",
        "Gerente Projetos de Captação",
        "Gerente Corporativo Enfermagem",
        "Gerente de Qualidade",
        "Gerente Médico",
        "Gerente Segurança Assistencial",
        "Gerente Comercial",
        "Gerente de Controladoria",
        "Gerente de Faturamento",
        "Gerente Financeiro",
        "Gerente Jurídico",
        "Gerente Tecnologia e Inovação",
        "Gerente Corporativo Operações",
        "Gerente Hospitalar",
    ]


def carregar_relacoes() -> list[tuple[str, str, str]]:
    """Relações Função x Gerência mockadas: (Função, Gerência, Papel).
    Papel: "R" = Responsável (dona da entrega) | "A" = Apoio / Interface."""
    return [
        # ---- 1. Operações Assistenciais -----------------------------------
        ("Pronto Socorro", "Gerente Hospitalar", "R"),
        ("Pronto Socorro", "Gerente Corporativo Operações", "A"),
        ("Pronto Socorro", "Gerente Médico", "A"),
        ("Pronto Socorro", "Gerente Segurança Assistencial", "A"),

        ("Unidade de Internação", "Gerente Hospitalar", "R"),
        ("Unidade de Internação", "Gerente Corporativo Enfermagem", "A"),
        ("Unidade de Internação", "Gerente Corporativo Operações", "A"),

        ("Serviços Ambulatoriais", "Gerente Hospitalar", "R"),
        ("Serviços Ambulatoriais", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "A"),
        ("Serviços Ambulatoriais", "Gerente Corporativo Operações", "A"),

        ("Procedimentos Cirúrgicos", "Gerente Hospitalar", "R"),
        ("Procedimentos Cirúrgicos", "Gerente Médico", "A"),
        ("Procedimentos Cirúrgicos", "Gerente Corporativo Operações", "A"),
        ("Procedimentos Cirúrgicos", "Gerente de Suprimentos", "A"),

        ("Medicina Diagnóstica", "Gerente Hospitalar", "R"),
        ("Medicina Diagnóstica", "Gerente Médico", "A"),
        ("Medicina Diagnóstica", "Gerente Tecnologia e Inovação", "A"),

        # ---- 2. Gestão de Fluxo e Apoio Clínico ----------------------------
        ("Gestão de Leitos/NIR", "Gerente Corporativo Operações", "R"),
        ("Gestão de Leitos/NIR", "Gerente Hospitalar", "A"),
        ("Gestão de Leitos/NIR", "Gerente Médico", "A"),

        ("Atendimento ao Paciente", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "R"),
        ("Atendimento ao Paciente", "Gerente Hospitalar", "A"),

        ("Farmácia", "Gerente de Suprimentos", "R"),
        ("Farmácia", "Gerente Segurança Assistencial", "A"),
        ("Farmácia", "Gerente Hospitalar", "A"),

        ("Logística de Medicamentos", "Gerente de Suprimentos", "R"),
        ("Logística de Medicamentos", "Gerente Corporativo Operações", "A"),

        ("Nutrição Clínica", "Gerente Corporativo Operações", "R"),
        ("Nutrição Clínica", "Gerente Hospitalar", "A"),

        ("Documentação Assistencial", "Gerente de Qualidade", "R"),
        ("Documentação Assistencial", "Gerente Corporativo Enfermagem", "A"),
        ("Documentação Assistencial", "Gerente Tecnologia e Inovação", "A"),

        ("Epidemiologia e Infecção Hospitalar", "Gerente Segurança Assistencial", "R"),
        ("Epidemiologia e Infecção Hospitalar", "Gerente Corporativo Enfermagem", "A"),
        ("Epidemiologia e Infecção Hospitalar", "Gerente de Qualidade", "A"),

        # ---- 3. Hotelaria, Logística e Infraestrutura ----------------------
        ("Higienização", "Gerente Corporativo Operações", "R"),
        ("Higienização", "Gerente Hospitalar", "A"),

        ("Rouparia", "Gerente Corporativo Operações", "R"),
        ("Rouparia", "Gerente de Suprimentos", "A"),

        ("Esterilização", "Gerente Corporativo Operações", "R"),
        ("Esterilização", "Gerente Segurança Assistencial", "A"),
        ("Esterilização", "Gerente de Suprimentos", "A"),

        ("Manutenção Predial", "Gerente de Infraestrutura", "R"),
        ("Manutenção Predial", "Gerente de Modernização", "A"),

        ("Engenharia Clínica", "Gerente de Infraestrutura", "R"),
        ("Engenharia Clínica", "Gerente Tecnologia e Inovação", "A"),
        ("Engenharia Clínica", "Gerente de Suprimentos", "A"),

        ("Obras", "Gerente de Modernização", "R"),
        ("Obras", "Gerente PMO", "A"),
        ("Obras", "Gerente de Infraestrutura", "A"),

        ("Segurança", "Gerente de Infraestrutura", "R"),
        ("Segurança", "Gerente Jurídico", "A"),

        ("Suprimentos", "Gerente de Suprimentos", "R"),
        ("Suprimentos", "Gerente de Controladoria", "A"),

        # ---- 4. Mercado e Ciclo de Receita ---------------------------------
        ("Comercial", "Gerente Comercial", "R"),
        ("Comercial", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "A"),

        ("Produto", "Gerente Comercial", "R"),
        ("Produto", "Gerente de Faturamento", "A"),

        ("Faturamento", "Gerente de Faturamento", "R"),
        ("Faturamento", "Gerente Financeiro", "A"),
        ("Faturamento", "Gerente Comercial", "A"),

        ("Finanças e Controladoria", "Gerente Financeiro", "R"),
        ("Finanças e Controladoria", "Gerente de Controladoria", "A"),

        ("Marketing", "Gerente Comunic. e Marketing", "R"),
        ("Marketing", "Gerente Comercial", "A"),

        ("Filantropia", "Gerente de Relações Institucionais", "R"),
        ("Filantropia", "Gerente Projetos de Captação", "A"),

        ("Inovação e Planejamento", "Gerente Tecnologia e Inovação", "R"),
        ("Inovação e Planejamento", "Gerente PMO", "A"),

        # ---- 5. Capital Humano e Governança Clínica ------------------------
        ("Pessoal", "Gerente de Gestão de Pessoas", "R"),

        ("Administração de Pessoal", "Gerente de Gestão de Pessoas", "R"),
        ("Administração de Pessoal", "Gerente de Controladoria", "A"),

        ("SESMT", "Gerente de Gestão de Pessoas", "R"),
        ("SESMT", "Gerente Segurança Assistencial", "A"),

        ("Relacionamento Médico", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "R"),
        ("Relacionamento Médico", "Gerente Médico", "A"),

        ("Práticas Médicas", "Gerente Médico", "R"),
        ("Práticas Médicas", "Gerente Segurança Assistencial", "A"),

        ("Resultados e Práticas Assistenciais", "Gerente Segurança Assistencial", "R"),
        ("Resultados e Práticas Assistenciais", "Gerente Corporativo Enfermagem", "A"),
        ("Resultados e Práticas Assistenciais", "Gerente Médico", "A"),

        # ---- 6. Governança Corporativa e Suporte ---------------------------
        ("Governança Corporativa", "Gerente PMO", "R"),
        ("Governança Corporativa", "Gerente Jurídico", "A"),

        ("Jurídico", "Gerente Jurídico", "R"),

        ("Qualidade", "Gerente de Qualidade", "R"),
        ("Qualidade", "Gerente Segurança Assistencial", "A"),

        ("TI", "Gerente Tecnologia e Inovação", "R"),
        ("TI", "Gerente de Infraestrutura", "A"),

        ("Ensino e Pesquisa", "Gerente Ensino e Pesquisa", "R"),
        ("Ensino e Pesquisa", "Gerente Médico", "A"),
    ]


@st.cache_data
def montar_base() -> tuple[pd.DataFrame, dict]:
    """Consolida estrutura + relações em um único DataFrame "longo",
    com uma linha por cruzamento Função x Gerência."""
    pilares = carregar_estrutura()
    relacoes = carregar_relacoes()

    funcao_para_pilar = {}
    for nome_pilar, info in pilares.items():
        for funcao in info["funcoes"]:
            funcao_para_pilar[funcao] = (nome_pilar, info["macroprocesso"])

    linhas = []
    for funcao, gerencia, papel in relacoes:
        pilar, macro = funcao_para_pilar[funcao]
        linhas.append(
            {
                "Pilar": pilar,
                "Macroprocesso": macro,
                "Função": funcao,
                "Gerência": gerencia,
                "Papel": papel,
            }
        )

    df = pd.DataFrame(linhas)
    return df, pilares


# ==============================================================================
# 4. FUNÇÕES DE APOIO (BUSCA, FILTROS E HTML)
# ==============================================================================

def normalizar_texto(texto: str) -> str:
    """Remove acentuação e caixa para permitir busca tolerante a acentos."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower().strip()


def filtrar_por_busca(df: pd.DataFrame, termo: str) -> pd.DataFrame:
    """Filtra linhas em que a Função OU a Gerência contenham o termo buscado."""
    if not termo:
        return df
    termo_norm = normalizar_texto(termo)
    mask = df["Função"].apply(lambda x: termo_norm in normalizar_texto(x)) | df["Gerência"].apply(
        lambda x: termo_norm in normalizar_texto(x)
    )
    return df[mask]


def badge_macro_html(macro: str) -> str:
    cor = CORES_MACRO[macro]
    return (
        f'<span class="badge-macro" style="background:{cor["bg"]}; color:{cor["text"]};">'
        f"{macro}</span>"
    )


def celula_papel_html(papel: str | None) -> str:
    """Gera o marcador visual (símbolo colorido) de cada célula da matriz."""
    if papel is None:
        return '<span class="celula-vazia">–</span>'
    cor = CORES_PAPEL[papel]
    return (
        f'<span class="celula-papel" style="color:{cor["bg"]};" '
        f'title="{cor["rotulo"]}">{cor["simbolo"]}</span>'
    )


def construir_tabela_html(df_pilar: pd.DataFrame, ordem_funcoes: list[str]) -> str:
    """Constrói a tabela HTML customizada (matriz Função x Gerência) para
    um pilar específico, já considerando os filtros aplicados.

    df_pilar: recorte já filtrado (busca + macroprocesso + gerências) do
              DataFrame longo, restrito ao pilar atual.
    ordem_funcoes: ordem original das funções dentro do pilar, para manter
                   a tabela sempre na mesma sequência lógica.
    """
    # Mantém apenas as funções que ainda possuem ao menos 1 relação visível
    # após os filtros, evitando linhas totalmente vazias.
    funcoes_visiveis = [f for f in ordem_funcoes if f in set(df_pilar["Função"])]
    if not funcoes_visiveis:
        return ""

    # Colunas (Gerências) relevantes = união das gerências que aparecem em
    # QUALQUER função deste pilar, após os filtros — ou seja, só aparecem
    # as gerências efetivamente relacionadas às funções em exibição.
    gerencias_visiveis = sorted(df_pilar["Gerência"].unique())

    # Dicionário rápido de acesso: (Função, Gerência) -> Papel
    mapa_papel = {(row["Função"], row["Gerência"]): row["Papel"] for _, row in df_pilar.iterrows()}

    # Mapa Função -> Macroprocesso (para o badge da primeira coluna)
    mapa_macro = df_pilar.drop_duplicates("Função").set_index("Função")["Macroprocesso"].to_dict()

    # ---------------- Cabeçalho ----------------
    colunas_header = "".join(
        f'<th title="{g}">{g}</th>' for g in gerencias_visiveis
    )
    thead = (
        "<thead><tr>"
        '<th class="col-funcao-header">Função</th>'
        f"{colunas_header}"
        "</tr></thead>"
    )

    # ---------------- Corpo da tabela ----------------
    linhas_html = []
    for funcao in funcoes_visiveis:
        macro = mapa_macro.get(funcao, "Apoio")
        celula_funcao = (
            f'<td class="col-funcao">{badge_macro_html(macro)}'
            f'<span class="nome-funcao">{funcao}</span></td>'
        )
        celulas = []
        for gerencia in gerencias_visiveis:
            papel = mapa_papel.get((funcao, gerencia))
            celulas.append(f"<td>{celula_papel_html(papel)}</td>")
        linhas_html.append(f"<tr>{celula_funcao}{''.join(celulas)}</tr>")

    tbody = f"<tbody>{''.join(linhas_html)}</tbody>"

    return f'<div class="tabela-wrapper"><table class="matriz-tabela">{thead}{tbody}</table></div>'


# ==============================================================================
# 5. COMPONENTES DE INTERFACE
# ==============================================================================

def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🏥 Matriz Área x Função — Santa Casa de Porto Alegre</div>
            <div class="hero-subtitle">
                Cruzamento entre as 38 Funções organizacionais (6 Pilares de Sinergia) e as
                22 Gerências/Áreas corporativas — Levantamento de Áreas 2026.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_legenda() -> None:
    itens_macro = "".join(
        f'<span class="legenda-item">'
        f'<span class="legenda-pill" style="background:{c["bg"]}; color:{c["text"]};">{nome}</span>'
        f"</span>"
        for nome, c in CORES_MACRO.items()
    )
    itens_papel = "".join(
        f'<span class="legenda-item">'
        f'<span class="legenda-simbolo" style="color:{c["bg"]};">{c["simbolo"]}</span> {c["rotulo"]}'
        f"</span>"
        for c in CORES_PAPEL.values()
    )
    st.markdown(
        f"""
        <div class="legenda-card">
            <div class="legenda-titulo">🎨 Macroprocesso (classificação da Função)</div>
            <div>{itens_macro}</div>
            <div class="legenda-titulo" style="margin-top:0.7rem;">🔵 Papel de responsabilidade na matriz</div>
            <div>{itens_papel}</div>
            <div style="font-size:0.78rem; color:#64748B; margin-top:0.5rem;">
                Células vazias (–) indicam que não há relação relevante mapeada entre aquela
                Função e aquela Gerência.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_estatisticas(df_visivel: pd.DataFrame, total_gerencias: int) -> None:
    total_funcoes = df_visivel["Função"].nunique()
    total_gerencias_ativas = df_visivel["Gerência"].nunique()
    total_relacoes = len(df_visivel)
    total_criticas = int((df_visivel["Papel"] == "R").sum())

    col1, col2, col3, col4 = st.columns(4)
    cartoes = [
        (col1, total_funcoes, "Funções visíveis"),
        (col2, f"{total_gerencias_ativas}/{total_gerencias}", "Gerências envolvidas"),
        (col3, total_relacoes, "Relações mapeadas"),
        (col4, total_criticas, "Papéis 'Responsável'"),
    ]
    for coluna, valor, rotulo in cartoes:
        with coluna:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-value">{valor}</div>
                    <div class="stat-label">{rotulo}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_sidebar(gerencias_todas: list[str]) -> tuple[str, str, list[str]]:
    """Renderiza os filtros da barra lateral e retorna
    (macro_filtro, termo_busca, gerencias_selecionadas)."""

    st.sidebar.markdown("## 🎛️ Painel de Filtros")
    st.sidebar.caption("Ajuste os filtros para focar em recortes específicos da matriz.")
    st.sidebar.markdown("---")

    # Inicializa valores padrão no session_state (necessário para o botão
    # de "Limpar filtros" funcionar corretamente).
    st.session_state.setdefault("macro_filtro", "Todos")
    st.session_state.setdefault("busca_funcao", "")
    st.session_state.setdefault("gerencias_selecionadas", gerencias_todas)

    st.sidebar.radio(
        "1️⃣ Macroprocesso",
        options=["Todos", "Finalístico", "Meio", "Apoio"],
        key="macro_filtro",
        help="Filtra os pilares/abas de acordo com a classificação de macroprocesso.",
    )

    st.sidebar.text_input(
        "2️⃣ Buscar Função ou Gerência",
        key="busca_funcao",
        placeholder="Ex.: leitos, farmácia, jurídico...",
        help="Busca por palavras-chave no nome da Função OU da Gerência.",
    )

    st.sidebar.multiselect(
        "3️⃣ Isolar Gerências específicas",
        options=gerencias_todas,
        key="gerencias_selecionadas",
        help="Remova gerências da lista para limpar o gráfico e focar em áreas específicas.",
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Limpar todos os filtros", use_container_width=True):
        st.session_state["macro_filtro"] = "Todos"
        st.session_state["busca_funcao"] = ""
        st.session_state["gerencias_selecionadas"] = gerencias_todas
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Fonte: Levantamento de Áreas 2026 — Redesenho Organizacional "
        "Santa Casa de Porto Alegre."
    )

    return (
        st.session_state["macro_filtro"],
        st.session_state["busca_funcao"],
        st.session_state["gerencias_selecionadas"],
    )


def render_exportacao(df_exportar: pd.DataFrame) -> None:
    """Renderiza os botões de download (CSV e Excel) para o recorte atual
    (todos os pilares/abas visíveis após os filtros aplicados)."""
    st.markdown("#### 📥 Exportar matriz filtrada (todas as abas visíveis)")
    col_csv, col_xlsx = st.columns(2)

    csv_bytes = df_exportar.to_csv(index=False).encode("utf-8-sig")
    with col_csv:
        st.download_button(
            label="⬇️ Baixar CSV",
            data=csv_bytes,
            file_name="matriz_area_funcao_filtrada.csv",
            mime="text/csv",
            use_container_width=True,
        )

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_exportar.to_excel(writer, index=False, sheet_name="Matriz Área x Função")
    with col_xlsx:
        st.download_button(
            label="⬇️ Baixar Excel",
            data=buffer.getvalue(),
            file_name="matriz_area_funcao_filtrada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ==============================================================================
# 6. APLICAÇÃO PRINCIPAL
# ==============================================================================

def main() -> None:
    df, pilares = montar_base()
    gerencias_todas = carregar_gerencias()

    render_hero()
    render_legenda()

    macro_filtro, termo_busca, gerencias_selecionadas = render_sidebar(gerencias_todas)

    # -------- Aplica os filtros globais (busca + gerências) --------------
    df_filtrado = filtrar_por_busca(df, termo_busca)
    df_filtrado = df_filtrado[df_filtrado["Gerência"].isin(gerencias_selecionadas)]

    if macro_filtro != "Todos":
        df_filtrado_macro = df_filtrado[df_filtrado["Macroprocesso"] == macro_filtro]
    else:
        df_filtrado_macro = df_filtrado

    render_estatisticas(df_filtrado_macro, total_gerencias=len(gerencias_todas))
    st.markdown("")

    # -------- Renderiza 1 aba por Pilar de Sinergia -----------------------
    nomes_pilares = list(pilares.keys())
    tabs = st.tabs(nomes_pilares)

    for tab, nome_pilar in zip(tabs, nomes_pilares):
        with tab:
            info_pilar = pilares[nome_pilar]
            macro_pilar = info_pilar["macroprocesso"]

            st.caption(
                f"Macroprocesso: {badge_macro_html(macro_pilar)}  |  "
                f"{len(info_pilar['funcoes'])} funções neste pilar",
            )
            # OBS: st.caption não renderiza HTML — usamos st.markdown abaixo
            # para garantir que o badge apareça formatado corretamente.
            st.markdown(
                f'Macroprocesso deste pilar: {badge_macro_html(macro_pilar)} '
                f'&nbsp;·&nbsp; {len(info_pilar["funcoes"])} funções mapeadas',
                unsafe_allow_html=True,
            )

            if macro_filtro != "Todos" and macro_filtro != macro_pilar:
                st.info(
                    f"ℹ️ Este pilar pertence ao macroprocesso **{macro_pilar}**. "
                    f"Ajuste o filtro de Macroprocesso na barra lateral para "
                    f"**Todos** ou **{macro_pilar}** para visualizar esta aba."
                )
                continue

            df_pilar = df_filtrado[df_filtrado["Pilar"] == nome_pilar]

            if df_pilar.empty:
                st.warning(
                    "⚠️ Nenhuma função ou gerência deste pilar corresponde aos "
                    "filtros atuais. Ajuste a busca ou as gerências selecionadas "
                    "na barra lateral."
                )
                continue

            html_tabela = construir_tabela_html(df_pilar, info_pilar["funcoes"])
            st.markdown(html_tabela, unsafe_allow_html=True)

    # -------- Exportação (considera todos os pilares após os filtros) -----
    st.markdown("---")
    render_exportacao(df_filtrado_macro)

    st.markdown("---")
    st.caption(
        "💡 Dica: passe o mouse sobre os símbolos ● e ◐ na matriz para ver o "
        "papel de responsabilidade completo daquele cruzamento."
    )


if __name__ == "__main__":
    main()
