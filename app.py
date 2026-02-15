import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz

# --- FUNÇÕES DE FORMATAÇÃO ---
def float_para_real_texto(valor):
    if pd.isna(valor): valor = 0
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_moeda_visual(valor):
    return f"R$ {float_para_real_texto(valor)}"

def hora_atual_brasilia():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_br)
    return agora.strftime("%d/%m/%Y às %H:%M")

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestor Financeiro", layout="wide", page_icon="💰")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("💰 Gestor Financeiro Pessoal - Gilmar")

# --- MENU LATERAL ---
st.sidebar.header("Navegação")
pagina = st.sidebar.radio("Ir para:", ["📅 Lançamentos e Edição", "📈 Comparativo e Evolução"])

st.sidebar.divider()
st.sidebar.caption(f"🔄 Dados de: {hora_atual_brasilia()}")

# --- CONEXÃO ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)

    # 1. Lê os DADOS (Essencial)
    df = conn.read(worksheet="Dados_App", usecols=list(range(13)), ttl=0)
    if "Categoria" in df.columns:
        df["Categoria"] = df["Categoria"].astype(str).str.strip()
    meses_disponiveis = df.columns[1:].tolist()
    if meses_disponiveis:
        df[meses_disponiveis] = df[meses_disponiveis].apply(pd.to_numeric, errors="coerce").fillna(0)

    # 2. Lê a CONFIGURAÇÃO (Opcional - Protegido contra erro)
    ultimo_mes_salvo = None
    categorias_entrada_custom = []
    categorias_invest_custom = []
    try:
        df_config = conn.read(worksheet="Config", ttl=0)
        if not df_config.empty:
            cfg = df_config.iloc[0]

            if "Ultimo_Mes" in df_config.columns:
                ultimo_mes_salvo = cfg.get("Ultimo_Mes")
            else:
                ultimo_mes_salvo = df_config.iloc[0, 0]

            if "Categorias_Entrada_Custom" in df_config.columns:
                categorias_entrada_custom = [
                    cat.strip() for cat in str(df_config.loc[0, "Categorias_Entrada_Custom"]).split("|")
                    if cat and cat.strip() and cat.strip().lower() != "nan"
                ]
            if "Categorias_Invest_Custom" in df_config.columns:
                categorias_invest_custom = [
                    cat.strip() for cat in str(df_config.loc[0, "Categorias_Invest_Custom"]).split("|")
                    if cat and cat.strip() and cat.strip().lower() != "nan"
                ]
    except Exception:
        # Se der erro aqui (aba não existe), vida que segue
        pass

    # --- PREPARAÇÃO GERAL ---
    categorias_entrada_padrao = ["Salário", "Reembolso", "Bônus e PLR", "Receita de Aluguel", "Renda - Outra", "Ajuda de Custo (Mãe)"]

    categorias_entrada = categorias_entrada_padrao + categorias_entrada_custom
    mask_entrada_global = df["Categoria"].isin(categorias_entrada)
    mask_invest_global = (
        df["Categoria"].str.contains("Investimento|Aplicação|CDB|CDI|Poupança|Fundo|Ações", case=False, na=False)
        | df["Categoria"].isin(categorias_invest_custom)
    )

except Exception as e:
    st.error(f"Erro crítico ao conectar ou ler planilha: {e}")
    st.info("💡 **Dica para deploy no Streamlit Cloud:** As credenciais do Google Sheets devem ser configuradas nas 'Secrets' do app no painel do Streamlit Cloud, não no arquivo .streamlit/secrets.toml.")
    df = None
    ultimo_mes_salvo = None
    categorias_entrada_custom = []
    categorias_invest_custom = []
    meses_disponiveis = []
    mask_entrada_global = None
    mask_invest_global = None
    conn = None

def conexao_valida(df_dados, mask_entrada, mask_invest):
    return (
        isinstance(df_dados, pd.DataFrame)
        and isinstance(mask_entrada, pd.Series)
        and isinstance(mask_invest, pd.Series)
        and len(mask_entrada) == len(df_dados)
        and len(mask_invest) == len(df_dados)
    )

if not conexao_valida(df, mask_entrada_global, mask_invest_global):
    st.warning("⚠️ Conexão com Google Sheets não estabelecida. Configure as credenciais corretamente para acessar os dados.")
    st.stop()

