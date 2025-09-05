#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>

#define ANCHO 600
#define ALTO 1100
#define TMAX 8760              // horas a simular, 8760 horas que es un año
#define NUM_HUMANOS 140000
#define NUM_CHARCAS 660000*0.02 //5% de la grilla tienen charcas, pendiete de hacer otros
#define MOSQ_INIT_MIN 0 // Las charcas pueden tener entre 0 y 30 mosquitos iniciales
#define MOSQ_INIT_MAX 15 //MAXIMO 40 mosquitos por grilla, para no saturar el sistma
#define RADIO_CONTAGIO 11.0f
#define HORAS_POR_DIA 24
#define BITING_DURATION 16     // horas activas
#define BITING_START 18        // hora de inicio de ventana
#define MAX_MOSQUITOS_CHARCA 15
#define MAX_MOSQ_TOTAL (NUM_CHARCAS * MAX_MOSQUITOS_CHARCA)


#define BETA_H 0.20f           // mosq(I) -> humano(E) por picadura
#define SIGMA_H (24*10)         // E->I (horas)
#define GAMMA_H (24*15)         // I->R (horas)
#define TIEMPO_INMUNIDAD (24*10) // horas que un REC permanece inmune antes de volver SUS 5 semanas

// Mosquitos
#define BETA_V 0.73f            // humano(I) -> mosq(I) por picadura
#define TIEMPO_MAX_VIDA (15*24)
#define TIEMPO_SIN_COMER_MAX 48
#define RADIO_VUELO_FACTOR 0.15f
#define REPRODUCCION 0.20f

// Muestreo de humanos por mosquito para chequear vecindad
#define HUMAN_SUBSAMPLE 12

typedef enum { SUS=0, EXP=1, INF=2, REC=3 } Estado;

typedef struct {
    float x, y;
    Estado estado;
    int t_exp, t_inf;      // contadores en horas
    int t_rec;             // contador de inmunidad
} Humano;

typedef struct {
    float x, y;
    float x0, y0;          // centro de vuelo (charca)
    int charca_id;
    Estado estado;         // SUS o INF
    int t_sin, t_vida;     // horas sin comer / vida
} Mosquito;

typedef struct {
    float x, y;
    int n_actual;          // mosquitos actuales (solo para control de capacidad)
} Charca;

// -------- Utiles --------
static inline float frand01(void){ return (float)rand() / (float)RAND_MAX; }

static inline float clampf(float v, float lo, float hi){
    return v < lo ? lo : (v > hi ? hi : v);
}

static inline int hora_del_dia(int paso){ return paso % HORAS_POR_DIA; }

static inline int puede_picardura_en_esta_hora(int paso){
    int h = hora_del_dia(paso);
    int d = (h - BITING_START + 24) % 24;
    return d < BITING_DURATION;
}

// distancia^2
static inline float dist2(float ax, float ay, float bx, float by){
    float dx = ax - bx, dy = ay - by;
    return dx*dx + dy*dy;
}

