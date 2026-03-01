# annex_lambda_brics_vs_fiat.py
# Reproduz o ANEXO do PDF:
# Sensibilidade ao parâmetro lambda no modelo BRICS vs FIAT (USD/EUR)
# - horizonte = 1260 dias (~5 anos)
# - simulações = 150 por combinação
# - alpha=0.5, k=2.0, vol_espec_base=0.04, intensidade=0.6, vol_ativos_base=0.1
# - adoção logística (curva) * nível (0, 0.5, 1.0)
# Gera:
# - tabela completa (CSV) e figuras 1–5 do anexo

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

OUTDIR = "figs_lambda_annex"
os.makedirs(OUTDIR, exist_ok=True)

# =============================
# CONFIG DO ANEXO
# =============================
dias = 252 * 5
simulacoes = 150

alpha = 0.5
k = 2.0

vol_espec_base = 0.04
intensidade_espec_base = 0.6
vol_ativos_base = 0.10

# adoção (mesma forma do seu script)
g_adocao = 0.02
t0_adocao = dias / 2

def curva_adocao(t):
    return 1.0 / (1.0 + np.exp(-g_adocao * (t - t0_adocao)))

# FIAT (hipótese explícita)
usd_mu_anual, usd_sigma_anual = 0.025, 0.06
eur_mu_anual, eur_sigma_anual = 0.020, 0.07

# BRICS-10 (mesma base)
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

capital_inicial = {pais: pib[pais] * 3.0 for pais in pib}
supply = sum(capital_inicial.values()) / 2.0

# =============================
# FUNÇÕES
# =============================

def pesos_por_pib(pib_dict, lambda_fator):
    base = {p: pib_dict[p] ** lambda_fator for p in pib_dict}
    s = sum(base.values())
    return {p: base[p] / s for p in base}

def hhi(w):
    return float(sum(v*v for v in w.values()))

def metricas(series):
    r = np.diff(np.log(series))
    ret_anual = float(np.mean(r) * 252)
    vol_anual = float(np.std(r) * np.sqrt(252))
    sharpe = float(ret_anual / vol_anual) if vol_anual > 1e-12 else np.nan
    peak = np.maximum.accumulate(series)
    dd = (series / peak) - 1.0
    mdd = float(np.min(dd))
    return ret_anual, vol_anual, sharpe, mdd

def simular_brics_path(seed, lambda_fator, nivel_adocao):
    rng = np.random.default_rng(seed)

    capital = capital_inicial.copy()
    ativos = sum(capital.values())

    preco0 = ativos / supply
    preco = preco0
    path = []

    for t in range(dias):
        A_t = curva_adocao(t) * nivel_adocao
        eficiencia = 0.002 * A_t  # até +0.2% a.a.

        # crescimento do capital (proxy)
        for pais in capital:
            crescimento = 0.03 + eficiencia + 0.01 * rng.normal()
            capital[pais] *= np.exp(crescimento / 252)

        # pesos por PIB^lambda
        w = pesos_por_pib(pib, lambda_fator)

        # drift do bloco (como seu modelo)
        drift_bloco = 0.02 + 0.01 * w.get("CH", 0.0) + 0.005 * w.get("IN", 0.0) + eficiencia

        # adoção reduz vol real e espec
        vol_ativos = vol_ativos_base * (1 - 0.3 * A_t)
        vol_espec = vol_espec_base * (1 - 0.7 * A_t)
        intensidade_espec = intensidade_espec_base * (1 - 0.7 * A_t)

        # evolução de "ativos" (motor)
        ativos *= np.exp(rng.normal(drift_bloco/252, vol_ativos/np.sqrt(252)))

        fund = ativos / supply

        # espec + mistura
        preco_espec = preco * np.exp(rng.normal(0, vol_espec))
        preco_misto = intensidade_espec * preco_espec + (1 - intensidade_espec) * preco

        # reconvergência
        preco_aj = preco_misto * (fund / preco_misto) ** k
        preco = (1 - alpha) * preco_misto + alpha * preco_aj

        path.append(preco / preco0)

    return np.array(path), w

def simular_fiat_path(seed, mu_anual, sigma_anual):
    rng = np.random.default_rng(seed)
    preco = 1.0
    path = []

    mu_d = mu_anual / 252
    sig_d = sigma_anual / np.sqrt(252)

    for _ in range(dias):
        preco *= np.exp(rng.normal(mu_d, sig_d))
        path.append(preco)

    return np.array(path)