# ==============================================================================
# PÁGINA 1: LANÇAMENTOS
# ==============================================================================
if pagina == "📅 Lançamentos e Edição":
    if df is None or mask_entrada_global is None or mask_invest_global is None:
        st.warning("⚠️ Conexão com Google Sheets não estabelecida. Configure as credenciais corretamente para acessar os dados.")
        st.stop()
    
    # Tenta usar o último mês salvo, se não, usa o primeiro
    indice_padrao = 0 
    if not meses_disponiveis:
        st.warning("⚠️ Nenhum mês encontrado na planilha. Verifique as colunas de dados.")
        st.stop()

    if ultimo_mes_salvo in meses_disponiveis:
        indice_padrao = meses_disponiveis.index(ultimo_mes_salvo)
    
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", meses_disponiveis, index=indice_padrao)
    
    st.subheader(f"📝 Lançamentos de {mes_selecionado}")

    df_entradas = df[mask_entrada_global].copy()
    df_investimentos = df[mask_invest_global].copy()
    df_gastos = df[~mask_entrada_global & ~mask_invest_global].copy()

    df_entradas["Valor"] = df_entradas[mes_selecionado]
    df_gastos["Valor"] = df_gastos[mes_selecionado]
    df_investimentos["Valor"] = df_investimentos[mes_selecionado]

    aba_entradas, aba_gastos, aba_invest = st.tabs(["🟢 Recebimentos", "🔴 Gastos", "📈 Investimentos"])

    with aba_entradas:
        st.caption("Receitas")
        df_entradas_display = df_entradas[["Categoria", "Valor"]].copy()
        df_entradas_editado = st.data_editor(
            df_entradas_display,
            column_config={
                "Categoria": "Descrição",
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            },
            width='stretch', num_rows="dynamic", key=f"editor_entradas_{mes_selecionado}"
        )

    with aba_gastos:
        st.caption("Despesas")
        df_gastos_display = df_gastos[["Categoria", "Valor"]].copy()
        df_gastos_editado = st.data_editor(
            df_gastos_display,
            column_config={
                "Categoria": "Descrição",
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            },
            width='stretch', num_rows="dynamic", key=f"editor_gastos_{mes_selecionado}"
        )

    with aba_invest:
        st.caption("Patrimônio Acumulado")
        df_invest_display = df_investimentos[["Categoria", "Valor"]].copy()
        df_invest_editado = st.data_editor(
            df_invest_display,
            column_config={
                "Categoria": "Descrição",
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            },
            width='stretch', num_rows="dynamic", key=f"editor_invest_{mes_selecionado}"
        )

    st.divider()
    if st.button("💾 Salvar Alterações", type="primary"):
        # --- SALVAR DADOS FINANCEIROS (PRIORIDADE) ---
        try:
            df_entradas_editado[mes_selecionado] = df_entradas_editado["Valor"].fillna(0)
            df_gastos_editado[mes_selecionado] = df_gastos_editado["Valor"].fillna(0)
            df_invest_editado[mes_selecionado] = df_invest_editado["Valor"].fillna(0)
            
            cols_reais = ["Categoria", mes_selecionado]
            df_final_mes = pd.concat([
                df_entradas_editado[cols_reais], 
                df_gastos_editado[cols_reais],
                df_invest_editado[cols_reais]
            ], ignore_index=True)
            
            todas_categorias = df_final_mes["Categoria"].unique()
            df_save = pd.DataFrame({"Categoria": todas_categorias})
            
            for mes in meses_disponiveis:
                if mes == mes_selecionado:
                    df_save = df_save.merge(df_final_mes, on="Categoria", how="left")
                else:
                    df_temp = df[["Categoria", mes]]
                    df_save = df_save.merge(df_temp, on="Categoria", how="left")
            
            df_save = df_save.fillna(0)
            
            conn.update(worksheet="Dados_App", data=df_save)
            msg_sucesso = f"✅ Dados salvos com sucesso!"
            
        except Exception as e:
            st.error(f"❌ ERRO ao salvar dados: {e}")
            st.stop()

        # --- SALVAR CONFIGURAÇÃO (OPCIONAL) ---
        try:
            categorias_entrada_custom = [
                cat for cat in df_entradas_editado["Categoria"].dropna().astype(str).str.strip().tolist()
                if cat and cat not in categorias_entrada_padrao
            ]
            categorias_invest_custom = [
                cat for cat in df_invest_editado["Categoria"].dropna().astype(str).str.strip().tolist()
                if cat and not pd.Series([cat]).str.contains(
                    "Investimento|Aplicação|CDB|CDI|Poupança|Fundo|Ações", case=False, na=False
                ).iloc[0]
            ]

            df_config_novo = pd.DataFrame({
                "Ultimo_Mes": [mes_selecionado],
                "Categorias_Entrada_Custom": ["|".join(sorted(set(categorias_entrada_custom)))],
                "Categorias_Invest_Custom": ["|".join(sorted(set(categorias_invest_custom)))],
            })
            conn.update(worksheet="Config", data=df_config_novo)
            msg_sucesso += " (Mês lembrado)"
        except Exception:
            # Se falhar aqui (sem aba Config), apenas avisa discretamente no console ou ignora
            st.toast("⚠️ Dica: Crie a aba 'Config' na planilha para o sistema lembrar o mês.", icon="💡")
        
        # Recarregar dados após salvar
        df = conn.read(worksheet="Dados_App", usecols=list(range(13)), ttl=0)
        if "Categoria" in df.columns:
            df["Categoria"] = df["Categoria"].astype(str).str.strip()
        meses_disponiveis = df.columns[1:].tolist()
        if meses_disponiveis:
            df[meses_disponiveis] = df[meses_disponiveis].apply(pd.to_numeric, errors="coerce").fillna(0)

        st.cache_data.clear()
        st.success(f"{msg_sucesso} - {hora_atual_brasilia()}")
        st.rerun()

    # Métricas
    total_entradas = df_entradas[mes_selecionado].sum()
    total_gastos = df_gastos[mes_selecionado].sum() 
    total_investido = df_investimentos[mes_selecionado].sum()
    saldo = total_entradas - total_gastos

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    
    delta_sobra = formatar_moeda_visual(saldo)
    if saldo < 0:
        delta_sobra = f"- {formatar_moeda_visual(abs(saldo))}"
    elif saldo > 0:
        delta_sobra = f"+ {formatar_moeda_visual(saldo)}"

    c1.metric("📥 Ganhos", formatar_moeda_visual(total_entradas))
    c2.metric("💸 Gastos", formatar_moeda_visual(total_gastos), delta_color="inverse")
    c3.metric("🏦 Investimentos", formatar_moeda_visual(total_investido), help="Total acumulado")
    c4.metric("💰 Sobra", formatar_moeda_visual(saldo), delta=delta_sobra)
    
    # Gráficos Mês
    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Gastos por Categoria**")
        df_pizza = df_gastos.copy()
        df_pizza = df_pizza[df_pizza[mes_selecionado] > 0]
        if not df_pizza.empty:
            fig = px.pie(df_pizza, values=mes_selecionado, names='Categoria', hole=0.5)
            fig.update_traces(texttemplate='%{percent:.1%}', hovertemplate='<b>%{label}</b><br>%{value:,.2f}')
            st.plotly_chart(fig, width='stretch')

    with col_g2:
        st.markdown("**Balanço**")
        fig_bar = px.bar(
            pd.DataFrame({"Tipo": ["Ganhos", "Gastos"], "Valor": [total_entradas, total_gastos]}),
            x="Tipo", y="Valor", color="Tipo", text_auto='.2s', color_discrete_map={"Ganhos": "#2ECC71", "Gastos": "#E74C3C"}
        )
        fig_bar.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.")
        st.plotly_chart(fig_bar, width='stretch')

