import json
from datetime import date
import streamlit as st
import streamlit.components.v1 as components

from azaven.engine import CycleInput, run_engine, resumen_humano

st.set_page_config(page_title="Aza/Ven – Ajuste por citopenias (HB)", layout="centered")

# -------------------------
# Defaults + Reset robusto
# -------------------------
DEFAULTS = {
    # Paciente
    "edad": 72,
    "sexo": "NA",

    # Ciclo
    "ciclo_numero": 2,
    "fecha_inicio_ciclo": date(2025, 11, 1),
    "usar_fecha_siguiente": True,
    "fecha_inicio_siguiente_ciclo": date.today(),

    # PAMO
    "pamo_realizada": "No realizado",
    "resultado_pamo_label": "ND",
    "blastos_text": "",

    # Hemograma
    "anc_actual": 600,
    "plt_actual": 42000,
    "neutropenia_g4": True,
    "plt_lt_25k_dias": 0,

    # Tratamiento
    "aza_dosis": 75.0,
    "aza_dias": 7,
    "ven_obj": 400,
    "ven_dias_plan": 21,

    # Antifúngico
    "antif": "posaconazole",

    # Delay
    "motivo_delay": "ninguno",
    "infeccion_fiebre": False,

    # Soporte
    "uso_gcsf": False,
    "transf_gr": False,
    "transf_plt": False,

    # Referencias (editables)
    "ref_guia": "",
    "ref_paper": "",
}

def init_defaults():
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_form():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    # cerrar refs si estaba abierto
    st.session_state["show_refs"] = False
    st.rerun()

def scroll_top():
    components.html("<script>window.scrollTo(0,0);</script>", height=0)

init_defaults()
if "show_refs" not in st.session_state:
    st.session_state["show_refs"] = False


# -------------------------
# Header
# -------------------------
st.title("Aza/Ven – Ajuste por citopenias (Hospital Británico) – Adultos")
st.caption("Motor institucional (Dr. Matías Carreras) – prototipo")

colH1, colH2, colH3, colH4 = st.columns([7, 1, 1, 1])

with colH2:
    if st.button("ℹ️", key="btn_info", help="Referencias / guía"):
        st.session_state["show_refs"] = not st.session_state["show_refs"]

with colH3:
    st.button("🧹", key="btn_reset", help="Limpiar formulario", on_click=reset_form)

with colH4:
    if st.button("⬆️", key="btn_top", help="Ir arriba"):
        scroll_top()

# Referencias (como pidió el doc: botón info con links)
if st.session_state["show_refs"]:
    with st.expander("ℹ️ Referencias / guía (pegá tus links)", expanded=True):
        st.text_input("Guía HB (link)", key="ref_guia", placeholder="https://...")
        st.text_input("Paper / consenso (link)", key="ref_paper", placeholder="https://...")
        st.markdown("- Disclaimer: herramienta de apoyo; no reemplaza juicio clínico.")
        if st.button("Cerrar", key="btn_close_refs"):
            st.session_state["show_refs"] = False
            st.rerun()

st.divider()


# -------------------------
# Inputs (SIN st.form -> reactivos)
# -------------------------
st.subheader("Datos del paciente")
edad = st.number_input("Edad (años) – Adultos (≥18)", min_value=18, max_value=120, step=1, key="edad")
sexo = st.selectbox("Sexo", ["NA", "F", "M", "X"], key="sexo")

st.subheader("Ciclo actual")
ciclo_numero = st.number_input("Número de ciclo", min_value=1, max_value=50, step=1, key="ciclo_numero")
fecha_inicio_ciclo = st.date_input("Fecha inicio de ciclo", key="fecha_inicio_ciclo")

usar_fecha_siguiente = st.checkbox(
    "Tengo fecha de inicio del próximo ciclo (real/planificada)",
    key="usar_fecha_siguiente"
)

fecha_inicio_siguiente_ciclo = None
if usar_fecha_siguiente:
    fecha_inicio_siguiente_ciclo = st.date_input("Fecha inicio del próximo ciclo", key="fecha_inicio_siguiente_ciclo")
else:
    fecha_inicio_siguiente_ciclo = None  # desaparece instantáneo


st.subheader("PAMO / respuesta")
pamo_realizada = st.radio("PAMO", ["No realizado", "Realizado"], horizontal=True, key="pamo_realizada")

resultado_pamo = None          # para el motor
blastos_medula_pct = None      # para el motor

if pamo_realizada == "Realizado":
    # Escenarios como estaban: ND/A/B
    resultado_pamo_label = st.selectbox(
        "Escenario (si la tenés)",
        ["ND", "A (<5% blastos)", "B (≥5% blastos)"],
        key="resultado_pamo_label"
    )

    # Blastos opcional real (vacío => None; evita el “0” por defecto)
    blastos_text = st.text_input(
        "% blastos médula (opcional) – dejá vacío si no lo tenés",
        key="blastos_text",
        placeholder="Ej: 1.5"
    ).strip()

    if blastos_text != "":
        try:
            blastos_medula_pct = float(blastos_text.replace(",", "."))
            if not (0.0 <= blastos_medula_pct <= 100.0):
                st.error("Blastos: debe estar entre 0 y 100.")
                blastos_medula_pct = None
        except ValueError:
            st.error("Blastos: ingresá un número válido (ej 1.5).")
            blastos_medula_pct = None

    # map a lo que espera el motor
    if resultado_pamo_label.startswith("A"):
        resultado_pamo = "A"
    elif resultado_pamo_label.startswith("B"):
        resultado_pamo = "B"
    else:
        resultado_pamo = None
