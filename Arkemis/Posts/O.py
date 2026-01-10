import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.style as style

# --- CONFIGURAZIONE STILE ---
style.use('dark_background')
mint_green = '#98f5e1'  # Colore specifico richiesto

# Configurazione globale dei parametri grafici per alta leggibilità su mobile
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['text.color'] = mint_green
plt.rcParams['axes.labelcolor'] = mint_green
plt.rcParams['xtick.color'] = mint_green
plt.rcParams['ytick.color'] = mint_green
plt.rcParams['axes.edgecolor'] = mint_green
plt.rcParams['grid.color'] = '#003322'  # Verde molto scuro per la griglia
plt.rcParams['font.size'] = 14

# --- DATI SIMULAZIONE ---
N_max = 15  # Riduco leggermente N per rendere l'animazione più fluida visivamente
N_values = np.arange(0.1, N_max + 0.1, 0.1) # Più punti per fluidità
num_frames = len(N_values)

# Funzioni di complessità (Scanate per visualizzazione)
def f_O1(n): return np.ones_like(n) * 2
def f_OlogN(n): return np.log2(n) * 5
def f_On(n): return n * 2
def f_OnLogN(n): return n * np.log2(n) * 1.5
def f_On2(n): return (n**2) / 1.5
def f_O2n(n): return 2**n / 2

# --- SETUP GRAFICO (9:16 VERTICALE) ---
fig, ax = plt.subplots(figsize=(9, 16), dpi=120) # Formato Reel
fig.patch.set_facecolor('black')
ax.set_facecolor('black')

# Rimuovo i bordi superiori e destri per uno stile più pulito
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Griglia
ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.4)

# Inizializzazione linee vuote con stili diversi per distinguerle
# Uso lo stesso colore (mint_green) ma cambio tratteggio e spessore
lines = []
styles = [
    ('-', 5, 'O(2^n)'),      # Esponenziale - Molto spessa
    ('--', 4, 'O(n^2)'),     # Quadratica - Spessa tratteggiata
    ('-', 3, 'O(n log n)'),  # Lineareitmica - Media
    (':', 3, 'O(n)'),        # Lineare - Punti
    ('-.', 2, 'O(log n)'),   # Logaritmica - Tratto punto
    ('-', 2, 'O(1)')         # Costante - Sottile
]

for style, width, label in styles:
    line, = ax.plot([], [], color=mint_green, linestyle=style, linewidth=width, label=label)
    lines.append(line)

(line_O2n, line_On2, line_OnLogN, line_On, line_OlogN, line_O1) = lines

# Limiti assi fissi per l'effetto "riempimento"
ax.set_xlim(0, N_max)
ax.set_ylim(0, 150) # Taglio l'esponenziale per mostrarne la velocità

# Etichette
ax.set_xlabel('Input Size (N)', fontsize=20, labelpad=20)
ax.set_ylabel('Operations / Time', fontsize=20, labelpad=20)
ax.set_title('Big O Complexity\nVisualized', fontsize=30, fontweight='bold', pad=30, color=mint_green)

# Legenda posizionata in alto a sinistra (dove le curve basse lasciano spazio)
legend = ax.legend(loc='upper left', frameon=False, fontsize=16)
for text in legend.get_texts():
    text.set_color(mint_green)

# Testo dinamico per il valore di N corrente
counter_text = ax.text(0.5, 0.85, '', transform=ax.transAxes, 
                       ha='center', fontsize=24, fontweight='bold', color=mint_green)

# --- ANIMAZIONE ---
def init():
    for line in lines:
        line.set_data([], [])
    counter_text.set_text('')
    return lines + [counter_text]

def animate(i):
    current_n = N_values[:i+1]
    
    # Aggiornamento dati
    line_O1.set_data(current_n, f_O1(current_n))
    line_OlogN.set_data(current_n, f_OlogN(current_n))
    line_On.set_data(current_n, f_On(current_n))
    line_OnLogN.set_data(current_n, f_OnLogN(current_n))
    line_On2.set_data(current_n, f_On2(current_n))
    line_O2n.set_data(current_n, f_O2n(current_n))
    
    # Aggiornamento contatore
    if len(current_n) > 0:
        val = current_n[-1]
        counter_text.set_text(f'N = {int(val)}')
    
    return lines + [counter_text]

ani = animation.FuncAnimation(fig, animate, init_func=init, frames=num_frames, interval=50, blit=True)

# Salvataggio
try:
    print("Generating Reel format video...")
    ani.save('big_o_reel.mp4', writer='ffmpeg', fps=30, dpi=120)
    print("Video 'big_o_reel.mp4' salvato con successo!")
except Exception as e:
    print(f"Errore nel salvataggio: {e}")

plt.close()