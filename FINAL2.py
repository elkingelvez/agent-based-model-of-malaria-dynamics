import random
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import calendar

# ----------------- PARÁMETROS -----------------
ANCHO, ALTO = 800, 600
TMAX = 2000  # poner 8760 para 1 año
TEST_MODE = True

NUM_HUMANOS = 200
NUM_CHARCAS = 4
MOSQUITOS_POR_CHARCA_INI = (10, 40)
RADIO_CONTAGIO = 10
HORAS_POR_SEMANA = 24 * 7
SEMANAS_POR_ANIO = 52
MAX_MOSQUITOS_CHARCA = 500

# Humanos SEIR
BETA_H = 0.25
SIGMA_H = 24 * 2
GAMMA_H = 24 * 5

# Mosquitos SI
BETA_V = 0.2
TIEMPO_MAX_VIDA = 15 * 24
TIEMPO_SIN_COMER_MAX = 48
RADIO_VUELO_FACTOR = 0.12
REPRODUCCION = 0.02

# Picadura: mosquitos activos N horas al día
BITING_DURATION = 12
BITING_START = 18

# Semillas iniciales
SEED_INFECTED_HUMANS = 3
SEED_INFECTED_MOSQUITOS = 8

# Estados
SUSCEPTIBLE = 0
EXPOSITO = 1
INFECTADO = 2
RECUPERADO = 3  # solo humanos

# Ajuste de TMAX si testing
if TEST_MODE and TMAX > 2000:
    TMAX = 2000

# ----------------- UTIL -----------------
def hora_del_dia(paso):
    return paso % 24

def puede_picardura_en_esta_hora(paso):
    h = hora_del_dia(paso)
    return ((h - BITING_START) % 24) < BITING_DURATION

# ----------------- CLASES -----------------
class Humano:
    __slots__ = ("x","y","estado","t_exp","t_inf","home_manzana")
    def __init__(self, x, y, estado=SUSCEPTIBLE, home_manzana=None):
        self.x = float(x)
        self.y = float(y)
        self.estado = estado
        self.t_exp = 0
        self.t_inf = 0
        self.home_manzana = home_manzana

    def mover(self):
        step = 3
        self.x = max(0, min(ANCHO, self.x + random.randint(-step, step)))
        self.y = max(0, min(ALTO, self.y + random.randint(-step, step)))

    def actualizar(self):
        if self.estado == EXPOSITO:
            self.t_exp += 1
            if self.t_exp >= SIGMA_H:
                self.estado = INFECTADO
                self.t_inf = 0
        elif self.estado == INFECTADO:
            self.t_inf += 1
            if self.t_inf >= GAMMA_H:
                self.estado = RECUPERADO

class Mosquito:
    __slots__ = ("x","y","x0","y0","estado","t_sin","t_vida")
    def __init__(self, x0, y0, estado=SUSCEPTIBLE):
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.x = self.x0 + random.uniform(-2,2)
        self.y = self.y0 + random.uniform(-2,2)
        self.estado = estado
        self.t_sin = 0
        self.t_vida = 0

    def mover(self):
        dx = random.uniform(-2.5, 2.5)
        dy = random.uniform(-2.5, 2.5)
        nx = self.x + dx
        ny = self.y + dy
        RADIO_VUELO = max(5, int(min(ANCHO, ALTO) * RADIO_VUELO_FACTOR))
        if (nx - self.x0)**2 + (ny - self.y0)**2 <= RADIO_VUELO**2:
            self.x = max(0, min(ANCHO, nx))
            self.y = max(0, min(ALTO, ny))

    def reproducir(self):
        if random.random() < REPRODUCCION:
            return Mosquito(self.x0, self.y0, SUSCEPTIBLE)
        return None

class Charca:
    __slots__ = ("x","y","mosquitos")
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.mosquitos = []

# ----------------- INICIALIZACIÓN -----------------
charcas = []
for _ in range(NUM_CHARCAS):
    margin = 30
    x = random.randint(margin, ANCHO - margin)
    y = random.randint(margin, ALTO - margin)
    charcas.append(Charca(x, y))

for ch in charcas:
    n = random.randint(MOSQUITOS_POR_CHARCA_INI[0], MOSQUITOS_POR_CHARCA_INI[1])
    for _ in range(n):
        ch.mosquitos.append(Mosquito(ch.x, ch.y))

humanos = []
for i in range(NUM_HUMANOS):
    if random.random() < 0.6:
        ch = random.choice(charcas)
        x = ch.x + random.uniform(-40, 40)
        y = ch.y + random.uniform(-40, 40)
        humanos.append(Humano(x, y, SUSCEPTIBLE))
    else:
        humanos.append(Humano(random.uniform(0, ANCHO), random.uniform(0, ALTO), SUSCEPTIBLE))

# sembrar infectados
for h in random.sample(humanos, min(SEED_INFECTED_HUMANS, len(humanos))):
    h.estado = INFECTADO
    h.t_inf = 0

