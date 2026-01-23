import json
from datetime import date
import streamlit as st
import streamlit.components.v1 as components

from azaven.engine import CycleInput, run_engine, resumen_humano

st.set_page_config(page_title="Aza/Ven – HB", layout="centered")

# =========================
#  RED + BLUE THEME (HB)
# =========================
st.markdown(
    """
<style>
:root{
  --hb-blue:#0B3D91;
  --hb-blue-2:#174EA6;
  --hb-red:#C1121F;
  --hb-red-2:#E11D2E;
  --hb-ice:#F4F7FF;
  --hb-ink:#0B1220;
  --hb-muted:#5B677A;
  --hb-border:#E3E9F6;
  --hb-card:#FFFFFF;
}

/* App background */
.stApp{
  background: radial-gradient(1200px 500px at 15% 0%, rgba(11,61,145,.14) 0%, rgba(11,61,145,0) 55%),
              radial-gradient(1200px 500px at 85% 0%, rgba(193,18,31,.12) 0%, rgba(193,18,31,0) 60%),
              linear-gradient(180deg, var(--hb-ice) 0%, #FFFFFF 55%);
  color: var(--hb-ink);
}

/* Headings */
h1{
  color: var(--hb-blue);
  letter-spacing:-0.3px;
  margin-bottom: 0.25rem;
}
h2, h3{
  color: var(--hb-ink);
  letter-spacing:-0.2px;
}

/* Caption */
.stCaption, small { color: var(--hb-muted) !important; }

/* Cards feel: expanders & blocks */
details{
  border: 1px solid var(--hb-border) !important;
  border-radius: 14px !important;
  background: var(--hb-card) !important;
  padding: 0.15rem 0.65rem !important;
}
summary{
  color: var(--hb-blue) !important;
  font-weight: 800 !important;
}

/* Divider */
hr, .stDivider { border-color: var(--hb-border) !important; }

/* Inputs focus */
div[data-baseweb="input"] input:focus,
div[data-baseweb="textarea"] textarea:focus,
div[data-baseweb="select"] > div:focus-within{
  box-shadow: 0 0 0 2px rgba(11,61,145,.18) !important;
  border-color: rgba(11,61,145,.35) !important;
}

/* Buttons - base */
.stButton>button{
  border-radius: 12px !important;
  font-weight: 800 !important;
  padding: 0.55rem 0.9rem !important;
  border: 1px solid rgba(11,61,145,.25) !important;
  background: #FFFFFF !important;
  color: var(--hb-blue) !important;
  transition: transform .02s ease-in-out, filter .12s ease-in-out, border-color .15s ease-in-out;
}
.stButton>button:hover{
  border-color: rgba(193,18,31,.40) !important;
  filter: saturate(1.05);
}
.stButton>button:active{ transform: translateY(1px); }

/* Primary button (Calculate) */
div.stButton > button[kind="primary"]{
  background: linear-gradient(90deg, var(--hb-blue) 0%, var(--hb-blue-2) 60%, var(--hb-red) 100%) !important;
  color: #FFFFFF !important;
  border: 0 !important;
}
div.stButton > button[kind="primary"]:hover{ filter: brightness(1.04) saturate(1.05); }

/* Alert rounding */
.stAlert [data-testid="stAlert"]{ border-radius: 14px !important; }

/* Slightly reduce top padding */
.block-container { padding-top: 1.4rem !important; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Helpers
# =========================
DEFAULTS = {
    "lang": "ES",
    "show_refs": False,

    # Patient
    "edad": 72,
    "sexo": "NA",

    # Cycle
    "ciclo_numero": 2,
    "fecha_inicio_ciclo": date(2025, 11, 1),
    "usar_fecha_siguiente": True,
    "fecha_inicio_siguiente_ciclo": date.today(),

    # PAMO
    "pamo_realizada": "No realizado",
    "escenario_pamo": "ND",
    "blastos_text": "",

    # CBC
    "anc_actual": 600,
    "plt_actual": 42000,
    "neutropenia_g4": True,
    "plt_lt_25k_dias": 0,

    # Treatment
    "aza_dosis": 75.0,
    "aza_dias": 7,
    "ven_obj": 400,
    "ven_dias_plan": 21,

    # Antifungal
    "antif": "posaconazole",

    # Delay
    "motivo_delay": "ninguno",
    "infeccion_fiebre": False,

    # Support
    "uso_gcsf": False,
    "transf_gr": False,
    "transf_plt": False,
}

def init_defaults():
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_form():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    # NO st.rerun(): el click ya dispara rerun

def scroll_top():
    components.html("<script>window.scrollTo(0,0);</script>", height=0)

init_defaults()

# =========================
# Language strings
# =========================
lang = st.session_state["lang"]

STR = {
    "ES": {
        "title": "Aza/Ven – Ajuste por citopenias (Hospital Británico) – Adultos",
        "caption": "Motor institucional (Dr. Matías Carreras) – prototipo",
        "lang": "🌐 Idioma / Language",
        "refs": "Referencias",
        "clear": "Limpiar",
        "top": "Arriba",
        "calc": "Calcular recomendación",

        "refs_title": "📚 Referencias (cargadas)",
        "ref_inst": "Documento institucional HB: “Manejo de AZA+VEN en LMA – v3 (Servicio de Hematología, Hospital Británico)”.",
        "ref_howitreat": "Wei AH, Loo S, Daver N. “How I treat patients with AML using azacitidine and venetoclax”. Blood. 2024.",
        "ref_link": "Abrir PDF (ASH)",

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
        "scenario": "Escenario (institucional)",
        "sc_nd": "ND (sin dato)",
        "sc_a": "A: <5% blastos (remisión/aplasia/hipocelular)",
        "sc_b": "B: ≥5% blastos",
        "blasts": "% blastos médula (opcional) – dejá vacío si no lo tenés",
        "blasts_help": "Helper: si cargás blastos, la app confirma si corresponde A (<5%) o B (≥5%).",

        "cbc": "Hemograma / citopenias",
        "anc": "ANC (/µL)",
        "plt": "Plaquetas (/µL)",
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
        "lang": "🌐 Language / Idioma",
        "refs": "References",
        "clear": "Clear",
        "top": "Top",
        "calc": "Calculate recommendation",

        "refs_title": "📚 References (preloaded)",
        "ref_inst": "HB institutional document: “AZA+VEN management in AML – v3 (Hematology Department, Hospital Británico)”.",
        "ref_howitreat": "Wei AH, Loo S, Daver N. “How I treat patients with AML using azacitidine and venetoclax”. Blood. 2024.",
        "ref_link": "Open PDF (ASH)",

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
        "scenario": "Scenario (institutional)",
        "sc_nd": "ND (unknown)",
        "sc_a": "A: <5% blasts (remission/aplastic/hypocellular)",
        "sc_b": "B: ≥5% blasts",
        "blasts": "BM blasts % (optional) – leave blank if unknown",
        "blasts_help": "Helper: if blasts are provided, the app confirms A (<5%) vs B (≥5%).",

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

        "ok": "Done. Recommendation generated.",
        "out": "Output (copy/paste)",
        "dl_txt": "Download TXT",
        "dl_json": "Download JSON (input)",
        "see_json": "View input JSON",
        "err_tip": "Tip: check required fields or out-of-range values.",
        "blasts_err_range": "Blasts must be between 0 and 100.",
        "blasts_err_num": "Enter a valid number (e.g., 1.5).",
    },
}[lang]

# =========================
# Header / Top bar (clean)
# =========================
st.title(STR["title"])
st.caption(STR["caption"])

bar = st.container()
with bar:
    c1, c2, c3, c4 = st.columns([3.6, 1.6, 0.9, 0.9])

    with c2:
        st.selectbox(STR["lang"], ["ES", "EN"], index=0 if st.session_state["lang"] == "ES" else 1, key="lang")

    with c3:
        if st.button(f"📚 {STR['refs']}", use_container_width=True, key="btn_refs"):
            st.session_state["show_refs"] = not st.session_state["show_refs"]

    with c4:
        st.button(STR["clear"], on_click=reset_form, use_container_width=True, key="btn_clear")

# small action row
a1, a2, a3 = st.columns([6, 1, 1])
with a3:
    if st.button(STR["top"], use_container_width=True, key="btn_top"):
        scroll_top()

if st.session_state["show_refs"]:
    with st.expander(STR["refs_title"], expanded=True):
        st.markdown(f"**1)** {STR['ref_inst']}")
        st.markdown(f"**2)** {STR['ref_howitreat']}  \n[{STR['ref_link']}](https://ashpublications.org/blood/article-pdf/doi/10.1182/blood.2024024009/2244051/blood.2024024009.pdf)")
        st.markdown("- *Disclaimer: decision support tool; does not replace clinical judgment.*")

st.divider()

# =========================
# Inputs (reactive)
# =========================
st.subheader(STR["patient"])
edad = st.number_input(STR["age"], min_value=18, max_value=120, step=1, key="edad")
sexo = st.selectbox(STR["sex"], ["NA", "F", "M", "X"], key="sexo")

st.subheader(STR["cycle"])
ciclo_numero = st.number_input(STR["cycle_n"], min_value=1, max_value=50, step=1, key="ciclo_numero")
fecha_inicio_ciclo = st.date_input(STR["cycle_start"], key="fecha_inicio_ciclo")

usar_fecha_siguiente = st.checkbox(STR["has_next"], key="usar_fecha_siguiente")
fecha_inicio_siguiente_ciclo = None
if usar_fecha_siguiente:
    fecha_inicio_siguiente_ciclo = st.date_input(STR["next_start"], key="fecha_inicio_siguiente_ciclo")

st.subheader(STR["pamo"])
pamo_realizada = st.radio(STR["pamo_done"], [STR["not_done"], STR["done"]], horizontal=True, key="pamo_realizada")

resultado_pamo = None
blastos_medula_pct = None

if pamo_realizada == STR["done"]:
    escenario = st.selectbox(
        STR["scenario"],
        [STR["sc_nd"], STR["sc_a"], STR["sc_b"]],
        key="escenario_pamo"
    )

    blastos_text = st.text_input(STR["blasts"], key="blastos_text", placeholder="Ej: 1.5 / e.g., 1.5").strip()

    # parse optional blasts
    if blastos_text != "":
        try:
            blastos_medula_pct = float(blastos_text.replace(",", "."))
            if not (0.0 <= blastos_medula_pct <= 100.0):
                st.error(STR["blasts_err_range"])
                blastos_medula_pct = None
        except ValueError:
            st.error(STR["blasts_err_num"])
            blastos_medula_pct = None

    # helper confirmation
    st.caption(STR["blasts_help"])
    if blastos_medula_pct is not None:
        if blastos_medula_pct < 5:
            st.info("→ " + STR["sc_a"])
        else:
            st.warning("→ " + STR["sc_b"])

    # map scenario to engine value (A/B/None)
    if "A:" in escenario:
        resultado_pamo = "A"
    elif "B:" in escenario:
        resultado_pamo = "B"
    else:
        resultado_pamo = None
else:
    # reset when not done
    st.session_state["escenario_pamo"] = STR["sc_nd"]
    st.session_state["blastos_text"] = ""
    resultado_pamo = None
    blastos_medula_pct = None

st.subheader(STR["cbc"])
anc_actual = st.number_input(STR["anc"], min_value=0, max_value=200000, step=50, key="anc_actual")
plt_actual = st.number_input(STR["plt"], min_value=0, max_value=2000000, step=1000, key="plt_actual")
neutropenia_g4 = st.checkbox(STR["g4"], key="neutropenia_g4")
plt_lt_25k_dias = st.number_input(STR["plt_days"], min_value=0, max_value=365, step=1, key="plt_lt_25k_dias")

st.subheader(STR["treat"])
colL, colR = st.columns(2)
with colL:
    aza_dosis = st.number_input(STR["aza_dose"], min_value=0.0, max_value=200.0, step=5.0, key="aza_dosis")
    aza_dias = st.number_input(STR["aza_days"], min_value=0, max_value=14, step=1, key="aza_dias")
with colR:
    ven_obj = st.number_input(STR["ven_goal"], min_value=0, max_value=600, step=50, key="ven_obj")
    ven_dias_plan = st.number_input(STR["ven_days"], min_value=0, max_value=28, step=1, key="ven_dias_plan")

st.subheader(STR["antif"])
antif = st.selectbox(
    STR["antif"],
    ["none", "isavuconazole", "voriconazole", "posaconazole"],
    key="antif"
)

st.subheader(STR["delay"])
motivo_delay = st.selectbox(
    STR["delay_reason"],
    ["ninguno", "citopenias_tratamiento", "infeccion", "sangrado", "internacion", "otro"],
    key="motivo_delay"
)
infeccion_fiebre = st.checkbox(STR["fever"], key="infeccion_fiebre")

st.subheader(STR["support"])
uso_gcsf = st.checkbox(STR["gcsf"], key="uso_gcsf")
transf_gr = st.checkbox(STR["rbc"], key="transf_gr")
transf_plt = st.checkbox(STR["plt_tx"], key="transf_plt")

st.divider()

# Centered primary CTA
ctaL, ctaC, ctaR = st.columns([1, 2, 1])
with ctaC:
    calcular = st.button(STR["calc"], type="primary", use_container_width=True, key="btn_calcular")

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

        st.success(STR["ok"])
        st.text_area(STR["out"], value=texto, height=320)

        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                STR["dl_txt"],
                data=texto.encode("utf-8"),
                file_name="recomendacion_aza_ven.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with d2:
            st.download_button(
                STR["dl_json"],
                data=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="input_aza_ven.json",
                mime="application/json",
                use_container_width=True,
            )

        with st.expander(STR["see_json"]):
            st.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json")

    except Exception as e:
        st.error(f"Error: {e}")
        st.info(STR["err_tip"])
