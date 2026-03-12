import copy
import re
import random
from typing import List, Tuple
from app.domain.cv_model import CVProfile
from app.core.knowledge.db_loader import ALL_WEAK_VERBS, VERBS_DB, clean_text


def _smart_replace(text: str) -> str:
    """
    Esta es la función maestra de reemplazo. 
    Consolida lo que hacía 'improve_bullet_narrative' y '_smart_replace'.
    """
    if not text:
        return text

    updated_text = text
    # Definimos el pool de verbos fuertes (Liderazgo + Operativo son los mejores para reemplazo)
    strong_pool = VERBS_DB.get("liderazgo", []) + VERBS_DB.get("operativo", [])

    # Usamos la lista de verbos débiles cargada desde el JSON
    for weak in ALL_WEAK_VERBS:
        # Buscamos el verbo débil como palabra completa (\b)
        pattern = re.compile(rf"\b{weak}\b", re.IGNORECASE)
        match = pattern.search(updated_text)

        if match:

            replacement = random.choice(strong_pool) if strong_pool else "lideré"

            # Lógica de capitalización inteligente
            if match.start() == 0:
                replacement = replacement.capitalize()
            else:
                replacement = replacement.lower()

            # Reemplazamos solo la primera ocurrencia
            updated_text = pattern.sub(replacement, updated_text, count=1)
            break  # Salimos del bucle tras el primer reemplazo para no sobre-procesar

    return updated_text


def optimize_cv(
        profile: CVProfile,
        missing_tech: List[str],
        missing_soft: List[str]
) -> Tuple[CVProfile, List[str], List[str]]:
    """
    Orquestador de la optimización del CV.
    """
    # Creamos una copia profunda para no modificar el objeto original (Inmutabilidad)
    optimized = copy.deepcopy(profile)

    # 1. OPTIMIZACIÓN NARRATIVA: Summary
    if optimized.summary:
        optimized.summary = _smart_replace(optimized.summary)

    # 2. OPTIMIZACIÓN NARRATIVA: Experiencia (Bullets)
    for exp in optimized.experience:
        # Aplicamos la transformación a cada bullet point
        exp.bullets = [_smart_replace(bullet) for bullet in exp.bullets]

    # 3. PROMOCIÓN DE SKILLS TÉCNICAS
    # Usamos clean_text para comparar sin importar tildes o mayúsculas
    experience_text = " ".join([b for exp in optimized.experience for b in exp.bullets])
    all_experience_normalized = clean_text(experience_text)

    skills_to_promote = []
    for skill in missing_tech:
        skill_clean = clean_text(skill)
        # Si la skill está en el texto pero no en la lista de skills oficial, la promocionamos
        if skill_clean in all_experience_normalized and skill_clean not in all_experience_normalized:
            skills_to_promote.append(skill)

    if skills_to_promote:
        optimized.skills.extend(skills_to_promote)

    # 4. SUGERENCIA DE SOFT SKILLS
    existing_soft_normalized = {clean_text(s) for s in optimized.soft_skills}
    soft_to_add = [
        s for s in missing_soft
        if clean_text(s) not in existing_soft_normalized
    ][:3]  # Limitamos a las 3 mejores sugerencias

    return optimized, skills_to_promote, soft_to_add