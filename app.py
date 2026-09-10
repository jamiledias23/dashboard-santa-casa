# -*- coding: utf-8 -*-
"""
================================================================================
 MATRIZ ÁREA x FUNÇÃO — SANTA CASA DE PORTO ALEGRE (VISUALIZAÇÃO EM BOLHAS)
 Cruzamento de 38 Funções (organizadas em 6 Pilares de Sinergia) x
 22 Gerências/Áreas corporativas, com foco em sobreposições/conflitos.
================================================================================

Como rodar:
-----------
1) Terminal local:
       pip install -r requirements.txt
       streamlit run app.py

2) Streamlit Community Cloud:
       Suba este arquivo (app.py) + requirements.txt para o repositório
       GitHub já existente, substituindo a versão anterior, e aguarde o
       redeploy automático.

Observação sobre os dados:
---------------------------
As relações Função x Gerência (bloco `carregar_relacoes`) estão mockadas
para fins de demonstração, incluindo o texto de "ponto de atenção /
sobreposição" de cada cruzamento. Em produção, este bloco deve ser
substituído por uma consulta à base real, mantendo o mesmo formato de
saída: uma lista de tuplas (Função, Gerência, Papel, Ponto de Atenção).
================================================================================
"""

import io
import unicodedata

import pandas as pd
import plotly.graph_objects as go
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

# Paleta de cores por papel de responsabilidade dentro da matriz.
CORES_PAPEL = {
    "R": {"rotulo": "Responsável (dona da entrega)", "cor": "#2563EB", "tamanho": 32},
    "A": {"rotulo": "Apoio / Interface",              "cor": "#F59E0B", "tamanho": 20},
}

