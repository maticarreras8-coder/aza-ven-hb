from datetime import date
from pydantic import BaseModel, Field
from typing import Optional, Literal

Antifungico = Literal["none", "isavuconazole", "voriconazole", "posaconazole"]
MotivoDelay = Literal["ninguno", "citopenias_tratamiento", "infeccion", "sangrado", "internacion", "otro"]

LEVELS = {
    0:  {"aza_dosis_mg_m2": 75.0, "aza_dias": 7, "ven_dias": 21},
    -1: {"aza_dosis_mg_m2": 75.0, "aza_dias": 7, "ven_dias": 14},
    -2: {"aza_dosis_mg_m2": 75.0, "aza_dias": 7, "ven_dias": 7},
    -3: {"aza_dosis_mg_m2": 50.0, "aza_dias": 5, "ven_dias": 5},
    -4: {"aza_dosis_mg_m2": 50.0, "aza_dias": 3, "ven_dias": 3},
}

def clamp_level(level: int) -> int:
    return max(-4, min(0, level))

def ajustar_ven_por_antifungico(target_mg: int, cls: Antifungico) -> int:
    if cls == "posaconazole":
        return 70
    if cls == "voriconazole":
        return 100
    if cls == "isavuconazole":
        return 200
    return target_mg

def nombre_antifungico(cls: Antifungico) -> str:
    return {
        "none": "Sin antifúngico",
        "isavuconazole": "Isavuconazol",
        "voriconazole": "Voriconazol",
        "posaconazole": "Posaconazol",
    }[cls]

def inferir_nivel(aza_dosis: float, aza_dias: int, ven_dias: int) -> int:
    for lvl, d in LEVELS.items():
        if abs(aza_dosis - d["aza_dosis_mg_m2"]) < 1e-6 and aza_dias == d["aza_dias"] and ven_dias == d["ven_dias"]:
            return lvl
    if aza_dias == 7 and aza_dosis >= 70:
        return 0
    return 0

class CycleInput(BaseModel):
    edad: int = Field(..., ge=0, le=120)
    sexo: Optional[Literal["F", "M", "X", "NA"]] = "NA"

    ciclo_numero: int = Field(..., ge=1)
    dia_ciclo_actual: Optional[int] = Field(None, ge=1, le=60)

    fecha_inicio_ciclo: date
    fecha_inicio_siguiente_ciclo: Optional[date] = None

    dia_pamo_planificado: Optional[int] = Field(None, ge=1, le=35)
    dia_pamo_real: Optional[int] = Field(None, ge=1, le=60)
    blastos_medula_pct: Optional[float] = Field(None, ge=0, le=100)
    resultado_pamo: Optional[Literal["A", "B"]] = None

    anc_actual: int = Field(..., ge=0)
    plt_actual: int = Field(..., ge=0)

    neutropenia_g4: Optional[bool] = None
    plt_lt_25k_dias: Optional[int] = Field(None, ge=0, le=365)

    aza_dosis_mg_m2: float
    aza_dias_total: int = Field(..., ge=0, le=14)

    ven_dosis_objetivo_mg: int = Field(..., ge=0, le=600)
    ven_dias_plan: int = Field(..., ge=0, le=28)

    antifungico_clase: Antifungico = "none"
    antifungico_nombre: Optional[str] = None

    motivo_delay: MotivoDelay = "ninguno"
    infeccion_fiebre_intercurrencia: Optional[bool] = False

    uso_gcsf: Optional[bool] = False
    transfusion_gr: Optional[bool] = False
    transfusion_plaquetas: Optional[bool] = False

