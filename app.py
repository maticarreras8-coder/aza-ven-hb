import json
from datetime import date
import streamlit as st
import streamlit.components.v1 as components

from azaven.engine import CycleInput, run_engine, resumen_humano

st.set_page_config(page_title="Aza/Ven – Ajuste por citopenias (HB)", layout="centered")

st.title("Aza/Ven – Ajuste por citopenias (HB) – Adultos")
st.caption("Motor institucional (Dr. Matías Carreras) – prototipo")

# Header actions
colH1, colH2, colH3 = st.columns([3, 1, 1])

with colH2:
    if st.button("⬆️ Arriba"):
        components.html("<script>window.scrollTo(0,0);</script>", height=0)


def reset_form():
    # Reset all widget/session state keys
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


with colH3:
    st.button("🧹 Limpiar", on_click=reset_form)

with colH1:
    with st.popover("ℹ️ Referencias / Notas"):
        st.markdown("- Guía HB: (pegá acá link interno o doc institucional)")
        st.markdown("- Publicaciones / consensos: (pegá links)")
        st.markdown("- **Disclaimer**: herramienta de apoyo, no reemplaza juicio clínico.")


with st.form("form"):
    st.subheader("Datos del paciente")
    edad = st.number_input("Edad (años) – Adultos (≥18)", min_value=18, max_value=120, value=72, step=1)
    sexo = st.selectbox("Sexo", ["NA", "F", "M", "X"], index=0)

    st.subheader("Ciclo actual")
    ciclo_numero = st.number_input("Número de ciclo", min_value=1, max_value=50, value=2, step=1)
    fecha_inicio_ciclo = st.date_input("Fecha inicio de ciclo", value=date(2025, 11, 1))

    # Session-state checkbox so it behaves well with reset and reruns
    if "usar_fecha_siguiente" not in st.session_state:
        st.session_state.usar_fecha_siguiente = True

    usar_fecha_siguiente = st.checkbox(
        "Tengo fecha de inicio del próximo ciclo (real/planificada)",
        key="usar_fecha_siguiente"
    )

    fecha_inicio_siguiente_ciclo = None
    if usar_fecha_siguiente:
        fecha_inicio_siguiente_ciclo = st.date_input(
            "Fecha inicio del próximo ciclo",
            value=date.today()
        )

    st.subheader("PAMO / respuesta (si la tenés)")
    pamo = st.radio("PAMO", ["No realizado", "Realizado"], horizontal=True, index=0)

    resultado_pamo = "ND"
    blastos_medula_pct = None

    if pamo == "Realizado":
        col1, col2 = st.columns(2)
        with col1:
            resultado_pamo = st.selectbox(
                "Resultado (opcional)",
                ["ND", "A (<5% blastos)", "B (≥5% blastos)"],
                index=1
            )
        with col2:
            blastos_medula_pct = st.number_input(
                "% blastos médula (opcional)",
                min_value=0.0, max_value=100.0, value=0.0, step=0.5
            )

    st.subheader("Hemograma / citopenias")

    c_anc, u_anc = st.columns([4, 1])
    with c_anc:
        anc_actual = st.number_input("ANC actual", min_value=0, max_value=200000, value=600, step=50)
    with u_anc:
        st.markdown("**/µL**")

    c_plt, u_plt = st.columns([4, 1])
    with c_plt:
        plt_actual = st.number_input("Plaquetas actuales", min_value=0, max_value=2000000, value=42000, step=1000)
    with u_plt:
        st.markdown("**/µL**")

    neutropenia_g4 = st.checkbox("Neutropenia G4 (o ANC<500)", value=True)
    plt_lt_25k_dias = st.number_input("Días con PLT <25.000 (si aplica)", min_value=0, max_value=365, value=0, step=1)

    st.subheader("Tratamiento (para inferir nivel actual)")
    col3, col4 = st.columns(2)
    with col3:
        aza_dosis = st.number_input("AZA dosis (mg/m²)", min_value=0.0, max_value=200.0, value=75.0, step=5.0)
        aza_dias = st.number_input("AZA días", min_value=0, max_value=14, value=7, step=1)
    with col4:
        ven_obj = st.number_input("VEN dosis objetivo (mg)", min_value=0, max_value=600, value=400, step=50)
        ven_dias_plan = st.number_input("VEN días plan", min_value=0, max_value=28, value=21, step=1)

    st.subheader("Antifúngico (HB)")
    antif = st.selectbox("Antifúngico", ["none", "isavuconazole", "voriconazole", "posaconazole"], index=3)

    st.subheader("Contexto del delay / intercurrencias")
    motivo_delay = st.selectbox(
        "Motivo principal de demora (si aplica)",
        ["ninguno", "citopenias_tratamiento", "infeccion", "sangrado", "internacion", "otro"],
        index=0
    )
    infeccion_fiebre = st.checkbox("Fiebre / infección intercurrente (flag)", value=False)

    st.subheader("Soporte (opcional)")
    uso_gcsf = st.checkbox("Usó/usa G-CSF", value=False)
    transf_gr = st.checkbox("Transfusión de GR", value=False)
    transf_plt = st.checkbox("Transfusión de plaquetas", value=False)

    with st.expander("📘 Abreviaturas"):
        st.markdown("""
- **PAMO**: punción aspiración de médula ósea  
- **ANC**: neutrófilos absolutos  
- **PLT**: plaquetas  
- **G4**: grado 4  
""")

    submitted = st.form_submit_button("Calcular recomendación")


if submitted:
    # Mapear resultado_pamo
    res_pamo = None
    if resultado_pamo.startswith("A"):
        res_pamo = "A"
    elif resultado_pamo.startswith("B"):
        res_pamo = "B"

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
        "resultado_pamo": res_pamo,
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
