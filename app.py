import json
from datetime import date
import streamlit as st

from azaven.engine import CycleInput, run_engine, resumen_humano

st.set_page_config(page_title="Aza/Ven – Ajuste por citopenias (HB)", layout="centered")

# ---------- Defaults & Reset ----------
DEFAULTS = {
    "edad": 72,
    "sexo": "NA",
    "ciclo_numero": 2,
    "fecha_inicio_ciclo": date(2025, 11, 1),
    "usar_fecha_siguiente": True,
    "fecha_inicio_siguiente_ciclo": date.today(),

    "pamo_realizada": "No realizado",
    "blastos_medula_pct": None,
    "escenario_pamo": "ND",

    "anc_actual": 600,
    "plt_actual": 42000,
    "neutropenia_g4": True,
    "plt_lt_25k_dias": 0,

    "aza_dosis": 75.0,
    "aza_dias": 7,
    "ven_obj": 400,
    "ven_dias_plan": 21,

    "antif": "posaconazole",
    "motivo_delay": "ninguno",
    "infeccion_fiebre": False,

    "uso_gcsf": False,
    "transf_gr": False,
    "transf_plt": False,
}

def reset_form():
    # reset SOLO nuestras keys
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.rerun()

# init defaults
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------- Header ----------
st.title("Aza/Ven – Ajuste por citopenias (HB) – Adultos")
st.caption("Motor institucional (Dr. Matías Carreras) – prototipo")

# ---------- Sidebar (siempre visible al scrollear) ----------
with st.sidebar:
    st.markdown("## Acciones")
    if st.button("⬆️ Arriba"):
        # Sidebar siempre visible; igual dejamos el scroll-to-top simple
        st.markdown("<script>window.scrollTo(0,0);</script>", unsafe_allow_html=True)

    st.button("🧹 Limpiar formulario", on_click=reset_form)

    st.markdown("---")
    with st.expander("ℹ️ Referencias / Notas", expanded=False):
        st.markdown("- Guía HB: **(pegá acá el link)**")
        st.markdown("- Publicaciones/consensos: **(pegá acá links)**")
        st.markdown("- Disclaimer: herramienta de apoyo, no reemplaza juicio clínico.")

    with st.expander("📘 Abreviaturas", expanded=False):
        st.markdown("""
- **PAMO**: punción aspiración de médula ósea  
- **ANC**: neutrófilos absolutos  
- **PLT**: plaquetas  
- **G4**: grado 4  
""")


# ---------- Main Form ----------
with st.form("form"):
    st.subheader("Datos del paciente")
    edad = st.number_input(
        "Edad (años) – Adultos (≥18)",
        min_value=18, max_value=120, step=1,
        key="edad"
    )
    sexo = st.selectbox("Sexo", ["NA", "F", "M", "X"], index=["NA","F","M","X"].index(st.session_state["sexo"]), key="sexo")

    st.subheader("Ciclo actual")
    ciclo_numero = st.number_input("Número de ciclo", min_value=1, max_value=50, step=1, key="ciclo_numero")
    fecha_inicio_ciclo = st.date_input("Fecha inicio de ciclo", key="fecha_inicio_ciclo")

    usar_fecha_siguiente = st.checkbox(
        "Tengo fecha de inicio del próximo ciclo (real/planificada)",
        key="usar_fecha_siguiente"
    )

    fecha_inicio_siguiente_ciclo = None
    if usar_fecha_siguiente:
        fecha_inicio_siguiente_ciclo = st.date_input(
            "Fecha inicio del próximo ciclo",
            key="fecha_inicio_siguiente_ciclo"
        )

    st.subheader("PAMO / respuesta")
    pamo_realizada = st.radio("PAMO", ["No realizado", "Realizado"], horizontal=True, key="pamo_realizada")

    resultado_pamo = "ND"
    blastos_medula_pct = None

    if pamo_realizada == "Realizado":
        # 1) blastos
        blastos_medula_pct = st.number_input(
            "% blastos médula",
            min_value=0.0, max_value=100.0, step=0.5,
            value=0.0 if st.session_state["blastos_medula_pct"] is None else float(st.session_state["blastos_medula_pct"]),
            key="blastos_medula_pct",
            help="Si no tenés el porcentaje, poné el mejor estimado o usá 'No realizado'."
        )

        # 2) escenarios derivados + opción manual
        #    A: <5% ; B: ≥5% (como base)
        derivado = "A" if blastos_medula_pct < 5 else "B"
        st.caption(f"Escenario sugerido por blastos: **{derivado}**")

        escenario_pamo = st.radio(
            "Escenario PAMO (podés forzarlo si tu criterio clínico difiere)",
            options=["A (<5% blastos)", "B (≥5% blastos)", "ND"],
            index=0 if derivado == "A" else 1,
            key="escenario_pamo"
        )

        if escenario_pamo.startswith("A"):
            resultado_pamo = "A"
        elif escenario_pamo.startswith("B"):
            resultado_pamo = "B"
        else:
            resultado_pamo = "ND"
    else:
        # no realizado => ND y sin blastos
        st.session_state["blastos_medula_pct"] = None
        st.session_state["escenario_pamo"] = "ND"
        resultado_pamo = "ND"
        blastos_medula_pct = None

    st.subheader("Hemograma / citopenias")
    # Unidades en el label (nunca se desalinean)
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
    antif = st.selectbox("Antifúngico", ["none", "isavuconazole", "voriconazole", "posaconazole"],
                         index=["none","isavuconazole","voriconazole","posaconazole"].index(st.session_state["antif"]),
                         key="antif")

    st.subheader("Contexto del delay / intercurrencias")
    motivo_delay = st.selectbox(
        "Motivo principal de demora (si aplica)",
        ["ninguno", "citopenias_tratamiento", "infeccion", "sangrado", "internacion", "otro"],
        index=["ninguno","citopenias_tratamiento","infeccion","sangrado","internacion","otro"].index(st.session_state["motivo_delay"]),
        key="motivo_delay"
    )
    infeccion_fiebre = st.checkbox("Fiebre / infección intercurrente (flag)", key="infeccion_fiebre")

    st.subheader("Soporte (opcional)")
    uso_gcsf = st.checkbox("Usó/usa G-CSF", key="uso_gcsf")
    transf_gr = st.checkbox("Transfusión de GR", key="transf_gr")
    transf_plt = st.checkbox("Transfusión de plaquetas", key="transf_plt")

    submitted = st.form_submit_button("Calcular recomendación")


# ---------- Run engine ----------
if submitted:
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
        "blastos_medula_pct": (float(blastos_medula_pct) if blastos_medula_pct is not None else None),
        "resultado_pamo": (None if resultado_pamo == "ND" else resultado_pamo),
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