class EngineOutput(BaseModel):
    grupo_edad: Literal["<80", ">=80"]
    escenario: Optional[Literal["A", "B"]]
    cumple_reinicio: bool

    duracion_ciclo_dias: Optional[int]
    ciclo_largo_mas_42: Optional[bool]

    nivel_inferido_actual: int
    nivel_recomendado: Optional[int] = None

    aza_dosis_recomendada_mg_m2: Optional[float] = None
    aza_dias_recomendado: Optional[int] = None

    ven_dias_recomendado: Optional[int] = None
    ven_dosis_ajustada_mg: int

    pamo_planificada_dia: Optional[int] = None
    inicio_proximo_ciclo_dia: Optional[int] = None

    recomendar_pamo: bool = False
    motivo_pamo: Optional[str] = None

    notas: list[str] = []

def aplicar_nivel(out: EngineOutput, level: int) -> None:
    level = clamp_level(level)
    out.nivel_recomendado = level
    out.aza_dosis_recomendada_mg_m2 = LEVELS[level]["aza_dosis_mg_m2"]
    out.aza_dias_recomendado = LEVELS[level]["aza_dias"]
    out.ven_dias_recomendado = LEVELS[level]["ven_dias"]

def run_engine(inp: CycleInput) -> EngineOutput:
    grupo = ">=80" if inp.edad >= 80 else "<80"

    escenario: Optional[str] = None
    if inp.resultado_pamo is not None:
        escenario = inp.resultado_pamo
    elif inp.blastos_medula_pct is not None:
        escenario = "A" if inp.blastos_medula_pct < 5 else "B"

    cumple_reinicio = (inp.anc_actual >= 1000) and (inp.plt_actual >= 50000)

    neut_g4 = inp.neutropenia_g4
    if neut_g4 is None:
        neut_g4 = inp.anc_actual < 500

    dur: Optional[int] = None
    ciclo_largo: Optional[bool] = None
    if inp.fecha_inicio_siguiente_ciclo:
        dur = (inp.fecha_inicio_siguiente_ciclo - inp.fecha_inicio_ciclo).days
        ciclo_largo = dur > 42

    nivel_actual = inferir_nivel(inp.aza_dosis_mg_m2, inp.aza_dias_total, inp.ven_dias_plan)

    ven_ajustada = ajustar_ven_por_antifungico(inp.ven_dosis_objetivo_mg, inp.antifungico_clase)
    antif_name = inp.antifungico_nombre or nombre_antifungico(inp.antifungico_clase)

    pamo_plan = inp.dia_pamo_planificado
    if pamo_plan is None and inp.ciclo_numero == 1:
        pamo_plan = 14 if grupo == ">=80" else 21

    out = EngineOutput(
        grupo_edad=grupo,
        escenario=escenario,
        cumple_reinicio=cumple_reinicio,
        duracion_ciclo_dias=dur,
        ciclo_largo_mas_42=ciclo_largo,
        nivel_inferido_actual=nivel_actual,
        ven_dosis_ajustada_mg=ven_ajustada,
        pamo_planificada_dia=pamo_plan,
        notas=[],
    )

    out.notas.append(f"Antifúngico: {antif_name} → VEN {ven_ajustada} mg/día (dosis ajustada).")

    if inp.uso_gcsf:
        out.notas.append("Soporte: usa/considera G-CSF (interpretar ANC en ese contexto).")
    if inp.transfusion_gr:
        out.notas.append("Soporte: transfusión de GR registrada.")
    if inp.transfusion_plaquetas:
        out.notas.append("Soporte: transfusión de plaquetas registrada.")

    if inp.ciclo_numero == 1:
        if grupo == ">=80":
            aplicar_nivel(out, -1)
            out.notas.append("C1 ≥80: iniciar NIVEL -1 (VEN 14d) y PAMO planificada D14.")
        else:
            aplicar_nivel(out, 0)
            out.notas.append("C1 <80: iniciar NIVEL 0 y PAMO planificada D21.")

        if escenario == "B":
            out.inicio_proximo_ciclo_dia = 28
            out.notas.append("C1 en escenario B: iniciar el próximo ciclo en D28 (sin esperar recuperación hematológica).")
        return out

    if escenario == "B":
        out.notas.append("Escenario B (≥5% blastos): NO bajar nivel por citopenias hasta lograr remisión.")
        return out

    intercurrencia = bool(inp.infeccion_fiebre_intercurrencia) or (inp.motivo_delay in ["infeccion", "sangrado", "internacion", "otro"])
    delay_es_citopenias = inp.motivo_delay in ["ninguno", "citopenias_tratamiento"]

    if escenario == "A":
        if not cumple_reinicio:
            out.notas.append("Escenario A: esperar ANC≥1000 y PLT≥50k para reiniciar.")

        gatillo_bajar = False
        if ciclo_largo is True:
            gatillo_bajar = True
        if neut_g4:
            gatillo_bajar = True
        if inp.plt_lt_25k_dias is not None and inp.plt_lt_25k_dias > 7:
            gatillo_bajar = True

        if gatillo_bajar and delay_es_citopenias and not intercurrencia:
            aplicar_nivel(out, nivel_actual - 1)
            out.notas.append(f"Gatillo de citopenias: bajar 1 nivel (de {nivel_actual} a {out.nivel_recomendado}).")
        elif gatillo_bajar and (intercurrencia or not delay_es_citopenias):
            aplicar_nivel(out, nivel_actual)
            out.notas.append("Gatillos presentes pero hay intercurrencia/motivo alternativo: NO bajar nivel automático; reevaluar causa.")
        else:
            aplicar_nivel(out, nivel_actual)
            out.notas.append(f"Sin gatillos: mantener nivel {nivel_actual}.")

        # Gatillo PAMO (para avisar en la app)
        motivos = []
        if ciclo_largo is True:
            motivos.append("ciclo >42 días")
        if neut_g4:
            motivos.append("neutropenia G4")
        if inp.plt_lt_25k_dias is not None and inp.plt_lt_25k_dias > 7:
            motivos.append("PLT <25k >7 días")

        if motivos:
            out.recomendar_pamo = True
            out.motivo_pamo = ", ".join(motivos)
            out.notas.append(f"Recomendar PAMO por: {out.motivo_pamo}.")

        if ciclo_largo is True and not out.recomendar_pamo:
            out.notas.append("Ciclo >42 días: considerar espaciar ciclos a 6–8 semanas.")

    return out

