"""Dashboard: Chuvas e Deslizamentos no Estado do RJ (2015-2024)."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st
from sqlalchemy import create_engine

BASE = Path(__file__).parent
DB = BASE / "database" / "chuvas.db"
CSV = BASE / "dados" / "simulacao_chuvas_deslizamentos_rj.csv"
ORDEM_RISCO = ["Baixo", "Médio", "Alto", "Crítico"]
CORES_RISCO = {"Baixo": "#6BAA75", "Médio": "#E9C46A", "Alto": "#F4813F", "Crítico": "#B5232D"}
COORDS = {
    "Rio de Janeiro": (-22.9068, -43.1729), "Niterói": (-22.8832, -43.1034),
    "Nova Iguaçu": (-22.7592, -43.4509), "Petrópolis": (-22.5050, -43.1789),
    "Teresópolis": (-22.4120, -42.9660), "Nova Friburgo": (-22.2819, -42.5311),
    "Angra dos Reis": (-23.0067, -44.3181), "Campos dos Goytacazes": (-21.7545, -41.3244),
}
COLUNAS = {"ano", "mes", "data", "municipio", "regiao_rj", "populacao", "chuva_mm", "temperatura_media",
           "ocorrencias_deslizamento", "desalojados", "obitos", "nivel_risco", "indice_solo", "umidade"}

st.set_page_config(page_title="Chuvas e Deslizamentos no RJ", page_icon="🌧️", layout="wide")


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values(["municipio", "data"])
    df["periodo_chuvoso"] = df["mes"].isin([12, 1, 2, 3]).map({True: "Chuvoso (dez–mar)", False: "Menos chuvoso (abr–nov)"})
    df["chuva_acum_3m"] = df.groupby("municipio")["chuva_mm"].transform(lambda s: s.rolling(3, min_periods=1).sum())
    return df


@st.cache_data
def carregar_base() -> tuple[pd.DataFrame, str]:
    """Lê do SQLite (via SQLAlchemy); se não existir, usa o CSV."""
    if DB.exists():
        engine = create_engine(f"sqlite:///{DB}")
        with engine.connect() as con:
            return preparar(pd.read_sql("SELECT * FROM ocorrencias", con)), "SQLite (SQLAlchemy)"
    return preparar(pd.read_csv(CSV, encoding="utf-8-sig")), "CSV"


# ---------------------------------------------------------------- dados + upload
base, fonte = carregar_base()
st.sidebar.header("Filtros")
arq = st.sidebar.file_uploader("Enviar outro CSV (mesmas colunas)", type="csv")
if arq is not None:
    novo = pd.read_csv(arq, encoding="utf-8-sig")
    if COLUNAS.issubset(novo.columns):
        base, fonte = preparar(novo), "CSV enviado"
    else:
        st.sidebar.error(f"Colunas ausentes: {', '.join(sorted(COLUNAS - set(novo.columns)))}")

anos = st.sidebar.slider("Período (anos)", int(base.ano.min()), int(base.ano.max()),
                         (int(base.ano.min()), int(base.ano.max())))
regioes = st.sidebar.multiselect("Região", sorted(base.regiao_rj.unique()), default=sorted(base.regiao_rj.unique()))
muns_disp = sorted(base[base.regiao_rj.isin(regioes)].municipio.unique())
muns = st.sidebar.multiselect("Município", muns_disp, default=muns_disp)
riscos = st.sidebar.multiselect("Nível de risco", ORDEM_RISCO, default=ORDEM_RISCO)
meses_ch = st.sidebar.checkbox("Somente meses chuvosos (dez–mar)")
st.sidebar.caption(f"Fonte dos dados: {fonte}")

df = base[base.ano.between(*anos) & base.regiao_rj.isin(regioes) & base.municipio.isin(muns) & base.nivel_risco.isin(riscos)]
if meses_ch:
    df = df[df.periodo_chuvoso.str.startswith("Chuvoso")]

# ---------------------------------------------------------------- cabeçalho
st.title("🌧️ Chuvas e Deslizamentos no Estado do Rio de Janeiro")
st.markdown(
    "**Problema:** o RJ sofre com deslizamentos de terra a cada temporada de chuvas. Este painel investiga **quanto a chuva "
    "explica os deslizamentos, onde os impactos se concentram e em que época do ano** (base simulada, 8 municípios, 2015–2024)."
)
if df.empty:
    st.warning("Nenhum registro com os filtros atuais. Ajuste os filtros na barra lateral.")
    st.stop()

# ---------------------------------------------------------------- KPIs
top = df.groupby("municipio").ocorrencias_deslizamento.sum().idxmax()
k = st.columns(6)
k[0].metric("Ocorrências", f"{df.ocorrencias_deslizamento.sum():,}".replace(",", "."))
k[1].metric("Desalojados", f"{df.desalojados.sum():,}".replace(",", "."))
k[2].metric("Óbitos", int(df.obitos.sum()))
k[3].metric("Chuva média/mês", f"{df.chuva_mm.mean():.0f} mm")
k[4].metric("Meses em risco Crítico", f"{(df.nivel_risco == 'Crítico').mean() * 100:.0f}%")
k[5].metric("Mais ocorrências", top)

aba1, aba2, aba3, aba4, aba5 = st.tabs(["Visão geral", "Análise temporal", "Mapa", "Correlação", "Dados e conclusão"])

# ---------------------------------------------------------------- visão geral
with aba1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Ocorrências por município")
        mun = df.groupby(["municipio", "regiao_rj"], as_index=False).agg(
            ocorrencias=("ocorrencias_deslizamento", "sum"), obitos=("obitos", "sum")).sort_values("ocorrencias", ascending=False)
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(data=mun, y="municipio", x="ocorrencias", hue="regiao_rj", dodge=False, ax=ax)
        ax.set(xlabel="Ocorrências", ylabel="")
        st.pyplot(fig)
    with c2:
        st.subheader("Chuva × ocorrências")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.scatterplot(data=df, x="chuva_mm", y="ocorrencias_deslizamento", hue="nivel_risco",
                        hue_order=ORDEM_RISCO, palette=CORES_RISCO, alpha=.7, ax=ax)
        if len(df) > 2:
            sns.regplot(data=df, x="chuva_mm", y="ocorrencias_deslizamento", scatter=False, color="black", ax=ax)
        ax.set(xlabel="Chuva (mm)", ylabel="Ocorrências")
        st.pyplot(fig)
    top_reg = mun.groupby("regiao_rj").ocorrencias.sum().sort_values(ascending=False)
    st.info(f"**Interpretação:** nos filtros atuais, a região com mais ocorrências é **{top_reg.index[0]}** "
            f"({top_reg.iloc[0] / top_reg.sum() * 100:.0f}% do total). A nuvem de pontos sobe junto com a chuva: "
            "quanto mais chuva, mais deslizamentos — e os meses 'Crítico' se concentram à direita do gráfico.")
    st.subheader("Resumo por município")
    st.dataframe(mun.rename(columns={"municipio": "Município", "regiao_rj": "Região", "ocorrencias": "Ocorrências", "obitos": "Óbitos"}),
                 use_container_width=True, hide_index=True)

# ---------------------------------------------------------------- temporal
with aba2:
    st.subheader("Série temporal com médias móveis")
    ts = df.groupby("data").agg(ocorrencias=("ocorrencias_deslizamento", "sum")).reset_index()
    ts["Média móvel 3m"] = ts.ocorrencias.rolling(3).mean()
    ts["Média móvel 12m"] = ts.ocorrencias.rolling(12).mean()
    g = px.line(ts, x="data", y=["ocorrencias", "Média móvel 3m", "Média móvel 12m"],
                labels={"value": "Ocorrências", "data": "", "variable": ""})
    st.plotly_chart(g, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Sazonalidade (média por mês)")
        sm = df.groupby("mes")[["chuva_mm", "ocorrencias_deslizamento"]].mean().reset_index()
        fig, ax = plt.subplots(figsize=(6, 3.8))
        sns.barplot(data=sm, x="mes", y="ocorrencias_deslizamento", color="#D1495B", ax=ax)
        ax2 = ax.twinx()
        ax2.plot(range(len(sm)), sm.chuva_mm, color="#1D4E89", marker="o")
        ax.set(xlabel="Mês", ylabel="Ocorrências (barras)"); ax2.set_ylabel("Chuva mm (linha)")
        st.pyplot(fig)
    with c2:
        st.subheader("Município × mês")
        pv = df.pivot_table(index="municipio", columns="mes", values="ocorrencias_deslizamento", aggfunc="mean")
        fig, ax = plt.subplots(figsize=(6, 3.8))
        sns.heatmap(pv, cmap="YlOrRd", annot=True, fmt=".0f", cbar=False, ax=ax)
        ax.set(xlabel="Mês", ylabel="")
        st.pyplot(fig)
    st.info("**Interpretação:** há forte sazonalidade — dezembro a março concentram a maior parte das ocorrências. "
            "A média móvel de 12 meses é praticamente plana: não há tendência de queda ou alta no período.")

# ---------------------------------------------------------------- mapa
with aba3:
    st.subheader("Mapa interativo dos impactos por município")
    metrica = st.radio("Tamanho do círculo", ["ocorrencias_deslizamento", "desalojados", "obitos"], horizontal=True)
    mp = df.groupby("municipio", as_index=False).agg(
        ocorrencias_deslizamento=("ocorrencias_deslizamento", "sum"), desalojados=("desalojados", "sum"),
        obitos=("obitos", "sum"), chuva_media=("chuva_mm", "mean"))
    mp = mp[mp.municipio.isin(COORDS)]
    mp["lat"] = mp.municipio.map(lambda m: COORDS[m][0])
    mp["lon"] = mp.municipio.map(lambda m: COORDS[m][1])
    mapa = px.scatter_map(mp, lat="lat", lon="lon", size=metrica, color="chuva_media", color_continuous_scale="YlOrRd",
                          hover_name="municipio", hover_data=["ocorrencias_deslizamento", "desalojados", "obitos"],
                          size_max=45, zoom=6.3, height=520, labels={"chuva_media": "Chuva média (mm)"})
    st.plotly_chart(mapa, use_container_width=True)
    st.info("**Interpretação:** os maiores círculos ficam na Região Serrana (Petrópolis, Teresópolis e Nova Friburgo), "
            "que também tem a maior chuva média.")

# ---------------------------------------------------------------- correlação
with aba4:
    st.subheader("Correlação estatística (Pearson)")
    cols = ["chuva_mm", "chuva_acum_3m", "indice_solo", "umidade", "temperatura_media",
            "ocorrencias_deslizamento", "desalojados", "obitos"]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    sns.heatmap(df[cols].corr(), annot=True, fmt=".2f", cmap="RdBu_r", center=0, vmin=-1, vmax=1, ax=ax)
    st.pyplot(fig)
    x = st.selectbox("Variável explicativa", ["chuva_mm", "chuva_acum_3m", "indice_solo", "umidade", "temperatura_media"])
    y = st.selectbox("Variável de impacto", ["ocorrencias_deslizamento", "desalojados", "obitos"])
    r = df[x].corr(df[y])
    rs = df[x].corr(df[y], method="spearman")
    st.metric(f"Correlação {x} × {y}", f"Pearson {r:.2f}", f"Spearman {rs:.2f}", delta_color="off")
    st.info("**Interpretação:** chuva (≈0,82) e índice de solo (≈0,72) são as variáveis mais associadas às ocorrências; "
            "temperatura e umidade quase não importam. Correlação não implica causalidade.")

# ---------------------------------------------------------------- dados + conclusão
with aba5:
    st.subheader("Tabela de dados filtrados")
    st.dataframe(df.drop(columns=["periodo_chuvoso"]), use_container_width=True, hide_index=True)
    st.download_button("Baixar CSV filtrado", df.to_csv(index=False).encode("utf-8"), "dados_filtrados.csv", "text/csv")
    st.subheader("Conclusão executiva")
    st.success(
        "- **Chuva é o fator central:** r ≈ 0,82 com as ocorrências; solo saturado agrava.\n"
        "- **Verão concentra o risco:** dez–mar têm ~58% das ocorrências.\n"
        "- **Região Serrana é prioridade:** ~57% das ocorrências e ~61% dos óbitos.\n"
        "- **Recomendação:** antecipar alertas e preparação para novembro–dezembro, focando Petrópolis, Teresópolis e Nova Friburgo.\n\n"
        "*Limitação: base simulada; os percentuais acima são do conjunto completo, sem filtros.*"
    )
