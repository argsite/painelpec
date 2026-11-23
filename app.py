from datetime import datetime
import io
import re
import unicodedata
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Painel de Monitoramento e-SUS APS",
    page_icon="🩺",
    layout="wide",
)

CONDITIONS = {
    "geral": {
        "label": "Geral - Todos os Pacientes",
        "file": "acompanhamento-condicao-saude_2026-11-13-13-26.csv",
        "metrics": [
            {
                "id": "consulta",
                "shortName": "Consulta (12m)",
                "bpDesc": "Ter pelo menos 01 (uma) consulta presencial ou remota nos últimos 12 meses.",
                "points": 25,
                "name": "Consultas Recentes",
                "forceCol": 21,
                "maxDays": 365,
            },
            {
                "id": "visita",
                "shortName": "Visita ACS (12m)",
                "bpDesc": "Ter pelo menos 01 (uma) visita domiciliar por ACS/TACS nos últimos 12 meses.",
                "points": 25,
                "name": "Visitas ACS",
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
                "searches": ["vacina", "imuniza", "polio", "penta"],
            },
        ],
    },
    "gestantes": {
        "label": "C3 - Gestantes e Puérperas",
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
                "searches": ["odonto", "odontologico", "odontológico"],
            },
        ],
    },
    "diabeticos": {
        "label": "C4 - Diabéticos",
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
                "searches": ["hemoglobina", "glicada", "hba1c"],
            },
            {
                "id": "pes",
                "shortName": "Avaliação Pés",
                "bpDesc": "Ter pelo menos 01 (uma) avaliação dos pés realizada nos últimos 12 (doze) meses.",
                "points": 15,
                "name": "Avaliação Pés",
                "searches": ["pe", "pes"],
                "exclude": "peso",
                "forceCol": 39,
            },
        ],
    },
    "hipertensos": {
        "label": "C5 - Hipertensos",
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
                "searches": ["vacina", "influenza", "imuniza"],
            },
        ],
    },
    "mulher": {
        "label": "C7 - Saúde da Mulher",
        "file": "acompanhamento-condicao-saude_2026-11-05-08-47.csv",
        "metrics": [
            {
                "id": "cito",
                "shortName": "Preventivo (36m)",
                "bpDesc": "Ter pelo menos 01 (um) exame de rastreamento para câncer do colo do útero em mulheres e homens transgênero de 25 a 64 anos nos últimos 36 meses.",
                "points": 20,
                "name": "Citopatológico",
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
                "searches": ["mama", "mamografia"],
                "maxDays": 730,
            },
        ],
    },
}


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
    import csv
    reader = csv.reader(lines, delimiter=delimiter)
    return list(reader)


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
            diff_days = abs((ref - dt).days)
            return diff_days <= max_days
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
            "Paciente": nome,
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


st.title("🩺 Painel de Monitoramento e-SUS APS")

cond_keys = list(CONDITIONS.keys())
cond_labels = [CONDITIONS[k]["label"] for k in cond_keys]

selected_idx = st.segmented_control(
    "Linha de Cuidado / Indicador",
    options=list(range(len(cond_keys))),
    format_func=lambda i: cond_labels[i],
    default=0,
)
current_cond = cond_keys[selected_idx if selected_idx is not None else 0]
cond_cfg = CONDITIONS[current_cond]

uploaded_file = st.file_uploader(
    f"Importar CSV ({cond_cfg['file']})",
    type=["csv"],
    key=f"uploader_{current_cond}",
)

csv_text = None
if uploaded_file is not None:
    csv_text = decode_csv_bytes(uploaded_file.getvalue())
else:
    try:
        with open(cond_cfg["file"], "rb") as f:
            csv_text = decode_csv_bytes(f.read())
    except FileNotFoundError:
        st.warning(f"Arquivo local `{cond_cfg['file']}` não encontrado. Faça o upload do CSV acima para analisar.")
        st.stop()

stats = analyze_condition_data(csv_text, current_cond)
if not stats or stats["total"] == 0:
    st.error("Não foi possível identificar cabeçalhos ou registros válidos no arquivo selecionado.")
    st.stop()

current_metrics = cond_cfg["metrics"]
total_patients = stats["total"]

# KPIs
kpi_cols = st.columns(4)
kpi_cols[0].metric("Total de Pacientes", total_patients)

if current_cond != "geral":
    total_pts = sum(
        m.get("points", 0)
        for p in stats["patients"]
        for m in current_metrics
        if p["_metrics"].get(m["id"])
    )
    final_score = round(total_pts / total_patients, 1) if total_patients > 0 else 0.0
    if final_score > 75:
        param = "Ótimo"
    elif final_score > 50:
        param = "Bom"
    elif final_score > 25:
        param = "Suficiente"
    else:
        param = "Regular"
    kpi_cols[1].metric("Score do Indicador", f"{final_score}", delta=param)

visible_metrics = [m for m in current_metrics if not m.get("hidden")]
col_cursor = 2 if current_cond != "geral" else 1
for m in visible_metrics:
    cnt = stats["metric_counts"].get(m["id"], 0)
    pct = round((cnt / total_patients) * 100) if total_patients > 0 else 0
    kpi_cols[col_cursor % 4].metric(m.get("name", m["shortName"]), f"{cnt} ({pct}%)")
    col_cursor += 1

