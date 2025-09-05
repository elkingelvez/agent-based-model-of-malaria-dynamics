clc
clear all
close all

%% Leer datos desde data4.txt, saltando la primera línea de encabezado
datos1= dlmread('simu1.txt', ',', 1, 0);
datos2= dlmread('simu2.txt', ',', 1, 0);
datos3= dlmread('simu3.txt', ',', 1, 0);
datos4= dlmread('simu4.txt', ',', 1, 0);
datos5= dlmread('simu5.txt', ',', 1, 0);

%%
hora = datos1(:,1);
dias = hora / 24; % Convertir horas a días

%% Datos humanos 1
hS1 = datos1(:,2);
hE1 = datos1(:,3);
hI1 = datos1(:,4);
hR1 = datos1(:,5);

% Datos humanos 2
hS2 = datos2(:,2);
hE2 = datos2(:,3);
hI2 = datos2(:,4);
hR2 = datos2(:,5);

% Datos humanos 3
hS3 = datos3(:,2);
hE3 = datos3(:,3);
hI3 = datos3(:,4);
hR3 = datos3(:,5);

% Datos humanos 4
hS4 = datos4(:,2);
hE4 = datos4(:,3);
hI4 = datos4(:,4);
hR4 = datos4(:,5);

% Datos humanos 5
hS5 = datos5(:,2);
hE5 = datos5(:,3);
hI5 = datos5(:,4);
hR5 = datos5(:,5);

% Datos promedio humanos
hS = (datos1(:,2)+datos2(:,2)+datos3(:,2)+datos4(:,2)+datos5(:,2))/5;
hE = datos5(:,3);
hI = (datos1(:,4)+datos2(:,4)+datos3(:,4)+datos4(:,4)+datos5(:,4))/5;
hR = datos5(:,5);

%% Datos mosquitos 1
vS1 = datos1(:,6);
vI1 = datos1(:,7);

% Datos mosquitos 2
vS2 = datos2(:,6);
vI2 = datos2(:,7);

%% Meses para el eje X
% meses = {' ', 'Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dic'};
meses = {'Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dic'};
% pos_mes = [1 32 60 91 121 152 182 213 244 274 305 335 365]; % inicio de cada mes
pos_mes = [16.5 46 75.5 106 136.5 167 197.5 228.2 259 289.2 320 350]; % inicio de cada mes


casos_epi = [104 115 136 94 90 121 113 119 132 128 120 129 107 141 137 144 ...
             113 154 165 164 158 180 190 197 227 197 205 189 123 113 108 130 ...
             89 120 116 119 142 112 88 121 128 142 127 110 150 129 125 108 ...
             114 124 143 127];

semanas = 1:52;
dias_miercoles = (semanas - 1) * 7 + 3;  % Miércoles ≈ día 3 de cada semana

%% === MATRIZ MONTE CARLO ===
hI_montecarlo = [hI1 hI2 hI3 hI4 hI5];

% Promedio
hI = mean(hI_montecarlo, 2);

% Percentiles (95% banda de confianza)
hI_low  = prctile(hI_montecarlo, 2.5, 2);
hI_high = prctile(hI_montecarlo, 97.5, 2);

%% Datos de semanas epidemiológicas (1 por semana, 52 semanas)
casos_epi = [104 115 136 94 90 121 113 119 132 128 120 129 107 141 137 144 ...
             113 154 165 164 158 180 190 197 227 197 205 189 123 113 108 130 ...
             89 120 116 119 142 112 88 121 128 142 127 110 150 129 125 108 ...
             114 124 143 127];

% Calcular día del año para cada miércoles de la semana
semanas = 1:52;
dias_miercoles = (semanas - 1) * 7 + 3;  % Miércoles ≈ día 3 de cada semana

%% Crear la gráfica

figure;
hold on;
plot(dias, hI2, 'r', 'LineWidth', 1, 'DisplayName', 'Simulations');
plot(dias, hI3, 'r', 'LineWidth', 1, 'HandleVisibility','off');
plot(dias, hI4, 'r', 'LineWidth', 1, 'HandleVisibility','off');
plot(dias, hI5, 'r', 'LineWidth', 1, 'HandleVisibility','off');

plot(dias, hI, 'k', 'LineWidth', 1.5, 'DisplayName', 'Mean');    % promedio

fill([dias; flipud(dias)], [hI_low; flipud(hI_high)], ...
     [0.8 0.8 1], 'EdgeColor','none','FaceAlpha',0.5, 'DisplayName', 'CI 95%');

plot(dias, hI1, 'r', 'LineWidth', 2, 'HandleVisibility','off');

plot(dias_miercoles, casos_epi, 'ko', 'MarkerFaceColor', 'b', 'DisplayName', 'Real report');

legend('show', 'FontSize', 14);

% Ejes y leyenda
xlabel('Month', 'FontSize', 20);
ylabel('Infected population', 'FontSize', 20);
xticks(pos_mes);
xticklabels(meses);
xlim([1 365]);
ylim([0 300]);
set(gca, 'FontSize', 14);
set(gcf, 'Position', [100 100 600 300]);
grid on; grid minor;

hold off;



