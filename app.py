import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Painel de Saúde - e-SUS",
    page_icon="🩺",
    layout="wide"
)

# Estilo CSS personalizado para embelezar os cards e métricas
st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(uploaded_file):
    # O e-SUS utiliza codificação latin1/ISO-8859-1 e cabeçalho na linha 25 (skiprows=24)
    try:
        df = pd.read_csv(uploaded_file, skiprows=24, sep=';', encoding='latin1')
        # Limpar colunas vazias ou nulas se houver
        df = df.dropna(how='all', axis=1)
        return df
    except Exception as e:
        st.error(f"Erro ao ler o ficheiro: {e}")
        return None

# Título Principal
st.title("🩺 Painel de Acompanhamento de Condições de Saúde")
st.markdown("Visualização interativa de dados do **e-SUS (Atenção Primária)** para apoio à Equipe de Saúde.")

# Barra lateral para upload do ficheiro ou uso do padrão
st.sidebar.header("📁 Dados do Relatório")
uploaded_file = st.sidebar.file_uploader("Carregue o relatório CSV do e-SUS", type=["csv"])

# Se nenhum ficheiro for carregado, tenta carregar o ficheiro padrão local se existir na pasta
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
    microareas = sorted(df['Microárea'].dropna().astype(str).unique().tolist())
    selected_microarea = st.sidebar.selectbox("Microárea", ["Todas"] + microareas)
    
    # Filtro por Situação de Consulta (Em dia vs Atrasadas > 180 dias)
    df['Dias_Consulta'] = pd.to_numeric(df['Dias desde o último atendimento médico'], errors='coerce').fillna(0)
    status_consulta = st.sidebar.radio("Situação da Consulta Médica", ["Todos", "Em dia (<= 6 meses)", "Atrasadas (> 6 meses)"])
    
    # Aplicar Filtros
    df_filtered = df.copy()
    if selected_microarea != "Todas":
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
    col2.metric("Microáreas Atendidas", len(df_filtered['Microárea'].unique()))
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
            
            # Gráfico de barras corrigido e otimizado
            fig_ma = px.bar(
                ma_counts, 
                x='Microárea', 
                y='Total', 
                text='Total',
                color='Microárea'
            )
            fig_ma.update_traces(textposition='outside')
            fig_ma.update_layout(
                xaxis_title="Microárea", 
                yaxis_title="Nº de Pacientes", 
                showlegend=False
            )
            st.plotly_chart(fig_ma, use_container_width=True)

    with col_g2:
        st.subheader("⚖️ Distribuição por Sexo e Faixa Etária")
        if 'Sexo' in df_filtered.columns:
            sexo_counts = df_filtered['Sexo'].value_counts().reset_index()
            sexo_counts.columns = ['Sexo', 'Total']
            fig_sexo = px.pie(sexo_counts, names='Sexo', values='Total', hole=0.4, 
                              color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_sexo, use_container_width=True)

    st.markdown("---")

    # --- TABELA DETALHADA PARA A EQUIPE DE SAÚDE ---
    st.subheader("📋 Lista Detalhada de Acompanhamento")
    
    # Selecionar colunas mais relevantes para exibição rápida
    colunas_exibir = [
        'Nome', 'Idade', 'Microárea', 'Telefone celular', 
        'Última medição de pressão arterial', 'Hemoglobina glicada', 
        'Dias desde o último atendimento médico'
    ]
    
    # Garantir que as colunas existem no dataframe
    colunas_disponiveis = [c for c in colunas_exibir if c in df_filtered.columns]

    # Campo de busca por nome
    search_query = st.text_input("🔍 Pesquisar paciente por nome:", "")
    if search_query:
        df_filtered = df_filtered[df_filtered['Nome'].str.contains(search_query, case=False, na=False)]

    st.dataframe(df_filtered[colunas_disponiveis], use_container_width=True, hide_index=True)

    # --- BOTÃO DE EXPORTAÇÃO DE RELATÓRIO FILTRADO ---
    csv_export = df_filtered.to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(
        label="📥 Descarregar Relatório Filtrado (CSV)",
        data=csv_export,
        file_name="relatorio_saude_filtrado.csv",
        mime="text/csv"
    )

else:
    st.warning("⚠️ Por favor, carregue um ficheiro CSV do e-SUS válido para iniciar o painel.")
