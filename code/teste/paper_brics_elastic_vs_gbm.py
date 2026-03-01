# paper_brics_elastic_vs_gbm.py
# Reproduz os testes do paper:
# - Choque Macro (30% em 5 países, sem spike)
# - Crise 2008-style (40% em 5 países + spike 60 dias com 2x em σ_cap e σ_spec)
# - BRICS Elástico vs GBM Macro vs GBM Puro
# - Figuras 1–10 e tabela consolidada

import os
import numpy as np
import matplotlib.pyplot as plt

# =============================
# CONFIG DO PAPER
# =============================
T_DIAS = 252 * 6            # 6 anos -> 1512
N_MC = 200                  # Monte Carlo
SHOCK_DAY = 756             # meio do horizonte (3º ano)
SPIKE_DAYS = 60             # 60 dias no cenário 2008
MU_CAP = 0.04               # µ_cap=4% a.a.
SIGMA_CAP = 0.12            # σ_cap=12% a.a.
SIGMA_SPEC = 0.05           # σ_spec=0.05 diário (multiplicativo)
ALPHA = 0.5
K = 2.0

# GBMs do paper
GBM_PURE_MU = 0.05          # µ=5% a.a.
GBM_PURE_SIGMA = 0.80       # σ=80% a.a.

# subconjunto fixo de 5 países (o paper fala subconjunto fixo; usamos os 5 primeiros abaixo)
BRICS_PIB = {
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
BRICS_ORDER = ["CH", "IN", "RU", "BR", "ZA", "EG", "ET", "IR", "SAU", "UAE"]
SHOCK_SET = set(BRICS_ORDER[:5])  # 5 países

OUTDIR = "figs_paper"
os.makedirs(OUTDIR, exist_ok=True)

# =============================
# MÉTRICAS
# =============================

def annualized_vol(series: np.ndarray) -> float:
    r = np.diff(np.log(series))
    return float(np.std(r) * np.sqrt(252))

def max_drawdown(series: np.ndarray) -> float:
    peak = np.maximum.accumulate(series)
    dd = series / peak - 1.0
    return float(np.min(dd))

def time_to_recover_peak(series: np.ndarray, shock_day: int) -> int:
    pre_peak = float(np.max(series[:shock_day])) if shock_day > 1 else float(series[0])
    post = series[shock_day:]
    idx = np.where(post >= pre_peak)[0]
    return int(idx[0]) if idx.size > 0 else -1

def time_to_reanchor(series: np.ndarray, fund: np.ndarray, shock_day: int, band: float = 0.05) -> int:
    err = np.abs(series - fund) / (fund + 1e-12)
    post = err[shock_day:]
    idx = np.where(post <= band)[0]
    return int(idx[0]) if idx.size > 0 else -1

def half_life_error(series: np.ndarray, fund: np.ndarray, shock_day: int) -> int:
    err = np.abs(series - fund) / (fund + 1e-12)
    e0 = float(err[shock_day])
    if e0 < 1e-12:
        return 0
    post = err[shock_day:]
    idx = np.where(post <= 0.5 * e0)[0]
    return int(idx[0]) if idx.size > 0 else -1

def mean_error(series: np.ndarray, fund: np.ndarray) -> float:
    err = np.abs(series - fund) / (fund + 1e-12)
    return float(np.mean(err))

def summarize_recovery(vals: np.ndarray) -> float:
    ok = vals[vals >= 0]
    return float(np.mean(ok)) if ok.size > 0 else -1.0

# =============================
# SIMULAÇÃO: BRICS ELÁSTICO (paper)
# =============================

def init_capital_and_supply() -> tuple[np.ndarray, float]:
    cap0 = np.array([3.0 * BRICS_PIB[c] for c in BRICS_ORDER], dtype=float)  # proxy = 3×PIB
    supply = float(np.sum(cap0) / 2.0)                                      # supply = metade do capital inicial agregado
    return cap0, supply

def simulate_brics_elastic(seed: int, shock_drop: float, spike: bool) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    cap, supply = init_capital_and_supply()

    P = float(np.sum(cap) / supply)
    series = np.empty(T_DIAS, dtype=float)
    fund = np.empty(T_DIAS, dtype=float)

    for t in range(T_DIAS):
        # choque no capital (aplica no dia do choque)
        if t == SHOCK_DAY:
            for i, c in enumerate(BRICS_ORDER):
                if c in SHOCK_SET:
                    cap[i] *= (1.0 - shock_drop)

        # spike 2008-style
        in_spike = spike and (SHOCK_DAY <= t < SHOCK_DAY + SPIKE_DAYS)
        sigma_cap_t = SIGMA_CAP * (2.0 if in_spike else 1.0)
        sigma_spec_t = SIGMA_SPEC * (2.0 if in_spike else 1.0)

        # evolução do capital (GBM por país)
        mu_d = MU_CAP / 252.0
        sig_d = sigma_cap_t / np.sqrt(252.0)
        z = rng.normal(size=cap.shape[0])
        cap *= np.exp((mu_d - 0.5 * sig_d**2) + sig_d * z)

        F = float(np.sum(cap) / supply)

        # componente especulativa
        eps = rng.normal(0.0, sigma_spec_t)
        P_spec = P * float(np.exp(eps))

        # reconvergência elástica
        P_adj = P_spec * (F / (P_spec + 1e-12)) ** K
        P = (1.0 - ALPHA) * P_spec + ALPHA * P_adj

        series[t] = P
        fund[t] = F

    # normaliza para começar em 1 (padrão do paper em figuras)
    series = series / series[0]
    fund = fund / fund[0]
    return series, fund

# =============================
# SIMULAÇÃO: GBM MACRO / PURO (paper)
# =============================

def simulate_gbm(seed: int, mu: float, sigma: float, shock_drop: float, spike: bool) -> np.ndarray:
    rng = np.random.default_rng(seed)
    P = 1.0
    series = np.empty(T_DIAS, dtype=float)

    for t in range(T_DIAS):
        if t == SHOCK_DAY:
            P *= (1.0 - shock_drop)

        in_spike = spike and (SHOCK_DAY <= t < SHOCK_DAY + SPIKE_DAYS)
        sigma_t = sigma * (2.0 if in_spike else 1.0)

        mu_d = mu / 252.0
        sig_d = sigma_t / np.sqrt(252.0)
        z = rng.normal()
        P *= np.exp((mu_d - 0.5 * sig_d**2) + sig_d * z)
        series[t] = P

    series = series / series[0]
    return series

# =============================
# EXPERIMENTOS DO PAPER
# =============================

def run_scenario(name: str, shock_drop: float, spike: bool) -> dict:
    # coleta métricas por modelo
    vol_el, mdd_el, rec_el, reac_el, hl_el, err_el = [], [], [], [], [], []
    vol_gm, mdd_gm, rec_gm = [], [], []
    vol_gp, mdd_gp, rec_gp = [], [], []

    # salva uma trajetória exemplo
    example_seed = 7
    ex_el, ex_f = simulate_brics_elastic(example_seed, shock_drop=shock_drop, spike=spike)
    ex_gm = simulate_gbm(example_seed, mu=MU_CAP, sigma=SIGMA_CAP, shock_drop=shock_drop, spike=spike)
    ex_gp = simulate_gbm(example_seed, mu=GBM_PURE_MU, sigma=GBM_PURE_SIGMA, shock_drop=shock_drop, spike=spike)

    for i in range(N_MC):
        s_el, f_el = simulate_brics_elastic(i, shock_drop=shock_drop, spike=spike)
        s_gm = simulate_gbm(i, mu=MU_CAP, sigma=SIGMA_CAP, shock_drop=shock_drop, spike=spike)
        s_gp = simulate_gbm(i, mu=GBM_PURE_MU, sigma=GBM_PURE_SIGMA, shock_drop=shock_drop, spike=spike)

        vol_el.append(annualized_vol(s_el))
        mdd_el.append(max_drawdown(s_el))
        rec_el.append(time_to_recover_peak(s_el, SHOCK_DAY))
        reac_el.append(time_to_reanchor(s_el, f_el, SHOCK_DAY, band=0.05))
        hl_el.append(half_life_error(s_el, f_el, SHOCK_DAY))
        err_el.append(mean_error(s_el, f_el))

        vol_gm.append(annualized_vol(s_gm))
        mdd_gm.append(max_drawdown(s_gm))
        rec_gm.append(time_to_recover_peak(s_gm, SHOCK_DAY))

        vol_gp.append(annualized_vol(s_gp))
        mdd_gp.append(max_drawdown(s_gp))
        rec_gp.append(time_to_recover_peak(s_gp, SHOCK_DAY))

    return {
        "name": name,
        "example": (ex_el, ex_f, ex_gm, ex_gp),
        "elastic": {
            "vol": np.array(vol_el),
            "mdd": np.array(mdd_el),
            "rec_peak": np.array(rec_el),
            "rec_fund5": np.array(reac_el),
            "half_life": np.array(hl_el),
            "mean_err": np.array(err_el),
        },
        "gbm_macro": {
            "vol": np.array(vol_gm),
            "mdd": np.array(mdd_gm),
            "rec_peak": np.array(rec_gm),
        },
        "gbm_pure": {
            "vol": np.array(vol_gp),
            "mdd": np.array(mdd_gp),
            "rec_peak": np.array(rec_gp),
        }
    }

def plot_trajectories(fig_path: str, title: str, s_el, s_gm, s_gp):
    plt.figure(figsize=(10, 4))
    plt.plot(s_el, label="BRICS Elástico")
    plt.plot(s_gm, label="GBM Macro")
    plt.plot(s_gp, label="GBM Puro", alpha=0.85)
    plt.axvline(SHOCK_DAY, linestyle="--", alpha=0.7)
    plt.title(title)
    plt.xlabel("Dias")
    plt.ylabel("Preço (normalizado)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=200)
    plt.close()

def plot_price_vs_fund(fig_path: str, title: str, s_el, f_el):
    plt.figure(figsize=(10, 4))
    plt.plot(s_el, label="Preço (BRICS Elástico)")
    plt.plot(f_el, label="Fundamental agregado")
    plt.axvline(SHOCK_DAY, linestyle="--", alpha=0.7)
    plt.title(title)
    plt.xlabel("Dias")
    plt.ylabel("Normalizado (início=1)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=200)
    plt.close()

def plot_bar_mean_std(fig_path: str, title: str, labels, arrays, ylabel):
    means = [float(np.mean(a)) for a in arrays]
    stds = [float(np.std(a)) for a in arrays]
    x = np.arange(len(labels))
    plt.figure(figsize=(8, 4))
    plt.bar(x, means, yerr=stds, capsize=4)
    plt.xticks(x, labels)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=200)
    plt.close()

def plot_stability_region(fig_path: str):
    # Figura 9 — região 0 < αk < 2
    alphas = np.linspace(0.05, 1.0, 300)
    k_max = 2.0 / alphas
    plt.figure(figsize=(8, 4))
    plt.fill_between(alphas, 0, np.minimum(k_max, 6.0), alpha=0.25, label="Região estável (0 < αk < 2)")
    plt.plot(alphas, k_max, label="Borda αk=2")
    plt.ylim(0, 6.0)
    plt.xlim(0.05, 1.0)
    plt.title("Região teórica de estabilidade local: 0 < αk < 2")
    plt.xlabel("α")
    plt.ylabel("k")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=200)
    plt.close()

def empirical_instability_probability(alpha: float, k: float, n: int = 60) -> float:
    # Figura 10 — max erro > 20% sob Crise 2008-style
    global ALPHA, K
    ALPHA_OLD, K_OLD = ALPHA, K
    ALPHA, K = alpha, k
    bad = 0
    for i in range(n):
        s_el, f_el = simulate_brics_elastic(i, shock_drop=0.40, spike=True)
        err = np.abs(s_el - f_el) / (f_el + 1e-12)
        if float(np.max(err[SHOCK_DAY:])) > 0.20:
            bad += 1
    ALPHA, K = ALPHA_OLD, K_OLD
    return bad / n

def plot_instability_probs(fig_path: str):
    points = [
        ("Estável (αk=1.0)", 0.5, 2.0),
        ("Borda (αk=2.0)", 1.0, 2.0),
        ("Instável (αk=2.5)", 1.0, 2.5),
    ]
    probs = [empirical_instability_probability(a, k, n=60) for _, a, k in points]
    labels = [p[0] for p in points]
    plt.figure(figsize=(9, 4))
    plt.bar(labels, [100*p for p in probs])
    plt.title("Probabilidade empírica de instabilidade (max erro > 20%) — Crise 2008-style")
    plt.ylabel("Probabilidade (%)")
    plt.xticks(rotation=10, ha="right")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=200)
    plt.close()