int main(void){
    // ---- Entradas del usuario ----
    char nombre_salida[256];
    unsigned int seed;
    int progreso_cada_seg; // 0 = sin progreso periódico

    printf("Nombre del archivo de salida (CSV): ");
    if (scanf("%255s", nombre_salida) != 1){ fprintf(stderr,"Entrada inválida\n"); return 1; }

    printf("Semilla (entero positivo): ");
    if (scanf("%u", &seed) != 1){ fprintf(stderr,"Entrada inválida\n"); return 1; }

    printf("Imprimir progreso cada N segundos (0 = desactivar): ");
    if (scanf("%d", &progreso_cada_seg) != 1){ fprintf(stderr,"Entrada inválida\n"); return 1; }

    srand(seed);

    FILE *f = fopen(nombre_salida, "w");
    if(!f){ perror("No pude abrir archivo de salida"); return 1; }
    fprintf(f, "hora,hS,hE,hI,hR,vS,vI,mosq_total\n");

    // ---- Inicialización ----
    Humano *H = (Humano*)malloc(sizeof(Humano)*NUM_HUMANOS);
    if(!H){ fprintf(stderr,"Memoria insuficiente (H)\n"); return 1; }

    Charca *C = (Charca*)malloc(sizeof(Charca)*NUM_CHARCAS);
    if(!C){ fprintf(stderr,"Memoria insuficiente (C)\n"); return 1; }

    Mosquito *M = (Mosquito*)malloc(sizeof(Mosquito)*MAX_MOSQ_TOTAL);
    if(!M){ fprintf(stderr,"Memoria insuficiente (M)\n"); return 1; }
    int M_count = 0;

    // Radio de vuelo (px)
    float RADIO_VUELO = fmaxf(5.0f, (float)(fmin(ANCHO, ALTO)) * RADIO_VUELO_FACTOR);

    // Charcas en el mapa
    for(int i=0;i<NUM_CHARCAS;i++){
        int margin=30;
        C[i].x = (float)(margin + rand()%(ANCHO-2*margin));
        C[i].y = (float)(margin + rand()%(ALTO-2*margin));
        C[i].n_actual = 0;
    }

    // Mosquitos iniciales alrededor de cada charca
    for(int i=0;i<NUM_CHARCAS;i++){
        int n = MOSQ_INIT_MIN + rand()%(MOSQ_INIT_MAX - MOSQ_INIT_MIN + 1);
        for(int k=0;k<n && M_count<MAX_MOSQ_TOTAL;k++){
            Mosquito mq;
            mq.x0 = C[i].x; mq.y0 = C[i].y;
            mq.x  = mq.x0 + (frand01()*4.0f - 2.0f);
            mq.y  = mq.y0 + (frand01()*4.0f - 2.0f);
            mq.estado = SUS;
            mq.t_sin = 0; mq.t_vida = 0;
            mq.charca_id = i;
            M[M_count++] = mq;
            C[i].n_actual++;
        }
    }

    // Humanos: algunos cerca de charcas, otros al azar
    for(int i=0;i<NUM_HUMANOS;i++){
        if (frand01() < 0.6f){
            int id = rand()%NUM_CHARCAS;
            float x = C[id].x + (frand01()*80.0f - 40.0f);
            float y = C[id].y + (frand01()*80.0f - 40.0f);
            H[i].x = clampf(x, 0.0f, (float)ANCHO);
            H[i].y = clampf(y, 0.0f, (float)ALTO);
        } else {
            H[i].x = frand01() * ANCHO;
            H[i].y = frand01() * ALTO;
        }
        H[i].estado = SUS;
        H[i].t_exp = 0; H[i].t_inf = 0; H[i].t_rec = 0;
    }

    // Semillas de estados iniciales en humanos y mosquitos
    int SEED_INFECTED_HUMANS   = 120;  // Infectados iniciales
    int SEED_EXPOSED_HUMANS    = 80;   // Expuestos iniciales
    int SEED_RECOVERED_HUMANS  = 50;   // Recuperados iniciales
    int SEED_INFECTED_MOSQUITOS = 200;


    // Infectados humanos iniciales
    for(int k=0;k<SEED_INFECTED_HUMANS;k++){
        int idx = rand()%NUM_HUMANOS;
        H[idx].estado = INF;
        H[idx].t_inf = 0;
    }

    // Expuestos humanos iniciales
    for(int k=0;k<SEED_EXPOSED_HUMANS;k++){
        int idx = rand()%NUM_HUMANOS;
        H[idx].estado = EXP;
        H[idx].t_exp = 0;
    }
        // Recuperados humanos iniciales
    for(int k=0;k<SEED_RECOVERED_HUMANS;k++){
        int idx = rand()%NUM_HUMANOS;
        H[idx].estado = REC;
        H[idx].t_rec = 0;
    }
    for(int k=0;k<SEED_INFECTED_MOSQUITOS && k<M_count;k++){
        int idx = rand()%M_count;
        M[idx].estado = INF;
        M[idx].t_sin = 0;
    }

    // ---- Timers ----
    clock_t cpu_ini = clock();
    time_t wall_ini = time(NULL);
    time_t last_progress = wall_ini;

    // ---- Bucle principal ----
    for(int paso=0; paso<TMAX; ++paso){

        // 1) Mover humanos + actualizar estados
        for(int i=0;i<NUM_HUMANOS;i++){
            int step = 3;
            H[i].x = clampf(H[i].x + (float)(rand()% (2*step+1) - step), 0.0f, (float)ANCHO);
            H[i].y = clampf(H[i].y + (float)(rand()% (2*step+1) - step), 0.0f, (float)ALTO);

            // SEIR con inmunidad temporal
            if (H[i].estado == EXP){
                H[i].t_exp++;
                if (H[i].t_exp >= SIGMA_H){
                    H[i].estado = INF;
                    H[i].t_inf = 0;
                }
            } else if (H[i].estado == INF){
                H[i].t_inf++;
                if (H[i].t_inf >= GAMMA_H){
                    H[i].estado = REC;
                    H[i].t_rec = 0;
                }
            } else if (H[i].estado == REC){
                H[i].t_rec++;
                if (H[i].t_rec >= TIEMPO_INMUNIDAD){
                    H[i].estado = SUS;
                    H[i].t_rec = 0;
                }
            }
        }

        // 2) Mosquitos: mover, envejecimiento, inanición, reproducción, muerte
        for(int i=0;i<NUM_CHARCAS;i++) C[i].n_actual = 0;
        for(int i=0;i<M_count;i++) C[M[i].charca_id].n_actual++;

        int i = 0;
        while(i < M_count){
            Mosquito *mq = &M[i];
            float dx = frand01()*5.0f - 2.5f;
            float dy = frand01()*5.0f - 2.5f;
            float nx = mq->x + dx, ny = mq->y + dy;
            float r2 = (nx - mq->x0)*(nx - mq->x0) + (ny - mq->y0)*(ny - mq->y0);
            if (r2 <= RADIO_VUELO*RADIO_VUELO){
                mq->x = clampf(nx, 0.0f, (float)ANCHO);
                mq->y = clampf(ny, 0.0f, (float)ALTO);
            }

            mq->t_vida++;
            mq->t_sin++;

            if (mq->t_vida > TIEMPO_MAX_VIDA || mq->t_sin > TIEMPO_SIN_COMER_MAX){
                int cid = mq->charca_id;
                C[cid].n_actual--;
                M[i] = M[M_count-1];
                M_count--;
                continue;
            }

            int cid = mq->charca_id;
            if (C[cid].n_actual < MAX_MOSQUITOS_CHARCA && M_count < MAX_MOSQ_TOTAL){
                if (frand01() < REPRODUCCION){
                    Mosquito hijo;
                    hijo.x0 = C[cid].x; hijo.y0 = C[cid].y;
                    hijo.x  = hijo.x0 + (frand01()*4.0f - 2.0f);
                    hijo.y  = hijo.y0 + (frand01()*4.0f - 2.0f);
                    hijo.estado = SUS;
                    hijo.t_sin = 0; hijo.t_vida = 0;
                    hijo.charca_id = cid;
                    M[M_count++] = hijo;
                    C[cid].n_actual++;
                }
            }

            i++;
        }

        // 3) Interacciones (picaduras)
        if (puede_picardura_en_esta_hora(paso)){
            float rc2 = RADIO_CONTAGIO * RADIO_CONTAGIO;
            for(int mi=0; mi<M_count; ++mi){
                Mosquito *mq = &M[mi];
                int reps = HUMAN_SUBSAMPLE < NUM_HUMANOS ? HUMAN_SUBSAMPLE : NUM_HUMANOS;
                for(int t=0; t<reps; ++t){
                    int hi = rand()%NUM_HUMANOS;
                    Humano *h = &H[hi];
                    if (dist2(mq->x, mq->y, h->x, h->y) <= rc2){
                        if (mq->estado == INF && (h->estado == SUS || h->estado == REC)){
                            if (frand01() < BETA_H){
                                h->estado = EXP;
                                h->t_exp = 0;
                            }
                        }
                        if (mq->estado == SUS && h->estado == INF){
                            if (frand01() < BETA_V){
                                mq->estado = INF;
                                mq->t_sin = 0;
                            }
                        }
                        mq->t_sin = 0;
                        break;
                    }
                }
            }
        }

        // 4) Conteos y CSV
        int hS=0,hE=0,hI=0,hR=0, vS=0,vI=0;
        for(int k=0;k<NUM_HUMANOS;k++){
            switch(H[k].estado){
                case SUS: hS++; break;
                case EXP: hE++; break;
                case INF: hI++; break;
                case REC: hR++; break;
            }
        }
        for(int k=0;k<M_count;k++){
            if (M[k].estado == SUS) vS++; else vI++;
        }
        if (paso % 4 == 0) {  // solo cada 4 horas
            fprintf(f, "%d,%d,%d,%d,%d,%d,%d,%d\n", paso, hS,hE,hI,hR, vS,vI, M_count);
        }

        // 5) Progresodata6da
        if (progreso_cada_seg > 0){
            time_t now = time(NULL);
            if (difftime(now, last_progress) >= progreso_cada_seg){
                double elapsed = difftime(now, wall_ini);
                printf("[INFO] t=%d/%d  elapsed=%.1fs  H(I)=%d  V(I)=%d  Mosq_total=%d\n",
                       paso, TMAX, elapsed, hI, vI, M_count);
                fflush(stdout);
                last_progress = now;
            }
        }
    }

    // ---- Fin ----
    fclose(f);
    clock_t cpu_fin = clock();
    time_t wall_fin = time(NULL);

    double cpu_secs = (double)(cpu_fin - cpu_ini) / CLOCKS_PER_SEC;
    double wall_secs = difftime(wall_fin, wall_ini);

    printf("Simulacion completada.\n");
    printf("Tiempo CPU: %.3f s\n", cpu_secs);
    printf("Tiempo pared: %.3f s\n", wall_secs);
    printf("Resultados escritos en: %s\n", nombre_salida);

    free(H); free(C); free(M);
    return 0;
}