# Paleta de cores por Macroprocesso (usada apenas no selo/legenda de cada aba).
CORES_MACRO = {
    "Finalístico": {"bg": "#E7F8EE", "text": "#15803D"},
    "Meio":        {"bg": "#EAF2FE", "text": "#1D4ED8"},
    "Apoio":       {"bg": "#F1F2F4", "text": "#334155"},
}

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

    .hero-container {
        padding: 1.6rem 1.8rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #0F2A4A 0%, #1B4B7A 55%, #2E6DA4 100%);
        color: white;
        margin-bottom: 1.1rem;
        box-shadow: 0 8px 24px rgba(15, 42, 74, 0.18);
    }
    .hero-title { font-size: 1.6rem; font-weight: 800; margin-bottom: 0.2rem; }
    .hero-subtitle { font-size: 0.92rem; opacity: 0.9; }

    .stat-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 0.9rem 1.1rem;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05);
    }
    .stat-value { font-size: 1.55rem; font-weight: 800; color: #0F2A4A; line-height: 1.1; }
    .stat-label { font-size: 0.76rem; color: #64748B; font-weight: 600; text-transform: uppercase; }

    .legenda-card {
        border-radius: 14px;
        border: 1px solid #E5E7EB;
        background: #FAFBFC;
        padding: 1rem 1.2rem;
        margin-bottom: 1.1rem;
    }
    .legenda-titulo { font-weight: 700; font-size: 0.92rem; color: #0F2A4A; margin-bottom: 0.5rem; }
    .legenda-item {
        display: inline-flex; align-items: center; gap: 0.4rem;
        margin-right: 1.4rem; margin-bottom: 0.3rem; font-size: 0.84rem; color: #1E293B;
    }
    .legenda-bolha {
        display: inline-block; width: 13px; height: 13px; border-radius: 50%;
    }
    .legenda-pill {
        display: inline-block; padding: 0.12rem 0.55rem; border-radius: 999px;
        font-weight: 700; font-size: 0.76rem;
    }
    .selo-macro {
        display: inline-block; padding: 0.15rem 0.65rem; border-radius: 999px;
        font-weight: 700; font-size: 0.78rem; margin-left: 0.4rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# 2. CAMADA DE DADOS (MOCK)
# ==============================================================================

def carregar_estrutura() -> dict:
    """Estrutura dos 6 Pilares de Sinergia. Os nomes das Funções já seguem o
    padrão de verbo de ação solicitado ("Gerenciar ...")."""
    return {
        "1️⃣ Operações Assistenciais": {
            "macroprocesso": "Finalístico",
            "funcoes": [
                "Gerenciar Pronto Socorro",
                "Gerenciar Unidade de Internação",
                "Gerenciar Serviços Ambulatoriais",
                "Gerenciar Procedimentos Cirúrgicos",
                "Gerenciar Medicina Diagnóstica",
            ],
        },
        "2️⃣ Gestão de Fluxo e Apoio Clínico": {
            "macroprocesso": "Meio",
            "funcoes": [
                "Gerenciar Leitos e NIR",
                "Gerenciar Atendimento ao Paciente",
                "Gerenciar Farmácia",
                "Gerenciar Logística de Medicamentos",
                "Gerenciar Nutrição Clínica",
                "Gerenciar Documentação Assistencial",
                "Gerenciar Epidemiologia e Infecção Hospitalar",
            ],
        },
        "3️⃣ Hotelaria, Logística e Infraestrutura": {
            "macroprocesso": "Meio",
            "funcoes": [
                "Gerenciar Higienização",
                "Gerenciar Rouparia",
                "Gerenciar Esterilização",
                "Gerenciar Manutenção Predial",
                "Gerenciar Engenharia Clínica",
                "Gerenciar Obras",
                "Gerenciar Segurança",
                "Gerenciar Suprimentos",
            ],
        },
        "4️⃣ Mercado e Ciclo de Receita": {
            "macroprocesso": "Apoio",
            "funcoes": [
                "Gerenciar Comercial",
                "Gerenciar Produto",
                "Gerenciar Faturamento",
                "Gerenciar Finanças e Controladoria",
                "Gerenciar Marketing",
                "Gerenciar Filantropia",
                "Gerenciar Inovação e Planejamento",
            ],
        },
        "5️⃣ Capital Humano e Governança Clínica": {
            "macroprocesso": "Apoio",
            "funcoes": [
                "Gerenciar Pessoal",
                "Gerenciar Administração de Pessoal",
                "Gerenciar SESMT",
                "Gerenciar Relacionamento Médico",
                "Gerenciar Práticas Médicas",
                "Gerenciar Resultados e Práticas Assistenciais",
            ],
        },
        "6️⃣ Governança Corporativa e Suporte": {
            "macroprocesso": "Apoio",
            "funcoes": [
                "Gerenciar Governança Corporativa",
                "Gerenciar Jurídico",
                "Gerenciar Qualidade",
                "Gerenciar TI",
                "Gerenciar Ensino e Pesquisa",
            ],
        },
    }


def carregar_gerencias() -> list[str]:
    """Lista oficial das 22 Gerências/Áreas existentes hoje na instituição
    (nome completo — usado em filtros, hover e exportação)."""
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


def carregar_abreviacoes() -> dict:
    """Rótulos curtos (com quebra de linha via <br>) usados no eixo X do
    gráfico, para reduzir a necessidade de rolagem horizontal. O nome
    completo continua disponível no hover."""
    return {
        "Gerente Corporativo Relacionamento com corpo clinico e clientes": "Rel. Corpo<br>Clínico/Clientes",
        "Gerente Ensino e Pesquisa": "Ensino e<br>Pesquisa",
        "Gerente de Gestão de Pessoas": "Gestão de<br>Pessoas",
        "Gerente Comunic. e Marketing": "Comunic. e<br>Marketing",
        "Gerente de Infraestrutura": "Infraestrutura",
        "Gerente de Modernização": "Modernização",
        "Gerente de Relações Institucionais": "Relações<br>Institucionais",
        "Gerente de Suprimentos": "Suprimentos",
        "Gerente PMO": "PMO",
        "Gerente Projetos de Captação": "Projetos de<br>Captação",
        "Gerente Corporativo Enfermagem": "Enfermagem<br>Corporativa",
        "Gerente de Qualidade": "Qualidade",
        "Gerente Médico": "Médico",
        "Gerente Segurança Assistencial": "Segurança<br>Assistencial",
        "Gerente Comercial": "Comercial",
        "Gerente de Controladoria": "Controladoria",
        "Gerente de Faturamento": "Faturamento",
        "Gerente Financeiro": "Financeiro",
        "Gerente Jurídico": "Jurídico",
        "Gerente Tecnologia e Inovação": "Tecnologia e<br>Inovação",
        "Gerente Corporativo Operações": "Operações<br>Corporativas",
        "Gerente Hospitalar": "Hospitalar",
    }


def carregar_relacoes() -> list[tuple[str, str, str, str]]:
    """Relações Função x Gerência mockadas:
    (Função, Gerência, Papel, Ponto de Atenção / Sobreposição).
    Papel: "R" = Responsável (dona da entrega) | "A" = Apoio / Interface.
    O 4º campo é o texto exibido no hover do gráfico de bolhas."""
    return [
        # ---- 1. Operações Assistenciais -----------------------------------
        ("Gerenciar Pronto Socorro", "Gerente Hospitalar", "R",
         "Unidade sob responsabilidade direta da liderança hospitalar local; falta padronização de modelo entre as diferentes unidades do complexo."),
        ("Gerenciar Pronto Socorro", "Gerente Corporativo Operações", "A",
         "Fluxo de regulação/triagem de urgência ainda concorre com a governança de leitos por especialidade, gerando atrasos de encaminhamento."),
        ("Gerenciar Pronto Socorro", "Gerente Médico", "A",
         "Protocolos clínicos de urgência dependem de alinhamento entre múltiplos diretores/coordenadores médicos, sem um único ponto de decisão."),
        ("Gerenciar Pronto Socorro", "Gerente Segurança Assistencial", "A",
         "Indicadores de segurança na porta de entrada são monitorados, mas a ação corretiva depende da adesão local, sem alçada formal de cobrança."),

        ("Gerenciar Unidade de Internação", "Gerente Hospitalar", "R",
         "Gestão operacional do dia a dia é local; padronização de indicadores entre hospitais ainda é heterogênea."),
        ("Gerenciar Unidade de Internação", "Gerente Corporativo Enfermagem", "A",
         "Supervisores de enfermagem seguem absorvendo tarefas administrativas de RH (escala, ponto, desligamento) que deveriam ficar fora da unidade assistencial."),
        ("Gerenciar Unidade de Internação", "Gerente Corporativo Operações", "A",
         "Integração com a Gestão de Leitos/NIR é parcial, pois leitos de especialidade mantêm governança própria."),

        ("Gerenciar Serviços Ambulatoriais", "Gerente Hospitalar", "R",
         "Agenda e capacidade ambulatorial variam de hospital para hospital, sem um padrão único de gestão de fila."),
        ("Gerenciar Serviços Ambulatoriais", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "A",
         "Experiência do paciente ambulatorial depende de coordenação com múltiplas áreas de agendamento/autorização, ainda fragmentadas."),
        ("Gerenciar Serviços Ambulatoriais", "Gerente Corporativo Operações", "A",
         "Uso da capacidade instalada (salas/consultórios) não é monitorado de forma centralizada entre unidades."),

        ("Gerenciar Procedimentos Cirúrgicos", "Gerente Hospitalar", "R",
         "Mapa cirúrgico e produtividade de salas são geridos localmente, com pouca comparabilidade entre hospitais."),
        ("Gerenciar Procedimentos Cirúrgicos", "Gerente Médico", "A",
         "Autonomia de diretores/coordenadores médicos especialistas dificulta padronização de protocolos cirúrgicos entre especialidades."),
        ("Gerenciar Procedimentos Cirúrgicos", "Gerente Corporativo Operações", "A",
         "Central de agendamento/autorização cirúrgica é sobrecarregada e compartilhada entre múltiplos blocos, sem dimensionamento por hospital."),
        ("Gerenciar Procedimentos Cirúrgicos", "Gerente de Suprimentos", "A",
         "Disponibilidade de OPME e materiais de alto custo depende de cotação/autorização prévia — fonte recorrente de atraso no início das cirurgias."),

        ("Gerenciar Medicina Diagnóstica", "Gerente Hospitalar", "R",
         "Resultado financeiro do CDI é acompanhado localmente, sem benchmarking sistemático entre unidades."),
        ("Gerenciar Medicina Diagnóstica", "Gerente Médico", "A",
         "Supervisão técnica de exames de imagem existe só em parte dos serviços (falta padronizar hemodinâmica, radioterapia e medicina nuclear)."),
        ("Gerenciar Medicina Diagnóstica", "Gerente Tecnologia e Inovação", "A",
         "Integração de equipamentos de imagem digital (PACS) com sistemas corporativos ainda depende de definição clara entre TI e Engenharia Clínica."),

        # ---- 2. Gestão de Fluxo e Apoio Clínico ----------------------------
        ("Gerenciar Leitos e NIR", "Gerente Corporativo Operações", "R",
         "Leitos de especialidades (cardiologia, pediatria, obstetrícia, TMO) mantêm governança própria fora do NIR, fragmentando a gestão única da capacidade."),
        ("Gerenciar Leitos e NIR", "Gerente Hospitalar", "A",
         "Giro de leitos local depende de integração em tempo real com o NIR corporativo, hoje parcial."),
        ("Gerenciar Leitos e NIR", "Gerente Médico", "A",
         "Falta um fluxo formal de escalonamento quando o NIR e a equipe médica discordam sobre prioridade de alta/transferência."),

        ("Gerenciar Atendimento ao Paciente", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "R",
         "Jornada do paciente passa por múltiplos pontos de contato (recepção, agendamento, autorizações) sem visão única de dono do processo."),
        ("Gerenciar Atendimento ao Paciente", "Gerente Hospitalar", "A",
         "Equipes de recepção/atendimento local nem sempre seguem o mesmo padrão definido corporativamente."),

        ("Gerenciar Farmácia", "Gerente de Suprimentos", "R",
         "Farmácias de bloco cirúrgico funcionam apenas como 'passagem' de estoque, gerando retrabalho de reposição."),
        ("Gerenciar Farmácia", "Gerente Segurança Assistencial", "A",
         "Stewardship de antimicrobianos e segurança medicamentosa exigem alinhamento constante, com sobreposição em auditoria de uso."),
        ("Gerenciar Farmácia", "Gerente Hospitalar", "A",
         "Falta de padronização entre farmácias locais gera diferença de nível de serviço entre hospitais."),

        ("Gerenciar Logística de Medicamentos", "Gerente de Suprimentos", "R",
         "Falhas recorrentes de rota entre CAF e unidades obrigam equipes assistenciais a buscar material no almoxarifado."),
        ("Gerenciar Logística de Medicamentos", "Gerente Corporativo Operações", "A",
         "Dimensionamento da logística interna (rotas/horários) não é revisado com a mesma frequência da demanda assistencial."),

        ("Gerenciar Nutrição Clínica", "Gerente Corporativo Operações", "R",
         "Nutrição assistencial ainda acumula tarefas operacionais de estoque/dispensação que poderiam ser da farmácia ou logística."),
        ("Gerenciar Nutrição Clínica", "Gerente Hospitalar", "A",
         "Padrão de dietas e cardápios varia entre unidades sem um único guia corporativo."),

        ("Gerenciar Documentação Assistencial", "Gerente de Qualidade", "R",
         "Qualidade acaba assumindo registros operacionais que deveriam ser preenchidos pelas próprias áreas gestoras (corresponsabilidade em construção)."),
        ("Gerenciar Documentação Assistencial", "Gerente Corporativo Enfermagem", "A",
         "Prontuário e registros de enfermagem demandam auditoria constante para garantir completude, consumindo tempo assistencial."),
        ("Gerenciar Documentação Assistencial", "Gerente Tecnologia e Inovação", "A",
         "Novos canais digitais (apps, portais de resultado) às vezes são implantados sem validação técnica prévia das áreas assistenciais."),

        ("Gerenciar Epidemiologia e Infecção Hospitalar", "Gerente Segurança Assistencial", "R",
         "Vigilância epidemiológica depende de dados de múltiplas unidades, com qualidade heterogênea de notificação."),
        ("Gerenciar Epidemiologia e Infecção Hospitalar", "Gerente Corporativo Enfermagem", "A",
         "Adesão a protocolos de controle de infecção varia entre equipes, exigindo reforço constante de auditoria."),
        ("Gerenciar Epidemiologia e Infecção Hospitalar", "Gerente de Qualidade", "A",
         "Indicadores de infecção se sobrepõem parcialmente aos indicadores gerais de qualidade assistencial, sem dashboard único."),

        # ---- 3. Hotelaria, Logística e Infraestrutura ----------------------
        ("Gerenciar Higienização", "Gerente Corporativo Operações", "R",
         "Fluxo de liberação de leitos entre Higienização e Enfermagem precisa de reforço quando há equipamentos assistenciais no quarto após a alta."),
        ("Gerenciar Higienização", "Gerente Hospitalar", "A",
         "Padrão de qualidade de higienização varia entre hospitais, sem indicador único corporativo."),

        ("Gerenciar Rouparia", "Gerente Corporativo Operações", "R",
         "Limite de responsabilidade entre Rouparia e Hotelaria sobre o enxoval ainda gera dúvida operacional recorrente."),
        ("Gerenciar Rouparia", "Gerente de Suprimentos", "A",
         "Reposição de itens de rouparia depende de integração de estoque com Suprimentos, hoje com rotas sujeitas a falha."),

        ("Gerenciar Esterilização", "Gerente Corporativo Operações", "R",
         "CME participa de etapas administrativas de compra de instrumentais que poderiam ser centralizadas em Suprimentos."),
        ("Gerenciar Esterilização", "Gerente Segurança Assistencial", "A",
         "Rastreabilidade de instrumentais exige integração constante com os protocolos de controle de infecção."),
        ("Gerenciar Esterilização", "Gerente de Suprimentos", "A",
         "Dobra/confecção de pacotes cirúrgicos por vezes ocorre na lavanderia, quando poderia ser centralizada no CME."),

        ("Gerenciar Manutenção Predial", "Gerente de Infraestrutura", "R",
         "Equipes de manutenção às vezes assumem tarefas de logística interna (ex.: transporte de cilindros de gás) por falta de equipe noturna dedicada."),
        ("Gerenciar Manutenção Predial", "Gerente de Modernização", "A",
         "Projetos de reforma de menor porte se sobrepõem entre Manutenção e Modernização, sem critério único de porte/complexidade."),

        ("Gerenciar Engenharia Clínica", "Gerente de Infraestrutura", "R",
         "Movimentação e baixa patrimonial de equipamentos médicos às vezes ocorre sem formalização prévia junto ao Patrimônio."),
        ("Gerenciar Engenharia Clínica", "Gerente Tecnologia e Inovação", "A",
         "Projetos de integração de equipamentos médicos digitais (ex.: PACS) não têm fronteira formal definida entre TI e Engenharia Clínica."),
        ("Gerenciar Engenharia Clínica", "Gerente de Suprimentos", "A",
         "Especificação técnica de compras de equipamentos exige alinhamento constante para evitar retrabalho entre as duas áreas."),

        ("Gerenciar Obras", "Gerente de Modernização", "R",
         "Cronograma de obras de expansão concorre por recursos e prioridade com a manutenção predial corrente."),
        ("Gerenciar Obras", "Gerente PMO", "A",
         "Abertura/fechamento de contas bancárias específicas de projeto e acompanhamento de compras dos projetos ainda geram dúvida sobre qual área conduz."),
        ("Gerenciar Obras", "Gerente de Infraestrutura", "A",
         "Mapeamento de necessidades complementares de segurança e TI em obras novas depende de alinhamento manual entre as áreas."),

        ("Gerenciar Segurança", "Gerente de Infraestrutura", "R",
         "Estrutura de segurança patrimonial tem alçada e grau hierárquico ainda em revisão frente ao porte da operação."),
        ("Gerenciar Segurança", "Gerente Jurídico", "A",
         "Ocorrências de segurança com desdobramento jurídico (ex.: ordens judiciais, sinistros) exigem apoio jurídico recorrente."),

        ("Gerenciar Suprimentos", "Gerente de Suprimentos", "R",
         "Contratação de PJ médico e de prestadores tramita hoje por Compras/Suprimentos, mas deveria ser conduzida pelo RH."),
        ("Gerenciar Suprimentos", "Gerente de Controladoria", "A",
         "Provisão contábil de ordens de compra em aberto gera divergência recorrente entre Suprimentos e Controladoria."),

        # ---- 4. Mercado e Ciclo de Receita ---------------------------------
        ("Gerenciar Comercial", "Gerente Comercial", "R",
         "Negociação de reajustes com operadoras concorre, em parte, com a atuação de relacionamento médico sobre o mesmo cliente final."),
        ("Gerenciar Comercial", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "A",
         "Captação e fidelização de médicos hoje se sobrepõe à atuação comercial voltada a operadoras, sem fronteira clara entre os dois tipos de cliente."),

        ("Gerenciar Produto", "Gerente Comercial", "R",
         "Desenvolvimento de novos produtos/planos depende de parametrização de preços que só é fechada tardiamente pelo Faturamento."),
        ("Gerenciar Produto", "Gerente de Faturamento", "A",
         "Regras comerciais nem sempre chegam prontas ao faturamento, gerando retrabalho de parametrização."),

        ("Gerenciar Faturamento", "Gerente de Faturamento", "R",
         "Ciclo da conta ainda tem gargalos entre autorização, revisão técnica e faturamento, sem responsável único por etapa."),
        ("Gerenciar Faturamento", "Gerente Financeiro", "A",
         "Auditoria de glosas e títulos a receber do pré-faturamento é acompanhada em paralelo pelo Financeiro, com pontos de divergência de critério."),
        ("Gerenciar Faturamento", "Gerente Comercial", "A",
         "Negociação de regras com operadoras deveria estar mais integrada ao faturamento desde o início do processo comercial."),

        ("Gerenciar Finanças e Controladoria", "Gerente Financeiro", "R",
         "Caixas hospitalares específicos (ensino/pesquisa, cemitério, HDJB) têm natureza financeira mas hoje respondem à gerência hospitalar local."),
        ("Gerenciar Finanças e Controladoria", "Gerente de Controladoria", "A",
         "Divergência de critério sobre PCLD (créditos de liquidação duvidosa) e provisões ainda demanda alinhamento recorrente."),

        ("Gerenciar Marketing", "Gerente Comunic. e Marketing", "R",
         "Ausência de diretriz institucional única para uso de IA generativa em campanhas gera iniciativas descentralizadas fora do padrão de marca."),
        ("Gerenciar Marketing", "Gerente Comercial", "A",
         "Ações de marketing e comercial para captação de pacientes particulares exigem alinhamento constante de calendário e mensagem."),

        ("Gerenciar Filantropia", "Gerente de Relações Institucionais", "R",
         "Atuação de Relações Institucionais depende de uma única pessoa, sem equipe própria, gerando assimetria frente à Captação de Recursos."),
        ("Gerenciar Filantropia", "Gerente Projetos de Captação", "A",
         "Sobreposição não formalizada entre quem origina (Relações Institucionais) e quem operacionaliza (Captação) os recursos captados."),

        ("Gerenciar Inovação e Planejamento", "Gerente Tecnologia e Inovação", "R",
         "Sobreposição não formalizada entre Inovação e TI Sistemas na condução de projetos de implantação de soluções de mercado ('Buy')."),
        ("Gerenciar Inovação e Planejamento", "Gerente PMO", "A",
         "Priorização de projetos de inovação concorre por orçamento e capacidade com o portfólio de obras/infraestrutura do PMO."),

        # ---- 5. Capital Humano e Governança Clínica ------------------------
        ("Gerenciar Pessoal", "Gerente de Gestão de Pessoas", "R",
         "Demandas de ampliação de quadro são criadas com frequência sem planejamento anual prévio, gerando redesenho organizacional constante."),

        ("Gerenciar Administração de Pessoal", "Gerente de Gestão de Pessoas", "R",
         "Responsabilidade sobre frequência, banco de horas e férias ainda é compartilhada de forma pouco clara com os gestores das áreas."),
        ("Gerenciar Administração de Pessoal", "Gerente de Controladoria", "A",
         "Orçamento de pessoal e realizado de folha exigem reconciliação manual recorrente entre RH e Controladoria."),

        ("Gerenciar SESMT", "Gerente de Gestão de Pessoas", "R",
         "Agendamento de exames periódicos e triagem de intercorrências às vezes é feito por outras áreas quando deveria ser conduzido pelo SESMT."),
        ("Gerenciar SESMT", "Gerente Segurança Assistencial", "A",
         "Segurança do trabalho e segurança do paciente compartilham temas de vigilância, mas ainda com pouca integração de indicadores."),

        ("Gerenciar Relacionamento Médico", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "R",
         "Diretores médicos atuam hoje de forma pouco padronizada, sem modelo único de governança de relacionamento com o corpo clínico."),
        ("Gerenciar Relacionamento Médico", "Gerente Médico", "A",
         "Credenciamento de corpo clínico passa pela aprovação do próprio chefe de especialidade em alguns casos, gerando risco de conflito de interesse."),

        ("Gerenciar Práticas Médicas", "Gerente Médico", "R",
         "Múltiplas 'práticas assistenciais' (gerência médica, líder de práticas, pessoas vinculadas a diferentes diretores) atuam sem modelo único definido."),
        ("Gerenciar Práticas Médicas", "Gerente Segurança Assistencial", "A",
         "Avaliação de novas tecnologias/práticas é feita em paralelo por diferentes áreas, com decisão final dependendo de comitê conjunto."),

        ("Gerenciar Resultados e Práticas Assistenciais", "Gerente Segurança Assistencial", "R",
         "Indicadores de desfecho e eventos adversos ainda dependem de integração manual de dados de múltiplas unidades."),
        ("Gerenciar Resultados e Práticas Assistenciais", "Gerente Corporativo Enfermagem", "A",
         "Coleta de indicadores assistenciais consome tempo da liderança de enfermagem, que também responde por parte da apuração de resultados."),
        ("Gerenciar Resultados e Práticas Assistenciais", "Gerente Médico", "A",
         "Prática assistencial médica se sobrepõe, em parte, com a gerência médica e com líderes de prática ligados a diferentes diretorias."),

        # ---- 6. Governança Corporativa e Suporte ---------------------------
        ("Gerenciar Governança Corporativa", "Gerente PMO", "R",
         "PMO Corporativo é hoje posicionado junto à área administrativa, quando deveria caminhar mais próximo da governança estratégica institucional."),
        ("Gerenciar Governança Corporativa", "Gerente Jurídico", "A",
         "Apoio jurídico a decisões de governança corporativa é recorrente, mas sem fórum formal conjunto definido."),

        ("Gerenciar Jurídico", "Gerente Jurídico", "R",
         "Reunião de documentos para defesas trabalhistas e gestão de imóveis por vezes é conduzida pelo Jurídico quando deveria voltar para RH/Patrimônio."),

        ("Gerenciar Qualidade", "Gerente de Qualidade", "R",
         "Qualidade é acionada tardiamente em projetos que deveriam ser conduzidos, desde o início, pelos próprios responsáveis pela área."),
        ("Gerenciar Qualidade", "Gerente Segurança Assistencial", "A",
         "Interfaces entre Qualidade e Segurança Assistencial ainda precisam de melhor integração de indicadores e fóruns."),

        ("Gerenciar TI", "Gerente Tecnologia e Inovação", "R",
         "Definição de perfis de acesso aos sistemas não está clara entre TI, Gestão de Pessoas e Qualidade."),
        ("Gerenciar TI", "Gerente de Infraestrutura", "A",
         "Monitoramento e manutenção de infraestrutura crítica (nobreaks, climatização) exige atuação conjunta e proativa entre TI e Engenharia."),

        ("Gerenciar Ensino e Pesquisa", "Gerente Ensino e Pesquisa", "R",
         "Médicos influentes por vezes negociam pesquisa e isenções de ensino diretamente com a Direção, sem passar pela gerência."),
        ("Gerenciar Ensino e Pesquisa", "Gerente Médico", "A",
         "Sobreposição entre Ensino e Educação Corporativa na formação de médicos celetistas do corpo clínico ainda não foi resolvida."),
    ]


@st.cache_data
def montar_base() -> tuple[pd.DataFrame, dict]:
    """Consolida estrutura + relações em um único DataFrame "longo",
    com uma linha por cruzamento Função x Gerência."""
    pilares = carregar_estrutura()
    relacoes = carregar_relacoes()
    abreviacoes = carregar_abreviacoes()

    funcao_para_pilar = {}
    for nome_pilar, info in pilares.items():
        for funcao in info["funcoes"]:
            funcao_para_pilar[funcao] = (nome_pilar, info["macroprocesso"])

    linhas = []
    for funcao, gerencia, papel, ponto_atencao in relacoes:
        pilar, macro = funcao_para_pilar[funcao]
        linhas.append(
            {
                "Pilar": pilar,
                "Macroprocesso": macro,
                "Função": funcao,
                "Gerência": gerencia,
                "Gerência (abreviada)": abreviacoes.get(gerencia, gerencia),
                "Papel": papel,
                "Papel (rótulo)": CORES_PAPEL[papel]["rotulo"],
                "Ponto de Atenção / Sobreposição": ponto_atencao,
            }
        )

    df = pd.DataFrame(linhas)
    return df, pilares


# ==============================================================================
# 3. FUNÇÕES DE APOIO (BUSCA E FILTROS)
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


# ==============================================================================
# 4. GRÁFICO DE BOLHAS MATRICIAL (PLOTLY)
# ==============================================================================

def criar_matriz_bolhas(df_pilar: pd.DataFrame, ordem_funcoes: list[str]) -> go.Figure:
    """Gera o gráfico de bolhas matricial para um Pilar específico.
    Eixo X = Gerências (rótulo abreviado, fonte pequena, quebra de linha).
    Eixo Y = Funções ("Gerenciar ..."), na ordem original do pilar.
    Cor/tamanho da bolha = Papel (Responsável x Apoio).
    Hover = Função, Gerência completa, Papel e Ponto de Atenção/Sobreposição.
    """
    # Mantém apenas as funções que ainda possuem ao menos 1 relação visível.
    funcoes_visiveis = [f for f in ordem_funcoes if f in set(df_pilar["Função"])]

    # Colunas (gerências) relevantes = união das gerências relacionadas às
    # funções deste pilar, já filtradas — ordenadas alfabeticamente pelo
    # nome completo para manter consistência entre recarregamentos.
    gerencias_visiveis = (
        df_pilar[["Gerência", "Gerência (abreviada)"]]
        .drop_duplicates()
        .sort_values("Gerência")
    )
    ordem_x = gerencias_visiveis["Gerência (abreviada)"].tolist()

    fig = go.Figure()

    for papel, estilo in CORES_PAPEL.items():
        subset = df_pilar[df_pilar["Papel"] == papel]
        if subset.empty:
            continue

        customdata = subset[["Função", "Gerência", "Papel (rótulo)", "Ponto de Atenção / Sobreposição"]].values

        fig.add_trace(
            go.Scatter(
                x=subset["Gerência (abreviada)"],
                y=subset["Função"],
                mode="markers",
                name=estilo["rotulo"],
                marker=dict(
                    size=estilo["tamanho"],
                    color=estilo["cor"],
                    line=dict(width=1.5, color="white"),
                    opacity=0.88,
                ),
                customdata=customdata,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Gerência: <b>%{customdata[1]}</b><br>"
                    "Papel: %{customdata[2]}<br><br>"
                    "<b>Ponto de atenção / sobreposição:</b><br>%{customdata[3]}"
                    "<extra></extra>"
                ),
            )
        )

    altura = max(420, 95 * len(funcoes_visiveis) + 160)

    fig.update_layout(
        xaxis=dict(
            title=None,
            type="category",
            categoryorder="array",
            categoryarray=ordem_x,
            tickfont=dict(size=10),
            tickangle=0,
            showgrid=True,
            gridcolor="#F1F2F4",
            side="top",
        ),
        yaxis=dict(
            title=None,
            type="category",
            categoryorder="array",
            categoryarray=funcoes_visiveis[::-1],  # primeira função no topo
            tickfont=dict(size=12),
            showgrid=True,
            gridcolor="#F1F2F4",
            automargin=True,
        ),
        legend=dict(title="Papel na matriz", orientation="h", y=-0.08, x=0),
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        height=altura,
    )
    return fig


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
                22 Gerências/Áreas corporativas — visualização em matriz de bolhas interativa.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_legenda() -> None:
    itens_papel = "".join(
        f'<span class="legenda-item">'
        f'<span class="legenda-bolha" style="background:{c["cor"]};"></span> {c["rotulo"]}'
        f"</span>"
        for c in CORES_PAPEL.values()
    )
    itens_macro = "".join(
        f'<span class="legenda-item">'
        f'<span class="legenda-pill" style="background:{c["bg"]}; color:{c["text"]};">{nome}</span>'
        f"</span>"
        for nome, c in CORES_MACRO.items()
    )
    st.markdown(
        f"""
        <div class="legenda-card">
            <div class="legenda-titulo">🔵 Papel de responsabilidade (cor e tamanho da bolha)</div>
            <div>{itens_papel}</div>
            <div class="legenda-titulo" style="margin-top:0.7rem;">🎨 Macroprocesso (classificação do Pilar)</div>
            <div>{itens_macro}</div>
            <div style="font-size:0.78rem; color:#64748B; margin-top:0.5rem;">
                💡 Passe o mouse sobre qualquer bolha para ver o principal ponto de atenção/sobreposição
                daquele cruzamento específico entre Função e Gerência.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_estatisticas(df_visivel: pd.DataFrame, total_gerencias: int) -> None:
    total_funcoes = df_visivel["Função"].nunique()
    total_gerencias_ativas = df_visivel["Gerência"].nunique()
    total_relacoes = len(df_visivel)
    total_responsavel = int((df_visivel["Papel"] == "R").sum())

    col1, col2, col3, col4 = st.columns(4)
    cartoes = [
        (col1, total_funcoes, "Funções visíveis"),
        (col2, f"{total_gerencias_ativas}/{total_gerencias}", "Gerências envolvidas"),
        (col3, total_relacoes, "Relações mapeadas"),
        (col4, total_responsavel, "Papéis 'Responsável'"),
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
    """Botões de download (CSV e Excel) para o recorte atual (todos os
    pilares/abas visíveis após os filtros aplicados)."""
    st.markdown("#### 📥 Exportar matriz filtrada (todas as abas visíveis)")
    colunas_exportar = ["Pilar", "Macroprocesso", "Função", "Gerência", "Papel (rótulo)", "Ponto de Atenção / Sobreposição"]
    df_export = df_exportar[colunas_exportar]

    col_csv, col_xlsx = st.columns(2)

    csv_bytes = df_export.to_csv(index=False).encode("utf-8-sig")
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
        df_export.to_excel(writer, index=False, sheet_name="Matriz Área x Função")
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

    df_filtrado_macro = (
        df_filtrado[df_filtrado["Macroprocesso"] == macro_filtro]
        if macro_filtro != "Todos"
        else df_filtrado
    )

    render_estatisticas(df_filtrado_macro, total_gerencias=len(gerencias_todas))
    st.markdown("")

    # -------- Renderiza 1 aba por Pilar de Sinergia -----------------------
    nomes_pilares = list(pilares.keys())
    tabs = st.tabs(nomes_pilares)

    for tab, nome_pilar in zip(tabs, nomes_pilares):
        with tab:
            info_pilar = pilares[nome_pilar]
            macro_pilar = info_pilar["macroprocesso"]
            cor_macro = CORES_MACRO[macro_pilar]

            st.markdown(
                f'<span class="selo-macro" style="background:{cor_macro["bg"]}; color:{cor_macro["text"]};">'
                f"{macro_pilar}</span> &nbsp; "
                f'<span style="color:#64748B; font-size:0.85rem;">{len(info_pilar["funcoes"])} funções mapeadas neste pilar</span>',
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

            fig = criar_matriz_bolhas(df_pilar, info_pilar["funcoes"])
            st.plotly_chart(fig, use_container_width=True, key=f"grafico_{nome_pilar}")

    # -------- Exportação (considera todos os pilares após os filtros) -----
    st.markdown("---")
    render_exportacao(df_filtrado_macro)

    st.markdown("---")
    st.caption(
        "💡 Dica: passe o mouse sobre as bolhas para ver o principal ponto de atenção/sobreposição "
        "de cada cruzamento. Use a legenda do gráfico (clique nos itens) para isolar só 'Responsável' ou só 'Apoio'."
    )


if __name__ == "__main__":
    main()
