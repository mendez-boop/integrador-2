import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# LÓGICA DE SIMULACIÓN MATEMÁTICA Y NEGOCIO
# ==========================================

def generar_demanda(num_dias, demandas, probabilidades, semilla=None):
    """
    Genera la demanda simulada utilizando la distribución acumulada[cite: 131, 132, 133, 173].
    """
    if semilla is not None:
        np.random.seed(semilla)
        
    # Calcular la distribución acumulada
    prob_acumulada = np.cumsum(probabilidades)
    
    # Generar números aleatorios uniformes U(0,1)
    numeros_aleatorios = np.random.rand(num_dias)
    
    # Mapear los números aleatorios a la demanda discreta usando intervalos
    demanda_simulada = []
    for u in numeros_aleatorios:
        for i, p_acum in enumerate(prob_acumulada):
            if u <= p_acum:
                demanda_simulada.append(demandas[i])
                break
                
    return np.array(demanda_simulada), numeros_aleatorios

def simular_politica(Q, demanda_simulada, p_compra, p_venta, v_rescate, c_faltante):
    """
    Simula el desempeño económico de una política de inventario específica[cite: 134, 135, 136, 137].
    """
    dias = len(demanda_simulada)
    costo_compra = Q * p_compra
    
    # Cálculos vectorizados para eficiencia
    ventas_reales = np.minimum(demanda_simulada, Q)
    ingreso_ventas = ventas_reales * p_venta
    
    sobrantes = np.maximum(0, Q - demanda_simulada)
    ingreso_rescate = sobrantes * v_rescate
    
    faltantes = np.maximum(0, demanda_simulada - Q)
    costo_penalizacion = faltantes * c_faltante
    
    # Utilidad diaria
    utilidad_diaria = ingreso_ventas + ingreso_rescate - costo_compra - costo_penalizacion
    
    # Métricas agregadas
    utilidad_total = np.sum(utilidad_diaria)
    utilidad_promedio = np.mean(utilidad_diaria)
    freq_quiebre = np.sum(faltantes > 0) / dias
    freq_excedente = np.sum(sobrantes > 0) / dias
    promedio_sobrante = np.mean(sobrantes)
    promedio_faltante = np.mean(faltantes)
    
    return {
        "Q": Q,
        "Utilidad Total": utilidad_total,
        "Utilidad Promedio": utilidad_promedio,
        "Freq. Quiebre (%)": freq_quiebre * 100,
        "Freq. Excedente (%)": freq_excedente * 100,
        "Promedio Sobrante": promedio_sobrante,
        "Promedio Faltante": promedio_faltante,
        "Detalle Diario": pd.DataFrame({
            "Día": np.arange(1, dias + 1),
            "Demanda": demanda_simulada,
            "Inventario Inicial": Q,
            "Ventas Reales": ventas_reales,
            "Sobrante": sobrantes,
            "Faltante": faltantes,
            "Utilidad": utilidad_diaria
        })
    }

# ==========================================
# INTERFAZ GRÁFICA (STREAMLIT)
# ==========================================

st.set_page_config(page_title="Simulación Monte Carlo - Inventario", layout="wide")

st.title("🛒 Simulación Monte Carlo: Gestión de Inventarios")
st.markdown("""
Esta herramienta permite evaluar políticas de inventario bajo incertidumbre para un producto de alta rotación, 
optimizando la utilidad esperada considerando costos de compra, venta, rescate y penalización por faltantes.
""")

# --- BARRA LATERAL: PARÁMETROS DE ENTRADA ---
st.sidebar.header("Parámetros del Sistema")

# Parámetros Económicos [cite: 120, 153, 154, 155, 156]
st.sidebar.subheader("Parámetros Económicos (Bs)")
p_compra = st.sidebar.number_input("Precio de Compra", min_value=1.0, value=24.0, step=1.0)
p_venta = st.sidebar.number_input("Precio de Venta", min_value=1.0, value=33.0, step=1.0)
v_rescate = st.sidebar.number_input("Valor de Rescate", min_value=0.0, value=18.0, step=1.0)
c_faltante = st.sidebar.number_input("Costo por Faltante", min_value=0.0, value=6.0, step=1.0)

# Parámetros de Simulación [cite: 157, 167]
st.sidebar.subheader("Parámetros de Simulación")
dias_simulacion = st.sidebar.slider("Días a Simular", min_value=30, max_value=365, value=100, step=10)
semilla = st.sidebar.number_input("Semilla Aleatoria (0 para ninguna)", min_value=0, value=42, step=1)
semilla_val = int(semilla) if semilla > 0 else None

# Distribución de Demanda [cite: 119, 152]
st.sidebar.subheader("Distribución de Demanda")
demandas = [40, 50, 60, 70, 80, 90]
probabilidades_def = [0.10, 0.20, 0.30, 0.25, 0.10, 0.05]

# Políticas a evaluar [cite: 121, 158]
politicas = [50, 60, 70, 80, 90]

# --- EJECUCIÓN DE LA SIMULACIÓN ---
# 1. Generar la demanda única para todas las políticas para asegurar una comparación justa
demanda_simulada, nums_aleatorios = generar_demanda(dias_simulacion, demandas, probabilidades_def, semilla_val)

