import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# --- FUNÇÕES DE FORMATAÇÃO ---
def float_para_real_texto(valor):
    if pd.isna(valor): valor = 0
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")

def texto_para_float(texto):
    if isinstance(texto, (int, float)): return float(texto)
    limpo = str(texto).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return 0.0

def formatar_moeda_visual(valor):
    return f"R$ {float_para_real_texto(valor)}"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestor Financeiro", layout="wide", page_icon="💰")

# Esconder menu padrão do Streamlit
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("💰 Gestor Financeiro Pessoal")

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Dados_App", usecols=list(range(13)), ttl=5)
    if "Categoria" in df.columns:
        df["Categoria"] = df["Categoria"].astype(str).str.strip()
    df = df.fillna(0)
except Exception as e:
    st.error(f"Erro ao ler planilha: {e}")
    st.stop()

# --- PREPARAÇÃO GERAL ---
meses_disponiveis = df.columns[1:].tolist()
categorias_entrada_padrao = ["Salário", "Reembolso", "Bônus e PLR", "Receita de Aluguel", "Renda - Outra", "Ajuda de Custo (Mãe)"]

mask_entrada_global = df["Categoria"].isin(categorias_entrada_padrao)
# Expressão regular para achar investimentos pelo nome
mask_invest_global = df["Categoria"].str.contains("Investimento|Aplicação|CDB|CDI|Poupança|Fundo|Ações", case=False, na=False)

# --- MENU LATERAL ---
st.sidebar.header("Navegação")
pagina = st.sidebar.radio("Ir para:", ["📅 Lançamentos e Edição", "📈 Comparativo e Evolução"])