all_mosq_flat = [mq for ch in charcas for mq in ch.mosquitos]
for mq in random.sample(all_mosq_flat, min(SEED_INFECTED_MOSQUITOS, len(all_mosq_flat))):
    mq.estado = INFECTADO
    mq.t_sin = 0

# historiales
hist_h_S, hist_h_E, hist_h_I, hist_h_R = [], [], [], []
hist_v_S, hist_v_I = [], []

# ----------------- BUCLE PRINCIPAL -----------------
start_time = time.time()
paso = 0
#aqui voy aa añadir lo de montecarlo
while paso < TMAX:
    # Humanos
    for h in humanos:
        h.mover()
        h.actualizar()

    # Mosquitos
    mosquitos_todos = []
    for ch in charcas:
        nuevos = []
        for mq in ch.mosquitos:
            mq.mover()
            mq.t_vida += 1
            mq.t_sin += 1

            if mq.t_vida > TIEMPO_MAX_VIDA or mq.t_sin > TIEMPO_SIN_COMER_MAX:
                continue

            if len(nuevos) + len(ch.mosquitos) < MAX_MOSQUITOS_CHARCA:
                hijo = mq.reproducir()
                if hijo:
                    nuevos.append(hijo)

            nuevos.append(mq)
        ch.mosquitos = nuevos
        mosquitos_todos.extend(ch.mosquitos)

    # Picaduras
    if puede_picardura_en_esta_hora(paso):
        for mq in mosquitos_todos:
            posibles = random.sample(humanos, min(12, len(humanos)))
            for h in posibles:
                dx = mq.x - h.x
                dy = mq.y - h.y
                if dx*dx + dy*dy <= RADIO_CONTAGIO * RADIO_CONTAGIO:
                    if mq.estado == INFECTADO and h.estado == SUSCEPTIBLE:
                        if random.random() < BETA_H:
                            h.estado = EXPOSITO
                            h.t_exp = 0
                    if mq.estado == SUSCEPTIBLE and h.estado == INFECTADO:
                        if random.random() < BETA_V:
                            mq.estado = INFECTADO
                            mq.t_sin = 0
                    mq.t_sin = 0
                    break

    # registro
    hist_h_S.append(sum(1 for h in humanos if h.estado == SUSCEPTIBLE))
    hist_h_E.append(sum(1 for h in humanos if h.estado == EXPOSITO))
    hist_h_I.append(sum(1 for h in humanos if h.estado == INFECTADO))
    hist_h_R.append(sum(1 for h in humanos if h.estado == RECUPERADO))
    hist_v_S.append(sum(1 for mq in mosquitos_todos if mq.estado == SUSCEPTIBLE))
    hist_v_I.append(sum(1 for mq in mosquitos_todos if mq.estado == INFECTADO))

    paso += 1
    if paso % 200 == 0:
        elapsed = time.time() - start_time
        print(f"[INFO] Paso {paso}/{TMAX}  elapsed {elapsed:.1f}s  H(I)={hist_h_I[-1]}  V(I)={hist_v_I[-1]}  Mosq_total={len(mosquitos_todos)}")

# ----------------- POSTPROCESADO DIARIO -----------------
HORAS_POR_DIA = 24
total_horas = len(hist_h_S)
n_dias = total_horas // HORAS_POR_DIA

hS = np.array(hist_h_S[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)
hE = np.array(hist_h_E[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)
hI = np.array(hist_h_I[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)
hR = np.array(hist_h_R[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)
vS = np.array(hist_v_S[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)
vI = np.array(hist_v_I[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)

hS_dia = hS[:, -1]
hE_dia = hE[:, -1]
hI_dia = hI[:, -1]
hR_dia = hR[:, -1]
vS_dia = vS[:, -1]
vI_dia = vI[:, -1]

dias = np.arange(1, n_dias+1)
mes_dias = [0,31,59,90,120,151,181,212,243,273,304,334,365]
mes_nombres = list(calendar.month_abbr)[1:]

# ----------------- GRAFICAS -----------------
plt.figure(figsize=(14,6))
plt.subplot(2,1,1)
plt.plot(dias, hS_dia, label='Humanos S')
plt.plot(dias, hE_dia, label='Humanos E')
plt.plot(dias, hI_dia, label='Humanos I')
plt.plot(dias, hR_dia, label='Humanos R')
plt.ylabel('N humanos')
plt.title('Evolución diaria de humanos (SEIR)')
plt.legend()
plt.xticks(mes_dias[:-1] + np.diff(mes_dias)//2, mes_nombres)

plt.subplot(2,1,2)
plt.plot(dias, vS_dia, label='Mosquitos S')
plt.plot(dias, vI_dia, label='Mosquitos I')
plt.ylabel('N mosquitos')
plt.title('Evolución diaria de mosquitos (SI)')
plt.xlabel('Mes del año')
plt.legend()
plt.xticks(mes_dias[:-1] + np.diff(mes_dias)//2, mes_nombres)

plt.tight_layout()
plt.show()

print("Simulación finalizada.")