def print_consolidated_table(res_macro: dict, res_2008: dict):
    # imprime a Tabela consolidada do paper (valores médios)
    def line(model_name: str, r: dict, is_elastic: bool):
        if is_elastic:
            vol = float(np.mean(r["vol"]))
            mdd = float(np.mean(r["mdd"]))
            rec_peak = summarize_recovery(r["rec_peak"])
            rec_fund = summarize_recovery(r["rec_fund5"])
            hl = summarize_recovery(r["half_life"])
            err = float(np.mean(r["mean_err"]))
            return (model_name, vol, mdd, rec_peak, rec_fund, hl, err)
        else:
            vol = float(np.mean(r["vol"]))
            mdd = float(np.mean(r["mdd"]))
            rec_peak = summarize_recovery(r["rec_peak"])
            return (model_name, vol, mdd, rec_peak)

    print("\n=== TABELA CONSOLIDADA (MÉDIAS) ===")
    print("Cenário | Modelo | Vol | MDD | Rec. pico | Rec. ≤5% fund | Half-life | Erro médio vs fund")

    for scen_name, res in [("Choque Macro", res_macro), ("Crise 2008-style", res_2008)]:
        e = line("BRICS Elástico", res["elastic"], True)
        gm = line("GBM Macro", res["gbm_macro"], False)
        gp = line("GBM Puro", res["gbm_pure"], False)

        print(f"{scen_name} | {e[0]} | {e[1]:.3f} | {e[2]:.3f} | {e[3]:.1f} | {e[4]:.1f} | {e[5]:.1f} | {e[6]:.4f}")
        print(f"{scen_name} | {gm[0]} | {gm[1]:.3f} | {gm[2]:.3f} | {gm[3]:.1f} | — | — | —")
        print(f"{scen_name} | {gp[0]} | {gp[1]:.3f} | {gp[2]:.3f} | {gp[3]:.1f} | — | — | —")