# Boas Práticas
if current_cond != "geral":
    st.subheader("Boas Práticas e Desempenho")
    bp_rows = []
    for m in current_metrics:
        cnt = stats["metric_counts"].get(m["id"], 0)
        pct = round((cnt / total_patients) * 100) if total_patients > 0 else 0
        bp_rows.append({
            "Boa Prática": f"{m.get('shortName') or m.get('name')} ({m.get('points', 0)} pts)",
            "Descrição": m["bpDesc"],
            "Alcance": f"{pct}%",
            "Realizados": cnt,
            "Pendentes": total_patients - cnt,
        })
    st.dataframe(pd.DataFrame(bp_rows), use_container_width=True, hide_index=True)

# Gráficos
st.subheader("Distribuições")
hide_sex = current_cond in ("gestantes", "mulher")
chart_cols = st.columns(2 if hide_sex else 3)

with chart_cols[0]:
    st.caption("Faixa Etária")
    df_faixa = pd.DataFrame(list(stats["faixa_etaria"].items()), columns=["Faixa Etária", "Pacientes"])
    st.bar_chart(df_faixa.set_index("Faixa Etária"), height=260)

if not hide_sex:
    with chart_cols[1]:
        st.caption("Sexo")
        df_sexo = pd.DataFrame(list(stats["sexo"].items()), columns=["Sexo", "Pacientes"])
        st.bar_chart(df_sexo.set_index("Sexo"), height=260)

with chart_cols[-1]:
    st.caption("Pacientes por Microárea")
    micro_sorted = sorted(stats["microareas"].items(), key=lambda x: x[1], reverse=True)
    df_micro = pd.DataFrame(micro_sorted, columns=["Microárea", "Pacientes"])
    st.bar_chart(df_micro.set_index("Microárea"), height=260)

# Acompanhamento Nominal e Busca Ativa
st.subheader("Acompanhamento Nominal e Busca Ativa")

tab_options = ["Matriz Geral"] + [f"Pendência: {m.get('shortName') or m.get('name')}" for m in current_metrics if not m.get("hidePendingTab")]
selected_tab = st.selectbox("Visualização", options=tab_options, key=f"view_{current_cond}")

f_col1, f_col2, f_col3 = st.columns(3)
micros_list = sorted(
    stats["microareas"].keys(),
    key=lambda x: (x == "Sem Micro", int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 999, x),
)
sel_micro = f_col1.selectbox("Microárea", ["Todas"] + micros_list, key=f"micro_{current_cond}")
sel_faixa = f_col2.selectbox(
    "Faixa Etária",
    ["Todas", "0-19 anos", "20-39 anos", "40-59 anos", "60-79 anos", "80+ anos"],
    key=f"faixa_{current_cond}",
)
search_q = f_col3.text_input("Buscar paciente, nascimento ou endereço", key=f"search_{current_cond}").strip().lower()

is_geral_tab = selected_tab == "Matriz Geral"
target_metric = None
if not is_geral_tab:
    for m in current_metrics:
        label_m = f"Pendência: {m.get('shortName') or m.get('name')}"
        if label_m == selected_tab:
            target_metric = m
            break

filtered_rows = []
for p in stats["patients"]:
    if not is_geral_tab and target_metric is not None:
        if p["_metrics"].get(target_metric["id"]):
            continue
    if sel_micro != "Todas" and p["Microárea"] != sel_micro:
        continue
    if sel_faixa != "Todas" and p["_faixa"] != sel_faixa:
        continue
    if search_q and not (
        search_q in p["Paciente"].lower()
        or search_q in p["Nascimento"].lower()
        or search_q in p["Endereço"].lower()
    ):
        continue

    row_dict = {
        "Paciente": p["Paciente"],
        "Nascimento": p["Nascimento"],
        "Idade": p["Idade"],
        "Endereço": p["Endereço"],
        "Microárea": p["Microárea"],
    }
    if is_geral_tab:
        for m in current_metrics:
            col_label = m.get("shortName") or m.get("name")
            row_dict[col_label] = "ATINGIDO" if p["_metrics"].get(m["id"]) else "PENDENTE"
    else:
        row_dict["Status"] = "PENDENTE"
    filtered_rows.append(row_dict)

df_nominal = pd.DataFrame(filtered_rows)
st.caption(f"Exibindo **{len(df_nominal)}** registro(s).")
st.dataframe(df_nominal, use_container_width=True, hide_index=True, height=420)

# Exportação CSV e XLSX
exp_col1, exp_col2 = st.columns(2)
base_filename = f"Acompanhamento_{re.sub(r'[^a-zA-Z0-9]', '_', cond_cfg['label'])}_{'Matriz_Geral' if is_geral_tab else 'Pendencia'}"

csv_out = df_nominal.to_csv(index=False, sep=";").encode("utf-8-sig")
exp_col1.download_button(
    "⬇️ Exportar CSV",
    data=csv_out,
    file_name=f"{base_filename}.csv",
    mime="text/csv",
)

xlsx_out = to_excel_bytes(df_nominal)
exp_col2.download_button(
    "⬇️ Exportar XLSX",
    data=xlsx_out,
    file_name=f"{base_filename}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