# ==============================================================================
# PÁGINA 1: LANÇAMENTOS (EDIÇÃO)
# ==============================================================================
if pagina == "📅 Lançamentos e Edição":
    
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", meses_disponiveis)
    st.subheader(f"📝 Lançamentos de {mes_selecionado}")

    df_entradas = df[mask_entrada_global].copy().sort_values(by="Categoria")
    df_saidas = df[~mask_entrada_global].copy().sort_values(by="Categoria")

    df_entradas["Valor_Visual"] = df_entradas[mes_selecionado].apply(float_para_real_texto)
    df_saidas["Valor_Visual"] = df_saidas[mes_selecionado].apply(float_para_real_texto)

    aba_entradas, aba_saidas = st.tabs(["🟢 Ganhos (Entradas)", "🔴 Contas e Investimentos"])

    with aba_entradas:
        df_entradas_editado = st.data_editor(
            df_entradas[["Categoria", "Valor_Visual"]],
            column_config={"Categoria": "Descrição", "Valor_Visual": "Valor (R$)"},
            use_container_width=True, num_rows="dynamic", key="editor_entradas"
        )

    with aba_saidas:
        st.info("💡 Para Investimentos, coloque o **Valor Total Acumulado** que você tem lá no banco.")
        df_saidas_editado = st.data_editor(
            df_saidas[["Categoria", "Valor_Visual"]],
            column_config={"Categoria": "Descrição", "Valor_Visual": "Valor (R$)"},
            use_container_width=True, num_rows="dynamic", key="editor_saidas"
        )

    st.divider()
    if st.button("💾 Salvar Alterações", type="primary"):
        try:
            df_entradas_editado[mes_selecionado] = df_entradas_editado["Valor_Visual"].apply(texto_para_float)
            df_saidas_editado[mes_selecionado] = df_saidas_editado["Valor_Visual"].apply(texto_para_float)
            
            # Recria a base completa mantendo dados dos outros meses
            cols_reais = ["Categoria", mes_selecionado]
            df_final_mes = pd.concat([df_entradas_editado[cols_reais], df_saidas_editado[cols_reais]], ignore_index=True)
            
            # Lógica para preservar outros meses
            todas_categorias = df_final_mes["Categoria"].unique()
            df_save = pd.DataFrame({"Categoria": todas_categorias})
            
            for mes in meses_disponiveis:
                if mes == mes_selecionado:
                    df_save = df_save.merge(df_final_mes, on="Categoria", how="left")
                else:
                    df_temp = df[["Categoria", mes]]
                    df_save = df_save.merge(df_temp, on="Categoria", how="left")
            
            df_save = df_save.fillna(0).sort_values(by="Categoria")
            conn.update(worksheet="Dados_App", data=df_save)
            st.success("✅ Salvo com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    # Cálculos
    total_entradas = df_entradas[mes_selecionado].sum()
    total_investido = df_saidas[mask_invest_global][mes_selecionado].sum()
    total_gastos_reais = df_saidas[~mask_invest_global][mes_selecionado].sum()
    saldo = total_entradas - total_gastos_reais

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📥 Ganhos", formatar_moeda_visual(total_entradas))
    c2.metric("💸 Gastos Reais", formatar_moeda_visual(total_gastos_reais), delta_color="inverse")
    c3.metric("🏦 Patrimônio Total", formatar_moeda_visual(total_investido), help="Total acumulado em investimentos")
    c4.metric("💰 Sobra de Caixa", formatar_moeda_visual(saldo), delta=formatar_moeda_visual(saldo))
    
    # Gráficos Mês
    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Despesas do Mês**")
        df_pizza = df_saidas[~mask_invest_global].copy()
        df_pizza = df_pizza[df_pizza[mes_selecionado] > 0]
        if not df_pizza.empty:
            fig = px.pie(df_pizza, values=mes_selecionado, names='Categoria', hole=0.5)
            fig.update_traces(texttemplate='%{percent:.1%}', hovertemplate='<b>%{label}</b><br>%{value:,.2f}')
            st.plotly_chart(fig, use_container_width=True)
            
    with col_g2:
        st.markdown("**Resumo**")
        fig_bar = px.bar(
            pd.DataFrame({"Tipo": ["Ganhos", "Gastos"], "Valor": [total_entradas, total_gastos_reais]}),
            x="Tipo", y="Valor", color="Tipo", text_auto='.2s', color_discrete_map={"Ganhos": "#2ECC71", "Gastos": "#E74C3C"}
        )
        fig_bar.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.")
        st.plotly_chart(fig_bar, use_container_width=True)


# ==============================================================================
# PÁGINA 2: EVOLUÇÃO (A NOVIDADE)
# ==============================================================================
elif pagina == "📈 Comparativo e Evolução":
    
    st.header("📈 Evolução do seu Dinheiro")
    
    # --- PROCESSAMENTO DOS DADOS ANUAIS ---
    historico = []
    
    # Variável para calcular o crescimento (Valor Mês Atual - Valor Mês Anterior)
    investimento_anterior = 0 
    
    for mes in meses_disponiveis:
        total_investido_mes = df[mask_invest_global][mes].sum()
        total_entradas_mes = df[mask_entrada_global][mes].sum()
        total_gastos_mes = df[~mask_entrada_global & ~mask_invest_global][mes].sum()
        
        # O quanto aumentou em relação ao mês anterior (Aporte + Rentabilidade)
        variacao_investimento = total_investido_mes - investimento_anterior
        if investimento_anterior == 0: variacao_investimento = 0 # Ignora o primeiro mês
        
        investimento_anterior = total_investido_mes
        
        historico.append({
            "Mês": mes,
            "Total Investido": total_investido_mes,
            "Aumento Mensal": variacao_investimento,
            "Sobra de Caixa": total_entradas_mes - total_gastos_mes
        })
    
    df_hist = pd.DataFrame(historico)
    
    # --- SEÇÃO 1: PATRIMÔNIO (INVESTIMENTOS) ---
    st.markdown("### 🏦 Seu Fundo de Investimento")
    st.info("Este gráfico mostra o valor total acumulado e quanto ele aumentou mês a mês.")
    
    # GRÁFICO DE ÁREA (PATRIMÔNIO ACUMULADO)
    fig_area = px.area(
        df_hist, x="Mês", y="Total Investido", 
        markers=True,
        title="Crescimento do Patrimônio Total"
    )
    # Deixar a linha verde bonita e preenchida
    fig_area.update_traces(line_color="#27AE60", fillcolor="rgba(46, 204, 113, 0.3)")
    fig_area.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.")
    
    # Adicionando tooltip personalizado
    fig_area.update_traces(hovertemplate='<b>%{x}</b><br>Total: R$ %{y:,.2f}')
    st.plotly_chart(fig_area, use_container_width=True)
    
    # GRÁFICO DE BARRAS (VARIAÇÃO MENSAL)
    st.markdown("#### 🚀 Quanto aumentou por mês (Aporte + Rendimento)?")
    
    # Remove meses com zero para o gráfico de barras não ficar poluído
    df_variacao = df_hist[df_hist["Aumento Mensal"] != 0]
    
    fig_var = px.bar(
        df_variacao, x="Mês", y="Aumento Mensal",
        text_auto='.2s',
        color="Aumento Mensal",
        color_continuous_scale="Blugrn" # Escala de cor Azul-Verde
    )
    fig_var.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.")
    fig_var.update_traces(texttemplate='R$ %{y:,.0f}', textposition='outside')
    st.plotly_chart(fig_var, use_container_width=True)

    # --- SEÇÃO 2: FLUXO DE CAIXA ---
    st.divider()
    st.markdown("### 🔵 Fluxo de Caixa (Sobras mensais)")
    
    fig_sobras = px.line(df_hist, x="Mês", y="Sobra de Caixa", markers=True)
    fig_sobras.update_traces(line_color="#2980B9", texttemplate='R$ %{y:,.0f}', textposition="top center")
    fig_sobras.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.")
    st.plotly_chart(fig_sobras, use_container_width=True)