def run_grid(lambda_vals, adocao_vals):
    rows = []
    for lam in lambda_vals:
        for ad in adocao_vals:
            # estatísticas BRICS
            br_m = []
            out_usd = 0
            out_eur = 0

            # HHI e China% (fixo dado λ)
            w0 = pesos_por_pib(pib, lam)
            hhi0 = hhi(w0)
            china_pct = 100.0 * w0.get("CH", 0.0)

            for i in range(simulacoes):
                br, _w = simular_brics_path(i, lam, ad)
                us = simular_fiat_path(i, usd_mu_anual, usd_sigma_anual)
                eu = simular_fiat_path(i, eur_mu_anual, eur_sigma_anual)

                br_m.append(metricas(br))

                if br[-1] > us[-1]:
                    out_usd += 1
                if br[-1] > eu[-1]:
                    out_eur += 1

            br_m = np.array(br_m)
            ret_m = float(np.mean(br_m[:,0]))
            vol_m = float(np.mean(br_m[:,1]))
            sharpe_m = float(np.mean(br_m[:,2]))
            mdd_m = float(np.mean(br_m[:,3]))

            rows.append({
                "lambda": lam,
                "adocao": ad,
                "HHI": hhi0,
                "China(%)": china_pct,
                "Vol_BRICS": vol_m,
                "MDD_BRICS": mdd_m,
                "Sharpe_BRICS": sharpe_m,
                "P(B>USD)": out_usd / simুলacoes,
                "P(B>EUR)": out_eur / simulações
            })
    return pd.DataFrame(rows)

def plots(df: pd.DataFrame, lambda_vals, adocao_vals):
    # Figura 1 - HHI vs lambda (adocao=0)
    d0 = df[df["adocao"] == 0.0].sort_values("lambda")
    plt.figure(figsize=(7,4))
    plt.plot(d0["lambda"], d0["HHI"], marker="o")
    plt.title("Figura 1 — HHI vs λ (adoção=0)")
    plt.xlabel("λ")
    plt.ylabel("HHI")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "Figura_1_HHI_vs_lambda.png"), dpi=200)
    plt.close()

    # Figura 2 - China (%) vs lambda (adocao=0)
    plt.figure(figsize=(7,4))
    plt.plot(d0["lambda"], d0["China(%)"], marker="o")
    plt.title("Figura 2 — China (%) vs λ (adoção=0)")
    plt.xlabel("λ")
    plt.ylabel("China (%)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "Figura_2_ChinaPct_vs_lambda.png"), dpi=200)
    plt.close()

    # Figura 3 - Volatilidade anualizada do BRICS vs lambda (por adocao)
    plt.figure(figsize=(7,4))
    for ad in adocao_vals:
        d = df[df["adocao"] == ad].sort_values("lambda")
        plt.plot(d["lambda"], d["Vol_BRICS"], marker="o", label=f"adoção={ad}")
    plt.title("Figura 3 — Volatilidade BRICS vs λ (por adoção)")
    plt.xlabel("λ")
    plt.ylabel("Vol anual")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "Figura_3_Vol_vs_lambda.png"), dpi=200)
    plt.close()

    # Figura 4 - Prob BRICS > USD no fim vs lambda (por adocao)
    plt.figure(figsize=(7,4))
    for ad in adocao_vals:
        d = df[df["adocao"] == ad].sort_values("lambda")
        plt.plot(d["lambda"], d["P(B>USD)"], marker="o", label=f"adoção={ad}")
    plt.title("Figura 4 — Prob(BRICS>USD) vs λ (por adoção)")
    plt.xlabel("λ")
    plt.ylabel("Probabilidade")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "Figura_4_Prob_vs_lambda.png"), dpi=200)
    plt.close()

    # Figura 5 - Sharpe médio vs lambda (por adocao)
    plt.figure(figsize=(7,4))
    for ad in adocao_vals:
        d = df[df["adocao"] == ad].sort_values("lambda")
        plt.plot(d["lambda"], d["Sharpe_BRICS"], marker="o", label=f"adoção={ad}")
    plt.title("Figura 5 — Sharpe BRICS vs λ (por adoção)")
    plt.xlabel("λ")
    plt.ylabel("Sharpe")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "Figura_5_Sharpe_vs_lambda.png"), dpi=200)
    plt.close()

def main():
    lambda_vals = [0.50, 0.75, 1.00, 1.25]
    adocao_vals = [0.0, 0.5, 1.0]

    df = run_grid(lambda_vals, adocao_vals)
    df = df.sort_values(["lambda", "adocao"]).reset_index(drop=True)

    csv_path = os.path.join(OUTDIR, "tabela_lambda_resultados.csv")
    df.to_csv(csv_path, index=False)

    print("\n=== ANEXO λ — RESULTADOS (primeiras linhas) ===")
    print(df.head(12).to_string(index=False))

    plots(df, lambda_vals, adocao_vals)

    print(f"\n✅ CSV: {csv_path}")
    print(f"✅ Figuras salvas em: ./{OUTDIR}/")

if __name__ == "__main__":
    main()
