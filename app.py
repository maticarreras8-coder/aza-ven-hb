import json
from datetime import date
import streamlit as st
import streamlit.components.v1 as components

from azaven.engine import CycleInput, run_engine, resumen_humano

st.set_page_config(page_title="Aza/Ven – Ajuste por citopenias (HB)", layout="centered")

# =========================
#  RED + BLUE THEME (CSS)
# =========================
st.markdown(
    """
<style>
/* Palette */
:root{
  --hb-blue:#0B3D91;
  --hb-red:#C1121F;
  --hb-ice:#F6F8FC;
  --hb-ink:#0B1220;
  --hb-muted:#5B677A;
  --hb-border:#E6EAF2;
}

/* App background */
.stApp{
  background: linear-gradient(180deg, var(--hb-ice) 0%, #FFFFFF 60%);
  color: var(--hb-ink);
}

/* Titles */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3{
  letter-spacing: -0.2px;
}
h1{
  color: var(--hb-blue);
}
h2, h3{
  color: var(--hb-ink);
}

/* Subtle divider */
hr, .stDivider{
  border-color: var(--hb-border) !important;
}

/* Buttons */
.stButton>button{
  border-radius: 10px !important;
  border: 1px solid var(--hb-border) !important;
  background: #FFFFFF !important;
  color: var(--hb-ink) !important;
  font-weight: 600 !important;
  padding: 0.55rem 0.85rem !important;
  transition: transform .02s ease-in-out, border-color .15s ease-in-out;
}
.stButton>button:hover{
  border-color: rgba(11,61,145,.35) !important;
}
.stButton>button:active{
  transform: translateY(1px);
}

/* Primary button override */
div.stButton > button[kind="primary"]{
  background: linear-gradient(90deg, var(--hb-blue) 0%, #174ea6 65%, var(--hb-red) 100%) !important;
  color: #FFFFFF !important;
  border: 0 !important;
}
div.stButton > button[kind="primary"]:hover{
  filter: brightness(1.03);
}

/* Inputs focus ring */
div[data-baseweb="input"] input:focus,
div[data-baseweb="textarea"] textarea:focus{
  box-shadow: 0 0 0 2px rgba(11,61,145,.18) !important;
  border-color: rgba(11,61,145,.35) !important;
}

/* Expander */
details{
  border: 1px solid var(--hb-border);
  border-radius: 12px;
  background: #FFFFFF;
  padding: 0.25rem 0.6rem;
}
summary{
  color: var(--hb-blue);
  font-weight: 700;
}

/* Success / error polish */
.stAlert [data-testid="stAlert"]{
  border-radius: 12px !important;
}

/* Caption */
small, .stCaption{
  color: var(--hb-muted) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Defaults + Reset
# =========================
DEFAULTS = {
    # language
    "lang": "ES",

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

    # UI
    "show_refs": False,
}

def init_defaults():
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_form():
    # Reset only our keys (no st.rerun here; click already triggers rerun)
    for k, v in DEFAULTS.items():
        st.session_state[k] = v

def scroll_top():
    components.html("<script>window.scrollTo(0,0);</script>", height=0)

init_defaults()

# =========================
# Language dict
# =========================
lang = st.session_state["lang"]
T = {
    "ES": {
        "title": "Aza/Ven – Ajuste por citopenias (Hospital Británico) – Adultos",
        "caption": "Motor institucional (Dr. Matías Carreras) – prototipo",
        "lang_label": "🌐 Idioma / Language",
        "refs_title": "ℹ️ Referencias / guía (pegá tus links)",
        "ref_guide": "Guía HB (link)",
        "ref_paper": "Paper / consenso (link)",
        "ref_disclaimer": "Disclaimer: herramienta de apoyo; no reemplaza juicio clínico.",
        "close": "Cerrar",
        "clear_help": "Limpiar formulario",
        "top_help": "Ir arriba",
        "refs_help": "Referencias / guía",
        "patient": "Datos del paciente",
        "age": "Edad (años) – Adultos (≥18)",
        "sex": "Sexo",
        "cycle": "Ciclo actual",
        "cycle_n": "Número de ciclo",
        "cycle_start": "Fecha inicio de ciclo",
        "has_next": "Tengo fecha de inicio del próximo ciclo (real/planificada)",
        "next_start": "Fecha inicio del próximo ciclo",
        "pamo": "PAMO / respuesta",
        "pamo_done": "PAMO",
        "not_done": "No realizado",
        "done": "Realizado",
        "pamo_scenario": "Escenario (si la tenés)",
        "blasts": "% blastos médula (opcional) – dejá vacío si no lo tenés",
        "cbc": "Hemograma / citopenias",
        "anc": "ANC actual (/µL)",
        "plt": "Plaquetas actuales (/µL)",
        "g4": "Neutropenia G4 (o ANC<500)",
        "plt_days": "Días con PLT <25.000 (si aplica)",
        "treat": "Tratamiento (para inferir nivel actual)",
        "aza_dose": "AZA dosis (mg/m²)",
        "aza_days": "AZA días",
        "ven_goal": "VEN dosis objetivo (mg)",
        "ven_days": "VEN días plan",
        "antif": "Antifúngico (HB)",
        "delay": "Contexto del delay / intercurrencias",
        "delay_reason": "Motivo principal de demora (si aplica)",
        "fever": "Fiebre / infección intercurrente (flag)",
        "support": "Soporte (opcional)",
        "gcsf": "Usó/usa G-CSF",
        "rbc": "Transfusión de GR",
        "plt_tx": "Transfusión de plaquetas",
        "calc": "Calcular recomendación",
        "ok": "Listo. Recomendación generada.",
        "out": "Salida (copiar/pegar)",
        "dl_txt": "Descargar TXT",
        "dl_json": "Descargar JSON (input)",
        "see_json": "Ver input JSON",
        "err_tip": "Tip: revisá campos obligatorios o valores fuera de rango.",
        "blasts_err_range": "Blastos: debe estar entre 0 y 100.",
        "blasts_err_num": "Blastos: ingresá un número válido (ej 1.5).",
    },
    "EN": {
        "title": "Aza/Ven – Cytopenia adjustment (Hospital Británico) – Adults",
        "caption": "Institutional engine (Dr. Matías Carreras) – prototype",
        "lang_label": "🌐 Language / Idioma",
        "refs_title": "ℹ️ References / guideline (paste links)",
        "ref_guide": "HB guideline (link)",
        "ref_paper": "Paper / consensus (link)",
        "ref_disclaimer": "Disclaimer: decision support tool; does not replace clinical judgment.",
        "close": "Close",
        "clear_help": "Clear form",
        "top_help": "Go to top",
        "refs_help": "References / guideline",
        "patient": "Patient data",
        "age": "Age (years) – Adults (≥18)",
        "sex": "Sex",
        "cycle": "Current cycle",
        "cycle_n": "Cycle number",
        "cycle_start": "Cycle start date",
        "has_next": "I have the next cycle start date (planned/real)",
        "next_start": "Next cycle start date",
        "pamo": "Bone marrow / response",
        "pamo_done": "Bone marrow",
        "not_done": "Not done",
        "done": "Done",
        "pamo_scenario": "Scenario (if available)",
        "blasts": "BM blasts % (optional) – leave blank if unknown",
        "cbc": "CBC / cytopenias",
        "anc": "ANC (/µL)",
        "plt": "Platelets (/µL)",
        "g4": "Grade 4 neutropenia (or ANC<500)",
        "plt_days": "Days with PLT <25,000 (if applicable)",
        "treat": "Treatment (to infer current intensity)",
        "aza_dose": "AZA dose (mg/m²)",
        "aza_days": "AZA days",
        "ven_goal": "VEN target dose (mg)",
        "ven_days": "VEN planned days",
        "antif": "Antifungal (HB)",
        "delay": "Delay / intercurrent events",
        "delay_reason": "Main reason for delay (if applicable)",
        "fever": "Fever / infection (flag)",
        "support": "Support (optional)",
        "gcsf": "G-CSF used",
        "rbc": "RBC transfusion",
        "plt_tx": "Platelet transfusion",
        "calc": "Calculate recommendation",
        "ok": "Done. Recommendation generated.",
        "out": "Output (copy/paste)",
        "dl_txt": "Download TXT",
        "dl_json": "Download JSON (input)",
        "see_json": "View input JSON",
        "err_tip": "Tip: check required fields or out-of-range values.",
        "blasts_err_range": "Blasts must be between 0 and 100.",
        "blasts_err_num": "Enter a valid number (e.g., 1.5).",
    }
}[lang]

# =========================
# Header + language selector
# =========================
st.title(T["title"])
st.caption(T["caption"])

topA, topB, topC, topD, topE = st.columns([5, 2, 1, 1, 1])

with topB:
    chosen = st.selectbox(T["lang_label"], ["ES", "EN"], index=0 if st.session_state["lang"] == "ES" else 1, key="lang")
    # T uses st.session_state["lang"]; after change, Streamlit reruns and updates.

with topC:
    if st.button("ℹ️", key="btn_info", help=T["refs_help"]):
        st.session_state["show_refs"] = not st.session_state["show_refs"]

with topD:
    st.button("🧹", key="btn_reset", help=T["clear_help"], on_click=reset_form)

with topE:
    if st.button("⬆️", key="btn_top", help=T["top_help"]):
        scroll_top()

if st.session_state["show_refs"]:
    with st.expander(T["refs_title"], expanded=True):
        st.text_input(T["ref_guide"], key="ref_guia", placeholder="https://...")
        st.text_input(T["ref_paper"], key="ref_paper", placeholder="https://...")
        st.markdown(f"- {T['ref_disclaimer']}")
        if st.button(T["close"], key="btn_close_refs"):
            st.session_state["show_refs"] = False

st.divider()

# =========================
# Inputs (reactivos; NO st.form)
# =========================
st.subheader(T["patient"])
edad = st.number_input(T["age"], min_value=18, max_value=120, step=1, key="edad")
sexo = st.selectbox(T["sex"], ["NA", "F", "M", "X"], key="sexo")

st.subheader(T["cycle"])
ciclo_numero = st.number_input(T["cycle_n"], min_value=1, max_value=50, step=1, key="ciclo_numero")
fecha_inicio_ciclo = st.date_input(T["cycle_start"], key="fecha_inicio_ciclo")

usar_fecha_siguiente = st.checkbox(T["has_next"], key="usar_fecha_siguiente")
fecha_inicio_siguiente_ciclo = None
if usar_fecha_siguiente:
    fecha_inicio_siguiente_ciclo = st.date_input(T["next_start"], key="fecha_inicio_siguiente_ciclo")

st.subheader(T["pamo"])
pamo_realizada = st.radio(T["pamo_done"], [T["not_done"], T["done"]], horizontal=True, key="pamo_realizada")

resultado_pamo = None
blastos_medula_pct = None

if pamo_realizada == T["done"]:
    resultado_pamo_label = st.selectbox(
        T["pamo_scenario"],
        ["ND", "A (<5% blastos)", "B (≥5% blastos)"],
        key="resultado_pamo_label"
    )

    blastos_text = st.text_input(
        T["blasts"],
        key="blastos_text",
        placeholder="Ej: 1.5 / e.g., 1.5"
    ).strip()

    if blastos_text != "":
        try:
            blastos_medula_pct = float(blastos_text.replace(",", "."))
            if not (0.0 <= blastos_medula_pct <= 100.0):
                st.error(T["blasts_err_range"])
                blastos_medula_pct = None
        except ValueError:
            st.error(T["blasts_err_num"])
            blastos_medula_pct = None

    if resultado_pamo_label.startswith("A"):
        resultado_pamo = "A"
    elif resultado_pamo_label.startswith("B"):
        resultado_pamo = "B"
    else:
        resultado_pamo = None
else:
    # reset PAMO-related fields when not done
    st.session_state["resultado_pamo_label"] = "ND"
    st.session_state["blastos_text"] = ""
    resultado_pamo = None
    blastos_medula_pct = None

st.subheader(T["cbc"])
anc_actual = st.number_input(T["anc"], min_value=0, max_value=200000, step=50, key="anc_actual")
plt_actual = st.number_input(T["plt"], min_value=0, max_value=2000000, step=1000, key="plt_actual")
neutropenia_g4 = st.checkbox(T["g4"], key="neutropenia_g4")
plt_lt_25k_dias = st.number_input(T["plt_days"], min_value=0, max_value=365, step=1, key="plt_lt_25k_dias")

st.subheader(T["treat"])
c1, c2 = st.columns(2)
with c1:
    aza_dosis = st.number_input(T["aza_dose"], min_value=0.0, max_value=200.0, step=5.0, key="aza_dosis")
    aza_dias = st.number_input(T["aza_days"], min_value=0, max_value=14, step=1, key="aza_dias")
with c2:
    ven_obj = st.number_input(T["ven_goal"], min_value=0, max_value=600, step=50, key="ven_obj")
    ven_dias_plan = st.number_input(T["ven_days"], min_value=0, max_value=28, step=1, key="ven_dias_plan")

st.subheader(T["antif"])
antif = st.selectbox(
    T["antif"],
    ["none", "isavuconazole", "voriconazole", "posaconazole"],
    key="antif"
)

st.subheader(T["delay"])
motivo_delay = st.selectbox(
    T["delay_reason"],
    ["ninguno", "citopenias_tratamiento", "infeccion", "sangrado", "internacion", "otro"],
    key="motivo_delay"
)
infeccion_fiebre = st.checkbox(T["fever"], key="infeccion_fiebre")

st.subheader(T["support"])
uso_gcsf = st.checkbox(T["gcsf"], key="uso_gcsf")
transf_gr = st.checkbox(T["rbc"], key="transf_gr")
transf_plt = st.checkbox(T["plt_tx"], key="transf_plt")

st.divider()

calcular = st.button(T["calc"], type="primary", key="btn_calcular")

# =========================
# Run engine
# =========================
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

        st.success(T["ok"])
        st.text_area(T["out"], value=texto, height=320)

        colA, colB = st.columns(2)
        with colA:
            st.download_button(
                T["dl_txt"],
                data=texto.encode("utf-8"),
                file_name="recomendacion_aza_ven.txt",
                mime="text/plain",
            )
        with colB:
            st.download_button(
                T["dl_json"],
                data=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="input_aza_ven.json",
                mime="application/json",
            )

        with st.expander(T["see_json"]):
            st.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json")

    except Exception as e:
        st.error(f"Error: {e}")
        st.info(T["err_tip"])
