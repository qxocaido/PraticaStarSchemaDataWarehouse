
import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 Dashboard de Vendas")
st.write("Análise de vendas utilizando modelagem multidimensional.")

# Conexão com o banco
def conectar_banco():
    return psycopg2.connect(
        host="localhost",
        database="starschema",
        user="postgres",
        password="postgres",
        port="5432"
    )

try:
    conexao = conectar_banco()

    # Busca os anos disponíveis
    anos = pd.read_sql_query("""
        SELECT DISTINCT ano
        FROM dim_tempo
        ORDER BY ano
    """, conexao)

    # Filtro de ano
    ano_selecionado = st.sidebar.selectbox(
        "Selecione o ano:",
        anos["ano"].tolist()
    )

    # Busca os dados das vendas
    consulta = """
        SELECT
            v.venda_id,
            v.quantidade,
            v.valor_unitario,
            v.valor_total,
            p.nome AS produto,
            p.categoria,
            c.estado,
            t.mes,
            t.ano
        FROM fato_vendas v
        JOIN dim_produto p
            ON v.produto_id = p.produto_id
        JOIN dim_cliente c
            ON v.cliente_id = c.cliente_id
        JOIN dim_tempo t
            ON v.tempo_id = t.tempo_id
        WHERE t.ano = %s
    """

    df = pd.read_sql_query(
        consulta,
        conexao,
        params=(ano_selecionado,)
    )

    conexao.close()

    # Indicadores
    faturamento = df["valor_total"].sum()
    quantidade_vendas = df["venda_id"].nunique()
    unidades_vendidas = df["quantidade"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Faturamento total",
        f"R$ {faturamento:,.2f}"
    )

    col2.metric(
        "Quantidade de vendas",
        quantidade_vendas
    )

    col3.metric(
        "Unidades vendidas",
        int(unidades_vendidas)
    )

    st.divider()

    # Gráfico de faturamento mensal
    st.subheader("Faturamento por mês")

    mensal = df.groupby("mes")["valor_total"].sum().reset_index()

    mensal["mes"] = mensal["mes"].map({
        1: "Janeiro", 2: "Fevereiro",
        3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro",
        11: "Novembro", 12: "Dezembro"
    })

    ordem_meses = [
        "Janeiro", "Fevereiro", "Março",
        "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro",
        "Outubro", "Novembro", "Dezembro"
    ]

    grafico_mensal = px.bar(
        mensal,
        x="mes",
        y="valor_total",
        category_orders={"mes": ordem_meses},
        labels={
            "mes": "Mês",
            "valor_total": "Faturamento (R$)"
        }
    )

    st.plotly_chart(grafico_mensal, use_container_width=True)

    # Gráficos por categoria e estado
    col4, col5 = st.columns(2)

    with col4:
        st.subheader("Faturamento por categoria")

        categoria = df.groupby(
            "categoria"
        )["valor_total"].sum().reset_index()

        grafico_categoria = px.pie(
            categoria,
            names="categoria",
            values="valor_total",
            hole=0.4
        )

        st.plotly_chart(
            grafico_categoria,
            use_container_width=True
        )

    with col5:
        st.subheader("Faturamento por estado")

        estado = df.groupby(
            "estado"
        )["valor_total"].sum().reset_index()

        grafico_estado = px.bar(
            estado,
            x="estado",
            y="valor_total",
            labels={
                "estado": "Estado",
                "valor_total": "Faturamento (R$)"
            }
        )

        st.plotly_chart(
            grafico_estado,
            use_container_width=True
        )

    # Ranking de produtos
    st.subheader("Produtos mais vendidos")

    produtos = df.groupby("produto").agg(
        unidades_vendidas=("quantidade", "sum"),
        faturamento=("valor_total", "sum")
    ).reset_index()

    produtos = produtos.sort_values(
        by="unidades_vendidas",
        ascending=False
    )

    st.dataframe(
        produtos,
        use_container_width=True,
        hide_index=True
    )

except Exception as erro:
    st.error(f"Erro ao carregar os dados: {erro}")
