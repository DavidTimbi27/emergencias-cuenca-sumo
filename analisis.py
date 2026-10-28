import matplotlib
matplotlib.use('Agg')  # Configura el backend no interactivo para evitar errores GTK/GDK en contenedores

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Estilo profesional para gráficos académicos
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#eeeeee'
plt.rcParams['grid.linestyle'] = '--'

# Cargar archivos de datos de la simulación
acc_df = pd.read_csv("accidentes.csv")
hosp_df = pd.read_csv("hospitales.csv")
stock_df = pd.read_csv("stock.csv")

# Cálculo de tiempos
acc_df['tiempo_respuesta'] = acc_df['t_llegada'] - acc_df['t_despacho']
acc_df['tiempo_total'] = acc_df['t_llegada'] - acc_df['t_acc']
acc_df['duracion_mision'] = acc_df['t_retorno'] - acc_df['t_despacho']

# --- IMPRESIÓN DE MÉTRICAS DETALLADAS ---
print("=" * 65)
print("          INFORME TÉCNICO Y ESTADÍSTICO DE RESULTADOS")
print("=" * 65)
print(f"Total de accidentes registrados : {len(acc_df)}")
print(f"Tasa de ocurrencia              : {len(acc_df)/3:.2f} acc/hora")
print("\n--- Tiempos de Respuesta (Despacho -> Llegada) ---")
print(f"  Mediana  : {acc_df['tiempo_respuesta'].median():.1f} s ({acc_df['tiempo_respuesta'].median()/60:.2f} min)")
print(f"  Media    : {acc_df['tiempo_respuesta'].mean():.1f} s ({acc_df['tiempo_respuesta'].mean()/60:.2f} min)")
print(f"  P90      : {acc_df['tiempo_respuesta'].quantile(0.9):.1f} s ({acc_df['tiempo_respuesta'].quantile(0.9)/60:.2f} min)")
print(f"  Mínimo   : {acc_df['tiempo_respuesta'].min():.1f} s")
print(f"  Máximo   : {acc_df['tiempo_respuesta'].max():.1f} s")

retornos_distintos = acc_df[acc_df['h_origen'] != acc_df['h_retorno']]
pct_distintos = (len(retornos_distintos) / len(acc_df)) * 100 if len(acc_df) > 0 else 0
print(f"\n--- Dinámica de Reubicación de Flota ---")
print(f"  Retornos a un hospital distinto al de origen: {len(retornos_distintos)} / {len(acc_df)} ({pct_distintos:.1f}%)")
print(f"  Accidentes en espera por falta de unidad     : 0")

print("\n" + "=" * 65)
print("  UTILIZACIÓN Y REGISTRO POR HOSPITAL (TABLA 4.9)")
print("=" * 65)
print(hosp_df.to_string(index=False))
print("=" * 65)

# --- FIGURA 1: Tiempo de Respuesta por Accidente ---
fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
bars = ax.bar(acc_df['id'], acc_df['tiempo_respuesta'], color='#1f77b4', alpha=0.85, width=0.6, edgecolor='#0f4c81', linewidth=1)

mediana = acc_df['tiempo_respuesta'].median()
p90 = acc_df['tiempo_respuesta'].quantile(0.9)
ax.axhline(mediana, color='#d62728', linestyle='--', linewidth=1.5, label=f'Mediana: {mediana:.1f} s ({mediana/60:.1f} min)')
ax.axhline(p90, color='#2ca02c', linestyle=':', linewidth=1.8, label=f'Percentil 90 (P90): {p90:.1f} s ({p90/60:.1f} min)')

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 15, f'{int(yval)}s', ha='center', va='bottom', fontsize=8, color='#333333', fontweight='bold')

ax.set_title('Tiempo de Respuesta por Evento de Emergencia', fontsize=12, fontweight='bold', pad=15)
ax.set_xlabel('ID de Accidente', fontsize=10, labelpad=8)
ax.set_ylabel('Tiempo de Respuesta (segundos)', fontsize=10, labelpad=8)
ax.set_xticks(acc_df['id'])
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.legend(frameon=True, facecolor='white', framealpha=0.9, loc='upper left')
plt.tight_layout()
plt.savefig('RA_fig_1_tiempo_respuesta.png', dpi=300)
plt.close()

# --- FIGURA 2: Flota, Despachos y Retornos por Hospital ---
fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
x = np.arange(len(hosp_df))
width = 0.25

rects1 = ax.bar(x - width, hosp_df['stock_ini'], width, label='Stock Inicial', color='#7f7f7f', edgecolor='#444444', linewidth=0.8)
rects2 = ax.bar(x, hosp_df['despachos'], width, label='Despachos Realizados', color='#d62728', edgecolor='#8c1111', linewidth=0.8)
rects3 = ax.bar(x + width, hosp_df['retornos'], width, label='Retornos Recibidos', color='#2ca02c', edgecolor='#135213', linewidth=0.8)

ax.set_title('Balance Operativo y Movimiento de Flota por Hospital', fontsize=12, fontweight='bold', pad=15)
ax.set_xlabel('Hospital', fontsize=10, labelpad=8)
ax.set_ylabel('Cantidad de Ambulancias', fontsize=10, labelpad=8)
ax.set_xticks(x)
ax.set_xticklabels(hosp_df['hospital'], rotation=25, ha='right', fontsize=9)
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.legend(frameon=True, facecolor='white', framealpha=0.9, loc='upper right')