# 2. Simular cada política
resultados = []
detalles_por_politica = {}

for q in politicas:
    res = simular_politica(q, demanda_simulada, p_compra, p_venta, v_rescate, c_faltante)
    detalles_por_politica[q] = res.pop("Detalle Diario")
    resultados.append(res)

df_resultados = pd.DataFrame(resultados)

# Identificar la mejor política [cite: 161]
mejor_politica = df_resultados.loc[df_resultados["Utilidad Promedio"].idxmax()]

# --- VISUALIZACIÓN DE RESULTADOS ---

# 1. Métricas Principales [cite: 162]
st.header("🏆 Resultados de la Simulación")
st.success(f"**La mejor política de inventario es pedir {mejor_politica['Q']:.0f} unidades diarias.**")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Utilidad Promedio Diaria", f"Bs {mejor_politica['Utilidad Promedio']:.2f}")
col2.metric("Probabilidad de Quiebre", f"{mejor_politica['Freq. Quiebre (%)']:.1f} %")
col3.metric("Promedio Sobrante Diario", f"{mejor_politica['Promedio Sobrante']:.1f} un.")
col4.metric("Promedio Faltante Diario", f"{mejor_politica['Promedio Faltante']:.1f} un.")

# 2. Tabla Comparativa [cite: 160]
st.subheader("📊 Tabla Comparativa de Políticas")
st.dataframe(df_resultados.style.format({
    "Utilidad Total": "Bs {:.2f}",
    "Utilidad Promedio": "Bs {:.2f}",
    "Freq. Quiebre (%)": "{:.1f}%",
    "Freq. Excedente (%)": "{:.1f}%",
    "Promedio Sobrante": "{:.2f}",
    "Promedio Faltante": "{:.2f}"
}), use_container_width=True)

# 3. Gráficos Comparativos [cite: 163]
col_g1, col_g2 = st.columns(2)

with col_g1:
    # Gráfico de utilidad promedio por política [cite: 164]
    fig1 = px.bar(df_resultados, x="Q", y="Utilidad Promedio", 
                  title="Utilidad Promedio por Política de Inventario",
                  labels={"Q": "Inventario Inicial (Q)", "Utilidad Promedio": "Utilidad (Bs)"},
                  color="Utilidad Promedio", color_continuous_scale="Viridis")
    st.plotly_chart(fig1, use_container_width=True)

with col_g2:
    # Gráfico de frecuencia de faltantes [cite: 165]
    fig2 = px.bar(df_resultados, x="Q", y="Freq. Quiebre (%)", 
                  title="Frecuencia de Quiebre de Stock por Política",
                  labels={"Q": "Inventario Inicial (Q)", "Freq. Quiebre (%)": "Quiebres (%)"},
                  color="Freq. Quiebre (%)", color_continuous_scale="Reds")
    st.plotly_chart(fig2, use_container_width=True)

# 4. Evolución Diaria (Análisis Detallado) [cite: 166]
st.subheader("📈 Evolución Diaria de la Política Seleccionada")
q_seleccionada = st.selectbox("Seleccione una política para ver su evolución:", politicas, index=politicas.index(mejor_politica['Q']))

df_detalle = detalles_por_politica[q_seleccionada]

fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=df_detalle["Día"], y=df_detalle["Demanda"], mode='lines+markers', name='Demanda Real', line=dict(color='blue')))
fig3.add_trace(go.Scatter(x=df_detalle["Día"], y=df_detalle["Inventario Inicial"], mode='lines', name='Inventario Inicial (Q)', line=dict(color='green', dash='dash')))
fig3.update_layout(title=f"Evolución de Demanda vs Inventario (Q={q_seleccionada})", xaxis_title="Día", yaxis_title="Unidades")
st.plotly_chart(fig3, use_container_width=True)

# 5. Conclusión Automática (Interpretación Técnica) [cite: 168, 169, 170]
st.subheader("🧠 Análisis Ejecutivo Automático")

motivo_ganancia = ""
if mejor_politica['Q'] < 70:
    motivo_ganancia = "minimizar el costo de capital inmovilizado y los productos sobrantes, aprovechando el valor de rescate[cite: 117]."
else:
    motivo_ganancia = "capturar la mayor cantidad de ventas posibles, evitando la alta penalización económica por falta de stock[cite: 116, 120]."

sacrificio = ""
if mejor_politica['Freq. Quiebre (%)'] > 20:
    sacrificio = f"Se asume un riesgo significativo de quiebre de stock del {mejor_politica['Freq. Quiebre (%)']:.1f}%, lo que podría afectar la satisfacción del cliente a largo plazo[cite: 116]."
else:
    sacrificio = f"Se asume un costo por excedente frecuente, ya que en el {mejor_politica['Freq. Excedente (%)']:.1f}% de los días sobra producto que debe ser liquidado a precio de rescate[cite: 117]."

st.info(f"""
**Interpretación:** La política óptima de **{mejor_politica['Q']:.0f} unidades** logra el mejor equilibrio financiero porque permite {motivo_ganancia} 

**Trade-off (Sacrificio):** {sacrificio}
""")
