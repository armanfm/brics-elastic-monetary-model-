import numpy as np
import matplotlib.pyplot as plt

# =============================
# CONFIG GERAL
# =============================

dias = 252 * 5
simulacoes = 300
anos = dias / 252

# BRICS (seu motor)
alpha = 0.5
k = 2

lambda_fator = 0.75  # controla concentração dos pesos por PIB (sem beta_capital)

vol_espec_base = 0.04
intensidade_espec_base = 0.6
vol_ativos_base = 0.10

# Adoção
g_adocao = 0.02
t0_adocao = dias / 2

def curva_adocao(t):
    return 1.0 / (1.0 + np.exp(-g_adocao * (t - t0_adocao)))

# =============================
# DADOS BRICS-10 (PIB nominal ~ ordem de grandeza atual, USD trilhões)
# =============================

pib = {
    "CH": 18.0,
    "IN": 3.7,
    "RU": 2.2,
    "BR": 2.1,
    "ZA": 0.4,
    "EG": 0.4,
    "ET": 0.15,
    "IR": 0.6,
    "SAU": 1.1,
    "UAE": 0.5
}

# Capital coerente (estoque proxy = 3x PIB)
capital_inicial = {pais: pib[pais] * 3.0 for pais in pib}

# Supply proporcional ao tamanho econômico (escala)
supply = sum(capital_inicial.values()) / 2.0

# =============================
# FIAT "PREVISÍVEL" (HIPÓTESE EXPLÍCITA)
# =============================
# Aqui NÃO tem mentira: isto é hipótese paramétrica.
# Você pode ajustar livremente.
usd_mu_anual, usd_sigma_anual = 0.025, 0.06   # ex: ~2.5% a.a., vol anual 6%
eur_mu_anual, eur_sigma_anual = 0.020, 0.07   # ex: ~2.0% a.a., vol anual 7%

# =============================
# PESOS (SEM beta_capital)
# =============================

def pesos_por_pib(pib_dict):
    base = {p: pib_dict[p] ** lambda_fator for p in pib_dict}
    s = sum(base.values())
    return {p: base[p] / s for p in base}

# =============================
# SIMULAÇÃO BRICS (SEU MODELO)
# =============================

def simular_brics_path(seed, nivel_adocao):

    rng = np.random.default_rng(seed)

    capital = capital_inicial.copy()
    ativos = sum(capital.values())

    preco0 = ativos / supply
    preco = preco0

    path = []

    # métricas internas
    hhi_list = []
    pesos_acum = {p: 0.0 for p in pib}

    for t in range(dias):

        A_t = curva_adocao(t) * nivel_adocao
        eficiencia = 0.002 * A_t  # até +0.2% a.a.

        # crescimento do capital (seu estilo)
        for pais in capital:
            crescimento = 0.03 + eficiencia + 0.01 * rng.normal()
            capital[pais] *= np.exp(crescimento / 252)

        # pesos dependem só do PIB (fixos no tempo)
        w = pesos_por_pib(pib)

        for p in w:
            pesos_acum[p] += w[p]

        # HHI
        hhi_list.append(sum(v**2 for v in w.values()))

        # drift do bloco (seu formato, sem inventar nada além do que já estava)
        drift_bloco = 0.02 + 0.01 * w.get("CH", 0.0) + 0.005 * w.get("IN", 0.0) + eficiencia

        # adoção reduz vol real e espec
        vol_ativos = vol_ativos_base * (1 - 0.3 * A_t)
        vol_espec = vol_espec_base * (1 - 0.7 * A_t)
        intensidade_espec = intensidade_espec_base * (1 - 0.7 * A_t)

        # ativos evoluem (seu motor)
        ativos *= np.exp(rng.normal(drift_bloco/252, vol_ativos/np.sqrt(252)))

        fund = ativos / supply

        # especulação + mistura
        preco_espec = preco * np.exp(rng.normal(0, vol_espec))
        preco_misto = intensidade_espec * preco_espec + (1 - intensidade_espec) * preco

        # reconvergência
        preco_aj = preco_misto * (fund / preco_misto) ** k
        preco = (1 - alpha) * preco_misto + alpha * preco_aj

        path.append(preco / preco0)

    pesos_medios = {p: pesos_acum[p] / dias for p in pesos_acum}
    hhi_medio = float(np.mean(hhi_list))

    return np.array(path), pesos_medios, hhi_medio

# =============================
# SIMULAÇÃO FIAT (HIPÓTESE PREVISÍVEL)
# =============================

def simular_fiat_path(seed, mu_anual, sigma_anual):

    rng = np.random.default_rng(seed)
    preco = 1.0
    path = []

    mu_d = mu_anual / 252
    sig_d = sigma_anual / np.sqrt(252)

    for t in range(dias):
        preco *= np.exp(rng.normal(mu_d, sig_d))
        path.append(preco)

    return np.array(path)

# =============================
# MÉTRICAS
# =============================

def metricas(series):
    r = np.diff(np.log(series))
    ret_anual = np.mean(r) * 252
    vol_anual = np.std(r) * np.sqrt(252)
    sharpe = ret_anual / vol_anual if vol_anual > 1e-12 else np.nan

    peak = np.maximum.accumulate(series)
    dd = (series / peak) - 1.0
    mdd = np.min(dd)

    var95 = np.percentile(r, 5)
    es95 = r[r <= var95].mean() if np.any(r <= var95) else np.nan

    return ret_anual, vol_anual, sharpe, mdd, var95, es95

# =============================
# EXECUÇÃO MONTE CARLO
# =============================

niveis_adocao = [0.0, 0.25, 0.5, 0.75, 1.0]

resultados = []  # por adoção
pesos_percentuais_final = None  # para print
hhi_const = None

