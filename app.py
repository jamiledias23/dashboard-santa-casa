# -*- coding: utf-8 -*-
"""
================================================================================
 MATRIZ ÁREA x FUNÇÃO — SANTA CASA DE PORTO ALEGRE (VISUALIZAÇÃO EM BOLHAS)
 Cruzamento de 37 Funções (organizadas em 6 Pilares de Sinergia) x
 22 Gerências/Áreas corporativas, com foco em pontos de atenção observados
 no Levantamento de Áreas (227 formulários respondidos).
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
As relações Função x Gerência (bloco `carregar_relacoes`) foram construídas
a partir de uma releitura cuidadosa das respostas do Levantamento de Áreas
2026 (227 formulários) e dos organogramas oficiais vigentes, priorizando o
que está de fato descrito nos cargos e relatado nas entrevistas — e não uma
atribuição teórica. Os textos de "Ponto de Atenção" são redigidos de forma
neutra e propositiva, sem citar pessoas e sem tom de julgamento. Em
produção, este bloco deve ser substituído/validado por uma consulta à base
oficial consolidada, mantendo o mesmo formato de saída: uma lista de tuplas
(Função, Gerência, Papel, Ponto de Atenção).
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

# Número de formulários que alimentaram o Levantamento de Áreas 2026 —
# informação fixa, exibida no painel de estatísticas independentemente
# dos filtros aplicados pelo usuário.
TOTAL_FORMULARIOS_RESPONDIDOS = 227

# Paleta de cores por papel de responsabilidade dentro da matriz.
CORES_PAPEL = {
    "R": {"rotulo": "Responsável (dona da entrega)", "cor": "#2563EB", "tamanho": 24},
    "A": {"rotulo": "Apoio / Interface",              "cor": "#F59E0B", "tamanho": 15},
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
    .stat-value { font-size: 1.5rem; font-weight: 800; color: #0F2A4A; line-height: 1.1; }
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
    .legenda-bolha { display: inline-block; width: 13px; height: 13px; border-radius: 50%; }

    .pilar-caption { color: #64748B; font-size: 0.85rem; margin-bottom: 0.4rem; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# 2. CAMADA DE DADOS
# ==============================================================================

def carregar_estrutura() -> dict:
    """Estrutura dos 6 Pilares de Sinergia (37 Funções no total). As Funções
    'Gerenciar Pessoal' e 'Gerenciar Administração de Pessoal' foram
    consolidadas em uma única Função, já que o Levantamento de Áreas mostrou
    que essa atividade é reportada de forma semelhante por diversas
    gerências, e não apenas pela área de Gestão de Pessoas."""
    return {
        "1️⃣ Operações Assistenciais": [
            "Gerenciar Pronto Socorro",
            "Gerenciar Unidade de Internação",
            "Gerenciar Serviços Ambulatoriais",
            "Gerenciar Procedimentos Cirúrgicos",
            "Gerenciar Medicina Diagnóstica",
        ],
        "2️⃣ Gestão de Fluxo e Apoio Clínico": [
            "Gerenciar Leitos e NIR",
            "Gerenciar Atendimento ao Paciente",
            "Gerenciar Farmácia",
            "Gerenciar Logística de Medicamentos",
            "Gerenciar Nutrição Clínica",
            "Gerenciar Documentação Assistencial",
            "Gerenciar Epidemiologia e Infecção Hospitalar",
        ],
        "3️⃣ Hotelaria, Logística e Infraestrutura": [
            "Gerenciar Higienização",
            "Gerenciar Rouparia",
            "Gerenciar Esterilização",
            "Gerenciar Manutenção Predial",
            "Gerenciar Engenharia Clínica",
            "Gerenciar Obras",
            "Gerenciar Segurança",
            "Gerenciar Suprimentos",
        ],
        "4️⃣ Mercado e Ciclo de Receita": [
            "Gerenciar Comercial",
            "Gerenciar Produto",
            "Gerenciar Faturamento",
            "Gerenciar Finanças e Controladoria",
            "Gerenciar Marketing",
            "Gerenciar Filantropia",
            "Gerenciar Inovação e Planejamento",
        ],
        "5️⃣ Capital Humano e Governança Clínica": [
            "Gerenciar Administração de Pessoal",
            "Gerenciar SESMT",
            "Gerenciar Relacionamento Médico",
            "Gerenciar Práticas Médicas",
            "Gerenciar Resultados e Práticas Assistenciais",
        ],
        "6️⃣ Governança Corporativa e Suporte": [
            "Gerenciar Governança Corporativa",
            "Gerenciar Jurídico",
            "Gerenciar Qualidade",
            "Gerenciar TI",
            "Gerenciar Ensino e Pesquisa",
        ],
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


def carregar_abreviacoes() -> dict:
    """Rótulos curtos (com quebra de linha via <br>) usados no eixo X do
    gráfico, para reduzir a necessidade de rolagem horizontal."""
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
    """Relações Função x Gerência: (Função, Gerência, Papel, Ponto de Atenção).
    Papel: "R" = Responsável (dona da entrega, conforme descrição de cargo) |
    "A" = Apoio / Interface. Os textos de Ponto de Atenção resgatam
    observações relatadas no Levantamento de Áreas, redigidas de forma
    neutra, sem citar pessoas."""
    return [
        # ---- 1. Operações Assistenciais -----------------------------------
        ("Gerenciar Pronto Socorro", "Gerente Hospitalar", "R",
         "A descrição de cargo atribui à gerência hospitalar a responsabilidade pelo desempenho assistencial, administrativo e financeiro da unidade. Na prática, a operação cotidiana do Pronto Socorro é conduzida por coordenações e supervisões de segmento, que reportam apenas indiretamente a essa gerência."),
        ("Gerenciar Pronto Socorro", "Gerente Corporativo Operações", "A",
         "A integração entre o fluxo de urgência e a governança de leitos por especialidade ainda depende de alinhamento manual entre as áreas."),
        ("Gerenciar Pronto Socorro", "Gerente Médico", "A",
         "Protocolos clínicos de urgência envolvem múltiplos diretores e coordenadores médicos por especialidade, sem um ponto único de consolidação das decisões."),
        ("Gerenciar Pronto Socorro", "Gerente Segurança Assistencial", "A",
         "O acompanhamento de indicadores de segurança na porta de entrada é centralizado, mas a implementação das ações corretivas depende da adesão de cada unidade local."),

        ("Gerenciar Unidade de Internação", "Gerente Hospitalar", "R",
         "Assim como no Pronto Socorro, a responsabilidade formal pelo resultado da internação é da gerência hospitalar, enquanto a gestão assistencial cotidiana é conduzida por coordenações que respondem também à Enfermagem Corporativa."),
        ("Gerenciar Unidade de Internação", "Gerente Corporativo Enfermagem", "A",
         "Lideranças de enfermagem da unidade relataram absorver tarefas de escala, ponto e desligamento que poderiam contar com mais apoio direto da área de Gestão de Pessoas."),
        ("Gerenciar Unidade de Internação", "Gerente Corporativo Operações", "A",
         "A integração com a governança de leitos corporativa ainda é parcial, já que parte dos leitos de especialidade é gerida separadamente."),

        ("Gerenciar Serviços Ambulatoriais", "Gerente Hospitalar", "R",
         "A gestão da agenda e da capacidade ambulatorial ocorre de forma própria em cada unidade hospitalar, sem um padrão único de referência entre elas."),
        ("Gerenciar Serviços Ambulatoriais", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "A",
         "A experiência do paciente ambulatorial passa por múltiplas frentes de agendamento e autorização, que podem se beneficiar de maior integração entre si."),
        ("Gerenciar Serviços Ambulatoriais", "Gerente Corporativo Operações", "A",
         "O uso da capacidade instalada (salas e consultórios) não é acompanhado de forma centralizada entre as unidades."),

        ("Gerenciar Procedimentos Cirúrgicos", "Gerente Hospitalar", "R",
         "A produtividade das salas cirúrgicas é acompanhada localmente. As cinco gerências hospitalares atuam hoje com estruturas distintas entre si para o mesmo cargo, o que pode dificultar a comparação entre unidades."),
        ("Gerenciar Procedimentos Cirúrgicos", "Gerente Médico", "A",
         "A autonomia de diretores e coordenadores médicos por especialidade dificulta a padronização de protocolos cirúrgicos entre unidades."),
        ("Gerenciar Procedimentos Cirúrgicos", "Gerente Corporativo Operações", "A",
         "A central de agendamento e autorização cirúrgica atende simultaneamente a múltiplos blocos, o que pode limitar a capacidade de resposta em momentos de pico."),
        ("Gerenciar Procedimentos Cirúrgicos", "Gerente de Suprimentos", "A",
         "A disponibilidade de OPME e materiais de alto custo depende de cotação prévia — processo apontado como fonte recorrente de atraso no início de cirurgias."),

        ("Gerenciar Medicina Diagnóstica", "Gerente Hospitalar", "R",
         "O resultado financeiro do CDI é acompanhado localmente, sem um benchmarking sistemático entre as unidades."),
        ("Gerenciar Medicina Diagnóstica", "Gerente Médico", "A",
         "A supervisão técnica de exames de imagem existe apenas em parte dos serviços, faltando padronização em áreas como hemodinâmica, radioterapia e medicina nuclear."),
        ("Gerenciar Medicina Diagnóstica", "Gerente Tecnologia e Inovação", "A",
         "A integração de equipamentos de imagem digital com os sistemas corporativos ainda depende de uma definição mais clara de fronteira entre TI e Engenharia Clínica."),

        # ---- 2. Gestão de Fluxo e Apoio Clínico ----------------------------
        ("Gerenciar Leitos e NIR", "Gerente Corporativo Operações", "R",
         "Leitos de especialidades como cardiologia, pediatria, obstetrícia e transplante de medula óssea mantêm gestão própria fora do NIR, o que fragmenta a governança única da capacidade hospitalar."),
        ("Gerenciar Leitos e NIR", "Gerente Hospitalar", "A",
         "O giro de leitos de cada unidade depende de integração em tempo real com o NIR corporativo, hoje parcial."),
        ("Gerenciar Leitos e NIR", "Gerente Médico", "A",
         "Quando o NIR e a equipe médica têm visões diferentes sobre a prioridade de uma alta ou transferência, ainda não há um fluxo formal de escalonamento."),

        ("Gerenciar Atendimento ao Paciente", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "R",
         "A jornada do paciente passa por múltiplos pontos de contato (recepção, agendamento, autorizações), o que reforça a importância de uma visão única de dono do processo."),
        ("Gerenciar Atendimento ao Paciente", "Gerente Hospitalar", "A",
         "As equipes de recepção de cada unidade nem sempre seguem exatamente o mesmo padrão definido corporativamente."),

        ("Gerenciar Farmácia", "Gerente de Suprimentos", "R",
         "A farmácia está estruturada hoje sob a lógica de suprimentos e logística, ligada à Direção Administrativa. Como parte da prática farmacêutica tem natureza clínica e de segurança do paciente, pode valer a pena avaliar se a governança técnica desse tema não teria maior aderência junto à Direção Técnica."),
        ("Gerenciar Farmácia", "Gerente Segurança Assistencial", "A",
         "Temas como uso racional de antimicrobianos e segurança medicamentosa são acompanhados em conjunto, e podem se beneficiar de um fluxo de auditoria mais integrado entre as duas áreas."),
        ("Gerenciar Farmácia", "Gerente Hospitalar", "A",
         "O nível de padronização entre as farmácias de cada unidade hospitalar ainda varia."),

        ("Gerenciar Logística de Medicamentos", "Gerente de Suprimentos", "R",
         "Falhas de rota entre o CAF e as unidades foram relatadas como causa de deslocamentos extras das equipes assistenciais até o almoxarifado."),
        ("Gerenciar Logística de Medicamentos", "Gerente Corporativo Operações", "A",
         "O dimensionamento das rotas de entrega interna pode não acompanhar, na mesma velocidade, as variações da demanda assistencial."),

        ("Gerenciar Nutrição Clínica", "Gerente Corporativo Enfermagem", "R",
         "A nutrição assistencial relatou absorver tarefas operacionais de estoque e dispensação de produtos que poderiam ficar mais concentradas em Suprimentos/Farmácia."),
        ("Gerenciar Nutrição Clínica", "Gerente Hospitalar", "A",
         "O padrão de dietas e cardápios ainda varia entre as unidades hospitalares."),

        ("Gerenciar Documentação Assistencial", "Gerente de Qualidade", "R",
         "A área de Qualidade relatou assumir, em parte, registros operacionais que poderiam ser preenchidos diretamente pelas áreas gestoras responsáveis — uma corresponsabilidade ainda em construção."),
        ("Gerenciar Documentação Assistencial", "Gerente Corporativo Enfermagem", "A",
         "A auditoria de completude do prontuário e dos registros de enfermagem consome tempo da liderança assistencial."),
        ("Gerenciar Documentação Assistencial", "Gerente Tecnologia e Inovação", "A",
         "Novos canais digitais de resultado/prontuário podem se beneficiar de uma etapa formal de validação técnica junto às áreas assistenciais antes da implantação."),

        ("Gerenciar Epidemiologia e Infecção Hospitalar", "Gerente Segurança Assistencial", "R",
         "A vigilância epidemiológica depende de dados de múltiplas unidades, com qualidade de notificação ainda heterogênea entre elas."),
        ("Gerenciar Epidemiologia e Infecção Hospitalar", "Gerente Corporativo Enfermagem", "A",
         "A adesão a protocolos de controle de infecção varia entre equipes, o que demanda reforço constante de auditoria."),
        ("Gerenciar Epidemiologia e Infecção Hospitalar", "Gerente de Qualidade", "A",
         "Os indicadores de infecção e os indicadores gerais de qualidade assistencial ainda não estão totalmente integrados em um único painel."),

        # ---- 3. Hotelaria, Logística e Infraestrutura ----------------------
        ("Gerenciar Higienização", "Gerente Corporativo Operações", "R",
         "O fluxo de liberação de leitos entre Higienização e Enfermagem pode ser reforçado nos casos em que equipamentos assistenciais permanecem no quarto após a alta."),
        ("Gerenciar Higienização", "Gerente Hospitalar", "A",
         "O padrão de qualidade de higienização varia entre hospitais, sem um indicador único corporativo."),

        ("Gerenciar Rouparia", "Gerente Corporativo Operações", "R",
         "O limite de responsabilidade entre Rouparia e Hotelaria sobre o enxoval ainda gera dúvida operacional recorrente."),
        ("Gerenciar Rouparia", "Gerente de Suprimentos", "A",
         "A reposição de itens de rouparia depende de integração de estoque com Suprimentos, com rotas por vezes sujeitas a falha."),

        ("Gerenciar Esterilização", "Gerente Corporativo Operações", "R",
         "O CME participa hoje de etapas administrativas de compra de instrumentais que poderiam ser mais centralizadas em Suprimentos."),
        ("Gerenciar Esterilização", "Gerente Segurança Assistencial", "A",
         "A rastreabilidade de instrumentais exige integração constante com os protocolos de controle de infecção."),
        ("Gerenciar Esterilização", "Gerente de Suprimentos", "A",
         "A dobra e a confecção de pacotes cirúrgicos por vezes ocorrem na lavanderia, quando poderiam ser centralizadas no CME."),

        ("Gerenciar Manutenção Predial", "Gerente de Infraestrutura", "R",
         "No período noturno, equipes de manutenção relataram assumir tarefas de logística interna (como transporte de cilindros de gás) pela ausência de equipe dedicada nesse turno."),
        ("Gerenciar Manutenção Predial", "Gerente de Modernização", "A",
         "Projetos de reforma de menor porte ainda não têm um critério único de porte/complexidade que defina se ficam com Manutenção ou com Modernização."),

        ("Gerenciar Engenharia Clínica", "Gerente de Infraestrutura", "R",
         "A movimentação e a baixa patrimonial de equipamentos médicos por vezes ocorrem sem formalização prévia junto à área de Patrimônio."),
        ("Gerenciar Engenharia Clínica", "Gerente Tecnologia e Inovação", "A",
         "Projetos de integração de equipamentos médicos digitais ainda não têm uma fronteira formalmente definida entre TI e Engenharia Clínica."),
        ("Gerenciar Engenharia Clínica", "Gerente de Suprimentos", "A",
         "A especificação técnica de compras de equipamentos pode se beneficiar de um checklist conjunto entre as duas áreas, reduzindo retrabalho."),

        ("Gerenciar Obras", "Gerente de Modernização", "R",
         "O cronograma de obras de expansão concorre por prioridade e recursos com a manutenção predial do dia a dia."),
        ("Gerenciar Obras", "Gerente PMO", "A",
         "A abertura/fechamento de contas específicas de projeto e o acompanhamento das compras associadas ainda geram dúvida sobre qual área conduz cada etapa."),
        ("Gerenciar Obras", "Gerente de Infraestrutura", "A",
         "O mapeamento de necessidades complementares de segurança e TI em obras novas depende, hoje, de alinhamento manual entre as áreas envolvidas."),

        ("Gerenciar Segurança", "Gerente Corporativo Operações", "R",
         "A coordenação de segurança patrimonial reporta hoje à Gerência de Operações. Já foi sugerido avaliar a realocação dessa função para a Direção Administrativa/Infraestrutura, por maior aderência com temas de patrimônio e proteção física."),
        ("Gerenciar Segurança", "Gerente de Infraestrutura", "A",
         "A estrutura de segurança patrimonial tem sua alçada e nível hierárquico ainda em avaliação frente ao porte atual da operação."),
        ("Gerenciar Segurança", "Gerente Jurídico", "A",
         "Ocorrências de segurança com desdobramento jurídico (como ordens judiciais e sinistros) geram apoio recorrente entre as duas áreas."),

        ("Gerenciar Suprimentos", "Gerente de Suprimentos", "R",
         "A formalização de contratos de prestadores PJ tramita hoje por Suprimentos/Compras, podendo ser um processo mais natural para a área de Gestão de Pessoas."),
        ("Gerenciar Suprimentos", "Gerente de Controladoria", "A",
         "A provisão contábil de ordens de compra em aberto ainda gera divergência recorrente de critério entre as duas áreas."),

        # ---- 4. Mercado e Ciclo de Receita ---------------------------------
        ("Gerenciar Comercial", "Gerente Comercial", "R",
         "A negociação de reajustes com operadoras e a atuação de relacionamento médico envolvem, em parte, o mesmo cliente final, o que reforça a importância de alinhamento entre as duas frentes."),
        ("Gerenciar Comercial", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "A",
         "A captação e a fidelização de médicos e a atuação comercial voltada a operadoras ainda não têm uma fronteira clara entre os dois tipos de cliente."),

        ("Gerenciar Produto", "Gerente Comercial", "R",
         "O desenvolvimento de novos produtos/planos depende da parametrização de preços, que hoje é finalizada em etapa posterior pelo Faturamento."),
        ("Gerenciar Produto", "Gerente de Faturamento", "A",
         "Regras comerciais nem sempre chegam previamente definidas ao faturamento, o que pode gerar retrabalho de parametrização."),

        ("Gerenciar Faturamento", "Gerente de Faturamento", "R",
         "O ciclo da conta ainda apresenta pontos de atenção entre autorização, revisão técnica e faturamento, sem um responsável único por etapa."),
        ("Gerenciar Faturamento", "Gerente Financeiro", "A",
         "A auditoria de glosas e os títulos a receber do pré-faturamento são acompanhados em paralelo pelo Financeiro, com critérios que podem ser melhor alinhados entre as áreas."),
        ("Gerenciar Faturamento", "Gerente Comercial", "A",
         "A negociação de regras com operadoras pode se beneficiar de maior integração com o faturamento desde o início do processo comercial."),

        ("Gerenciar Finanças e Controladoria", "Gerente Financeiro", "R",
         "Caixas hospitalares específicos (como ensino/pesquisa, cemitério e HDJB) têm natureza financeira, mas hoje respondem à gerência hospitalar local."),
        ("Gerenciar Finanças e Controladoria", "Gerente de Controladoria", "A",
         "Critérios de provisão (como PCLD — créditos de liquidação duvidosa) ainda demandam alinhamento recorrente entre Financeiro e Controladoria."),

        ("Gerenciar Marketing", "Gerente Comunic. e Marketing", "R",
         "Ainda não existe uma diretriz institucional única para uso de inteligência artificial generativa em campanhas, o que pode levar a iniciativas fora do padrão de marca."),
        ("Gerenciar Marketing", "Gerente Comercial", "A",
         "Ações de marketing e comercial voltadas à captação de pacientes particulares podem se beneficiar de um calendário e mensagem mais alinhados entre as áreas."),

        ("Gerenciar Filantropia", "Gerente de Relações Institucionais", "R",
         "A atuação de Relações Institucionais depende hoje de uma única pessoa, sem equipe própria, o que pode gerar diferença de capacidade frente à área de Captação de Recursos."),
        ("Gerenciar Filantropia", "Gerente Projetos de Captação", "A",
         "A fronteira entre quem origina (Relações Institucionais) e quem operacionaliza (Captação) os recursos captados ainda não está formalizada."),

        ("Gerenciar Inovação e Planejamento", "Gerente Tecnologia e Inovação", "R",
         "A condução de projetos de implantação de soluções de mercado ('comprar' versus 'construir') ainda não tem uma fronteira formalizada entre Inovação e TI Sistemas."),
        ("Gerenciar Inovação e Planejamento", "Gerente PMO", "A",
         "Os projetos de inovação concorrem por orçamento e capacidade com o portfólio de obras e infraestrutura do PMO."),

        # ---- 5. Capital Humano e Governança Clínica ------------------------
        # OBS: "Gerenciar Administração de Pessoal" concentra também o que
        # antes seria "Gerenciar Pessoal" — o Levantamento de Áreas mostrou
        # que múltiplas gerências reportam executar, na prática, parte desta
        # atividade (escala, ponto, recrutamento), e não apenas a área de RH.
        ("Gerenciar Administração de Pessoal", "Gerente de Gestão de Pessoas", "R",
         "Processos de folha, férias, rescisões e recrutamento são conduzidos pela área. Demandas de ampliação de quadro, no entanto, surgem com frequência sem um planejamento anual prévio, levando a ajustes constantes de estrutura."),
        ("Gerenciar Administração de Pessoal", "Gerente Hospitalar", "A",
         "O controle e o fechamento de ponto das equipes ainda é feito de forma manual em algumas unidades — um processo com potencial de automação."),
        ("Gerenciar Administração de Pessoal", "Gerente Corporativo Enfermagem", "A",
         "Lideranças de enfermagem relataram dedicar parte relevante do seu tempo a escala, ponto e desligamento de equipe, tarefas que poderiam contar com mais apoio direto da área de Gestão de Pessoas."),
        ("Gerenciar Administração de Pessoal", "Gerente Corporativo Operações", "A",
         "Supervisões operacionais também relataram realizar controle manual de ponto e horas extras de suas equipes."),
        ("Gerenciar Administração de Pessoal", "Gerente Médico", "A",
         "A gestão de escalas e ponto médico é hoje conduzida, em parte, pelas coordenações médicas de cada segmento."),
        ("Gerenciar Administração de Pessoal", "Gerente de Suprimentos", "A",
         "A formalização de contratos de médicos PJ e de outros prestadores tramita hoje por Suprimentos/Compras, o que reforça a oportunidade de aproximar esse fluxo da Gestão de Pessoas."),

        ("Gerenciar SESMT", "Gerente de Gestão de Pessoas", "R",
         "O agendamento de exames periódicos e a triagem de intercorrências ocupacionais às vezes são conduzidos por outras áreas, podendo ser mais concentrados no SESMT."),
        ("Gerenciar SESMT", "Gerente Segurança Assistencial", "A",
         "Segurança do trabalho e segurança do paciente compartilham temas de vigilância, com oportunidade de maior integração de indicadores entre as duas frentes."),

        ("Gerenciar Relacionamento Médico", "Gerente Corporativo Relacionamento com corpo clinico e clientes", "R",
         "A atuação dos diretores médicos junto ao corpo clínico ainda ocorre de forma pouco padronizada entre as unidades, sem um modelo único de governança de relacionamento."),
        ("Gerenciar Relacionamento Médico", "Gerente Médico", "A",
         "Em alguns casos, o credenciamento de corpo clínico passa pela aprovação do próprio chefe da especialidade envolvida, o que pode ser revisto para reduzir risco de conflito de interesse."),

        ("Gerenciar Práticas Médicas", "Gerente Médico", "R",
         "Existem hoje diferentes frentes de 'prática assistencial' (gerência médica, lideranças de prática e pessoas vinculadas a diferentes diretorias) atuando sem um modelo único definido, o que pode gerar sobreposição de papéis."),
        ("Gerenciar Práticas Médicas", "Gerente Segurança Assistencial", "A",
         "A avaliação de novas tecnologias e práticas envolve, em paralelo, diferentes áreas (regulatória, custo, uso clínico), com a decisão final dependendo de um comitê conjunto."),

        ("Gerenciar Resultados e Práticas Assistenciais", "Gerente Segurança Assistencial", "R",
         "Os indicadores de desfecho e eventos adversos ainda dependem de integração manual de dados vindos de múltiplas unidades."),
        ("Gerenciar Resultados e Práticas Assistenciais", "Gerente Corporativo Enfermagem", "A",
         "Parte da coleta de indicadores assistenciais é realizada pela própria liderança de enfermagem, que também apoia a apuração de resultados."),
        ("Gerenciar Resultados e Práticas Assistenciais", "Gerente Médico", "A",
         "A atuação em prática assistencial médica se sobrepõe, em parte, com a gerência médica e com lideranças de prática vinculadas a diferentes diretorias."),

        # ---- 6. Governança Corporativa e Suporte ---------------------------
        ("Gerenciar Governança Corporativa", "Gerente PMO", "R",
         "O PMO Corporativo está hoje posicionado junto à área administrativa; pode valer avaliar um posicionamento mais próximo da governança estratégica institucional."),
        ("Gerenciar Governança Corporativa", "Gerente Jurídico", "A",
         "O apoio jurídico a decisões de governança corporativa é recorrente, ainda sem um fórum conjunto formalmente definido."),

        ("Gerenciar Jurídico", "Gerente Jurídico", "R",
         "A reunião de documentos para defesas trabalhistas e alguns temas de gestão de imóveis são conduzidos hoje pelo Jurídico, podendo contar com mais apoio direto de RH/Patrimônio."),

        ("Gerenciar Qualidade", "Gerente de Qualidade", "R",
         "A área de Qualidade é acionada, em alguns projetos, apenas em etapa avançada, quando poderia estar envolvida desde o início pelos próprios responsáveis da área."),
        ("Gerenciar Qualidade", "Gerente Segurança Assistencial", "A",
         "As interfaces entre Qualidade e Segurança Assistencial têm oportunidade de maior integração de indicadores e fóruns conjuntos."),

        ("Gerenciar TI", "Gerente Tecnologia e Inovação", "R",
         "A definição de perfis de acesso aos sistemas ainda não está totalmente clara entre TI, Gestão de Pessoas e Qualidade."),
        ("Gerenciar TI", "Gerente de Infraestrutura", "A",
         "O monitoramento de infraestrutura crítica (nobreaks, climatização) depende de atuação conjunta e proativa entre TI e Engenharia."),

        ("Gerenciar Ensino e Pesquisa", "Gerente Ensino e Pesquisa", "R",
         "Em alguns casos, tratativas de pesquisa e isenções de ensino são conduzidas diretamente com a Direção, sem passar pela gerência responsável."),
        ("Gerenciar Ensino e Pesquisa", "Gerente Médico", "A",
         "A formação de médicos celetistas do corpo clínico ainda é tratada tanto por Ensino quanto por Educação Corporativa, sem uma definição única de responsabilidade."),
    ]


@st.cache_data
def montar_base() -> tuple[pd.DataFrame, dict]:
    """Consolida estrutura + relações em um único DataFrame "longo",
    com uma linha por cruzamento Função x Gerência."""
    pilares = carregar_estrutura()
    relacoes = carregar_relacoes()
    abreviacoes = carregar_abreviacoes()

    funcao_para_pilar = {}
    for nome_pilar, funcoes in pilares.items():
        for funcao in funcoes:
            funcao_para_pilar[funcao] = nome_pilar

    linhas = []
    for funcao, gerencia, papel, ponto_atencao in relacoes:
        linhas.append(
            {
                "Pilar": funcao_para_pilar[funcao],
                "Função": funcao,
                "Gerência": gerencia,
                "Gerência (abreviada)": abreviacoes.get(gerencia, gerencia),
                "Papel": papel,
                "Ponto de Atenção": ponto_atencao,
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
    Eixo Y = Funções ("Gerenciar ..."), na ordem original do pilar, com
    espaçamento reduzido para facilitar a visualização.
    Cor/tamanho da bolha = Papel (Responsável x Apoio).
    Hover = Função, Gerência completa e Ponto de Atenção (sem o rótulo de
    Papel, para manter o texto mais enxuto).
    """
    funcoes_visiveis = [f for f in ordem_funcoes if f in set(df_pilar["Função"])]

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

        customdata = subset[["Função", "Gerência", "Ponto de Atenção"]].values

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
                    "Gerência: <b>%{customdata[1]}</b><br><br>"
                    "<b>Ponto de atenção:</b><br>%{customdata[2]}"
                    "<extra></extra>"
                ),
            )
        )

    # Espaçamento vertical reduzido (menos altura por função) para diminuir
    # a necessidade de rolagem, mantendo boa legibilidade das bolhas.
    altura = max(340, 58 * len(funcoes_visiveis) + 130)

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
            tickfont=dict(size=11),
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
                Cruzamento entre as Funções organizacionais (6 Pilares de Sinergia) e as
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
    st.markdown(
        f"""
        <div class="legenda-card">
            <div class="legenda-titulo">🔵 Papel de responsabilidade (cor e tamanho da bolha)</div>
            <div>{itens_papel}</div>
            <div style="font-size:0.78rem; color:#64748B; margin-top:0.5rem;">
                💡 Passe o mouse sobre qualquer bolha para ver o principal ponto de atenção
                daquele cruzamento entre Função e Gerência.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_estatisticas(df_visivel: pd.DataFrame, total_gerencias: int) -> None:
    total_funcoes = df_visivel["Função"].nunique()
    total_gerencias_ativas = df_visivel["Gerência"].nunique()
    total_relacoes = len(df_visivel)

    col1, col2, col3, col4 = st.columns(4)
    cartoes = [
        (col1, total_funcoes, "Funções visíveis"),
        (col2, f"{total_gerencias_ativas}/{total_gerencias}", "Gerências envolvidas"),
        (col3, total_relacoes, "Relações mapeadas"),
        (col4, TOTAL_FORMULARIOS_RESPONDIDOS, "Formulários respondidos"),
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


def render_sidebar(gerencias_todas: list[str]) -> tuple[str, list[str]]:
    """Renderiza os filtros da barra lateral e retorna
    (termo_busca, gerencias_selecionadas)."""

    st.sidebar.markdown("## 🎛️ Painel de Filtros")
    st.sidebar.caption("Ajuste os filtros para focar em recortes específicos da matriz.")
    st.sidebar.markdown("---")

    st.session_state.setdefault("busca_funcao", "")
    st.session_state.setdefault("gerencias_selecionadas", gerencias_todas)

    st.sidebar.text_input(
        "1️⃣ Buscar Função ou Gerência",
        key="busca_funcao",
        placeholder="Ex.: leitos, farmácia, jurídico...",
        help="Busca por palavras-chave no nome da Função OU da Gerência.",
    )

    st.sidebar.multiselect(
        "2️⃣ Isolar Gerências específicas",
        options=gerencias_todas,
        key="gerencias_selecionadas",
        help="Remova gerências da lista para limpar o gráfico e focar em áreas específicas.",
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Limpar todos os filtros", use_container_width=True):
        st.session_state["busca_funcao"] = ""
        st.session_state["gerencias_selecionadas"] = gerencias_todas
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Fonte: Levantamento de Áreas 2026 — Redesenho Organizacional "
        "Santa Casa de Porto Alegre."
    )

    return (
        st.session_state["busca_funcao"],
        st.session_state["gerencias_selecionadas"],
    )


def render_exportacao(df_exportar: pd.DataFrame) -> None:
    """Botões de download (CSV e Excel) para o recorte atual (todos os
    pilares/abas visíveis após os filtros aplicados)."""
    st.markdown("#### 📥 Exportar matriz filtrada (todas as abas visíveis)")
    colunas_exportar = ["Pilar", "Função", "Gerência", "Papel", "Ponto de Atenção"]
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

    termo_busca, gerencias_selecionadas = render_sidebar(gerencias_todas)

    # -------- Aplica os filtros globais (busca + gerências) --------------
    df_filtrado = filtrar_por_busca(df, termo_busca)
    df_filtrado = df_filtrado[df_filtrado["Gerência"].isin(gerencias_selecionadas)]

    render_estatisticas(df_filtrado, total_gerencias=len(gerencias_todas))
    st.markdown("")

    # -------- Renderiza 1 aba por Pilar de Sinergia -----------------------
    nomes_pilares = list(pilares.keys())
    tabs = st.tabs(nomes_pilares)

    for tab, nome_pilar in zip(tabs, nomes_pilares):
        with tab:
            funcoes_pilar = pilares[nome_pilar]
            st.markdown(
                f'<div class="pilar-caption">{len(funcoes_pilar)} funções mapeadas neste pilar</div>',
                unsafe_allow_html=True,
            )

            df_pilar = df_filtrado[df_filtrado["Pilar"] == nome_pilar]

            if df_pilar.empty:
                st.warning(
                    "⚠️ Nenhuma função ou gerência deste pilar corresponde aos "
                    "filtros atuais. Ajuste a busca ou as gerências selecionadas "
                    "na barra lateral."
                )
                continue

            fig = criar_matriz_bolhas(df_pilar, funcoes_pilar)
            st.plotly_chart(fig, use_container_width=True, key=f"grafico_{nome_pilar}")

    # -------- Exportação (considera todos os pilares após os filtros) -----
    st.markdown("---")
    render_exportacao(df_filtrado)

    st.markdown("---")
    st.caption(
        "💡 Dica: passe o mouse sobre as bolhas para ver o principal ponto de atenção "
        "de cada cruzamento. Use a legenda do gráfico (clique nos itens) para isolar só 'Responsável' ou só 'Apoio'."
    )


if __name__ == "__main__":
    main()
