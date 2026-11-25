"""
Gerador da base de dados fictícia "Café Serra Alta".

Modelo estrela pensado para Power BI:
  Dimensões: dim_calendario, dim_produto, dim_linha, dim_canal, dim_regiao, dim_cliente
  Fatos:     fato_vendas, fato_producao, fato_perdas, fato_marketing,
             fato_preco_materia_prima

Todos os dados são FICTÍCIOS e gerados com semente fixa (reprodutível).
Uso:  python scripts/gerar_base.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)
BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "dados"
OUT.mkdir(exist_ok=True)

INICIO, FIM = "2024-01-01", "2025-12-31"

# --------------------------------------------------------------------------
# dim_calendario
# --------------------------------------------------------------------------
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
datas = pd.date_range(INICIO, FIM, freq="D")
dim_calendario = pd.DataFrame({
    "data": datas.date,
    "ano": datas.year,
    "trimestre": "T" + datas.quarter.astype(str),
    "mes_num": datas.month,
    "mes_nome": [MESES[m - 1] for m in datas.month],
    "ano_mes": datas.strftime("%Y-%m"),
    "dia": datas.day,
    "dia_semana_num": datas.dayofweek + 1,
    "dia_semana": [DIAS[d] for d in datas.dayofweek],
    "fim_de_semana": np.where(datas.dayofweek >= 5, "Sim", "Não"),
})

# --------------------------------------------------------------------------
# dim_produto  (custos unitários BASE em R$ — variam no tempo nos fatos)
# kg_cafe = kg de café verde consumido por unidade (inclui quebra de torra ~18%)
# --------------------------------------------------------------------------
produtos = [
    # id, sku, nome, linha, categoria, peso_g, kg_cafe, embalagem, producao, mao_obra, preco_revenda, perda_pct, mix
    (1, "CSA-TRD-250", "Tradicional Moído 250g", "Tradicional", "Moído", 250, 0.305, 0.85, 0.55, 0.60, 22.90, 0.025, 0.20),
    (2, "CSA-TRD-500", "Tradicional Moído 500g", "Tradicional", "Moído", 500, 0.610, 1.20, 0.95, 0.90, 41.90, 0.025, 0.22),
    (3, "CSA-EXF-500", "Extraforte Moído 500g", "Tradicional", "Moído", 500, 0.610, 1.20, 1.05, 0.90, 43.90, 0.030, 0.12),
    (4, "CSA-GOU-250", "Gourmet Moído 250g", "Gourmet", "Moído", 250, 0.305, 1.60, 0.70, 0.95, 32.90, 0.020, 0.10),
    (5, "CSA-GOU-G250", "Gourmet Grãos 250g", "Gourmet", "Grãos", 250, 0.300, 1.75, 0.60, 0.95, 36.90, 0.018, 0.07),
    (6, "CSA-ESP-250", "Especial Microlote 250g", "Especiais", "Grãos", 250, 0.300, 2.40, 0.80, 1.60, 64.90, 0.015, 0.04),
    (7, "CSA-DES-250", "Descafeinado Moído 250g", "Gourmet", "Moído", 250, 0.305, 1.60, 1.90, 1.00, 34.90, 0.030, 0.04),
    (8, "CSA-CAP-10", "Cápsulas Compatíveis 10un", "Cápsulas", "Cápsulas", 55, 0.068, 3.10, 1.40, 0.80, 24.90, 0.040, 0.13),
    (9, "CSA-FSV-1KG", "Food Service Grãos 1kg", "Food Service", "Grãos", 1000, 1.200, 2.10, 1.70, 1.40, 89.90, 0.015, 0.05),
    (10, "CSA-SOL-100", "Solúvel Premium 100g", "Tradicional", "Solúvel", 100, 0.230, 1.90, 2.30, 0.70, 28.90, 0.020, 0.03),
]
dim_produto = pd.DataFrame(produtos, columns=[
    "id_produto", "sku", "produto", "linha", "categoria", "peso_g", "kg_cafe_verde_un",
    "custo_embalagem_base", "custo_producao_base", "custo_mao_obra_base",
    "preco_revenda_sugerido", "perda_media_pct", "_mix"])
LINHAS = ["Tradicional", "Gourmet", "Especiais", "Cápsulas", "Food Service"]
dim_linha = pd.DataFrame({"id_linha": range(1, len(LINHAS) + 1), "linha": LINHAS,
                          "posicionamento": ["Volume", "Premium", "Super Premium", "Conveniência", "B2B"]})
dim_produto.insert(3, "id_linha", dim_produto.linha.map(dict(zip(LINHAS, dim_linha.id_linha))))
dim_produto["unidades_por_caixa"] = np.where(dim_produto.peso_g >= 1000, 6,
                                    np.where(dim_produto.peso_g >= 500, 10, 20))
dim_produto["data_lancamento"] = pd.to_datetime("2020-03-01").date()
dim_produto.loc[dim_produto.id_produto == 6, "data_lancamento"] = pd.to_datetime("2024-04-01").date()
dim_produto.loc[dim_produto.id_produto == 8, "data_lancamento"] = pd.to_datetime("2023-08-01").date()

# --------------------------------------------------------------------------
# dim_canal  (preço de venda = preço de revenda sugerido × fator do canal)
# --------------------------------------------------------------------------
dim_canal = pd.DataFrame([
    (1, "E-commerce Próprio", "Direto ao consumidor", 1.00, 0.05, 0.18),
    (2, "Supermercados", "Revenda", 0.64, 0.06, 0.38),
    (3, "Atacado / Distribuidores", "Revenda", 0.58, 0.07, 0.27),
    (4, "Cafeterias e Empórios", "Revenda", 0.70, 0.03, 0.17),
], columns=["id_canal", "canal", "tipo_canal", "fator_preco", "desconto_medio_pct", "_peso"])

# --------------------------------------------------------------------------
# dim_regiao  (CD em Varginha-MG; frete R$/kg cresce com a distância)
# --------------------------------------------------------------------------
dim_regiao = pd.DataFrame([
    (1, "MG", "Minas Gerais", "Sudeste", 0, 0.55, 0.16),
    (2, "SP", "São Paulo", "Sudeste", 320, 0.80, 0.30),
    (3, "RJ", "Rio de Janeiro", "Sudeste", 380, 0.90, 0.11),
    (4, "ES", "Espírito Santo", "Sudeste", 620, 1.10, 0.03),
    (5, "PR", "Paraná", "Sul", 720, 1.20, 0.07),
    (6, "SC", "Santa Catarina", "Sul", 950, 1.40, 0.05),
    (7, "RS", "Rio Grande do Sul", "Sul", 1350, 1.75, 0.06),
    (8, "GO", "Goiás", "Centro-Oeste", 750, 1.25, 0.04),
    (9, "DF", "Distrito Federal", "Centro-Oeste", 820, 1.30, 0.05),
    (10, "BA", "Bahia", "Nordeste", 1450, 1.95, 0.05),
    (11, "PE", "Pernambuco", "Nordeste", 2150, 2.50, 0.04),
    (12, "CE", "Ceará", "Nordeste", 2600, 2.85, 0.04),
], columns=["id_regiao", "uf", "estado", "regiao", "distancia_cd_km", "frete_por_kg", "_peso"])

# --------------------------------------------------------------------------
# dim_cliente
# --------------------------------------------------------------------------
prefixos = {
    2: ["Supermercado", "Rede", "Mercado", "Hiper"],
    3: ["Distribuidora", "Atacadão", "Comercial", "Central"],
    4: ["Café", "Empório", "Cafeteria", "Padaria Artesanal"],
}
sufixos = ["Bela Vista", "Horizonte", "São Jorge", "Bom Preço", "Nova Era", "Primavera", "Serrano",
           "Do Vale", "Ipê", "Aurora", "Monte Verde", "Estrela", "Real", "Paulista", "Mineiro",
           "Atlântico", "Cerrado", "Pioneiro", "Campo Belo", "Jardim", "Boa Safra", "Grão Fino",
           "Santa Luzia", "Três Rios", "Imperial", "União", "Litoral", "Planalto", "Rota Sul", "Alvorada"]
clientes, cid = [], 1
for _, r in dim_regiao.iterrows():
    clientes.append((cid, f"Consumidor Final {r.uf}", 1, r.id_regiao, "B2C", pd.Timestamp("2020-03-01").date()))
    cid += 1
for canal_id, n in [(2, 55), (3, 25), (4, 70)]:
    for _ in range(n):
        reg = rng.choice(dim_regiao.id_regiao, p=dim_regiao._peso / dim_regiao._peso.sum())
        nome = f"{rng.choice(prefixos[canal_id])} {rng.choice(sufixos)}"
        inicio = pd.Timestamp("2019-01-01") + pd.Timedelta(days=int(rng.integers(0, 2300)))
        clientes.append((cid, nome, canal_id, reg, "B2B", inicio.date()))
        cid += 1
dim_cliente = pd.DataFrame(clientes, columns=["id_cliente", "cliente", "id_canal", "id_regiao", "tipo_cliente", "cliente_desde"])
# nomes únicos
dup = dim_cliente.duplicated("cliente", keep=False)
dim_cliente.loc[dup, "cliente"] = dim_cliente.loc[dup, "cliente"] + " " + dim_cliente.loc[dup, "id_cliente"].astype(str)
porte = rng.choice(["Pequeno", "Médio", "Grande"], size=len(dim_cliente), p=[0.5, 0.35, 0.15])
dim_cliente["porte"] = np.where(dim_cliente.tipo_cliente == "B2C", "Varejo Online", porte)

# --------------------------------------------------------------------------
# fato_preco_materia_prima  (R$/kg de café verde arábica — alta em 2025)
# --------------------------------------------------------------------------
meses = pd.date_range(INICIO, FIM, freq="MS")
t = np.arange(len(meses))
preco_kg = 19.5 + 0.55 * t + 1.2 * np.sin(t / 2.2) + rng.normal(0, 0.45, len(t))  # ~R$19,5 -> ~R$33
fato_preco_mp = pd.DataFrame({
    "data": meses.date,
    "ano_mes": meses.strftime("%Y-%m"),
    "materia_prima": "Café verde arábica",
    "preco_kg": preco_kg.round(2),
    "preco_saca_60kg": (preco_kg * 60).round(2),
})
mp_por_mes = dict(zip(fato_preco_mp.ano_mes, fato_preco_mp.preco_kg))
inflacao_mes = {m: 1 + 0.0042 * i for i, m in enumerate(fato_preco_mp.ano_mes)}  # ~5% a.a.

# --------------------------------------------------------------------------
# fato_vendas  (pedido x produto)
# --------------------------------------------------------------------------
sazonal = {1: 0.92, 2: 0.88, 3: 0.95, 4: 0.97, 5: 1.05, 6: 1.15, 7: 1.20, 8: 1.12,
           9: 1.00, 10: 0.98, 11: 1.08, 12: 1.22}
dow = np.array([1.10, 1.05, 1.05, 1.08, 1.12, 0.85, 0.60])
cli_por_canal = {c: dim_cliente[dim_cliente.id_canal == c] for c in dim_canal.id_canal}
qtd_media = {1: 2.2, 2: 48, 3: 120, 4: 18}  # unidades por linha de pedido
pedidos_dia = {1: 22, 2: 6, 3: 2.2, 4: 7}

linhas, id_pedido = [], 100000
for d in datas:
    crescimento = 1 + 0.17 * ((d - pd.Timestamp(INICIO)).days / 365)
    fator = sazonal[d.month] * dow[d.dayofweek] * crescimento
    for _, c in dim_canal.iterrows():
        cli = cli_por_canal[c.id_canal]
        n_ped = rng.poisson(pedidos_dia[c.id_canal] * fator)
        if n_ped == 0:
            continue
        if c.id_canal == 1:
            w = dim_regiao.set_index("id_regiao").loc[cli.id_regiao, "_peso"].values
            esc = cli.sample(n_ped, replace=True, weights=w, random_state=int(rng.integers(1e9)))
        else:
            esc = cli.sample(n_ped, replace=True, random_state=int(rng.integers(1e9)))
        for _, cl in esc.iterrows():
            id_pedido += 1
            mix = dim_produto._mix.values.copy()
            if c.id_canal == 4:
                mix = mix * np.array([.3, .3, .3, 1.5, 2, 3, 1, .6, 5, .3])
            if d < pd.Timestamp("2024-04-01"):
                mix[5] = 0  # Microlote lançado em abr/2024
            mix = mix / mix.sum()
            n_itens = min(1 + rng.poisson(1.3 if c.id_canal == 1 else 2.5), 6)
            itens = rng.choice(dim_produto.id_produto, size=n_itens, replace=False, p=mix)
            for p in itens:
                qtd = max(1, int(rng.gamma(2.0, qtd_media[c.id_canal] / 2.0)))
                if c.id_canal != 1:
                    cx = dim_produto.loc[p - 1, "unidades_por_caixa"]
                    qtd = max(cx, int(round(qtd / cx)) * cx) if c.id_canal == 3 else qtd
                linhas.append((id_pedido, d.date(), cl.id_cliente, c.id_canal, cl.id_regiao, p, qtd))

fato_vendas = pd.DataFrame(linhas, columns=["id_pedido", "data", "id_cliente", "id_canal", "id_regiao", "id_produto", "quantidade"])
fato_vendas.insert(0, "id_venda", np.arange(1, len(fato_vendas) + 1))
fato_vendas["ano_mes"] = pd.to_datetime(fato_vendas.data).dt.strftime("%Y-%m")

# --------------------------------------------------------------------------
# fato_producao  (lotes semanais por produto, dimensionados pela demanda)
# --------------------------------------------------------------------------
fv_dt = pd.to_datetime(fato_vendas.data)
dem_sem = fato_vendas.assign(semana=fv_dt.dt.to_period("W-SUN").dt.start_time).groupby(["semana", "id_produto"]).quantidade.sum()
lotes, id_lote = [], 1
for (semana, p), qtd_dem in dem_sem.items():
    prod = dim_produto.loc[p - 1]
    am = semana.strftime("%Y-%m")
    if am not in mp_por_mes:
        am = INICIO[:7]
    perda_pct = float(np.clip(rng.normal(prod.perda_media_pct, prod.perda_media_pct * 0.35), 0.003, 0.12))
    # eventos pontuais de perda alta (falha de torra/máquina)
    if rng.random() < 0.025:
        perda_pct += rng.uniform(0.04, 0.09)
    qtd_boa = int(qtd_dem * rng.uniform(1.00, 1.06))
    qtd_prod = int(np.ceil(qtd_boa / (1 - perda_pct)))
    qtd_perdida = qtd_prod - qtd_boa
    inf = inflacao_mes[am]
    ruido = lambda: rng.normal(1, 0.03)
    c_mp = qtd_prod * prod.kg_cafe_verde_un * mp_por_mes[am] * ruido()
    c_prod = qtd_prod * prod.custo_producao_base * inf * ruido() * (1.08 if semana.month in (12, 1, 2) else 1)  # energia no verão
    c_emb = qtd_prod * prod.custo_embalagem_base * inf * ruido()
    c_mo = qtd_prod * prod.custo_mao_obra_base * inf * ruido()
    total = c_mp + c_prod + c_emb + c_mo
    lotes.append((id_lote, f"L{semana:%y%m%d}-{prod.sku[4:]}", semana.date(), am, p, qtd_prod, qtd_boa, qtd_perdida,
                  round(perda_pct, 4), round(c_mp, 2), round(c_prod, 2), round(c_emb, 2), round(c_mo, 2),
                  round(total * qtd_perdida / qtd_prod, 2), round(total, 2)))
    id_lote += 1
fato_producao = pd.DataFrame(lotes, columns=[
    "id_lote", "codigo_lote", "data_producao", "ano_mes", "id_produto", "qtd_produzida", "qtd_aprovada", "qtd_perdida",
    "perda_pct", "custo_materia_prima", "custo_producao", "custo_embalagem", "custo_mao_obra", "custo_perdas", "custo_total_lote"])

# custo unitário por unidade APROVADA (perdas absorvidas) por produto/mês
cu = fato_producao.groupby(["ano_mes", "id_produto"]).agg(
    mp=("custo_materia_prima", "sum"), pr=("custo_producao", "sum"), em=("custo_embalagem", "sum"),
    mo=("custo_mao_obra", "sum"), tot=("custo_total_lote", "sum"), perd=("custo_perdas", "sum"),
    prod=("qtd_produzida", "sum"), boa=("qtd_aprovada", "sum")).reset_index()
for col, src in [("cu_materia_prima", "mp"), ("cu_producao", "pr"), ("cu_embalagem", "em"), ("cu_mao_obra", "mo")]:
    cu[col] = cu[src] / cu["prod"]          # custo "limpo" por unidade produzida
cu["cu_perdas"] = cu["perd"] / cu["boa"]     # rateio da perda sobre unidades boas
fato_vendas = fato_vendas.merge(cu[["ano_mes", "id_produto", "cu_materia_prima", "cu_producao", "cu_embalagem", "cu_mao_obra", "cu_perdas"]],
                                on=["ano_mes", "id_produto"], how="left")

# --------------------------------------------------------------------------
# Preços, impostos, frete e custos por linha de venda
# --------------------------------------------------------------------------
P = dim_produto.set_index("id_produto")
C = dim_canal.set_index("id_canal")
R = dim_regiao.set_index("id_regiao")
q = fato_vendas.quantidade
# reajuste de preço: +6% jul/24, +9% fev/25, +7% ago/25 (repasse da alta do café)
dt = pd.to_datetime(fato_vendas.data)
reajuste = np.select([dt >= "2025-08-01", dt >= "2025-02-01", dt >= "2024-07-01"],
                     [1.06 * 1.09 * 1.07, 1.06 * 1.09, 1.06], 1.0)
revenda = P.loc[fato_vendas.id_produto, "preco_revenda_sugerido"].values * reajuste
preco = revenda * C.loc[fato_vendas.id_canal, "fator_preco"].values
desc_pct = np.clip(rng.normal(C.loc[fato_vendas.id_canal, "desconto_medio_pct"].values, 0.02), 0, 0.20)
# promoções de Black Friday no e-commerce
bf = (dt.dt.month == 11) & (dt.dt.day >= 20) & (fato_vendas.id_canal == 1)
desc_pct = np.where(bf, desc_pct + 0.15, desc_pct)

fato_vendas["preco_revenda_unit"] = revenda.round(2)
fato_vendas["preco_venda_unit"] = preco.round(2)
fato_vendas["receita_bruta"] = (q * fato_vendas.preco_venda_unit).round(2)
fato_vendas["desconto"] = (fato_vendas.receita_bruta * desc_pct).round(2)
fato_vendas["impostos"] = ((fato_vendas.receita_bruta - fato_vendas.desconto) * 0.1825).round(2)  # ICMS+PIS/COFINS simplificado
fato_vendas["receita_liquida"] = (fato_vendas.receita_bruta - fato_vendas.desconto - fato_vendas.impostos).round(2)
fato_vendas["receita_revenda"] = (q * fato_vendas.preco_revenda_unit).round(2)  # quanto o revendedor fatura (preço ao consumidor)

for col in ["materia_prima", "producao", "embalagem", "mao_obra", "perdas"]:
    fato_vendas[f"custo_{col}"] = (q * fato_vendas[f"cu_{col}"]).round(2)
    fato_vendas.drop(columns=f"cu_{col}", inplace=True)

peso_kg = q * P.loc[fato_vendas.id_produto, "peso_g"].values / 1000 * 1.12  # + caixa/pallet
frete_kg = R.loc[fato_vendas.id_regiao, "frete_por_kg"].values
taxa_fixa = np.where(fato_vendas.id_canal == 1, 9.0, 4.0)  # e-commerce: despacho por pacote
fato_vendas["peso_kg"] = peso_kg.round(3)
fato_vendas["custo_transporte"] = (peso_kg * frete_kg * rng.normal(1, 0.08, len(q)) +
                                   taxa_fixa / fato_vendas.groupby("id_pedido").id_venda.transform("count")).round(2)

# --------------------------------------------------------------------------
# fato_marketing  (investimento mensal por mídia e linha)
# --------------------------------------------------------------------------
midias = [("Instagram Ads", "Digital", 0.26, 0.012, 0.025), ("Google Ads", "Digital", 0.24, 0.035, 0.045),
          ("Influenciadores", "Digital", 0.14, 0.018, 0.020), ("E-mail Marketing", "Digital", 0.04, 0.060, 0.050),
          ("Trade Marketing (PDV)", "Offline", 0.20, 0.0, 0.0), ("Feiras e Eventos", "Offline", 0.12, 0.0, 0.0)]
linhas_prod = dim_produto.groupby("linha")._mix.sum()
receita_mes = fato_vendas.groupby("ano_mes").receita_bruta.sum()
mkt, id_m = [], 1
for am, rec in receita_mes.items():
    verba = rec * rng.uniform(0.055, 0.075)  # ~6,5% da receita bruta
    if am.endswith("-11"):
        verba *= 1.35
    for nome, tipo, share, ctr, conv in midias:
        for linha, lshare in linhas_prod.items():
            inv = verba * share * lshare * rng.normal(1, 0.12)
            if nome == "Feiras e Eventos" and am[-2:] not in ("03", "05", "08", "10"):
                continue
            cpm = {"Instagram Ads": 18, "Google Ads": 32, "Influenciadores": 25, "E-mail Marketing": 4}.get(nome)
            imp = int(inv / cpm * 1000 * rng.normal(1, 0.1)) if cpm else 0
            cli = int(imp * ctr * rng.normal(1, 0.15)) if cpm else 0
            convs = int(cli * conv * rng.normal(1, 0.2)) if cpm else 0
            mkt.append((id_m, f"{am}-01", am, nome, tipo, linha, round(max(inv, 0), 2), imp, cli, convs))
            id_m += 1
fato_marketing = pd.DataFrame(mkt, columns=["id_marketing", "data", "ano_mes", "midia", "tipo_midia", "linha",
                                            "investimento", "impressoes", "cliques", "conversoes"])
fato_marketing.insert(5, "id_linha", fato_marketing.linha.map(dict(zip(dim_linha.linha, dim_linha.id_linha))))
fato_marketing = fato_marketing.drop(columns="linha")

# --------------------------------------------------------------------------
# fato_perdas  (produção + armazenagem + transporte, com motivo)
# --------------------------------------------------------------------------
motivos_prod = ["Torra fora do padrão", "Falha na selagem", "Granulometria incorreta", "Contaminação/Umidade", "Setup de máquina"]
perdas, id_p = [], 1
for _, l in fato_producao.iterrows():
    if l.qtd_perdida <= 0:
        continue
    cu_lote = l.custo_total_lote / l.qtd_produzida
    perdas.append((id_p, l.data_producao, l.id_produto, "Produção", rng.choice(motivos_prod, p=[.32, .25, .15, .08, .20]),
                   int(l.qtd_perdida), round(l.custo_perdas, 2), l.id_lote))
    id_p += 1
# armazenagem (vencimento) e avarias de transporte: amostra de vendas
amostra = fato_vendas.sample(frac=0.03, random_state=SEED)
for _, v in amostra.iterrows():
    etapa = rng.choice(["Transporte", "Armazenagem"], p=[0.65, 0.35])
    motivo = rng.choice(["Avaria no transporte", "Extravio"], p=[.85, .15]) if etapa == "Transporte" else \
             rng.choice(["Vencimento", "Embalagem danificada no estoque"], p=[.6, .4])
    qtd = max(1, int(v.quantidade * rng.uniform(0.02, 0.12)))
    cu_v = (v.custo_materia_prima + v.custo_producao + v.custo_embalagem + v.custo_mao_obra) / v.quantidade
    perdas.append((id_p, v.data, v.id_produto, etapa, motivo, qtd, round(qtd * cu_v, 2), None))
    id_p += 1
fato_perdas = pd.DataFrame(perdas, columns=["id_perda", "data", "id_produto", "etapa", "motivo", "quantidade", "custo_perda", "id_lote"])
fato_perdas["id_lote"] = fato_perdas.id_lote.astype("Int64")

# --------------------------------------------------------------------------
# Exportação
# --------------------------------------------------------------------------
dim_produto = dim_produto.drop(columns=["_mix", "linha"])
dim_canal = dim_canal.drop(columns="_peso")
dim_regiao = dim_regiao.drop(columns="_peso")
fato_vendas = fato_vendas.drop(columns="ano_mes")

tabelas = {
    "dim_calendario": dim_calendario, "dim_produto": dim_produto, "dim_canal": dim_canal,
    "dim_regiao": dim_regiao, "dim_cliente": dim_cliente, "dim_linha": dim_linha,
    "fato_vendas": fato_vendas, "fato_producao": fato_producao, "fato_perdas": fato_perdas,
    "fato_marketing": fato_marketing, "fato_preco_materia_prima": fato_preco_mp,
}
for nome, df in tabelas.items():
    df.to_csv(OUT / f"{nome}.csv", index=False, encoding="utf-8")
with pd.ExcelWriter(OUT / "cafe_serra_alta.xlsx", engine="openpyxl") as xw:
    for nome, df in tabelas.items():
        df2 = df.copy()
        for col in df2.columns:
            if col.startswith("data") or col == "cliente_desde":
                df2[col] = pd.to_datetime(df2[col])
        df2.to_excel(xw, sheet_name=nome, index=False)

for nome, df in tabelas.items():
    print(f"{nome:28s} {len(df):>7,} linhas")