def main():
    # 1) Cenário Choque Macro (30% em 5 países, sem spike)
    res_macro = run_scenario("Choque Macro", shock_drop=0.30, spike=False)
    # 2) Cenário 2008-style (40% + spike 60 dias)
    res_2008 = run_scenario("Crise 2008-style", shock_drop=0.40, spike=True)

    # imprime tabela
    print_consolidated_table(res_macro, res_2008)

    # figuras do paper
    # Fig 1 e 2 (Choque Macro)
    ex_el, ex_f, ex_gm, ex_gp = res_macro["example"]
    plot_trajectories(
        os.path.join(OUTDIR, "Figura_1_ChoqueMacro_Trajetorias.png"),
        "Figura 1 — Choque Macro: BRICS Elástico vs GBM Macro vs GBM Puro",
        ex_el, ex_gm, ex_gp
    )
    plot_price_vs_fund(
        os.path.join(OUTDIR, "Figura_2_ChoqueMacro_Preco_vs_Fund.png"),
        "Figura 2 — Choque Macro: BRICS Elástico (preço) e fundamental agregado",
        ex_el, ex_f
    )

    # Fig 3 e 4 (2008)
    ex_el, ex_f, ex_gm, ex_gp = res_2008["example"]
    plot_trajectories(
        os.path.join(OUTDIR, "Figura_3_2008_Trajetorias.png"),
        "Figura 3 — Crise 2008-style: BRICS Elástico vs GBM Macro vs GBM Puro",
        ex_el, ex_gm, ex_gp
    )
    plot_price_vs_fund(
        os.path.join(OUTDIR, "Figura_4_2008_Preco_vs_Fund.png"),
        "Figura 4 — Crise 2008-style: BRICS Elástico (preço) e fundamental agregado",
        ex_el, ex_f
    )

    # Fig 5/6 volatilidade (média ± desvio)
    plot_bar_mean_std(
        os.path.join(OUTDIR, "Figura_5_Vol_ChoqueMacro.png"),
        "Figura 5 — Volatilidade anualizada (Choque Macro): média ± desvio padrão",
        ["BRICS Elástico", "GBM Macro", "GBM Puro"],
        [res_macro["elastic"]["vol"], res_macro["gbm_macro"]["vol"], res_macro["gbm_pure"]["vol"]],
        ylabel="Vol anualizada"
    )
    plot_bar_mean_std(
        os.path.join(OUTDIR, "Figura_6_Vol_2008.png"),
        "Figura 6 — Volatilidade anualizada (Crise 2008-style): média ± desvio padrão",
        ["BRICS Elástico", "GBM Macro", "GBM Puro"],
        [res_2008["elastic"]["vol"], res_2008["gbm_macro"]["vol"], res_2008["gbm_pure"]["vol"]],
        ylabel="Vol anualizada"
    )

    # Fig 7/8 max drawdown (média ± desvio)
    plot_bar_mean_std(
        os.path.join(OUTDIR, "Figura_7_MDD_ChoqueMacro.png"),
        "Figura 7 — Max drawdown (Choque Macro): média ± desvio padrão",
        ["BRICS Elástico", "GBM Macro", "GBM Puro"],
        [res_macro["elastic"]["mdd"], res_macro["gbm_macro"]["mdd"], res_macro["gbm_pure"]["mdd"]],
        ylabel="Max drawdown"
    )
    plot_bar_mean_std(
        os.path.join(OUTDIR, "Figura_8_MDD_2008.png"),
        "Figura 8 — Max drawdown (Crise 2008-style): média ± desvio padrão",
        ["BRICS Elástico", "GBM Macro", "GBM Puro"],
        [res_2008["elastic"]["mdd"], res_2008["gbm_macro"]["mdd"], res_2008["gbm_pure"]["mdd"]],
        ylabel="Max drawdown"
    )

    # Fig 9 (região teórica 0<αk<2)
    plot_stability_region(os.path.join(OUTDIR, "Figura_9_Regiao_Estabilidade.png"))

    # Fig 10 (prob instabilidade empírica)
    plot_instability_probs(os.path.join(OUTDIR, "Figura_10_Prob_Instabilidade.png"))

    print(f"\n✅ Figuras salvas em: ./{OUTDIR}/")

if __name__ == "__main__":
    main()
