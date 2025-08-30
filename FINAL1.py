"""
malaria_seir_si_pygame.py

Modelo agente-puro: Humanos (SEIR) y Mosquitos (SI).
Mosquitos nacen y se mueven alrededor de charcas fijas.
Visualización con pygame y gráficas finales con matplotlib.

Requisitos:
    pip install pygame numpy matplotlib
"""

import pygame
import random
import numpy as np
import matplotlib.pyplot as plt
import time
import os
from math import sqrt

# ----------------- PARÁMETROS -----------------
ANCHO, ALTO = 800, 600         # tamaño ventana (px)
TMAX = 2000                    # horas totales a simular (poner 8760 para 1 año)
TEST_MODE = True               # si True, TMAX bajo para pruebas; si False, pon TMAX=8760

NUM_HUMANOS = 200
NUM_CHARCAS = 4
MOSQUITOS_POR_CHARCA_INI = (10, 40)  # rango inicial por charca
RADIO_CONTAGIO = 10            # px (distancia para considerar picadura)
HORAS_POR_SEMANA = 24 * 7
SEMANAS_POR_ANIO = 52
MAX_MOSQUITOS_CHARCA = 500  # máximo por charca

# Humanos SEIR
BETA_H = 0.25     # probabilidad mosquito(I) -> humano(E) por picadura
SIGMA_H = 24 * 2  # horas desde E -> I (ej: 2 días)
GAMMA_H = 24 * 5  # horas desde I -> R (ej: 5 días)

# Mosquitos SI
BETA_V = 0.2      # probabilidad humano(I) -> mosquito(I) por picadura
TIEMPO_MAX_VIDA = 15 * 24  # horas
TIEMPO_SIN_COMER_MAX = 48  # horas sin alimentarse que mata
RADIO_VUELO_FACTOR = 0.12  # radio de vuelo relativo a dimensión menor (fracción)
REPRODUCCION = 0.02  # probabilidad por mosquito por hora de generar 1 hijo (si capacidad)

# Picadura: mosquitos activos N horas al día
BITING_DURATION = 12  # horas al día que pueden picar (p.ej. 12)
BITING_START = 18     # hora del día en que comienza la ventana (ej: 18 -> 6PM)

# Semillas iniciales
SEED_INFECTED_HUMANS = 3
SEED_INFECTED_MOSQUITOS = 8

# Estados
SUSCEPTIBLE = 0
EXPOSITO = 1
INFECTADO = 2
RECUPERADO = 3  # solo humanos

# Colores
COLOR_CHARCA = (173, 216, 230)
COLOR_FONDO = (240, 240, 240)
COLORES_H = {
    SUSCEPTIBLE: (0, 120, 255),
    EXPOSITO:   (255, 165, 0),
    INFECTADO:  (220, 0, 0),
    RECUPERADO: (140, 140, 140)
}
COLORES_V = {SUSCEPTIBLE: (0, 180, 0), INFECTADO: (160, 0, 160)}

# Visual / rendimiento
DRAW_MOSQUITOS = True
DRAW_HUMANS = True
FPS = 60
SAVE_FRAMES_EVERY = 1000
os.makedirs("capturas_vector", exist_ok=True)

# Ajustes según mapa
RADIO_VUELO = max(5, int(min(ANCHO, ALTO) * RADIO_VUELO_FACTOR))
CHARCA_DRAW_RAD = max(6, int(min(ANCHO, ALTO) * 0.04))

# Ajuste de TMAX si testing
if TEST_MODE and TMAX > 2000:
    TMAX = 2000

# ----------------- UTIL -----------------
def hora_del_dia(paso):
    return paso % 24

def puede_picardura_en_esta_hora(paso):
    h = hora_del_dia(paso)
    return ((h - BITING_START) % 24) < BITING_DURATION

