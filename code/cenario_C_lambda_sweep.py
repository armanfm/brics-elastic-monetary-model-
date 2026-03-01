import numpy as np
import matplotlib.pyplot as plt

# =============================
# CONFIG
# =============================

dias = 252 * 5
simulacoes = 150
shock_day = dias // 2

alpha = 0.5
k = 2.0

mu_cap = 0.04
sigma_cap_base = 0.12
sigma_spec_base = 0.01

shock_drop = 0.40
vol_spike_multiplier = 2
vol_spike_days = 60

shock_subset = ["CH"]  # choque no núcleo dominante

# =============================
# DADOS BRICS
# =============================

pib = {
    "CH": 18.0, "IN": 3.7, "RU": 2.2, "BR": 2.1,
    "ZA": 0.4, "EG": 0.4, "ET": 0.15, "IR": 0.6,
    "SAU": 1.1, "UAE": 0.5
}

capital_base = {p: pib[p] * 3.0 for p in pib}
supply = sum(capital_base.values()) / 2.0

# =============================
# MÉTRICAS
# =============================

def annual_vol(series):
    r = np.diff(np.log(series))
    return np.std(r) * np.sqrt(252)

def max_dd(series):
    peak = np.maximum.accumulate(series)
    return np.min((series - peak) / peak)

# =============================
# LAMBDA SWEEP
# =============================

lambda_values = np.linspace(0.3, 1.2, 10)

vol_results = []
mdd_results = []
china_weights = []

for lambda_fator in lambda_values:

    # calcular pesos
    base = {p: pib[p] ** lambda_fator for p in pib}
    s = sum(base.values())
    w = {p: base[p] / s for p in base}

    china_weights.append(w["CH"])

    vols = []
    mdds = []

    for sim in range(simulacoes):

        rng = np.random.default_rng(sim)
        capital = capital_base.copy()
        P_elastic = 1.0
        path = []

        for t in range(dias):

            sigma_cap = sigma_cap_base
            sigma_spec = sigma_spec_base

            if t == shock_day:
                for pais in shock_subset:
                    capital[pais] *= (1 - shock_drop)

            if shock_day <= t < shock_day + vol_spike_days:
                sigma_cap *= vol_spike_multiplier
                sigma_spec *= vol_spike_multiplier

            for pais in capital:
                capital[pais] *= np.exp(
                    rng.normal(mu_cap/252, sigma_cap/np.sqrt(252))
                )

            C_eff = sum(w[p] * capital[p] for p in capital)
            P_fund = C_eff / supply

            eps = rng.normal(0, sigma_spec)
            P_spec = P_elastic * np.exp(eps)

            P_adj = P_spec * (P_fund / P_spec) ** k
            P_elastic = (1 - alpha) * P_spec + alpha * P_adj

            path.append(P_elastic)

        path = np.array(path)

        vols.append(annual_vol(path))
        mdds.append(max_dd(path))

    vol_results.append(np.mean(vols))
    mdd_results.append(np.mean(mdds))

# =============================
# PLOT
# =============================

plt.figure(figsize=(10,5))

plt.subplot(1,2,1)
plt.plot(lambda_values, vol_results, marker='o')
plt.xlabel("λ")
plt.ylabel("Volatilidade")
plt.title("Volatilidade vs λ (Choque China)")
plt.grid(True)

plt.subplot(1,2,2)
plt.plot(lambda_values, mdd_results, marker='o')
plt.xlabel("λ")
plt.ylabel("Max Drawdown")
plt.title("Drawdown vs λ (Choque China)")
plt.grid(True)

plt.tight_layout()
plt.savefig("cenario_C_lambda_sweep.png", dpi=300, bbox_inches="tight")
plt.savefig("cenario_C_lambda_sweep.pdf", bbox_inches="tight")
plt.show()