else:
    # No realizado => limpiar campos y dejar Nones
    st.session_state["resultado_pamo_label"] = "ND"
    st.session_state["blastos_text"] = ""
    resultado_pamo = None
    blastos_medula_pct = None


st.subheader("Hemograma / citopenias")
anc_actual = st.number_input("ANC actual (/µL)", min_value=0, max_value=200000, step=50, key="anc_actual")
plt_actual = st.number_input("Plaquetas actuales (/µL)", min_value=0, max_value=2000000, step=1000, key="plt_actual")
neutropenia_g4 = st.checkbox("Neutropenia G4 (o ANC<500)", key="neutropenia_g4")
plt_lt_25k_dias = st.number_input("Días con PLT <25.000 (si aplica)", min_value=0, max_value=365, step=1, key="plt_lt_25k_dias")


st.subheader("Tratamiento (para inferir nivel actual)")
col3, col4 = st.columns(2)
with col3:
    aza_dosis = st.number_input("AZA dosis (mg/m²)", min_value=0.0, max_value=200.0, step=5.0, key="aza_dosis")
    aza_dias = st.number_input("AZA días", min_value=0, max_value=14, step=1, key="aza_dias")
with col4:
    ven_obj = st.number_input("VEN dosis objetivo (mg)", min_value=0, max_value=600, step=50, key="ven_obj")
    ven_dias_plan = st.number_input("VEN días plan", min_value=0, max_value=28, step=1, key="ven_dias_plan")


st.subheader("Antifúngico (HB)")
antif = st.selectbox(
    "Antifúngico",
    ["none", "isavuconazole", "voriconazole", "posaconazole"],
    key="antif"
)

st.subheader("Contexto del delay / intercurrencias")
motivo_delay = st.selectbox(
    "Motivo principal de demora (si aplica)",
    ["ninguno", "citopenias_tratamiento", "infeccion", "sangrado", "internacion", "otro"],
    key="motivo_delay"
)
infeccion_fiebre = st.checkbox("Fiebre / infección intercurrente (flag)", key="infeccion_fiebre")

st.subheader("Soporte (opcional)")
uso_gcsf = st.checkbox("Usó/usa G-CSF", key="uso_gcsf")
transf_gr = st.checkbox("Transfusión de GR", key="transf_gr")
transf_plt = st.checkbox("Transfusión de plaquetas", key="transf_plt")

st.divider()

calcular = st.button("Calcular recomendación", type="primary", key="btn_calcular")


# -------------------------
# Run engine
# -------------------------
if calcular:
    payload = {
        "edad": int(edad),
        "sexo": sexo,
        "ciclo_numero": int(ciclo_numero),
        "fecha_inicio_ciclo": str(fecha_inicio_ciclo),

        "anc_actual": int(anc_actual),
        "plt_actual": int(plt_actual),
        "neutropenia_g4": bool(neutropenia_g4),
        "plt_lt_25k_dias": int(plt_lt_25k_dias),

        "aza_dosis_mg_m2": float(aza_dosis),
        "aza_dias_total": int(aza_dias),

        "ven_dosis_objetivo_mg": int(ven_obj),
        "ven_dias_plan": int(ven_dias_plan),

        "antifungico_clase": antif,

        "motivo_delay": motivo_delay,
        "infeccion_fiebre_intercurrencia": bool(infeccion_fiebre),

        "uso_gcsf": bool(uso_gcsf),
        "transfusion_gr": bool(transf_gr),
        "transfusion_plaquetas": bool(transf_plt),

        "blastos_medula_pct": blastos_medula_pct,
        "resultado_pamo": resultado_pamo,
    }

    if usar_fecha_siguiente and fecha_inicio_siguiente_ciclo:
        payload["fecha_inicio_siguiente_ciclo"] = str(fecha_inicio_siguiente_ciclo)

    try:
        out = run_engine(CycleInput(**payload))
        texto = resumen_humano(out)

        st.success("Listo. Recomendación generada.")
        st.text_area("Salida (copiar/pegar)", value=texto, height=320)

        colA, colB = st.columns(2)
        with colA:
            st.download_button(
                "Descargar TXT",
                data=texto.encode("utf-8"),
                file_name="recomendacion_aza_ven.txt",
                mime="text/plain",
            )
        with colB:
            st.download_button(
                "Descargar JSON (input)",
                data=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="input_aza_ven.json",
                mime="application/json",
            )

        with st.expander("Ver input JSON"):
            st.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json")

    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Tip: revisá campos obligatorios o valores fuera de rango.")
