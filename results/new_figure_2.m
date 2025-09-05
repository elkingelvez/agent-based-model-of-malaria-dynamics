clc
clear all
close all

%% Leer datos desde data4.txt, saltando la primera línea de encabezado
datos1= dlmread('2porciento.txt', ',', 1, 0);
datos2= dlmread('3porciento.txt', ',', 1, 0);
datos3= dlmread('4porciento.txt', ',', 1, 0);


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

%% Crear la gráfica

figure;
hold on;
plot(dias, hI1, 'b', 'LineWidth', 1, 'DisplayName', '2% larval habitats');
plot(dias, hI2, 'g', 'LineWidth', 1, 'DisplayName', '3% larval habitats');
plot(dias, hI3, 'm', 'LineWidth', 1, 'DisplayName', '4% larval habitats');

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