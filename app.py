import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px


# Configuração da página
st.set_page_config(page_title="Finanças Família", layout="wide", page_icon="💰")


# Conectar com o Google Sheets
# Nota: As credenciais devem ser configuradas no Streamlit Cloud ou localmente em .streamlit/secrets.toml
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erro ao conectar ao Google Sheets. Verifique suas configurações de Secrets.")
    st.stop()


# Título
st.title("👨‍👩‍👧 Controle Financeiro Familiar")


# --- ENTRADA DE DADOS ---
with st.sidebar:
    st.header("Novo Gasto/Receita")
    with st.form("form_lancamento", clear_on_submit=True):
        data = st.date_input("Data", datetime.now())
        desc = st.text_input("Descrição (Ex: Supermercado, Aluguel)")
        quem = st.selectbox("Quem?", ["Marido", "Esposa", "Ambos"])
        categoria = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Educação", "Outros", "Salário"])
        tipo = st.selectbox("Tipo", ["Saída à Vista", "Crédito Parcelado", "Receita/Salário"])
        valor = st.number_input("Valor R$", min_value=0.0, format="%.2f")
        parc = st.number_input("Qtd Parcelas (se crédito)", min_value=1, value=1)
        enviar = st.form_submit_button("Registrar")


    if enviar:
        if desc and valor > 0:
            novos_dados = []
            for i in range(parc):
                # Lógica de cálculo do mês de referência
                mes_total = data.month + i - 1
                mes_ref = (mes_total % 12) + 1
                ano_ref = data.year + (mes_total // 12)
                
                valor_parc = valor / parc
                descricao_final = f"{desc} ({i+1}/{parc})" if parc > 1 else desc
                
                novos_dados.append({
                    "Data": data.strftime("%Y-%m-%d"),
                    "Descricao": descricao_final,
                    "Responsavel": quem,
                    "Categoria": categoria,
                    "Tipo": tipo,
                    "Valor": valor_parc,
                    "Parcelas": f"{i+1}/{parc}",
                    "Mes_Referencia": f"{ano_ref}-{mes_ref:02d}"
                })
            
            # Ler dados atuais para anexar os novos
            try:
                df_existente = conn.read(worksheet="Página1")
                df_novo = pd.DataFrame(novos_dados)
                df_final = pd.concat([df_existente, df_novo], ignore_index=True)
                conn.update(worksheet="Página1", data=df_final)
                st.success(f"Lançamento de '{desc}' processado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar dados: {e}")
        else:
            st.warning("Por favor, preencha a descrição e o valor.")


# --- VISUALIZAÇÃO ---
try:
    df = conn.read(worksheet="Página1")
    
    if not df.empty:
        # Filtro de Mês de Referência
        meses_disponiveis = sorted(df['Mes_Referencia'].unique(), reverse=True)
        mes_selecionado = st.selectbox("Selecione o Mês de Referência", meses_disponiveis)
        
        df_mes = df[df['Mes_Referencia'] == mes_selecionado]
        
        st.subheader(f"📊 Resumo de {mes_selecionado}")
        
        col1, col2, col3 = st.columns(3)
        receita = df_mes[df_mes['Tipo'] == 'Receita/Salário']['Valor'].sum()
        despesa = df_mes[df_mes['Tipo'] != 'Receita/Salário']['Valor'].sum()
        saldo = receita - despesa
        
        col1.metric("Ganhos", f"R$ {receita:,.2f}")
        col2.metric("Gastos", f"R$ {despesa:,.2f}", delta_color="inverse")
        col3.metric("Saldo Final", f"R$ {saldo:,.2f}", delta="No Azul" if saldo > 0 else "No Vermelho")
        
        c1, c2 = st.columns(2)
        
        with c1:
