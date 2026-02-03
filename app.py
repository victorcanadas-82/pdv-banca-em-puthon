import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- BANCO DE DADOS ---
conn = sqlite3.connect('banca_estoque.db', check_same_thread=False)
c = conn.cursor()

# Adicionada a coluna preco_custo
c.execute('''CREATE TABLE IF NOT EXISTS produtos 
             (id INTEGER PRIMARY KEY, codigo_barras TEXT, nome TEXT, 
              preco_custo REAL, preco_venda REAL, estoque INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS historico_vendas 
             (id INTEGER PRIMARY KEY, data_hora TEXT, nome_produto TEXT, valor REAL, tipo TEXT)''')
conn.commit()

# --- FUNÇÕES ---
def registrar_venda_db(nome_prod, preco, tipo, id_prod=None):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if id_prod:
        c.execute("UPDATE produtos SET estoque = estoque - 1 WHERE id = ?", (id_prod,))
    c.execute("INSERT INTO historico_vendas (data_hora, nome_produto, valor, tipo) VALUES (?, ?, ?, ?)", 
              (agora, nome_prod, preco, tipo))
    conn.commit()

# --- INTERFACE ---
st.set_page_config(page_title="Banca Pro", layout="wide")
st.title("🏪 PDV Banca com Gestão de Lucro")

aba1, aba2, aba3, aba4 = st.tabs(["🛒 Vendas", "📊 Estoque", "📈 Faturamento", "➕ Cadastro"])

# ... (Abas de Vendas e Faturamento permanecem similares, apenas mudando 'preco' para 'preco_venda')

with aba1:
    col_cod, col_man = st.columns(2)
    with col_cod:
        st.subheader("Venda por Código")
        barcode_venda = st.text_input("Bipe o código", key="venda_barcode")
        if barcode_venda:
            prod = pd.read_sql("SELECT * FROM produtos WHERE codigo_barras = ?", conn, params=(barcode_venda,))
            if not prod.empty:
                item = prod.iloc[0]
                st.info(f"**Item:** {item['nome']} | **R$ {item['preco_venda']:.2f}**")
                if st.button("Confirmar Venda Bipada"):
                    registrar_venda_db(item['nome'], item['preco_venda'], "Código", item['id'])
                    st.success("Venda registrada!")

    with col_man:
        st.subheader("Venda Manual")
        nome_manual = st.text_input("Nome do Item")
        valor_manual = st.number_input("Valor R$", min_value=0.0)
        if st.button("Confirmar Venda Manual"):
            registrar_venda_db(nome_manual, valor_manual, "Manual")
            st.success("Venda manual registrada!")

with aba2:
    st.header("Controle de Inventário")
    estoque_df = pd.read_sql("SELECT codigo_barras, nome, preco_custo, preco_venda, estoque FROM produtos", conn)
    st.dataframe(estoque_df, use_container_width=True)

with aba3:
    st.header("Relatório de Faturamento")
    hoje = datetime.now().strftime("%Y-%m-%d")
    detalhes = pd.read_sql("SELECT * FROM historico_vendas WHERE data_hora LIKE ?", conn, params=(f"{hoje}%",))
    st.metric("Total Hoje", f"R$ {detalhes['valor'].sum():.2f}")
    st.dataframe(detalhes)

with aba4:
    st.header("Cadastrar Novo Produto")
    with st.form("form_cad", clear_on_submit=True):
        f_cod = st.text_input("Código de Barras")
        f_nome = st.text_input("Nome do Produto")
        
        col_lucro1, col_lucro2, col_lucro3 = st.columns(3)
        with col_lucro1:
            f_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.10)
        with col_lucro2:
            f_porcentagem = st.number_input("Margem de Lucro (%)", min_value=0.0, step=5.0, value=30.0)
        
        # Cálculo automático da sugestão de venda
        f_venda_sugerido = f_custo + (f_custo * (f_porcentagem / 100))
        
        with col_lucro3:
            f_venda = st.number_input("Preço Final de Venda (R$)", min_value=0.0, value=f_venda_sugerido, step=0.10)
            st.caption(f"Sugestão: R$ {f_venda_sugerido:.2f}")

        f_estoque = st.number_input("Estoque Inicial", min_value=0)
        
        if st.form_submit_button("Salvar Produto"):
            c.execute('''INSERT INTO produtos (codigo_barras, nome, preco_custo, preco_venda, estoque) 
                         VALUES (?, ?, ?, ?, ?)''', (f_cod, f_nome, f_custo, f_venda, f_estoque))
            conn.commit()
            st.success(f"Produto {f_nome} cadastrado com lucro de {f_porcentagem}%!")