def distancia2(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy

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
        # movimiento aleatorio simple (puedes reemplazar por rutinas de manzanas)
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

    def dibujar(self, surf):
        if DRAW_HUMANS:
            pygame.draw.circle(surf, COLORES_H[self.estado], (int(self.x), int(self.y)), 4)

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
        # Movimiento aleatorio limitado al radio de vuelo alrededor de (x0,y0)
        dx = random.uniform(-2.5, 2.5)
        dy = random.uniform(-2.5, 2.5)
        nx = self.x + dx
        ny = self.y + dy
        if (nx - self.x0)**2 + (ny - self.y0)**2 <= RADIO_VUELO**2:
            self.x = max(0, min(ANCHO, nx))
            self.y = max(0, min(ALTO, ny))
        # envejecimiento/hambre se aumentan fuera
    def reproducir(self):
        if random.random() < REPRODUCCION:
            return Mosquito(self.x0, self.y0, SUSCEPTIBLE)
        return None

    def dibujar(self, surf):
        if DRAW_MOSQUITOS:
            pygame.draw.circle(surf, COLORES_V[self.estado], (int(self.x), int(self.y)), 2)

class Charca:
    __slots__ = ("x","y","mosquitos")
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.mosquitos = []

# ----------------- INICIALIZACIÓN -----------------
pygame.init()
ventana = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("SEIR (humanos) - SI (mosquitos) alrededor de charcas")
clock = pygame.time.Clock()

# Crear charcas (ubicaciones)
charcas = []
for _ in range(NUM_CHARCAS):
    margin = 30
    x = random.randint(margin, ANCHO - margin)
    y = random.randint(margin, ALTO - margin)
    charcas.append(Charca(x, y))

# poblar mosquitos por charca
for ch in charcas:
    n = random.randint(MOSQUITOS_POR_CHARCA_INI[0], MOSQUITOS_POR_CHARCA_INI[1])
    for _ in range(n):
        ch.mosquitos.append(Mosquito(ch.x, ch.y))

# crear humanos distribuidos por el mapa (opcionalmente cerca de manzanas)
humanos = []
for i in range(NUM_HUMANOS):
    # opcional: distribuir humanos cerca de charcas o al azar
    if random.random() < 0.6:
        ch = random.choice(charcas)
        x = ch.x + random.uniform(-40, 40)
        y = ch.y + random.uniform(-40, 40)
        humanos.append(Humano(x, y, SUSCEPTIBLE, home_manzana=None))
    else:
        humanos.append(Humano(random.uniform(0, ANCHO), random.uniform(0, ALTO), SUSCEPTIBLE, home_manzana=None))

# sembrar infectados humanos y mosquitos
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

# contador tiempo real
start_time = time.time()

# ----------------- BUCLE PRINCIPAL -----------------
paso = 0
ejecutando = True
while ejecutando and paso < TMAX:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

    ventana.fill(COLOR_FONDO)

    # dibujar charcas
    for ch in charcas:
        pygame.draw.circle(ventana, COLOR_CHARCA, (int(ch.x), int(ch.y)), CHARCA_DRAW_RAD)
        pygame.draw.circle(ventana, (120,120,120), (int(ch.x), int(ch.y)), CHARCA_DRAW_RAD, 1)

    # mover humanos
    for h in humanos:
        h.mover()
        h.actualizar()
        h.dibujar(ventana)

    # mover mosquitos por charca, reproducir y muerte
    mosquitos_todos = []
    for ch in charcas:
        nuevos = []
        for mq in ch.mosquitos:
            mq.mover()
            mq.t_vida += 1
            mq.t_sin += 1

            # muerte por edad o inanición
            if mq.t_vida > TIEMPO_MAX_VIDA or mq.t_sin > TIEMPO_SIN_COMER_MAX:
                continue

            # reproducción local (capacidad por charca arbitraria)
            # reproducción solo si no se alcanzó el máximo
            if len(nuevos) + len(ch.mosquitos) < MAX_MOSQUITOS_CHARCA:
                hijo = mq.reproducir()
            if hijo and len(nuevos) + len(ch.mosquitos) < 800:
                nuevos.append(hijo)

            nuevos.append(mq)
        ch.mosquitos = nuevos
        mosquitos_todos.extend(ch.mosquitos)

       # dibujar mosquitos asociados a esta charca
        for mq in ch.mosquitos:
            mq.dibujar(ventana)

    # interacciones PICADURAS (solo durante horas activas)
    if puede_picardura_en_esta_hora(paso):
        # Para cada mosquito intentamos una picadura (submuestreo de humanos para velocidad)
        for mq in mosquitos_todos:
            posibles = random.sample(humanos, min(12, len(humanos)))
            for h in posibles:
                dx = mq.x - h.x
                dy = mq.y - h.y
                if dx*dx + dy*dy <= RADIO_CONTAGIO * RADIO_CONTAGIO:
                    # mosquito infecta humano
                    if mq.estado == INFECTADO and h.estado == SUSCEPTIBLE:
                        if random.random() < BETA_H:
                            h.estado = EXPOSITO
                            h.t_exp = 0
                    # humano infecta mosquito
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

    # flip y tick
    pygame.display.flip()
    clock.tick(FPS)

    paso += 1

    # progreso cada cierto pasos
    if paso % 200 == 0:
        elapsed = time.time() - start_time
        print(f"[INFO] Paso {paso}/{TMAX}  elapsed {elapsed:.1f}s  H(I)={hist_h_I[-1]}  V(I)={hist_v_I[-1]}  Mosq_total={len(mosquitos_todos)}")

    # guardar frame ocasional (opcional)
    if paso % SAVE_FRAMES_EVERY == 0:
        pygame.image.save(ventana, f"capturas_vector/vector_{paso:05d}.png")

pygame.quit()

# ----------------- POSTPROCESADO: semanas epidemiológicas -----------------
# Cortar al número de horas relevante (52 semanas => 52*168 = 8736)
horas_relevantes = min(len(hist_h_S), HORAS_POR_SEMANA * SEMANAS_POR_ANIO)
if horas_relevantes < HORAS_POR_SEMANA:
    print("[WARN] No hay suficientes horas para agrupar en semanas completas; se graficará por horas disponibles.")
hS = np.array(hist_h_S[:horas_relevantes])
hE = np.array(hist_h_E[:horas_relevantes])
hI = np.array(hist_h_I[:horas_relevantes])
hR = np.array(hist_h_R[:horas_relevantes])
vS = np.array(hist_v_S[:horas_relevantes])
vI = np.array(hist_v_I[:horas_relevantes])

if horas_relevantes >= HORAS_POR_SEMANA:
    n_sem = horas_relevantes // HORAS_POR_SEMANA
    reshape_size = (n_sem, HORAS_POR_SEMANA)
    hS_weeks = hS[:n_sem*HORAS_POR_SEMANA].reshape(reshape_size).mean(axis=1)
    hE_weeks = hE[:n_sem*HORAS_POR_SEMANA].reshape(reshape_size).mean(axis=1)
    hI_weeks = hI[:n_sem*HORAS_POR_SEMANA].reshape(reshape_size).mean(axis=1)
    hR_weeks = hR[:n_sem*HORAS_POR_SEMANA].reshape(reshape_size).mean(axis=1)
    vS_weeks = vS[:n_sem*HORAS_POR_SEMANA].reshape(reshape_size).mean(axis=1)
    vI_weeks = vI[:n_sem*HORAS_POR_SEMANA].reshape(reshape_size).mean(axis=1)
else:
    n_sem = 0
    hS_weeks = hE_weeks = hI_weeks = hR_weeks = np.array([])
    vS_weeks = vI_weeks = np.array([])

# ----------------- GRAFICAS FINALES -----------------
# Humanos horario
plt.figure(figsize=(10,6))
plt.plot(hist_h_S, label='Humanos S')
plt.plot(hist_h_E, label='Humanos E')
plt.plot(hist_h_I, label='Humanos I')
plt.plot(hist_h_R, label='Humanos R')
plt.xlabel('Horas')
plt.ylabel('N humanos')
plt.legend()
plt.title('Evolución humana hora a hora')
plt.tight_layout()
plt.show()

# Mosquitos horario
plt.figure(figsize=(10,4))
plt.plot(hist_v_S, label='Mosq S')
plt.plot(hist_v_I, label='Mosq I')
plt.xlabel('Horas')
plt.ylabel('N mosquitos')
plt.legend()
plt.title('Mosquitos hora a hora')
plt.tight_layout()
plt.show()

import calendar

# ----------------- POSTPROCESADO DIARIO -----------------
HORAS_POR_DIA = 24
total_horas = len(hist_h_S)
n_dias = total_horas // HORAS_POR_DIA

# Recortar arrays a múltiplos de 24 horas
hS = np.array(hist_h_S[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)
hE = np.array(hist_h_E[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)
hI = np.array(hist_h_I[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)
hR = np.array(hist_h_R[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)
vS = np.array(hist_v_S[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)
vI = np.array(hist_v_I[:n_dias*HORAS_POR_DIA]).reshape(n_dias, HORAS_POR_DIA)

# Conteo total diario (tomamos el estado al final de cada día)
hS_dia = hS[:, -1]
hE_dia = hE[:, -1]
hI_dia = hI[:, -1]
hR_dia = hR[:, -1]
vS_dia = vS[:, -1]
vI_dia = vI[:, -1]

# Eje de días
dias = np.arange(1, n_dias+1)

# Convertir días a meses (aprox. mes calendario para 365 días)
mes_dias = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]  # acumulado días inicio de cada mes
mes_nombres = list(calendar.month_abbr)[1:]  # ['Jan', 'Feb', ..., 'Dec']

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
plt.xticks(mes_dias[:-1] + np.diff(mes_dias)//2, mes_nombres)  # centrar mes en la gráfica

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
