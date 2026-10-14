import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Painel de Saúde - e-SUS (Completo)",
    page_icon="🩺",
    layout="wide"
)

# Estilo CSS personalizado
st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, skiprows=24, sep=';', encoding='latin1')
        df = df.dropna(how='all', axis=1)
        # Remover coluna vazia 'Unnamed: 43' se existir
        if 'Unnamed: 43' in df.columns:
            df = df.drop(columns=['Unnamed: 43'])
        return df
    except Exception as e:
        st.error(f"Erro ao ler o ficheiro: {e}")
        return None

# Título Principal
st.title("🩺 Painel Completo de Acompanhamento - e-SUS")
st.markdown("Visualização e gestão integral dos dados do relatório de saúde da equipa.")

# Barra lateral para upload do ficheiro ou uso do padrão
st.sidebar.header("📁 Dados do Relatório")
uploaded_file = st.sidebar.file_uploader("Carregue o relatório CSV do e-SUS", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    try:
        df = load_data('acompanhamento-condicao-saude_2026-10-14-11-39.csv')
        st.sidebar.success("📂 A usar o ficheiro predefinido na pasta!")
    except:
        df = None

if df is not None:
    # --- FILTROS NA BARRA LATERAL ---
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros Operacionais")
    
    # Filtro por Microárea
    microareas = sorted(df['Microárea'].dropna().astype(str).unique().tolist()) if 'Microárea' in df.columns else []
    selected_microarea = st.sidebar.selectbox("Microárea", ["Todas"] + microareas)
    
    # Filtro por Situação de Consulta
    if 'Dias desde o último atendimento médico' in df.columns:
        df['Dias_Consulta'] = pd.to_numeric(df['Dias desde o último atendimento médico'], errors='coerce').fillna(0)
    else:
        df['Dias_Consulta'] = 0

    status_consulta = st.sidebar.radio("Situação da Consulta Médica", ["Todos", "Em dia (<= 6 meses)", "Atrasadas (> 6 meses)"])
    
    # Aplicar Filtros
    df_filtered = df.copy()
    if selected_microarea != "Todas" and 'Microárea' in df.columns:
        df_filtered = df_filtered[df_filtered['Microárea'].astype(str) == selected_microarea]
    
    if status_consulta == "Em dia (<= 6 meses)":
        df_filtered = df_filtered[df_filtered['Dias_Consulta'] <= 180]
    elif status_consulta == "Atrasadas (> 6 meses)":
        df_filtered = df_filtered[df_filtered['Dias_Consulta'] > 180]

    # --- INDICADORES PRINCIPAIS (KPIs) ---
    total_pacientes = len(df_filtered)
    atrasadas_count = len(df_filtered[df_filtered['Dias_Consulta'] > 180])
    em_dia_count = total_pacientes - atrasadas_count
    pct_em_dia = (em_dia_count / total_pacientes * 100) if total_pacientes > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Pacientes", total_pacientes)
    col2.metric("Microáreas Atendidas", len(df_filtered['Microárea'].unique()) if 'Microárea' in df.columns else 0)
    col3.metric("Consultas em Dia", f"{em_dia_count} ({pct_em_dia:.1f}%)")
    col4.metric("Consultas Atrasadas (>6m)", atrasadas_count, delta=f"-{atrasadas_count}" if atrasadas_count > 0 else "0", delta_color="inverse")

    st.markdown("---")

    # --- GRÁFICOS ANALÍTICOS (PLOTLY) ---
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📊 Pacientes por Microárea")
        if 'Microárea' in df_filtered.columns:
            ma_counts = df_filtered['Microárea'].astype(str).value_counts().reset_index()
            ma_counts.columns = ['Microárea', 'Total']
            fig_ma = px.bar(
                ma_counts, x='Microárea', y='Total', text='Total', color='Microárea'
            )
            fig_ma.update_traces(textposition='outside')
            fig_ma.update_layout(xaxis_title="Microárea", yaxis_title="Nº de Pacientes", showlegend=False)
            st.plotly_chart(fig_ma, use_container_width=True)

    with col_g2:
        st.subheader("⚖️ Distribuição por Sexo")
        if 'Sexo' in df_filtered.columns:
            sexo_counts = df_filtered['Sexo'].value_counts().reset_index()
            sexo_counts.columns = ['Sexo', 'Total']
            fig_sexo = px.pie(sexo_counts, names='Sexo', values='Total', hole=0.4, 
                              color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_sexo, use_container_width=True)

    st.markdown("---")

    # --- TABELA DETALHADA COM TODAS AS COLUNAS ---
    st.subheader("📋 Relatório Completo de Pacientes")
    
    # Campo de busca por nome
    search_query = st.text_input("🔍 Pesquisar paciente por nome ou CPF:", "")
    if search_query:
        if 'Nome' in df_filtered.columns and 'CPF' in df_filtered.columns:
            df_filtered = df_filtered[
                df_filtered['Nome'].str.contains(search_query, case=False, na=False) | 
                df_filtered['CPF'].str.contains(search_query, case=False, na=False)
            ]

    # Opção para escolher colunas
    todas_colunas = list(df.columns)
    # Remover colunas auxiliares criadas internamente
    if 'Dias_Consulta' in todas_colunas:
        todas_colunas.remove('Dias_Consulta')

    modo_visualizacao = st.radio("Modo de Exibição da Tabela:", ["Resumo Essencial", "Ver Todas as 43 Colunas"])

    if modo_visualizacao == "Ver Todas as 43 Colunas":
        colunas_selecionadas = todas_colunas
    else:
        # Colunas padrão recomendadas para visão rápida
        colunas_selecionadas = [c for c in [
            'Nome', 'Data de nascimento', 'Idade', 'Sexo', 'Microárea', 
            'Telefone celular', 'Última medição de pressão arterial', 
            'Hemoglobina glicada', 'Dias desde o último atendimento médico'
        ] if c in todas_colunas]

    st.dataframe(df_filtered[colunas_selecionadas], use_container_width=True, hide_index=True)

    # --- BOTÃO DE EXPORTAÇÃO ---
    st.markdown("---")
    csv_export = df_filtered[todas_colunas].to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(
        label="📥 Descarregar Relatório Completo Filtrado (CSV)",
        data=csv_export,
        file_name="relatorio_saude_completo_filtrado.csv",
        mime="text/csv"
    )

else:
    st.warning("⚠️ Por favor, carregue um ficheiro CSV do e-SUS válido para iniciar o painel.")