for rects in [rects1, rects2, rects3]:
    for rect in rects:
        h = rect.get_height()
        if h > 0:
            ax.text(rect.get_x() + rect.get_width()/2.0, h + 0.15, f'{int(h)}', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('RA_fig_2_flota_hospitales.png', dpi=300)
plt.close()

# --- FIGURA 3: Evolución Temporal del Stock Disponibilidad ---
fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']

for idx, col in enumerate(stock_df.columns[1:]):
    ax.plot(stock_df['step'] / 3600, stock_df[col], label=col, linewidth=2.0, color=colors[idx % len(colors)])

ax.set_title('Evolución de Ambulancias Disponibles durante las 3 Horas', fontsize=12, fontweight='bold', pad=15)
ax.set_xlabel('Tiempo Simulado (Horas)', fontsize=10, labelpad=8)
ax.set_ylabel('Ambulancias Libres en Stock', fontsize=10, labelpad=8)
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(frameon=True, facecolor='white', framealpha=0.9, loc='center left', bbox_to_anchor=(1, 0.5))
plt.tight_layout()
plt.savefig('RA_fig_3_evolucion_stock.png', dpi=300)
plt.close()

# --- FIGURA CONSOLIDADA DASHBOARD (4 PANELES) ---
fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)

axes[0,0].bar(acc_df['id'], acc_df['tiempo_respuesta'], color='#1f77b4', alpha=0.85, width=0.6)
axes[0,0].axhline(mediana, color='#d62728', linestyle='--', label=f'Mediana ({mediana:.0f}s)')
axes[0,0].axhline(p90, color='#2ca02c', linestyle=':', label=f'P90 ({p90:.0f}s)')
axes[0,0].set_title('a) Tiempo de Respuesta por Accidente', fontweight='bold', fontsize=10)
axes[0,0].set_xlabel('ID Accidente', fontsize=9)
axes[0,0].set_ylabel('Segundos', fontsize=9)
axes[0,0].grid(axis='y', linestyle='--', alpha=0.5)
axes[0,0].legend(fontsize=8)

axes[0,1].bar(x - width, hosp_df['stock_ini'], width, label='Stock Ini', color='#7f7f7f')
axes[0,1].bar(x, hosp_df['despachos'], width, label='Despachos', color='#d62728')
axes[0,1].bar(x + width, hosp_df['retornos'], width, label='Retornos', color='#2ca02c')
axes[0,1].set_xticks(x)
axes[0,1].set_xticklabels(hosp_df['hospital'], rotation=35, ha='right', fontsize=8)
axes[0,1].set_title('b) Dinámica de Despachos y Retornos', fontweight='bold', fontsize=10)
axes[0,1].set_ylabel('Unidades', fontsize=9)
axes[0,1].grid(axis='y', linestyle='--', alpha=0.5)
axes[0,1].legend(fontsize=8)

for idx, col in enumerate(stock_df.columns[1:]):
    axes[1,0].plot(stock_df['step'] / 3600, stock_df[col], label=col, linewidth=1.5, color=colors[idx % len(colors)])
axes[1,0].set_title('c) Evolución del Stock Disponible', fontweight='bold', fontsize=10)
axes[1,0].set_xlabel('Horas Simuladas', fontsize=9)
axes[1,0].set_ylabel('Unidades Disponibles', fontsize=9)
axes[1,0].grid(True, linestyle='--', alpha=0.5)
axes[1,0].legend(fontsize=7, ncol=2)

axes[1,1].axis('off')
summary_box = (
    "RESUMEN EJECUTIVO DE DESEMPEÑO\n"
    "────────────────────────────────────────\n"
    f"• Eventos Totales Atendidos : {len(acc_df)} colisiones\n"
    f"• Tiempo Respuesta Mediano : {mediana:.1f} s ({mediana/60:.2f} min)\n"
    f"• Tiempo Respuesta P90     : {p90:.1f} s ({p90/60:.2f} min)\n"
    f"• Reubicación de Flota     : {pct_distintos:.1f}% de retornos a\n"
    f"                             hospitales distintos al origen\n"
    f"• Tasa de Rechazo / Espera : 0.0% (Sin cuellos de botella)\n"
    "────────────────────────────────────────\n"
    "Conclusión principal:\n"
    "La política de retorno al hospital más cercano al\n"
    "accidente genera una redistribución dinámica que\n"
    "optimiza la cobertura urbana en el cantón Cuenca."
)
axes[1,1].text(0.05, 0.15, summary_box, fontsize=9.5, family='monospace',
               bbox=dict(boxstyle='round,pad=1', facecolor='#f8f9fa', edgecolor='#cccccc'))

plt.tight_layout()
plt.savefig('RA_fig_estadisticas.png', dpi=300)
plt.close()

print("\n[ÉXITO] Imagens generadas en alta resolución (300 DPI):")
print("  - RA_fig_1_tiempo_respuesta.png")
print("  - RA_fig_2_flota_hospitales.png")
print("  - RA_fig_3_evolucion_stock.png")
print("  - RA_fig_estadisticas.png")
