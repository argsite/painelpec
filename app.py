import csv
from datetime import datetime
import io
import re
import unicodedata
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Painel de Monitoramento e-SUS APS",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# ESTILO VISUAL (Réplica fiel do Tailwind / Glass-Card do index.html original)
# ==============================================================================
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* Oculta barra padrão do Streamlit para destacar o header customizado */
        header[data-testid="stHeader"] {
            background: transparent;
            height: 0.5rem;
        }
        .stApp {
            background-color: #f8fafc;
            font-family: 'Inter', sans-serif;
            color: #1e293b;
        }
        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 2rem !important;
            max-width: 96% !important;
        }

        /* Header Azul Principal */
        .esus-header {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: #ffffff;
            padding: 1.15rem 1.75rem;
            border-radius: 1rem;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.18);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .esus-header-title {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            margin: 0;
        }
        .esus-status-pill {
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.25);
            padding: 0.4rem 0.9rem;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
        }

        /* Glass Card */
        .glass-card {
            background: rgba(255, 255, 255, 0.97);
            border-radius: 1rem;
            padding: 1.35rem 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
            border: 1px solid #e2e8f0;
            margin-bottom: 1rem;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .glass-card:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.06);
        }
        .kpi-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .kpi-label {
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin: 0;
        }
        .kpi-value-row {
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
            margin-top: 0.4rem;
        }
        .kpi-value {
            font-size: 2.15rem;
            font-weight: 800;
            color: #1e293b;
            line-height: 1.1;
            margin: 0;
        }
        .kpi-pct {
            font-size: 1.05rem;
            font-weight: 700;
        }
        .kpi-badge {
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.2rem 0.55rem;
            border-radius: 0.375rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .kpi-icon-circle {
            width: 3.25rem;
            height: 3.25rem;
            border-radius: 9999px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.35rem;
            flex-shrink: 0;
        }
        .kpi-progress-bg {
            width: 100%;
            height: 0.5rem;
            background-color: #e2e8f0;
            border-radius: 9999px;
            margin-top: 1rem;
            overflow: hidden;
        }
        .kpi-progress-fill {
            height: 100%;
            border-radius: 9999px;
            transition: width 0.6s ease;
        }

        /* Títulos de Seção */
        .section-title {
            font-size: 1.08rem;
            font-weight: 700;
            color: #334155;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 0.65rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Tabela de Boas Práticas */
        .bp-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }
        .bp-table thead th {
            background-color: #f8fafc;
            color: #475569;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.74rem;
            letter-spacing: 0.04em;
            padding: 0.75rem 0.9rem;
            border-bottom: 1px solid #e2e8f0;
        }
        .bp-table tbody tr {
            border-bottom: 1px solid #f1f5f9;
            transition: background-color 0.15s;
        }
        .bp-table tbody tr:hover {
            background-color: #f8fafc;
        }
        .bp-table td {
            padding: 0.75rem 0.9rem;
            vertical-align: middle;
        }
        .pts-tag {
            font-size: 0.68rem;
            background-color: #e2e8f0;
            color: #475569;
            padding: 0.15rem 0.5rem;
            border-radius: 0.35rem;
            font-weight: 700;
            margin-left: 0.45rem;
        }

        /* Estilização do Segmented Control / Botões */
        div[data-baseweb="segmented-control"] {
            background-color: #e2e8f0 !important;
            padding: 0.25rem !important;
            border-radius: 0.75rem !important;
        }
        div[data-testid="stDownloadButton"] button {
            background-color: #059669 !important;
            color: white !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 0.5rem !important;
            padding: 0.45rem 1rem !important;
        }
        div[data-testid="stDownloadButton"] button:hover {
            background-color: #047857 !important;
        }

        /* Footer */
        .esus-footer {
            background-color: #1e293b;
            color: #94a3b8;
            text-align: center;
            padding: 0.9rem;
            border-radius: 0.75rem;
            font-size: 0.82rem;
            margin-top: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# CONFIGURAÇÕES DAS LINHAS DE CUIDADO E MÉTRICAS
# ==============================================================================
CONDITIONS = {
    "geral": {
        "label": "Geral",
        "full_label": "Geral - Todos os Pacientes",
        "file": "acompanhamento-condicao-saude_2026-11-13-13-26.csv",
        "metrics": [
            {
                "id": "consulta",
                "shortName": "Consulta (12m)",
                "bpDesc": "Ter pelo menos 01 (uma) consulta presencial ou remota nos últimos 12 meses.",
                "points": 25,
                "name": "Consultas Recentes",
                "icon": "fa-user-doctor",
                "hex": "#6366f1",
                "bg": "#e0e7ff",
                "forceCol": 21,
                "maxDays": 365,
            },
            {
                "id": "visita",
                "shortName": "Visita ACS (12m)",
                "bpDesc": "Ter pelo menos 01 (uma) visita domiciliar por ACS/TACS nos últimos 12 meses.",
                "points": 25,
                "name": "Visitas ACS",
                "icon": "fa-house-medical",
                "hex": "#10b981",
                "bg": "#d1fae5",
                "forceCol": 27,
                "maxDays": 365,
            },
            {
                "id": "peso_altura",
                "shortName": "Peso/Altura (12m)",
                "bpDesc": "Ter pelo menos 01 (um) registro de peso e altura nos últimos 12 meses.",
                "points": 25,
                "hidden": True,
                "forceCol": 31,
                "maxDays": 365,
            },
            {
                "id": "pa",
                "shortName": "Aferição PA (12m)",
                "bpDesc": "Ter pelo menos 01 (um) registro de aferição de pressão arterial nos últimos 12 meses.",
                "points": 25,
                "hidden": True,
                "forceCol": 33,
                "maxDays": 365,
            },
        ],
    },
    "infantil": {
        "label": "C2 - Desenvolvimento Infantil",
        "full_label": "C2 - Desenvolvimento Infantil",
        "file": "acompanhamento-condicao-saude_2026-11-05-08-44.csv",
        "metrics": [
            {
                "id": "consulta_1",
                "shortName": "1ª Cons. (30d)",
                "bpDesc": "Ter a 1ª consulta presencial realizada por médica(o) ou enfermeira(o), até o 30º dia de vida.",
                "points": 20,
                "hidden": True,
                "forceCol": 21,
            },
            {
                "id": "consulta_med_inf",
                "shortName": "9 Consultas (2a)",
                "bpDesc": "Ter pelo menos 09 (nove) consultas presenciais ou remotas realizadas por médica(o) ou enfermeira(o) até dois anos de vida.",
                "points": 20,
                "hidden": True,
                "forceCol": 21,
                "maxDays": 730,
            },
            {
                "id": "peso_altura_inf",
                "shortName": "9 Pesos/Alturas",
                "bpDesc": "Ter pelo menos 09 (nove) registros simultâneos de peso e altura até os dois anos de vida.",
                "points": 20,
                "hidden": True,
                "forceCol": 31,
                "maxDays": 730,
            },
            {
                "id": "visita_acs_inf",
                "shortName": "2 Visitas ACS",
                "bpDesc": "Ter pelo menos 02 (duas) visitas domiciliares realizadas por ACS/TACS, sendo a primeira até os 30 dias e a segunda até 6 meses.",
                "points": 20,
                "hidden": True,
                "forceCol": 27,
                "maxDays": 180,
            },
            {
                "id": "vacina_inf",
                "shortName": "Vacinas",
                "bpDesc": "Ter vacinas contra difteria, tétano, coqueluche, hepatite B, infecções por Haemophilus influenza e tipo b, poliomielite, sarampo, caxumba e rubéola, pneumocócica, com todas as doses.",
                "points": 20,
                "name": "Vacinação Avaliada",
                "icon": "fa-child-reaching",
                "hex": "#0ea5e9",
                "bg": "#e0f2fe",
                "searches": ["vacina", "imuniza", "polio", "penta"],
            },
        ],
    },
    "gestantes": {
        "label": "C3 - Gestantes e Puérperas",
        "full_label": "C3 - Gestantes e Puérperas",
        "file": "acompanhamento-condicao-saude_2026-11-05-07-42 (1).csv",
        "metrics": [
            {
                "id": "cons_12s",
                "shortName": "1ª Cons. (12 sem)",
                "bpDesc": "Ter a 1ª consulta presencial ou remota realizada por médica(o) ou enfermeira(o), até a 12ª semana de gestação.",
                "points": 10,
                "hidden": True,
                "forceCol": 21,
            },
            {
                "id": "cons_7",
                "shortName": "7 Consultas",
                "bpDesc": "Ter pelo menos 07 (sete) consultas presenciais ou remotas realizadas por médica(o) ou enfermeira(o) durante a gestação.",
                "points": 9,
                "hidden": True,
                "forceCol": 21,
            },
            {
                "id": "pa_7",
                "shortName": "7 Aferições PA",
                "bpDesc": "Ter pelo menos 07 (sete) registros de aferição de pressão arterial realizados durante o período da gestação.",
                "points": 9,
                "hidden": True,
                "forceCol": 33,
            },
            {
                "id": "peso_7",
                "shortName": "7 Pesos/Alturas",
                "bpDesc": "Ter pelo menos 07 (sete) registros simultâneos de peso e altura durante o período da gestação.",
                "points": 9,
                "hidden": True,
                "forceCol": 31,
            },
            {
                "id": "vd_3",
                "shortName": "3 Visitas ACS",
                "bpDesc": "Ter pelo menos 03 (três) visitas domiciliares realizadas por ACS/TACS, após a primeira consulta do pré-natal.",
                "points": 9,
                "hidden": True,
                "forceCol": 27,
            },
            {
                "id": "vac_dtpa",
                "shortName": "Vacina dTpa",
                "bpDesc": "Ter vacina acelular contra difteria, tétano, coqueluche (dTpa) registrada a partir da 20ª semana.",
                "points": 9,
                "hidden": True,
                "forceCol": 46,
                "notDash": True,
            },
            {
                "id": "testes_1tri",
                "shortName": "Testes 1º Tri",
                "bpDesc": "Ter registro dos testes rápidos ou exames para sífilis, HIV e hepatites B e C no 1º trimestre.",
                "points": 9,
                "hidden": True,
                "forceCols": [50, 51, 52, 53],
                "requireAllSim": True,
            },
            {
                "id": "testes_3tri",
                "shortName": "Testes 3º Tri",
                "bpDesc": "Ter registro dos testes rápidos ou exames para sífilis e HIV realizados no 3º trimestre.",
                "points": 9,
                "hidden": True,
                "forceCols": [54, 55],
                "requireAllSim": True,
            },
            {
                "id": "cons_puerp",
                "shortName": "Cons. Puerpério",
                "bpDesc": "Ter pelo menos 01 (um) registro de consulta durante o puerpério.",
                "points": 9,
                "hidden": True,
            },
            {
                "id": "vd_puerp",
                "shortName": "Visita Puerpério",
                "bpDesc": "Ter pelo menos 01 (uma) visita domiciliar por ACS/TACS durante o puerpério.",
                "points": 9,
                "hidden": True,
            },
            {
                "id": "odonto",
                "shortName": "Odonto",
                "bpDesc": "Ter pelo menos 01 (uma) atividade em saúde bucal durante a gestação.",
                "points": 9,
                "name": "Atend. Odontológico",
                "icon": "fa-tooth",
                "hex": "#a855f7",
                "bg": "#f3e8ff",
                "searches": ["odonto", "odontologico", "odontológico"],
            },
        ],
    },
    "diabeticos": {
        "label": "C4 - Diabéticos",
        "full_label": "C4 - Diabéticos",
        "file": "acompanhamento-condicao-saude_2026-11-04-15-17.csv",
        "metrics": [
            {
                "id": "consulta_med",
                "shortName": "Cons. Médica (6m)",
                "bpDesc": "Ter pelo menos 01 (uma) consulta presencial ou remota realizadas por médica(o) ou enfermeira(o), nos últimos 06 (seis) meses.",
                "points": 20,
                "hidden": True,
                "forceCol": 21,
                "maxDays": 180,
            },
            {
                "id": "pa_recente",
                "shortName": "Aferição PA (6m)",
                "bpDesc": "Ter pelo menos 01 (um) registro de aferição de pressão arterial realizado nos últimos 06 (seis) meses.",
                "points": 15,
                "hidden": True,
                "forceCol": 33,
                "maxDays": 180,
            },
            {
                "id": "peso_altura",
                "shortName": "Peso/Altura (12m)",
                "bpDesc": "Ter pelo menos 01 (um) registro simultâneos de peso e altura realizado nos últimos 12 (doze) meses.",
                "points": 15,
                "hidden": True,
                "forceCol": 31,
                "maxDays": 365,
            },
            {
                "id": "visita_acs",
                "shortName": "Visita ACS (12m)",
                "bpDesc": "Ter pelo menos 02 (duas) visitas domiciliares realizadas por ACS/TACS, com intervalo mínimo de 30 (trinta) dias, nos últimos 12 (doze) meses.",
                "points": 20,
                "hidden": True,
                "forceCol": 27,
                "maxDays": 365,
            },
            {
                "id": "hba1c",
                "shortName": "Solic. HbA1c",
                "bpDesc": "Ter pelo menos 01 (um) registro de solicitação de hemoglobina glicada realizada ou avaliada, nos últimos 12 (doze) meses.",
                "points": 15,
                "name": "HBA1C Solicitada",
                "icon": "fa-vial",
                "hex": "#14b8a6",
                "bg": "#ccfbf1",
                "searches": ["hemoglobina", "glicada", "hba1c"],
            },
            {
                "id": "pes",
                "shortName": "Avaliação Pés",
                "bpDesc": "Ter pelo menos 01 (uma) avaliação dos pés realizada nos últimos 12 (doze) meses.",
                "points": 15,
                "name": "Avaliação Pés",
                "icon": "fa-shoe-prints",
                "hex": "#6366f1",
                "bg": "#e0e7ff",
                "searches": ["pe", "pes"],
                "exclude": "peso",
                "forceCol": 39,
            },
        ],
    },
    "hipertensos": {
        "label": "C5 - Hipertensos",
        "full_label": "C5 - Hipertensos",
        "file": "acompanhamento-condicao-saude_2026-11-04-15-17 (1).csv",
        "metrics": [
            {
                "id": "consulta_med",
                "shortName": "Cons. Médica (6m)",
                "bpDesc": "Ter pelo menos 01 (uma) consulta presencial ou remota realizadas por médica(o) ou enfermeira(o), nos últimos 06 (seis) meses.",
                "points": 25,
                "hidden": True,
                "forceCol": 21,
                "maxDays": 180,
            },
            {
                "id": "pa",
                "shortName": "Aferição de PA (6m)",
                "bpDesc": "Ter pelo menos 01 (um) registro de aferição de pressão arterial realizado nos últimos 06 (seis) meses.",
                "points": 25,
                "name": "Aferição de PA",
                "icon": "fa-heart-pulse",
                "hex": "#f43f5e",
                "bg": "#ffe4e6",
                "searches": ["pressao", "pa", "afericao", "pressão"],
                "forceCol": 33,
                "maxDays": 180,
            },
            {
                "id": "peso_altura",
                "shortName": "Peso/Altura (12m)",
                "bpDesc": "Ter pelo menos 01 (um) registro simultâneos de peso e altura realizado nos últimos 12 (doze) meses.",
                "points": 25,
                "hidden": True,
                "forceCol": 31,
                "maxDays": 365,
            },
            {
                "id": "visita_acs",
                "shortName": "Visita ACS (12m)",
                "bpDesc": "Ter pelo menos 02 (duas) visitas domiciliares realizadas por ACS/TACS, com intervalo mínimo de 30 (trinta) dias, nos últimos 12 (doze) meses.",
                "points": 25,
                "hidden": True,
                "forceCol": 27,
                "maxDays": 365,
            },
        ],
    },
    "idosos": {
        "label": "C6 - Idosos",
        "full_label": "C6 - Idosos",
        "file": "acompanhamento-condicao-saude_2026-11-05-08-41.csv",
        "metrics": [
            {
                "id": "consulta_med_12m",
                "shortName": "Cons. Médica (12m)",
                "bpDesc": "Ter realizado pelo menos 01 (uma) consulta por profissional médica(o) ou enfermeira(o) nos últimos 12 meses.",
                "points": 25,
                "hidden": True,
                "forceCol": 21,
                "maxDays": 365,
            },
            {
                "id": "peso_altura",
                "shortName": "Peso/Altura (12m)",
                "bpDesc": "Ter realizado pelo menos 01 (um) registro simultâneo de peso e altura nos últimos 12 meses.",
                "points": 25,
                "hidden": True,
                "forceCol": 31,
                "maxDays": 365,
            },
            {
                "id": "visita_acs",
                "shortName": "Visita ACS (12m)",
                "bpDesc": "Ter pelo menos 02 (duas) visitas domiciliares realizadas por ACS/TACS, com intervalo mínimo de 30 dias, nos últimos 12 meses.",
                "points": 25,
                "hidden": True,
                "forceCol": 27,
                "maxDays": 365,
            },
            {
                "id": "vacina",
                "shortName": "Vacina Influenza",
                "bpDesc": "Ter registro de 1 (uma) dose da vacina contra influenza realizada nos últimos 12 meses.",
                "points": 25,
                "name": "Vacina Influenza",
                "icon": "fa-syringe",
                "hex": "#f97316",
                "bg": "#ffedd5",
                "searches": ["vacina", "influenza", "imuniza"],
            },
        ],
    },
    "mulher": {
        "label": "C7 - Saúde da Mulher",
        "full_label": "C7 - Saúde da Mulher",
        "file": "acompanhamento-condicao-saude_2026-11-05-08-47.csv",
        "metrics": [
            {
                "id": "cito",
                "shortName": "Preventivo (36m)",
                "bpDesc": "Ter pelo menos 01 (um) exame de rastreamento para câncer do colo do útero em mulheres e homens transgênero de 25 a 64 anos nos últimos 36 meses.",
                "points": 20,
                "name": "Citopatológico",
                "icon": "fa-microscope",
                "hex": "#ec4899",
                "bg": "#fce7f3",
                "searches": ["cito", "preventivo", "colo"],
                "maxDays": 1095,
            },
            {
                "id": "hpv",
                "shortName": "Vacina HPV",
                "bpDesc": "Ter pelo menos 01 (uma) dose da vacina HPV para crianças e adolescentes do sexo feminino de 09 a 14 anos de idade.",
                "points": 30,
                "hidden": True,
            },
            {
                "id": "saude_sexual",
                "shortName": "Atenção Saúde Sexual",
                "bpDesc": "Ter pelo 01 (um) atendimento presencial ou remoto sobre atenção à saúde sexual e reprodutiva nos últimos 12 meses.",
                "points": 30,
                "hidden": True,
            },
            {
                "id": "mama",
                "shortName": "Mamografia (24m)",
                "bpDesc": "Ter registro de pelo menos 01 (um) exame de rastreamento para câncer de mama de 50 a 69 anos nos últimos 24 meses.",
                "points": 20,
                "name": "Mamografia",
                "icon": "fa-x-ray",
                "hex": "#d946ef",
                "bg": "#fae8ff",
                "searches": ["mama", "mamografia"],
                "maxDays": 730,
            },
        ],
    },
}


# ==============================================================================
# FUNÇÕES DE LEITURA, NORMALIZAÇÃO E CÁLCULO (Com Cache em Memória)
# ==============================================================================
def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def sanitize_text(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val)
    replacements = {
        "Ã§": "ç", "Ã‡": "Ç", "Ã£": "ã", "Ãƒ": "Ã",
        "Ã¡": "á", "Ã ": "Á", "Ã©": "é", "Ã‰": "É",
        "Ã­": "í", "Ã“": "Ó", "Ãº": "ú", "Ãš": "Ú",
        "Ãª": "ê", "ÃÊ": "Ê", "Ã´": "ô", "Ã”": "Ô",
        "Ã ": "à", "Ã€": "À",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    s = re.sub(r"[\ufffd\x7f-\x9f]", "", s)
    return s.strip()


def decode_csv_bytes(raw_bytes: bytes) -> str:
    try:
        text = raw_bytes.decode("iso-8859-1")
    except UnicodeDecodeError:
        text = raw_bytes.decode("utf-8", errors="replace")
    return sanitize_text(text)


def parse_rows(csv_text: str) -> list[list[str]]:
    lines = csv_text.splitlines()
    if not lines:
        return []
    first_chunk = "\n".join(lines[:30])
    delimiter = ";" if first_chunk.count(";") >= first_chunk.count(",") else ","
    return list(csv.reader(lines, delimiter=delimiter))


def has_date_or_recent(val: str, max_days: int | None) -> bool:
    if not val or val == "-":
        return False
    val = val.strip()
    if val.upper() == "SIM":
        return True
    if re.fullmatch(r"\d+", val):
        return True if max_days is None else int(val) <= max_days

    m = re.search(r"(\d{2})/(\d{2})/(\d{2,4})", val)
    if m:
        if max_days is None:
            return True
        day, month, year_str = int(m.group(1)), int(m.group(2)), int(m.group(3))
        year = year_str + 2000 if year_str < 100 else year_str
        try:
            dt = datetime(year, month, day)
            ref = datetime(2026, 11, 5)
            return abs((ref - dt).days) <= max_days
        except ValueError:
            return False
    return False


@st.cache_data(show_spinner=False)
def analyze_condition_data(csv_text: str, condition_key: str) -> dict:
    rows = parse_rows(csv_text)
    if not rows:
        return {}

    header_idx = 24
    for i in range(min(len(rows), 50)):
        if not rows[i]:
            continue
        row_norm = strip_accents(" ".join(rows[i]).lower())
        if "idade" in row_norm and "sexo" in row_norm:
            header_idx = i
            break

    if header_idx >= len(rows):
        return {}

    fields = rows[header_idx]
    data_rows = rows[header_idx + 1 :]
    current_metrics = CONDITIONS[condition_key]["metrics"]

    col_micro = col_idade = col_nome = col_sexo = col_nascimento = -1
    col_rua = col_num = col_bairro = -1
    metric_cols = {m["id"]: -1 for m in current_metrics}

    for idx, f in enumerate(fields):
        if not f:
            continue
        norm = strip_accents(sanitize_text(f).lower()).strip()
        if any(k in norm for k in ("nome", "cidadao", "paciente")):
            col_nome = idx
        if norm in ("microarea", "microarea / area") or "micro" in norm:
            col_micro = idx
        if norm in ("idade", "idade (anos)"):
            col_idade = idx
        if norm == "sexo":
            col_sexo = idx
        if "nascimento" in norm:
            col_nascimento = idx
        if norm in ("rua", "logradouro", "endereco"):
            col_rua = idx
        if norm in ("numero", "n"):
            col_num = idx
        if norm == "bairro":
            col_bairro = idx

        for m in current_metrics:
            searches = m.get("searches")
            if not searches:
                continue
            matched = False
            for s in searches:
                s_norm = strip_accents(s.lower())
                if s_norm in ("pe", "pes", "pa"):
                    if re.search(rf"\b{s_norm}\b", norm):
                        matched = True
                        break
                elif s_norm in norm:
                    matched = True
                    break
            excluded = m.get("exclude")
            pass_excl = (strip_accents(excluded.lower()) not in norm) if excluded else True
            if matched and pass_excl:
                metric_cols[m["id"]] = idx

    for m in current_metrics:
        if metric_cols[m["id"]] == -1 and m.get("forceCol") is not None:
            if len(fields) > m["forceCol"]:
                metric_cols[m["id"]] = m["forceCol"]

    total = 0
    metric_counts = {m["id"]: 0 for m in current_metrics}
    microareas: dict[str, int] = {}
    sexo_counts = {"Feminino": 0, "Masculino": 0}
    faixa_counts = {
        "0-19 anos": 0,
        "20-39 anos": 0,
        "40-59 anos": 0,
        "60-79 anos": 0,
        "80+ anos": 0,
    }
    patients = []
    current_year = datetime.now().year

    for row in data_rows:
        if not row or len(row) < 2:
            continue
        nome_raw = sanitize_text(row[col_nome]) if 0 <= col_nome < len(row) else ""
        idade_raw = sanitize_text(row[col_idade]) if 0 <= col_idade < len(row) else ""
        if col_nome != -1 and not nome_raw and col_idade != -1 and not idade_raw:
            continue

        total += 1
        nome = nome_raw if nome_raw else f"Paciente {total}"
        micro = sanitize_text(row[col_micro]) if 0 <= col_micro < len(row) and sanitize_text(row[col_micro]) else "Sem Micro"
        nascimento = sanitize_text(row[col_nascimento]) if 0 <= col_nascimento < len(row) and sanitize_text(row[col_nascimento]) else "-"

        end_parts = []
        if 0 <= col_rua < len(row) and sanitize_text(row[col_rua]):
            end_parts.append(sanitize_text(row[col_rua]))
        if 0 <= col_num < len(row) and sanitize_text(row[col_num]):
            end_parts.append(f"Nº {sanitize_text(row[col_num])}")
        if 0 <= col_bairro < len(row) and sanitize_text(row[col_bairro]):
            end_parts.append(sanitize_text(row[col_bairro]))
        endereco = ", ".join(end_parts).upper() if end_parts else "-"

        microareas[micro] = microareas.get(micro, 0) + 1

        if 0 <= col_sexo < len(row):
            s_val = sanitize_text(row[col_sexo]).lower()
            if s_val.startswith("m"):
                sexo_counts["Masculino"] += 1
            elif s_val.startswith("f"):
                sexo_counts["Feminino"] += 1

        idade_texto = idade_raw if idade_raw else "-"
        faixa_str = ""
        idade_num = None

        if idade_raw:
            m_date = re.search(r"\d{2}/\d{2}/(\d{4})", idade_raw)
            if m_date:
                idade_num = current_year - int(m_date.group(1))
            elif "menor" in idade_raw.lower():
                idade_num = 0
            else:
                m_num = re.match(r"^(\d+)", idade_raw)
                if m_num:
                    idade_num = int(m_num.group(1))

        if idade_num is not None:
            if idade_num < 20:
                faixa_counts["0-19 anos"] += 1
                faixa_str = "0-19 anos"
            elif idade_num < 40:
                faixa_counts["20-39 anos"] += 1
                faixa_str = "20-39 anos"
            elif idade_num < 60:
                faixa_counts["40-59 anos"] += 1
                faixa_str = "40-59 anos"
            elif idade_num < 80:
                faixa_counts["60-79 anos"] += 1
                faixa_str = "60-79 anos"
            else:
                faixa_counts["80+ anos"] += 1
                faixa_str = "80+ anos"

        p_metrics = {}
        for m in current_metrics:
            mid = m["id"]
            has_met = False

            if m.get("requireAllSim") and m.get("forceCols"):
                has_met = True
                for c in m["forceCols"]:
                    if len(row) > c:
                        v = sanitize_text(row[c]).upper()
                        if v not in ("SIM", "NAO_SE_APLICA", "NÃO SE APLICA"):
                            has_met = False
                            break
                    else:
                        has_met = False
                        break
            elif m.get("notDash"):
                c_idx = metric_cols[mid]
                if 0 <= c_idx < len(row):
                    v = sanitize_text(row[c_idx])
                    has_met = v not in ("", "-")
            elif m.get("checkSim") and m.get("forceCols"):
                for c in m["forceCols"]:
                    if len(row) > c and sanitize_text(row[c]).upper() == "SIM":
                        has_met = True
                        break
            else:
                c_idx = metric_cols[mid]
                if 0 <= c_idx < len(row):
                    has_met = has_date_or_recent(sanitize_text(row[c_idx]), m.get("maxDays"))

            p_metrics[mid] = has_met
            if has_met:
                metric_counts[mid] += 1

        patients.append({
            "Nome do(a) Paciente": nome,
            "Nascimento": nascimento,
            "Idade": idade_texto,
            "Endereço": endereco,
            "Microárea": micro,
            "_faixa": faixa_str,
            "_metrics": p_metrics,
        })

    return {
        "total": total,
        "metric_counts": metric_counts,
        "microareas": microareas,
        "sexo": sexo_counts,
        "faixa_etaria": faixa_counts,
        "patients": patients,
    }


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Acompanhamento") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


def render_kpi_card(
    title: str,
    value_str: str,
    border_hex: str,
    icon_cls: str,
    icon_hex: str,
    icon_bg: str,
    sub_html: str = "",
    bar_pct: float | None = None,
    bar_hex: str = "#3b82f6",
):
    progress_html = (
        f'<div class="kpi-progress-bg"><div class="kpi-progress-fill" style="width: {min(max(bar_pct, 0), 100)}%; background-color: {bar_hex};"></div></div>'
        if bar_pct is not None
        else '<div style="height: 0.5rem; margin-top: 1rem;"></div>'
    )
    st.markdown(
        f"""
        <div class="glass-card" style="border-left: 4px solid {border_hex};">
            <div class="kpi-top">
                <div>
                    <p class="kpi-label">{title}</p>
                    <div class="kpi-value-row">
                        <h2 class="kpi-value">{value_str}</h2>
                        {sub_html}
                    </div>
                </div>
                <div class="kpi-icon-circle" style="background-color: {icon_bg}; color: {icon_hex};">
                    <i class="fa-solid {icon_cls}"></i>
                </div>
            </div>
            {progress_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# INTERFACE PRINCIPAL
# ==============================================================================
if "csv_store" not in st.session_state:
    st.session_state["csv_store"] = {}

cond_keys = list(CONDITIONS.keys())
cond_labels = [CONDITIONS[k]["label"] for k in cond_keys]

selected_idx = st.segmented_control(
    "Linha de Cuidado",
    options=list(range(len(cond_keys))),
    format_func=lambda i: cond_labels[i],
    default=0,
    label_visibility="collapsed",
)
current_cond = cond_keys[selected_idx if selected_idx is not None else 0]
cond_cfg = CONDITIONS[current_cond]

csv_text = st.session_state["csv_store"].get(current_cond)
data_source_status = "Dados Em Memória"

if csv_text is None:
    try:
        with open(cond_cfg["file"], "rb") as f:
            csv_text = decode_csv_bytes(f.read())
            st.session_state["csv_store"][current_cond] = csv_text
            data_source_status = "Dados Carregados"
    except FileNotFoundError:
        data_source_status = "Selecione um arquivo"

status_icon = (
    '<i class="fa-solid fa-check-circle" style="color: #86efac;"></i>'
    if csv_text
    else '<i class="fa-solid fa-circle-exclamation" style="color: #fde047;"></i>'
)

st.markdown(
    f"""
    <div class="esus-header">
        <div class="esus-header-title">
            <i class="fa-solid fa-file-medical"></i>
            <span>Painel de Monitoramento e-SUS APS</span>
        </div>
        <div class="esus-status-pill">
            {status_icon}
            <span>{data_source_status}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("📂 Importar ou substituir relatório CSV do e-SUS PEC", expanded=(csv_text is None)):
    uploaded_file = st.file_uploader(
        f"Selecione o arquivo CSV correspondente a {cond_cfg['full_label']}",
        type=["csv"],
        key=f"uploader_{current_cond}",
    )
    if uploaded_file is not None:
        decoded = decode_csv_bytes(uploaded_file.getvalue())
        if st.session_state["csv_store"].get(current_cond) != decoded:
            st.session_state["csv_store"][current_cond] = decoded
            st.rerun()

if not csv_text:
    st.markdown(
        """
        <div style="background-color: #fefce8; border-left: 4px solid #facc15; padding: 1rem 1.25rem; border-radius: 0 0.5rem 0.5rem 0; color: #854d0e;">
            <strong><i class="fa-solid fa-triangle-exclamation"></i> Importar relatório do PEC</strong><br>
            <span style="font-size: 0.9rem;">Carregue o arquivo CSV correspondente acima para gerar a análise desta linha de cuidado.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

stats = analyze_condition_data(csv_text, current_cond)
if not stats or stats["total"] == 0:
    st.error("Não foi possível identificar cabeçalhos ou registros válidos no arquivo selecionado.")
    st.stop()

current_metrics = cond_cfg["metrics"]
total_patients = stats["total"]

# ==============================================================================
# 1. CARDS DE KPIs
# ==============================================================================
visible_metrics = [m for m in current_metrics if not m.get("hidden")]
num_cards = 1 + (1 if current_cond != "geral" else 0) + len(visible_metrics)
kpi_cols = st.columns(min(max(num_cards, 2), 4))

with kpi_cols[0]:
    render_kpi_card(
        title=f"Total de {cond_cfg['full_label']}",
        value_str=str(total_patients),
        border_hex="#3b82f6",
        icon_cls="fa-users",
        icon_hex="#2563eb",
        icon_bg="#dbeafe",
    )

col_idx = 1
if current_cond != "geral":
    total_pts = sum(
        m.get("points", 0)
        for p in stats["patients"]
        for m in current_metrics
        if p["_metrics"].get(m["id"])
    )
    final_score = round(total_pts / total_patients, 1) if total_patients > 0 else 0.0

    if final_score > 75:
        param, s_hex, s_bg, s_txt = "Ótimo", "#10b981", "#d1fae5", "#047857"
    elif final_score > 50:
        param, s_hex, s_bg, s_txt = "Bom", "#3b82f6", "#dbeafe", "#1d4ed8"
    elif final_score > 25:
        param, s_hex, s_bg, s_txt = "Suficiente", "#facc15", "#fef9c3", "#a16207"
    else:
        param, s_hex, s_bg, s_txt = "Regular", "#f43f5e", "#ffe4e6", "#be123c"

    badge_html = f'<span class="kpi-badge" style="background-color: {s_bg}; color: {s_txt};">{param}</span>'
    with kpi_cols[col_idx % len(kpi_cols)]:
        render_kpi_card(
            title="Score do Indicador",
            value_str=f"{final_score}",
            border_hex=s_hex,
            icon_cls="fa-ranking-star",
            icon_hex=s_txt,
            icon_bg=s_bg,
            sub_html=badge_html,
            bar_pct=final_score,
            bar_hex=s_hex,
        )
    col_idx += 1

for m in visible_metrics:
    cnt = stats["metric_counts"].get(m["id"], 0)
    pct = round((cnt / total_patients) * 100) if total_patients > 0 else 0
    pct_html = f'<span class="kpi-pct" style="color: {m["hex"]};">({pct}%)</span>'
    with kpi_cols[col_idx % len(kpi_cols)]:
        render_kpi_card(
            title=m.get("name", m["shortName"]),
            value_str=str(cnt),
            border_hex=m["hex"],
            icon_cls=m.get("icon", "fa-check"),
            icon_hex=m["hex"],
            icon_bg=m.get("bg", "#e2e8f0"),
            sub_html=pct_html,
            bar_pct=pct,
            bar_hex=m["hex"],
        )
    col_idx += 1

# ==============================================================================
# 2. TABELA DE BOAS PRÁTICAS E DESEMPENHO
# ==============================================================================
if current_cond != "geral":
    rows_html = []
    for m in current_metrics:
        cnt = stats["metric_counts"].get(m["id"], 0)
        pct = round((cnt / total_patients) * 100) if total_patients > 0 else 0
        not_done = total_patients - cnt
        rows_html.append(
            f"""
            <tr>
                <td>
                    <div style="font-weight: 700; color: #1e293b;">
                        {m.get("shortName") or m.get("name")}
                        <span class="pts-tag">{m.get("points", 0)} pts</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #64748b; margin-top: 0.25rem;">{m["bpDesc"]}</div>
                </td>
                <td style="text-align: center; font-weight: 800; color: #334155; width: 6rem;">{pct}%</td>
                <td style="text-align: center; font-weight: 700; color: #059669; width: 7rem;">{cnt}</td>
                <td style="text-align: center; font-weight: 700; color: #f43f5e; width: 7rem;">{not_done}</td>
            </tr>
            """
        )

    st.markdown(
        f"""
        <div class="glass-card">
            <div class="section-title">
                <i class="fa-solid fa-list-check" style="color: #2563eb;"></i>
                <span>Boas Práticas e Desempenho</span>
            </div>
            <div style="overflow-x: auto;">
                <table class="bp-table">
                    <thead>
                        <tr>
                            <th style="text-align: left;">Descrição da Boa Prática</th>
                            <th style="text-align: center;">Alcance</th>
                            <th style="text-align: center;">Realizados</th>
                            <th style="text-align: center;">Pendentes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows_html)}
                    </tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# 3. GRÁFICOS MODERNOS (Plotly estilizado idêntico ao Chart.js)
# ==============================================================================
hide_sex = current_cond in ("gestantes", "mulher")
chart_cols = st.columns(2 if hide_sex else 3)

plotly_layout_base = dict(
    margin=dict(l=15, r=15, t=10, b=20),
    height=275,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#64748b", size=12),
    showlegend=False,
)

with chart_cols[0]:
    st.markdown(
        """
        <div class="glass-card" style="padding-bottom: 0.5rem;">
            <div class="section-title">
                <i class="fa-solid fa-chart-bar" style="color: #3b82f6;"></i>
                <span>Distribuição por Faixa Etária</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    fig_idade = go.Figure(
        data=[
            go.Bar(
                x=list(stats["faixa_etaria"].keys()),
                y=list(stats["faixa_etaria"].values()),
                marker=dict(
                    color="rgba(59, 130, 246, 0.78)",
                    line=dict(color="rgb(59, 130, 246)", width=1.2),
                ),
                hovertemplate="%{x}: <b>%{y}</b> pacientes<extra></extra>",
            )
        ]
    )
    fig_idade.update_layout(**plotly_layout_base)
    fig_idade.update_yaxes(gridcolor="#e2e8f0", zeroline=False)
    st.plotly_chart(fig_idade, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

if not hide_sex:
    with chart_cols[1]:
        st.markdown(
            """
            <div class="glass-card" style="padding-bottom: 0.5rem;">
                <div class="section-title">
                    <i class="fa-solid fa-venus-mars" style="color: #ec4899;"></i>
                    <span>Distribuição por Sexo</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig_sexo = go.Figure(
            data=[
                go.Pie(
                    labels=["Feminino", "Masculino"],
                    values=[stats["sexo"]["Feminino"], stats["sexo"]["Masculino"]],
                    hole=0.58,
                    marker=dict(
                        colors=["rgba(236, 72, 153, 0.82)", "rgba(59, 130, 246, 0.82)"],
                        line=dict(color="#ffffff", width=2),
                    ),
                    textinfo="percent",
                    hovertemplate="%{label}: <b>%{value}</b> (%{percent})<extra></extra>",
                )
            ]
        )
        fig_sexo.update_layout(
            margin=dict(l=15, r=15, t=10, b=25),
            height=275,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#64748b", size=12),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_sexo, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

with chart_cols[-1]:
    st.markdown(
        """
        <div class="glass-card" style="padding-bottom: 0.5rem;">
            <div class="section-title">
                <i class="fa-solid fa-map-location-dot" style="color: #10b981;"></i>
                <span>Pacientes por Microárea</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    micro_sorted = sorted(stats["microareas"].items(), key=lambda x: x[1], reverse=True)
    fig_micro = go.Figure(
        data=[
            go.Bar(
                x=[m[0] for m in micro_sorted],
                y=[m[1] for m in micro_sorted],
                marker=dict(
                    color="rgba(16, 185, 129, 0.78)",
                    line=dict(color="rgb(16, 185, 129)", width=1.2),
                ),
                hovertemplate="%{x}: <b>%{y}</b> pacientes<extra></extra>",
            )
        ]
    )
    fig_micro.update_layout(**plotly_layout_base)
    fig_micro.update_yaxes(gridcolor="#e2e8f0", zeroline=False)
    fig_micro.update_xaxes(tickangle=-35)
    st.plotly_chart(fig_micro, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# 4. ACOMPANHAMENTO NOMINAL E BUSCA ATIVA
# ==============================================================================
st.markdown(
    """
    <div class="glass-card" style="padding-bottom: 0.75rem;">
        <div class="section-title" style="margin-bottom: 0.5rem;">
            <i class="fa-solid fa-list-check" style="color: #2563eb;"></i>
            <span>Acompanhamento Nominal e Busca Ativa</span>
        </div>
    """,
    unsafe_allow_html=True,
)

tab_options = ["Matriz Geral"] + [
    f"Pendência: {m.get('shortName') or m.get('name')}"
    for m in current_metrics
    if not m.get("hidePendingTab")
]

selected_tab = st.segmented_control(
    "Aba Nominal",
    options=tab_options,
    default="Matriz Geral",
    key=f"nom_tab_{current_cond}",
    label_visibility="collapsed",
)
if not selected_tab:
    selected_tab = "Matriz Geral"

f_col1, f_col2, f_col3 = st.columns([1.2, 1.2, 2])
micros_list = sorted(
    stats["microareas"].keys(),
    key=lambda x: (
        x == "Sem Micro",
        int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 999,
        x,
    ),
)
sel_micro = f_col1.selectbox(
    "Microárea",
    ["Todas as Microáreas"] + micros_list,
    key=f"micro_{current_cond}",
    label_visibility="collapsed",
)
sel_faixa = f_col2.selectbox(
    "Faixa Etária",
    ["Todas as Idades", "0-19 anos", "20-39 anos", "40-59 anos", "60-79 anos", "80+ anos"],
    key=f"faixa_{current_cond}",
    label_visibility="collapsed",
)
search_q = (
    f_col3.text_input(
        "Buscar",
        placeholder="🔍 Buscar paciente, nascimento ou endereço...",
        key=f"search_{current_cond}",
        label_visibility="collapsed",
    )
    .strip()
    .lower()
)

is_geral_tab = selected_tab == "Matriz Geral"
target_metric = None
if not is_geral_tab:
    for m in current_metrics:
        if f"Pendência: {m.get('shortName') or m.get('name')}" == selected_tab:
            target_metric = m
            break

filtered_display = []
filtered_export = []

for p in stats["patients"]:
    if not is_geral_tab and target_metric is not None:
        if p["_metrics"].get(target_metric["id"]):
            continue
    if sel_micro != "Todas as Microáreas" and p["Microárea"] != sel_micro:
        continue
    if sel_faixa != "Todas as Idades" and p["_faixa"] != sel_faixa:
        continue
    if search_q and not (
        search_q in p["Nome do(a) Paciente"].lower()
        or search_q in p["Nascimento"].lower()
        or search_q in p["Endereço"].lower()
    ):
        continue

    base_row = {
        "Nome do(a) Paciente": p["Nome do(a) Paciente"],
        "Nascimento": p["Nascimento"],
        "Idade": p["Idade"],
        "Endereço": p["Endereço"],
        "Microárea": p["Microárea"],
    }
    row_disp = dict(base_row)
    row_exp = dict(base_row)

    if is_geral_tab:
        for m in current_metrics:
            col_label = m.get("shortName") or m.get("name")
            ok = p["_metrics"].get(m["id"], False)
            row_disp[col_label] = "✅ Atingido" if ok else "❌ Pendente"
            row_exp[col_label] = "ATINGIDO" if ok else "PENDENTE"
    else:
        row_disp["Status"] = "🔴 Pendente"
        row_exp["Status"] = "PENDENTE"

    filtered_display.append(row_disp)
    filtered_export.append(row_exp)

df_display = pd.DataFrame(filtered_display)
df_export = pd.DataFrame(filtered_export)

info_col, btn_csv_col, btn_xlsx_col = st.columns([3.5, 1, 1])

if is_geral_tab:
    info_col.markdown(
        f"<p style='font-size: 0.88rem; color: #64748b; font-weight: 600; margin-top: 0.45rem;'>"
        f"<i class='fa-solid fa-users' style='color: #3b82f6;'></i> Exibindo <strong style='color: #1e293b;'>{len(df_display)}</strong> de {total_patients} pacientes na Matriz Geral.</p>",
        unsafe_allow_html=True,
    )
else:
    m_title = target_metric.get("shortName") or target_metric.get("name") if target_metric else ""
    info_col.markdown(
        f"<p style='font-size: 0.88rem; color: #64748b; font-weight: 600; margin-top: 0.45rem;'>"
        f"<i class='fa-solid fa-triangle-exclamation' style='color: #f43f5e;'></i> Exibindo <strong style='color: #1e293b;'>{len(df_display)}</strong> pacientes com pendência em <strong style='color: #1e293b;'>{m_title}</strong>.</p>",
        unsafe_allow_html=True,
    )

pendencia_suffix = f"Pendencia_{target_metric['id']}" if target_metric else "Pendencia"
base_filename = (
    f"Acompanhamento_{re.sub(r'[^a-zA-Z0-9]', '_', cond_cfg['full_label'])}_"
    f"{'Matriz_Geral' if is_geral_tab else pendencia_suffix}"
)

btn_csv_col.download_button(
    "📄 Exportar CSV",
    data=df_export.to_csv(index=False, sep=";").encode("utf-8-sig"),
    file_name=f"{base_filename}.csv",
    mime="text/csv",
    use_container_width=True,
)
btn_xlsx_col.download_button(
    "📊 Exportar XLSX",
    data=to_excel_bytes(df_export),
    file_name=f"{base_filename}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

if df_display.empty:
    st.info("Nenhum paciente encontrado com estes filtros.")
else:
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=460,
        column_config={
            "Nome do(a) Paciente": st.column_config.TextColumn(pinned=True, width="medium"),
        },
    )

st.markdown("</div>", unsafe_allow_html=True)

# Footer igual ao original
st.markdown(
    """
    <div class="esus-footer">
        Gerado a partir dos dados do e-SUS PEC • by @argsite
    </div>
    """,
    unsafe_allow_html=True,
)
