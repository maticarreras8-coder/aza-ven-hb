import json
from datetime import date
import streamlit as st

from azaven.engine import CycleInput, run_engine, resumen_humano

st.set_page_config(page_title="Aza/Ven – Ajuste por citopenias (HB)", layout="centered")

st.title("Aza/Ven – Ajuste por citopenias (Hospital Británico)")
st.caption("Motor institucional (Dr. Matías Carreras) – prototipo")

with st.form("form"):
    st.subheader("Datos del paciente")
    edad = st.number_input("Edad (años)", min_value=0, max_value=120, value=72, step=1)
    sexo = st.selectbox("Sexo", ["NA", "F", "M", "X"], index=0)

    st.subheader("Ciclo actual")
    ciclo_numero = st.number_input("Número de ciclo", min_value=1, max_value=50, value=2, step=1)
    fecha_inicio_ciclo = st.date_input("Fecha inicio de ciclo", value=date(2025, 11, 1))
    usar_fecha_siguiente = st.checkbox("Tengo fecha de inicio del próximo ciclo (real/planificada)", value=True)
    fecha_inicio_siguiente_ciclo = None
    if usar_fecha_siguiente:
        fecha_inicio_siguiente_ciclo = st.date_input("Fecha inicio del próximo ciclo", value=date(2025, 12, 20))

    st.subheader("PAMO / respuesta (si la tenés)")
    col1, col2 = st.columns(2)
    with col1:
        resultado_pamo = st.selectbox("Resultado (opcional)", ["ND", "A (<5% blastos)", "B (≥5% blastos)"], index=1)
    with col2:
        blastos_medula_pct = st.number_input("% blastos médula (opcional)", min_value=0.0, max_value=100.0, value=1.0, step=0.5)

    st.subheader("Hemograma / citopenias")
    anc_actual = st.number_input("ANC actual", min_value=0, max_value=200000, value=600, step=50)
    plt_actual = st.number_input("Plaquetas actuales", min_value=0, max_value=2000000, value=42000, step=1000)
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
        "blastos_medula_pct": float(blastos_medula_pct),
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
