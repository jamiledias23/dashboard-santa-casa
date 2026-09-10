# -*- coding: utf-8 -*-
"""
================================================================================
 DASHBOARD DE GOVERNANÇA ORGANIZACIONAL - SANTA CASA DE PORTO ALEGRE
 Matrizes: GEREX x Função | Unidade Operacional x Função | Entrega x Unidade
================================================================================

Autor: Engenharia de Dados / Design Organizacional
Objetivo: Visualizar, em formato de matriz de bolhas, o grau de sobreposição
          de responsabilidades identificado no levantamento de áreas (226
          respostas de formulário / 113 cargos detalhados), permitindo à
          liderança priorizar zonas críticas de redesenho organizacional.

Como rodar:
-----------
1) Terminal local:
       pip install streamlit pandas plotly
       streamlit run app.py

2) Google Colab:
       !pip install streamlit plotly -q
       !npm install -g localtunnel -q
       !streamlit run app.py &>/content/log.txt &
       !npx localtunnel --port 8501
   (Acesse a URL impressa pelo localtunnel; a senha é o IP externo do Colab,
    obtido com `!wget -q -O - ipv4.icanhazip.com`)

3) Streamlit Community Cloud:
       Suba este arquivo (app.py) num repositório GitHub com um
       requirements.txt contendo: streamlit / pandas / plotly
       e aponte o deploy para app.py.
================================================================================
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 1. CONFIGURAÇÃO GERAL DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Matrizes Organizacionais | Santa Casa POA",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Mapas visuais fixos, usados em todo o dashboard -----------------------------
# Peso (0 a 3) = nível de sobreposição/conflito de responsabilidade identificado
# nas respostas do levantamento de áreas. 0 = função bem alocada, sem disputa;
# 3 = sobreposição crítica (múltiplas áreas reivindicando ou "empurrando" a
# mesma entrega).
COR_POR_PESO = {
    0: "#BDBDBD",  # cinza  -> sem sobreposição relevante
    1: "#1f77b4",  # azul   -> sobreposição leve / interface normal
    2: "#FF7F0E",  # laranja-> sobreposição moderada, requer atenção
    3: "#D62728",  # vermelho -> sobreposição crítica, ação prioritária
}
ROTULO_POR_PESO = {
    0: "0 · Sem sobreposição",
    1: "1 · Sobreposição leve",
    2: "2 · Sobreposição moderada",
    3: "3 · Sobreposição crítica",
}
# Tamanho do marcador em pixels. É crescente e proporcional ao peso; usa-se um
# piso mínimo de 10px apenas para que o peso 0 (sem sobreposição) permaneça
# visível como referência no mapa, e não desapareça do gráfico.
TAMANHO_POR_PESO = {0: 10, 1: 18, 2: 26, 3: 36}


# ==============================================================================
# 2. CAMADA DE DADOS
# ==============================================================================
# Os dados abaixo consolidam, em formato longo (uma linha por cruzamento),
# o resultado da análise das respostas do Levantamento de Áreas 2026.
# Cada matriz é representada por uma lista de tuplas:
#   (eixo_x, eixo_y, peso, objetivo, entrega_principal, alerta_sobreposicao,
#    recomendacao_governanca)
#
# Em um pipeline de produção, este bloco seria substituído por uma consulta a
# um data warehouse (ex.: tabela fato "cruzamentos_estrutura" alimentada pelo
# ETL do formulário). Aqui ele é declarado localmente para que o dashboard
# rode de forma autocontida, sem dependência de arquivos externos.
# ------------------------------------------------------------------------------

def _construir_dataframe(registros: list[tuple], nome_eixo_x: str, nome_eixo_y: str) -> pd.DataFrame:
    """Converte uma lista de tuplas cruas em um DataFrame padronizado,
    já enriquecido com as colunas visuais (cor e tamanho do marcador)."""
    colunas = [
        "eixo_x", "eixo_y", "peso", "objetivo",
        "entrega_principal", "alerta_sobreposicao", "recomendacao",
    ]
    df = pd.DataFrame(registros, columns=colunas)
    df["cor"] = df["peso"].map(COR_POR_PESO)
    df["tamanho"] = df["peso"].map(TAMANHO_POR_PESO)
    df["peso_rotulo"] = df["peso"].map(ROTULO_POR_PESO)
    df.attrs["rotulo_x"] = nome_eixo_x
    df.attrs["rotulo_y"] = nome_eixo_y
    return df


@st.cache_data
def carregar_dados() -> dict[str, pd.DataFrame]:
    """Monta as 3 matrizes organizacionais e retorna um dicionário
    {nome_da_matriz: DataFrame}. Cacheado para não reprocessar a cada
    interação do usuário na sidebar."""

    # --------------------------------------------------------------------
    # MATRIZ 1 · GEREX (Gerência Executiva/Corporativa) x FUNÇÃO
    # --------------------------------------------------------------------
    # Leitura da matriz: cada célula responde "o quanto esta GEREX está
    # hoje envolvida na execução desta Função, e o quanto isso é uma
    # sobreposição frente ao dono natural da função".
    matriz_gerex_funcao = [
        ("GEREX Enfermagem", "Supervisão Assistencial", 0,
         "Prestação direta de cuidado ao paciente pela equipe de enfermagem.",
         "Escalas e cuidado assistencial",
         "Função nuclear da área; nenhuma sobreposição relevante identificada.",
         "Manter como está — função corretamente alocada."),
        ("GEREX Enfermagem", "Gestão de Leitos / NIR", 2,
         "Apoio à regulação de leitos e integração bloco cirúrgico x UTI x internação.",
         "Giro de leitos por unidade",
         "Enfermagem atua na ponta da regulação sem um enfermeiro de referência formal no NIR, gerando duplicidade de comando.",
         "Formalizar 1 enfermeiro(a) de referência do NIR por turno, com alçada clara sobre priorização de leitos."),
        ("GEREX Enfermagem", "Administração de Pessoal", 3,
         "Controle de ponto, escala e desligamento da equipe de enfermagem.",
         "Fechamento de ponto e escalas",
         "Recorrente em dezenas de respostas: supervisores de enfermagem revisam ponto e conduzem desligamentos manualmente, tarefa que deveria ser do RH.",
         "Migrar validação de ponto/escala para o sistema de RH com aprovação por exceção da liderança assistencial."),
        ("GEREX Enfermagem", "Educação Corporativa / Capacitação", 2,
         "Treinamento técnico da equipe assistencial em protocolos e POPs.",
         "Treinamentos e formação funcional",
         "Supervisão assistencial conduz treinamentos e revisa POPs que deveriam ser centralizados na Educação Corporativa/Qualidade.",
         "Centralizar logística e registro de treinamentos na Educação Corporativa; manter conteúdo técnico com a Enfermagem."),

        ("GEREX Operações", "Gestão de Leitos / NIR", 2,
         "Governança da capacidade hospitalar e giro de leitos.",
         "Ocupação e giro de leitos",
         "Leitos de especialidades (cardiologia, pediatria, obstetrícia, TMO) mantêm gestão própria fora do NIR, fragmentando a governança única.",
         "Consolidar todos os leitos sob governança única do NIR, mantendo critérios clínicos com as especialidades."),
        ("GEREX Operações", "Administração de Pessoal", 2,
         "Gestão de equipes operacionais (hotelaria, recepção, segurança).",
         "Escalas de equipes operacionais",
         "Supervisores de operações fazem controle manual de ponto/horas extras, sem apoio sistêmico do RH.",
         "Automatizar apuração de ponto operacional com alertas de cobertura, liberando a supervisão para gestão de indicadores."),
        ("GEREX Operações", "Compras e Contratos", 1,
         "Aquisição de insumos para atividades acessórias (estacionamento, cemitério, hotelaria).",
         "Reposição de insumos operacionais",
         "Interface normal de demanda; sem indícios de disputa relevante.",
         "Manter fluxo atual de solicitação via sistema."),

        ("GEREX Suprimentos", "Compras e Contratos", 0,
         "Aquisição, cadastro, planejamento e logística de materiais e medicamentos.",
         "Abastecimento institucional",
         "Função nuclear da área; sem sobreposição relevante.",
         "Manter como está — função corretamente alocada."),
        ("GEREX Suprimentos", "Manutenção de Equipamentos", 1,
         "Aquisição de equipamentos médico-hospitalares e insumos de manutenção.",
         "Compra de equipamentos e peças",
         "Interface esperada com Engenharia Clínica na especificação técnica de compras.",
         "Formalizar checklist conjunto Suprimentos-Engenharia Clínica para compras de equipamentos."),
        ("GEREX Suprimentos", "Administração de Pessoal", 1,
         "Contratação de prestadores de serviço (PJ) tramitada operacionalmente por Compras.",
         "Formalização de contratos PJ",
         "Contratação de médicos PJ e prestadores do CHC tramita hoje por Compras, mas a decisão e a gestão são do RH/áreas fim.",
         "Migrar a etapa de formalização contratual de PJ para o RH, mantendo Compras apenas no registro sistêmico."),

        ("GEREX Financeiro", "Faturamento e Ciclo da Receita", 0,
         "Gestão do caixa, contas a pagar/receber e sustentabilidade financeira.",
         "Fluxo de caixa e resultado financeiro",
         "Função nuclear da área; sobreposição pontual com o Comercial em negociação de reajustes.",
         "Formalizar matriz de alçadas entre Financeiro e Comercial para negociações com operadoras."),
        ("GEREX Financeiro", "Gestão de Leitos / NIR", 3,
         "Governança do contrato SUS, com impacto direto na regulação do acesso.",
         "Gestão do contrato e produção SUS",
         "Contrato SUS hoje tem duplo reporte entre Gerência de Operações e Financeiro, sem definição de área única responsável.",
         "Definir formalmente 1 área dona do contrato SUS (recomenda-se Operações, com Financeiro em apoio técnico)."),
        ("GEREX Financeiro", "Compras e Contratos", 1,
         "Aprovação orçamentária e priorização de pagamentos a fornecedores.",
         "Priorização de pagamentos",
         "Interface esperada de aprovação financeira; sem indícios de disputa relevante.",
         "Manter fluxo atual de aprovação por alçada."),

        ("GEREX Gestão de Pessoas", "Administração de Pessoal", 0,
         "Folha de pagamento, ponto, férias, rescisões e relações trabalhistas.",
         "Folha de pagamento e conformidade trabalhista",
         "Função nuclear da área; sem sobreposição relevante.",
         "Manter como está — função corretamente alocada."),
        ("GEREX Gestão de Pessoas", "Educação Corporativa / Capacitação", 2,
         "Capacitação técnica e comportamental de lideranças e equipes.",
         "Trilhas de capacitação institucional",
         "Sobreposição não resolvida entre Educação Corporativa (RH) e a área de Ensino na formação de médicos celetistas do corpo clínico.",
         "Unificar a formação de médicos celetistas em uma única área (Educação Corporativa ou Ensino), eliminando a duplicidade de plataformas."),

        ("GEREX Qualidade", "Educação Corporativa / Capacitação", 2,
         "Revisão de POPs, protocolos assistenciais e auditorias de conformidade.",
         "POPs e protocolos assistenciais",
         "Qualidade e Educação Corporativa disputam quem conduz a revisão/registro de treinamentos e POPs, gerando retrabalho.",
         "Definir Qualidade como dona técnica dos POPs e Educação Corporativa como dona da logística/registro de treinamento."),
        ("GEREX Qualidade", "Coordenação Médica", 1,
         "Apoio a protocolos clínicos, indicadores de segurança e acreditação.",
         "Indicadores de segurança assistencial",
         "Interface esperada e bem resolvida na maioria das respostas.",
         "Manter fóruns mensais conjuntos de indicadores de segurança."),

        ("GEREX TI e Inovação", "Manutenção de Equipamentos", 3,
         "Integração de sistemas, conectividade e software de equipamentos médicos digitais.",
         "Integração de equipamentos médicos digitais",
         "TI e Engenharia Clínica não têm fronteira formalizada em projetos de integração de equipamentos médicos (ex.: PACS, imagem digital).",
         "Criar comitê conjunto TI + Engenharia Clínica com escopo formal por tipo de projeto (rede/dados = TI; hardware clínico = Eng. Clínica)."),
        ("GEREX TI e Inovação", "Faturamento e Ciclo da Receita", 1,
         "Suporte a sistemas de faturamento e parametrizações do ERP.",
         "Sustentação de sistemas de faturamento",
         "Interface técnica esperada; sem indícios de disputa relevante.",
         "Manter fluxo atual de chamados e SLA de atendimento."),
        ("GEREX TI e Inovação", "Gestão de Leitos / NIR", 1,
         "Automação e dashboards de ocupação e regulação hospitalar.",
         "Painéis de ocupação hospitalar",
         "Interface técnica esperada; sem indícios de disputa relevante.",
         "Manter roadmap conjunto de automação do NIR."),

        ("GEREX Engenharia e Infraestrutura", "Manutenção de Equipamentos", 0,
         "Manutenção preventiva/corretiva de infraestrutura predial e equipamentos.",
         "Disponibilidade de infraestrutura",
         "Função nuclear da área; sobreposição pontual com TI em projetos digitais (ver GEREX TI).",
         "Manter escopo predial/eletromecânico com Engenharia; digital/rede com TI."),
        ("GEREX Engenharia e Infraestrutura", "Compras e Contratos", 1,
         "Especificação técnica para aquisição de equipamentos e obras.",
         "Especificação técnica de compras",
         "Interface esperada de validação técnica; sem indícios de disputa relevante.",
         "Manter checklist técnico conjunto com Suprimentos."),
    ]
    df1 = _construir_dataframe(matriz_gerex_funcao, "GEREX", "Função")

    # --------------------------------------------------------------------
    # MATRIZ 2 · UNIDADE OPERACIONAL x FUNÇÃO
    # --------------------------------------------------------------------
    # Leitura da matriz: o quanto cada hospital/unidade apresenta desvio ou
    # inconsistência de modelo na execução de cada função-padrão do complexo.
    matriz_unidade_funcao = [
        ("HDJB (Gravataí)", "Faturamento e Ciclo da Receita", 3,
         "Autorizações e faturamento local do Hospital Dom João Becker.",
         "Fechamento de contas locais",
         "HDJB opera central de agendamento/autorizações sem acesso aos chatbots, IA e automações de faturamento implantados na matriz — trilhas paralelas e isoladas.",
         "Integrar HDJB à mesma esteira digital de faturamento/autorização da matriz, eliminando o processo manual paralelo."),
        ("HDJB (Gravataí)", "Administração de Pessoal", 2,
         "Gestão de pessoal em modelo estrutural mais vertical que os demais hospitais.",
         "Gestão de escalas e ponto local",
         "Modelo organizacional do HDJB é mais verticalizado (recuperação financeira) e diverge do modelo horizontal dos demais hospitais.",
         "Definir explicitamente o HDJB como exceção de modelo (vertical) no desenho organizacional, evitando padronização forçada."),
        ("HDJB (Gravataí)", "Manutenção Predial", 1,
         "Manutenção de infraestrutura predial e equipamentos da unidade.",
         "Disponibilidade predial local",
         "Interface local resolvida, com equipe própria de manutenção e engenharia clínica.",
         "Manter modelo atual, com reporte técnico à Engenharia corporativa."),
        ("HSC (Santa Clara)", "Gestão de Leitos / NIR", 2,
         "Maior hospital geral do complexo, porta de entrada SUS.",
         "Giro de leitos de alta complexidade",
         "Volume elevado e leitos de especialidades (UTI cardíaca, neonatal) com gestão própria fora do NIR único.",
         "Priorizar o HSC no plano de consolidação da governança única de leitos pelo NIR."),
        ("HSF (São Francisco)", "Relacionamento com Corpo Clínico", 2,
         "Hospital de referência em especialidades com diretores médicos historicamente influentes.",
         "Relacionamento e agenda médica",
         "Múltiplos diretores/coordenadores médicos especialistas atuam com forte autonomia, dificultando padronização de processos entre especialidades.",
         "Estabelecer fórum único de coordenação médica do HSF com pauta e alçada de decisão formalizadas."),
        ("HSJ (São José)", "Supervisão Assistencial", 1,
         "Assistência hospitalar geral.",
         "Cuidado assistencial padronizado",
         "Sem indícios de desvio relevante frente ao modelo padrão.",
         "Manter monitoramento padrão via indicadores corporativos."),
        ("PPF (Pereira Filho)", "Supervisão Assistencial", 1,
         "Assistência em reabilitação pulmonar e cuidados de longa permanência.",
         "Reabilitação e cuidado continuado",
         "Perfil assistencial específico (reabilitação) pouco representado nos indicadores corporativos padrão.",
         "Criar indicador específico de reabilitação/permanência para o PPF dentro do painel corporativo."),
        ("HCSA (Criança Santo Antônio)", "Gestão de Leitos / NIR", 1,
         "Hospital pediátrico, com leitos de UTI neonatal e pediátrica.",
         "Giro de leitos pediátricos",
         "Leitos pediátricos/neonatais mantidos com gestão própria por especificidade clínica.",
         "Manter critério clínico pediátrico com a especialidade, mas reportar disponibilidade ao NIR em tempo real."),
        ("HDVS (Dom Vicente Scherer)", "Administração de Pessoal", 1,
         "Centro de referência em transplantes.",
         "Gestão de escalas de equipe de transplante",
         "Sem indícios de desvio relevante frente ao modelo padrão.",
         "Manter monitoramento padrão via indicadores corporativos."),
        ("HNT (Nora Teixeira)", "Faturamento e Ciclo da Receita", 1,
         "Unidade com maior foco em atendimento particular/convênio.",
         "Faturamento particular e convênios",
         "Volume relevante de faturamento particular exige rotina própria de conferência, sem indícios de conflito estrutural.",
         "Manter rotina local, com auditoria periódica corporativa."),
    ]
    df2 = _construir_dataframe(matriz_unidade_funcao, "Unidade Operacional", "Função")

    # --------------------------------------------------------------------
    # MATRIZ 3 · ENTREGA x UNIDADE OPERACIONAL
    # --------------------------------------------------------------------
    # Leitura da matriz: o quanto cada unidade apresenta risco/gap na
    # entrega-chave analisada (independentemente de qual área a executa).
    matriz_entrega_unidade = [
        ("HDJB (Gravataí)", "Faturamento sem Glosa", 3,
         "Entrega de contas fechadas corretamente, sem necessidade de retrabalho.",
         "Redução de glosas e retrabalho",
         "Sistemas isolados da matriz geram duplicação de processos e maior risco de erro/retrabalho no fechamento de contas.",
         "Priorizar integração sistêmica do HDJB como pré-requisito antes de qualquer meta de redução de glosa."),
        ("HDJB (Gravataí)", "Capacitação de Equipes", 2,
         "Formação técnica continuada das equipes locais.",
         "Trilhas de capacitação aplicadas",
         "Modelo de educação corporativa nem sempre alcança a unidade com a mesma frequência da matriz.",
         "Incluir o HDJB no calendário corporativo de capacitação com meta de cobertura equivalente à matriz."),
        ("HSC (Santa Clara)", "Gestão de Leitos", 2,
         "Disponibilidade e giro adequado de leitos de alta complexidade.",
         "Taxa de ocupação e giro de leitos",
         "Fragmentação da governança de leitos entre NIR e especialidades gera ociosidade e atrasos de alocação.",
         "Medir e reportar mensalmente o impacto da fragmentação de leitos no HSC como indicador de acompanhamento do projeto."),
        ("HSJ (São José)", "Segurança do Paciente", 1,
         "Prevenção de eventos adversos e adesão a protocolos de segurança.",
         "Indicadores de segurança assistencial",
         "Sem indícios de gap relevante frente ao padrão corporativo.",
         "Manter monitoramento padrão via indicadores corporativos."),
        ("HSF (São Francisco)", "Comunicação com Corpo Clínico", 2,
         "Alinhamento de fluxos, escalas e decisões com o corpo clínico especializado.",
         "Comunicação e alinhamento médico",
         "Autonomia elevada de diretores médicos dificulta comunicação padronizada de mudanças de processo.",
         "Criar canal formal único de comunicação de mudanças de processo para o corpo clínico do HSF."),
        ("PPF (Pereira Filho)", "Capacitação de Equipes", 1,
         "Formação técnica voltada a reabilitação e cuidado de longa permanência.",
         "Trilhas de capacitação em reabilitação",
         "Sem indícios de gap relevante frente ao padrão corporativo.",
         "Manter monitoramento padrão via indicadores corporativos."),
        ("HCSA (Criança Santo Antônio)", "Gestão de Leitos", 1,
         "Disponibilidade de leitos pediátricos/neonatais.",
         "Giro de leitos pediátricos",
         "Especificidade clínica pediátrica gera leve desalinhamento com a governança geral do NIR.",
         "Reportar leitos pediátricos ao painel único do NIR, mantendo decisão clínica com a especialidade."),
        ("HDVS (Dom Vicente Scherer)", "Manutenção Preventiva", 1,
         "Disponibilidade de infraestrutura crítica para transplantes.",
         "Continuidade operacional de equipamentos críticos",
         "Sem indícios de gap relevante frente ao padrão corporativo.",
         "Manter monitoramento padrão via indicadores corporativos."),
        ("HNT (Nora Teixeira)", "Faturamento sem Glosa", 1,
         "Fechamento de contas particulares/convênio sem glosa.",
         "Redução de glosas em convênios",
         "Sem indícios de gap relevante frente ao padrão corporativo.",
         "Manter auditoria periódica corporativa."),
    ]
    df3 = _construir_dataframe(matriz_entrega_unidade, "Unidade Operacional", "Entrega")

    return {
        "GEREX x Função": df1,
        "Unidade Operacional x Função": df2,
        "Entrega x Unidade Operacional": df3,
    }


# ==============================================================================
# 3. COMPONENTES DE VISUALIZAÇÃO
# ==============================================================================

def criar_grafico_bolhas(df: pd.DataFrame, rotulo_x: str, rotulo_y: str, titulo: str) -> go.Figure:
    """Gera o gráfico de bolhas matricial (Plotly Scatter) para o DataFrame
    filtrado, com tamanho proporcional ao peso e cor por nível de alerta."""

    fig = go.Figure()

    # Uma trace por nível de peso, para que a legenda funcione como filtro
    # nativo de "nível de alerta" dentro do próprio gráfico.
    for peso in sorted(df["peso"].unique()):
        subset = df[df["peso"] == peso]
        if subset.empty:
            continue

        # customdata carrega os campos exibidos no tooltip, na ordem usada
        # pelo hovertemplate abaixo.
        customdata = subset[["objetivo", "entrega_principal", "alerta_sobreposicao", "peso"]].values

        fig.add_trace(
            go.Scatter(
                x=subset["eixo_x"],
                y=subset["eixo_y"],
                mode="markers",
                name=ROTULO_POR_PESO[peso],
                marker=dict(
                    size=subset["tamanho"],
                    color=COR_POR_PESO[peso],
                    line=dict(width=1, color="white"),
                    opacity=0.85,
                ),
                customdata=customdata,
                hovertemplate=(
                    "<b>%{x} × %{y}</b><br><br>"
                    "<b>Objetivo da relação:</b> %{customdata[0]}<br>"
                    "<b>Principal entrega:</b> %{customdata[1]}<br>"
                    "<b>Alerta de sobreposição:</b> %{customdata[2]}<br>"
                    "<b>Peso:</b> %{customdata[3]} / 3"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=dict(text=titulo, x=0.02, xanchor="left", font=dict(size=20)),
        xaxis=dict(title=rotulo_x, type="category", tickangle=-30, showgrid=True, gridcolor="#EEEEEE"),
        yaxis=dict(title=rotulo_y, type="category", showgrid=True, gridcolor="#EEEEEE"),
        legend=dict(title="Nível de sobreposição", orientation="h", y=-0.25),
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=60, b=10),
        height=620,
    )
    return fig


def render_diagnostico(df: pd.DataFrame) -> None:
    """Renderiza o painel de diagnóstico rápido: métricas-resumo e a lista
    expansível de recomendações de governança para o recorte atual."""

    st.subheader("📊 Diagnóstico Rápido")

    total_cruzamentos = len(df)
    zonas_criticas = int((df["peso"] == 3).sum())
    zonas_moderadas = int((df["peso"] == 2).sum())
    peso_medio = round(df["peso"].mean(), 2) if total_cruzamentos else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🟥 Zonas Críticas (peso 3)", zonas_criticas)
    col2.metric("🟧 Zonas Moderadas (peso 2)", zonas_moderadas)
    col3.metric("📈 Peso médio do recorte", peso_medio)
    col4.metric("🔎 Cruzamentos exibidos", total_cruzamentos)

    if zonas_criticas > 0:
        st.error(
            f"⚠️ Há **{zonas_criticas} cruzamento(s) crítico(s)** no recorte atual — "
            "recomenda-se priorização imediata na governança do redesenho."
        )

    # Lista expansível com recomendações, ordenada da maior para a menor
    # severidade, incluindo apenas cruzamentos com peso >= 2 (moderado ou
    # crítico), que são os que efetivamente demandam ação de governança.
    relevantes = df[df["peso"] >= 2].sort_values("peso", ascending=False)

    with st.expander(f"📋 Recomendações de Governança ({len(relevantes)} itens com peso ≥ 2)", expanded=False):
        if relevantes.empty:
            st.info("Nenhum cruzamento com sobreposição moderada/crítica no recorte atual selecionado.")
        else:
            for _, row in relevantes.iterrows():
                emoji = "🟥" if row["peso"] == 3 else "🟧"
                st.markdown(
                    f"""
{emoji} **{row['eixo_x']} × {row['eixo_y']}** — *peso {row['peso']}*
- **Alerta:** {row['alerta_sobreposicao']}
- **Recomendação:** {row['recomendacao']}
---
"""
                )


# ==============================================================================
# 4. APLICAÇÃO PRINCIPAL (SIDEBAR + LAYOUT)
# ==============================================================================

def main() -> None:
    dados = carregar_dados()

    # --------------------------- SIDEBAR ------------------------------------
    st.sidebar.title("🏥 Painel de Controle")
    st.sidebar.markdown("Levantamento de Áreas 2026 — Redesenho Organizacional")
    st.sidebar.markdown("---")

    matriz_selecionada = st.sidebar.radio(
        "1️⃣ Selecione a matriz de análise:",
        options=list(dados.keys()),
        index=0,
    )

    df_base = dados[matriz_selecionada]
    rotulo_x = df_base.attrs["rotulo_x"]
    rotulo_y = df_base.attrs["rotulo_y"]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**2️⃣ Filtros dinâmicos ({matriz_selecionada})**")

    opcoes_x = sorted(df_base["eixo_x"].unique())
    opcoes_y = sorted(df_base["eixo_y"].unique())

    filtro_x = st.sidebar.multiselect(
        f"Filtrar {rotulo_x}:", options=opcoes_x, default=opcoes_x,
        help="Remova itens para limpar o gráfico e focar em áreas específicas.",
    )
    filtro_y = st.sidebar.multiselect(
        f"Filtrar {rotulo_y}:", options=opcoes_y, default=opcoes_y,
        help="Remova itens para limpar o gráfico e focar em funções/entregas específicas.",
    )

    filtro_peso_min = st.sidebar.slider(
        "Peso mínimo de sobreposição a exibir:",
        min_value=0, max_value=3, value=0,
        help="Use para exibir apenas cruzamentos a partir de determinado nível de alerta.",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Peso 0-3 representa o nível de sobreposição/conflito de responsabilidade "
        "identificado nas respostas do Levantamento de Áreas: "
        "0 = função bem alocada · 3 = sobreposição crítica."
    )

    # Aplica os filtros escolhidos pelo usuário
    df_filtrado = df_base[
        df_base["eixo_x"].isin(filtro_x)
        & df_base["eixo_y"].isin(filtro_y)
        & (df_base["peso"] >= filtro_peso_min)
    ].copy()

    # --------------------------- ÁREA PRINCIPAL -----------------------------
    st.title(f"Matriz: {matriz_selecionada}")
    st.caption(
        "Bolhas maiores e mais quentes (laranja/vermelho) indicam maior "
        "sobreposição de responsabilidade entre as áreas cruzadas. "
        "Passe o mouse sobre qualquer bolha para ver o detalhe do cruzamento."
    )

    if df_filtrado.empty:
        st.warning(
            "Nenhum cruzamento atende aos filtros selecionados. "
            "Ajuste os filtros na barra lateral para visualizar o gráfico."
        )
        return

    fig = criar_grafico_bolhas(
        df_filtrado,
        rotulo_x=rotulo_x,
        rotulo_y=rotulo_y,
        titulo=f"{rotulo_x} × {rotulo_y} — Mapa de Sobreposição de Responsabilidades",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    render_diagnostico(df_filtrado)

    # Rodapé com nota metodológica
    st.markdown("---")
    st.caption(
        "Fonte: Levantamento de Áreas — Redesenho Organizacional Santa Casa de Porto Alegre "
        "(226 respostas / 113 cargos detalhados analisados). "
        "Pesos e alertas consolidados a partir das respostas sobre objetivo, entregas, "
        "áreas relacionadas e conflitos/duplicidades reportados por cada cargo."
    )


if __name__ == "__main__":
    main()