# ==============================================================================
# PÁGINA 2: EVOLUÇÃO
# ==============================================================================
elif pagina == "📈 Comparativo e Evolução" and conexao_valida(df, mask_entrada_global, mask_invest_global):
    
    st.header("📈 Evolução do seu Dinheiro")
    
    historico = []
    investimento_anterior = 0 
    
    for mes in meses_disponiveis:
        total_investido_mes = df[mask_invest_global][mes].sum()
        total_entradas_mes = df[mask_entrada_global][mes].sum()
        total_gastos_mes = df[~mask_entrada_global & ~mask_invest_global][mes].sum()
        
        if total_investido_mes == 0 and total_entradas_mes == 0 and total_gastos_mes == 0:
            break

        variacao_investimento = total_investido_mes - investimento_anterior
        investimento_anterior = total_investido_mes
        
        historico.append({
            "Mês": mes,
            "Total Investido": total_investido_mes,
            "Aumento Mensal": variacao_investimento,
            "Sobra de Caixa": total_entradas_mes - total_gastos_mes
        })
    
    df_hist = pd.DataFrame(historico)
    
    if not df_hist.empty:
        df_hist["Txt_Investido"] = df_hist["Total Investido"].apply(formatar_moeda_visual)
        df_hist["Txt_Aumento"] = df_hist["Aumento Mensal"].apply(formatar_moeda_visual)
        df_hist["Txt_Sobra"] = df_hist["Sobra de Caixa"].apply(formatar_moeda_visual)
        
        st.markdown("### 🏦 Patrimônio")
        fig_area = px.area(
            df_hist, x="Mês", y="Total Investido", 
            markers=True
        )
        fig_area.update_traces(line_color="#27AE60", fillcolor="rgba(46, 204, 113, 0.3)")
        fig_area.update_layout(yaxis_tickprefix="R$ ", separators=",.")
        fig_area.update_traces(hovertemplate='<b>%{x}</b><br>Total: %{customdata}', customdata=df_hist["Txt_Investido"])
        st.plotly_chart(fig_area, use_container_width=True)
        
        st.markdown("#### 🚀 Variação Mensal")
        fig_var = px.bar(
            df_hist, x="Mês", y="Aumento Mensal",
            text="Txt_Aumento", 
            color="Aumento Mensal",
            color_continuous_scale="Blugrn" 
        )
        fig_var.update_layout(yaxis_tickprefix="R$ ", separators=",.")
        fig_var.update_traces(textposition='outside')
        st.plotly_chart(fig_var, use_container_width=True)

        st.divider()
        st.markdown("### 🔵 Fluxo de Caixa")
        fig_sobras = px.line(df_hist, x="Mês", y="Sobra de Caixa", markers=True, text="Txt_Sobra")
        fig_sobras.update_traces(line_color="#2980B9", textposition="top center")
        fig_sobras.update_layout(yaxis_tickprefix="R$ ", separators=",.")
        st.plotly_chart(fig_sobras, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum dado encontrado.")

else:
    st.warning("⚠️ Conexão com Google Sheets não estabelecida. Configure as credenciais corretamente para acessar os dados.")