print("\n============================================================")
print("MONTE CARLO - BRICS (restritivo) vs FIAT (hipótese previsível)")
print("============================================================")
print(f"FIAT hipóteses: USD mu={usd_mu_anual:.3f} sigma={usd_sigma_anual:.3f} | EUR mu={eur_mu_anual:.3f} sigma={eur_sigma_anual:.3f}")
print("Obs: mu/sigma FIAT são hipótese explícita (ajustável), não 'verdade escondida'.")
print("============================================================")

for nivel in niveis_adocao:

    br_m = []
    us_m = []
    eu_m = []

    out_usd = 0
    out_eur = 0

    pesos_totais = {p: 0.0 for p in pib}
    hhi_vals = []

    for i in range(simulacoes):

        br, pesos_medios, hhi_m = simular_brics_path(i, nivel)
        us = simular_fiat_path(i, usd_mu_anual, usd_sigma_anual)
        eu = simular_fiat_path(i, eur_mu_anual, eur_sigma_anual)

        br_m.append(metricas(br))
        us_m.append(metricas(us))
        eu_m.append(metricas(eu))

        if br[-1] > us[-1]:
            out_usd += 1
        if br[-1] > eu[-1]:
            out_eur += 1

        for p in pesos_medios:
            pesos_totais[p] += pesos_medios[p]
        hhi_vals.append(hhi_m)

    br_m = np.array(br_m)
    us_m = np.array(us_m)
    eu_m = np.array(eu_m)

    def resumo(arr):
        return {
            "ret_anual": float(np.mean(arr[:,0])),
            "vol_anual": float(np.mean(arr[:,1])),
            "sharpe": float(np.mean(arr[:,2])),
            "max_dd": float(np.mean(arr[:,3])),
            "VaR95_d": float(np.mean(arr[:,4])),
            "ES95_d": float(np.mean(arr[:,5])),
        }

    rB = resumo(br_m)
    rU = resumo(us_m)
    rE = resumo(eu_m)

    hhi_medio = float(np.mean(hhi_vals))
    pesos_percentuais = {p: (pesos_totais[p] / simulacoes) * 100 for p in pesos_totais}

    resultados.append({
        "adocao": nivel,
        "BRICS": rB,
        "USD": rU,
        "EUR": rE,
        "prob_gt_usd": out_usd / simulacoes,
        "prob_gt_eur": out_eur / simulacoes,
        "hhi": hhi_medio,
        "pesos_pct": pesos_percentuais
    })

    print(f"\n=== Adoção = {nivel} ===")
    print("BRICS:", {k: round(v,4) for k,v in rB.items()})
    print("USD  :", {k: round(v,4) for k,v in rU.items()})
    print("EUR  :", {k: round(v,4) for k,v in rE.items()})
    print("Prob BRICS > USD:", round(out_usd/simulacoes, 3))
    print("Prob BRICS > EUR:", round(out_eur/simulacoes, 3))
    print("HHI médio:", round(hhi_medio, 3))

# =============================
# IMPRIMIR PESOS % (fixos) UMA VEZ
# =============================

print("\n============================================================")
print("PESOS PERCENTUAIS MÉDIOS DO BLOCO (por PIB^lambda)")
print("============================================================")
pesos0 = resultados[0]["pesos_pct"]
for pais, peso in sorted(pesos0.items(), key=lambda x: -x[1]):
    print(f"{pais}: {peso:.2f}%")
print("HHI:", round(resultados[0]["hhi"], 3))

# =============================
# GRÁFICOS (SEM PLACEHOLDER)
# =============================

adocoes = [r["adocao"] for r in resultados]

br_ret = [r["BRICS"]["ret_anual"]*100 for r in resultados]
us_ret = [r["USD"]["ret_anual"]*100 for r in resultados]
eu_ret = [r["EUR"]["ret_anual"]*100 for r in resultados]

br_vol = [r["BRICS"]["vol_anual"]*100 for r in resultados]
us_vol = [r["USD"]["vol_anual"]*100 for r in resultados]
eu_vol = [r["EUR"]["vol_anual"]*100 for r in resultados]

p_usd = [r["prob_gt_usd"]*100 for r in resultados]
p_eur = [r["prob_gt_eur"]*100 for r in resultados]

hhi = [r["hhi"] for r in resultados]
china = [r["pesos_pct"]["CH"] for r in resultados]

plt.figure(figsize=(16, 5))

plt.subplot(1, 3, 1)
plt.plot(adocoes, br_ret, marker='o', label="BRICS")
plt.plot(adocoes, us_ret, marker='s', label="USD")
plt.plot(adocoes, eu_ret, marker='^', label="EUR")
plt.xlabel("Adoção")
plt.ylabel("Retorno anual médio (%)")
plt.title("Retorno anual (Monte Carlo)")
plt.grid(True, alpha=0.3)
plt.legend()

plt.subplot(1, 3, 2)
plt.plot(adocoes, p_usd, marker='s', label="Prob BRICS > USD")
plt.plot(adocoes, p_eur, marker='^', label="Prob BRICS > EUR")
plt.axhline(50, linestyle='--', alpha=0.5)
plt.xlabel("Adoção")
plt.ylabel("Probabilidade (%)")
plt.title("Chance de outperform")
plt.grid(True, alpha=0.3)
plt.legend()

plt.subplot(1, 3, 3)
plt.plot(adocoes, hhi, marker='o', label="HHI")
plt.plot(adocoes, china, marker='s', label="China (%)")
plt.xlabel("Adoção")
plt.title("Concentração do bloco")
plt.grid(True, alpha=0.3)
plt.legend()

plt.tight_layout()
plt.show()
