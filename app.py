import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
conn = sqlite3.connect('banca_estoque.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS produtos 
             (id INTEGER PRIMARY KEY, codigo_barras TEXT, nome TEXT, preco REAL, estoque INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS historico_vendas 
             (id INTEGER PRIMARY KEY, data_hora TEXT, nome_produto TEXT, valor REAL, tipo TEXT)''')
conn.commit()

# --- FUNÇÕES ---
def registrar_venda_db(nome_prod, preco, tipo, id_prod=None):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Se for venda de produto cadastrado, abate estoque
    if id_prod:
        c.execute("UPDATE produtos SET estoque = estoque - 1 WHERE id = ?", (id_prod,))
    
    # Registra no histórico (serve para cadastrados e manuais)
    c.execute("INSERT INTO historico_vendas (data_hora, nome_produto, valor, tipo) VALUES (?, ?, ?, ?)", 
              (agora, nome_prod, preco, tipo))
    conn.commit()

# --- INTERFACE ---
st.set_page_config(page_title="Banca Pro", layout="wide")
st.title("🏪 PDV Banca - Gestão Completa")

aba1, aba2, aba3, aba4 = st.tabs(["🛒 Vendas", "📊 Estoque", "📈 Faturamento", "➕ Cadastro"])

with aba1:
    col_cod, col_man = st.columns(2)
    
    with col_cod:
        st.subheader("Venda por Código")
        barcode_venda = st.text_input("Bipe o código", key="venda_barcode")
        if barcode_venda:
            prod = pd.read_sql("SELECT * FROM produtos WHERE codigo_barras = ?", conn, params=(barcode_venda,))
            if not prod.empty:
                item = prod.iloc[0]
                st.info(f"**Item:** {item['nome']} | **R$ {item['preco']:.2f}**")
                if st.button("Confirmar Venda Bipada"):
                    registrar_venda_db(item['nome'], item['preco'], "Código", item['id'])
                    st.success("Venda registrada!")
            else:
                st.warning("Não cadastrado.")

    with col_man:
        st.subheader("Venda Manual")
        nome_manual = st.text_input("Nome do Item (Ex: Jornal Antigo)")
        valor_manual = st.number_input("Valor R$", min_value=0.0, step=0.50)
        if st.button("Confirmar Venda Manual"):
            if nome_manual and valor_manual > 0:
                registrar_venda_db(nome_manual, valor_manual, "Manual")
                st.success("Venda manual registrada!")
            else:
                st.error("Preencha nome e valor.")

with aba2:
    st.header("Controle de Inventário")
    estoque_df = pd.read_sql("SELECT codigo_barras, nome, preco, estoque FROM produtos", conn)
    
    estoque_baixo = estoque_df[estoque_df['estoque'] < 5]
    if not estoque_baixo.empty:
        st.warning(f"⚠️ **Atenção:** {len(estoque_baixo)} itens com estoque baixo!")
        st.dataframe(estoque_baixo)
    
    st.dataframe(estoque_df, use_container_width=True)

with aba3:
    st.header("Relatório de Faturamento")
    hoje = datetime.now().strftime("%Y-%m-%d")
    detalhes = pd.read_sql("SELECT data_hora, nome_produto, valor, tipo FROM historico_vendas WHERE data_hora LIKE ?", 
                           conn, params=(f"{hoje}%",))
    
    total_dia = detalhes['valor'].sum()
    st.metric("Faturamento de Hoje", f"R$ {total_dia:.2f}")
    st.dataframe(detalhes, use_container_width=True)

    # --- BOTÃO EXPORTAR EXCEL ---
    if not detalhes.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            detalhes.to_excel(writer, index=False, sheet_name='Vendas_Hoje')
        
        st.download_button(
            label="📥 Baixar Relatório em Excel",
            data=output.getvalue(),
            file_name=f"faturamento_{hoje}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with aba4:
    st.header("Cadastrar Produto")
    with st.form("form_cad", clear_on_submit=True):
        c1 = st.text_input("Código de Barras")
        c2 = st.text_input("Nome")
        c3 = st.number_input("Preço", min_value=0.0)
        c4 = st.number_input("Estoque Inicial", min_value=0)
        if st.form_submit_button("Salvar"):
            c.execute("INSERT INTO produtos (codigo_barras, nome, preco, estoque) VALUES (?, ?, ?, ?)", (c1, c2, c3, c4))
            conn.commit()
            st.success("Cadastrado!")