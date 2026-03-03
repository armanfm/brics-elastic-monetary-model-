import numpy as np
import matplotlib.pyplot as plt

# ==============================
# CONFIG
# ==============================

T = 252 * 6                 # 6 anos
UPDATE_INTERVAL = 21        # mensal (~21 dias úteis)

ALPHA = 0.5
K = 2.0
LAMBDA = 0.5

# Capital real
MU_CAP = 0.04
SIGMA_CAP = 0.12

# Clearing
TRADE_INTENSITY = 0.25
V_NOISE = 0.20

# Supply rule
BETA_SUPPLY = 1.0
EMA_HALFLIFE_WINDOWS = 3
CAP_ANNUAL = 0.10
CAP_PER_WINDOW = CAP_ANNUAL / 12.0

# Preço especulativo
SIGMA_SPEC = 0.04

# ==============================
# DADOS BRICS-10 (proxy PIB)
# ==============================

PIB = {
    "CH": 18.0, "IN": 3.7, "RU": 2.2, "BR": 2.1,
    "ZA": 0.4, "EG": 0.4, "ET": 0.15, "IR": 0.6,
    "SAU": 1.1, "UAE": 0.5
}

countries = list(PIB.keys())

# Governança λ
w = np.array([PIB[c] ** LAMBDA for c in countries])
w /= w.sum()

HHI = np.sum(w*w)
print("HHI:", round(HHI,4))

# ==============================
# FUNÇÕES AUXILIARES
# ==============================

def ema_update(prev, x, alpha):
    return alpha * x + (1 - alpha) * prev

EMA_ALPHA = 1.0 - (0.5 ** (1.0 / EMA_HALFLIFE_WINDOWS))

rng = np.random.default_rng(42)

# ==============================
# INICIALIZAÇÃO
# ==============================

cap = np.array([3.0 * PIB[c] for c in countries])
C_report = float(np.sum(w * cap))
supply = C_report

P = 1.0

P_hist = []
F_hist = []
S_hist = []
V_hist = []
g_clear_hist = []
g_ema_hist = []

V_acc = 0.0
V_last = None
g_ema = 0.0

# ==============================
# SIMULAÇÃO
# ==============================

for t in range(T):

    # Evolução do capital (GBM simples)
    mu_d = MU_CAP / 252
    sig_d = SIGMA_CAP / np.sqrt(252)
    z = rng.normal(size=len(cap))
    cap *= np.exp((mu_d - 0.5*sig_d**2) + sig_d*z)

    activity = np.sum(w * cap)

    # Volume diário clearing
    V_daily = (TRADE_INTENSITY / UPDATE_INTERVAL) * activity \
              * (1 + rng.normal(0, V_NOISE))
    V_daily = max(0.0, V_daily)
    V_acc += V_daily

    # Atualização mensal (escada)
    if (t % UPDATE_INTERVAL == 0) and (t > 0):

        V_t = V_acc
        V_acc = 0.0

        if V_last is None or V_last <= 0:
            g_clear = 0.0
        else:
            g_clear = np.log((V_t + 1e-12)/(V_last + 1e-12))

        V_last = V_t

        # EMA suavização
        g_ema = ema_update(g_ema, g_clear, EMA_ALPHA)

        # Regra de supply
        delta = np.clip(BETA_SUPPLY * g_ema,
                        -CAP_PER_WINDOW,
                        CAP_PER_WINDOW)

        supply *= np.exp(delta)

        # Atualiza capital reportado
        C_report = np.sum(w * cap)

        V_hist.append(V_t)
        g_clear_hist.append(g_clear)
        g_ema_hist.append(g_ema)

    # Fundamental
    F = C_report / (supply + 1e-12)

    # Reconvergência elástica
    P_spec = P * np.exp(rng.normal(0, SIGMA_SPEC))
    P_adj = P_spec * (F / (P_spec + 1e-12))**K
    P = (1-ALPHA)*P_spec + ALPHA*P_adj

    P_hist.append(P)
    F_hist.append(F)
    S_hist.append(supply)

# Normalização
P_hist = np.array(P_hist)/P_hist[0]
F_hist = np.array(F_hist)/F_hist[0]
S_hist = np.array(S_hist)/S_hist[0]

# ==============================
# MÉTRICAS
# ==============================

def annual_vol(series):
    r = np.diff(np.log(series + 1e-12))
    return np.std(r)*np.sqrt(252)

def max_dd(series):
    peak = np.maximum.accumulate(series)
    dd = series/peak - 1
    return np.min(dd)

print("Vol anual:", round(annual_vol(P_hist),4))
print("Max DD:", round(max_dd(P_hist),4))
print("Erro médio |P-F|:",
      round(np.mean(np.abs(P_hist-F_hist)/F_hist),4))

# ==============================
# PLOTS
# ==============================

plt.figure(figsize=(10,4))
plt.plot(P_hist, label="Preço")
plt.plot(F_hist, label="Fundamental")
plt.title("Preço vs Fundamental")
plt.legend()
plt.show()

plt.figure(figsize=(10,4))
plt.plot(S_hist)
plt.title("Supply Endógeno")
plt.show()

plt.figure(figsize=(10,4))
plt.plot(g_clear_hist, label="g_clearing")
plt.plot(g_ema_hist, label="EMA")
plt.legend()
plt.title("Mini-PIB via Clearing")
plt.show()