def resumen_humano(out: EngineOutput) -> str:
    lineas = []
    if out.recomendar_pamo:
        lineas.append(f"🚨 HACER PAMO AHORA ({out.motivo_pamo})")
        lineas.append("")

    lineas.append(f"Grupo edad: {out.grupo_edad}")
    lineas.append(f"Escenario: {out.escenario if out.escenario else 'ND'}")
    lineas.append(f"Cumple reinicio (ANC≥1000 y PLT≥50k): {'Sí' if out.cumple_reinicio else 'No'}")
    if out.duracion_ciclo_dias is not None:
        lineas.append(f"Duración del ciclo: {out.duracion_ciclo_dias} días ({'>42' if out.ciclo_largo_mas_42 else '≤42'})")
    if out.pamo_planificada_dia is not None:
        lineas.append(f"PAMO planificada: D{out.pamo_planificada_dia}")
    if out.inicio_proximo_ciclo_dia is not None:
        lineas.append(f"Inicio próximo ciclo sugerido: D{out.inicio_proximo_ciclo_dia}")

    if out.nivel_recomendado is not None:
        lineas.append("")
        lineas.append("RECOMENDACIÓN:")
        lineas.append(f"• Nivel: {out.nivel_recomendado}")
        lineas.append(f"• Azacitidina: {out.aza_dosis_recomendada_mg_m2} mg/m² × {out.aza_dias_recomendado} días")
        lineas.append(f"• Venetoclax: {out.ven_dias_recomendado} días")
        lineas.append(f"• Dosis VEN ajustada por antifúngico: {out.ven_dosis_ajustada_mg} mg/día")

    if out.notas:
        lineas.append("")
        lineas.append("NOTAS / ALERTAS:")
        for n in out.notas:
            lineas.append(f"• {n}")

    return "\n".join(lineas)
