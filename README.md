# Radar de Segurança Viária no Brasil

**Disciplina:** Linguagens de programação

**Professor:** Alexandre Neves Louzada

**Aluno:** André de Moraes Costa

Projeto da Avaliação G1 de Análise e Visualização de Dados com Python. 

Analisa uma base simulada (960 linhas = 8 municípios × 120 meses) para responder: quanto a chuva explica os deslizamentos, onde os impactos se concentram e em que época do ano?

## 🔗 Links
- Repositório: <https://github.com/demoraescosta/projeto-g1>
- Página do projeto (GitHub Pages): `https://demoraescosta.github.io/projeto-g1/`
- Dashboard (Streamlit Cloud): `https://SEU-APP.streamlit.app`

## Principais resultados
- Correlação chuva × ocorrências ≈ **0,82** (índice de solo ≈ 0,72).
- Dez–mar concentram ~**58%** das ocorrências.
- Região Serrana: ~**57%** das ocorrências e ~**61%** dos óbitos.
- Nível 'Crítico' responde por ~78% dos óbitos.

## Tecnologias
Python · Pandas · NumPy · Matplotlib · Seaborn · Streamlit · Plotly · SQLAlchemy + SQLite · GitHub / GitHub Pages

## Funcionalidades
- **Intermediárias:** filtros múltiplos, KPIs dinâmicos, análise temporal, dashboard em abas, visualizações comparativas, análise geográfica, upload de CSV.
- **Avançadas:** persistência SQLite com SQLAlchemy, mapa interativo (Plotly), séries temporais com médias móveis, correlação estatística (Pearson/Spearman).

## Estrutura
```
projeto-g1/
├── app.py              # dashboard Streamlit
├── requirements.txt
├── README.md
├── index.html          # página do projeto (GitHub Pages)
├── dados/              # CSV original
├── database/           # chuvas.db (SQLite, gerado no notebook)
├── notebooks/          # análise completa (.ipynb)
└── imagens/            # gráficos exportados
```

## Como executar
```bash
pip install -r requirements.txt
streamlit run app.py
```
O banco `database/chuvas.db` é gerado pela seção 7 do notebook; se não existir, o app lê o CSV.

## Publicação
1. **GitHub:** crie o repositório e envie a pasta (`git init && git add . && git commit -m "G1" && git push`).
2. **GitHub Pages:** Settings → Pages → Branch `main` / pasta `/ (root)`.
3. **Streamlit Cloud:** share.streamlit.io → New app → selecione o repositório, arquivo `app.py`.

