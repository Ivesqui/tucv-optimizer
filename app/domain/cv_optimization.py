from app.domain.cv_model import CVProfile
from typing import List, Tuple
import copy
import re
from app.infrastructure.nlp.skills_detector import _weak_verbs_raw, _verbs_raw

def _smart_replace(text: str, weak_list: list, strong_list: list) -> str:
    if not text:
        return text

    updated_text = text
    for weak in weak_list:
        # Buscamos el verbo débil (palabra completa, ignorando mayúsculas)
        pattern = re.compile(rf"\b{weak}\b", re.IGNORECASE)
        match = pattern.search(updated_text)

        if match:
            replacement = strong_list[0] if strong_list else "lideré"

            # Lógica de capitalización:
            # Si el match está al inicio del texto, Capitalize.
            # Si no, mantenemos minúscula para que fluya en la frase.
            if match.start() == 0:
                replacement = replacement.capitalize()
            else:
                replacement = replacement.lower()

            # Reemplazamos solo la primera ocurrencia para evitar sobre-optimización
            updated_text = pattern.sub(replacement, updated_text, count=1)
            break

    return updated_text

def optimize_cv(
        profile: CVProfile,
        missing_tech: List[str],
        missing_soft: List[str]
) -> Tuple[CVProfile, List[str], List[str]]:
    optimized = copy.deepcopy(profile)

    # 1. Cargar diccionarios
    weak_list = _weak_verbs_raw.get("verbos_debiles", [])
    strong_list = _verbs_raw.get("liderazgo", []) + _verbs_raw.get("operativo", [])

    # 2. OPTIMIZACIÓN NARRATIVA: Summary
    if optimized.summary:
        optimized.summary = _smart_replace(optimized.summary, weak_list, strong_list)

    # 3. OPTIMIZACIÓN NARRATIVA: Experiencia (Bullets)
    for exp in optimized.experience:
        optimized_bullets = []
        for bullet in exp.bullets:
            optimized_bullets.append(_smart_replace(bullet, weak_list, strong_list))
        exp.bullets = optimized_bullets

    # 4. PROMOCIÓN DE SKILLS (Tu lógica original)
    existing_lower = {s.lower() for s in optimized.skills}
    all_text_lower = optimized.to_plain_text().lower()

    skills_to_promote = []
    for skill in missing_tech:
        if skill.lower() in all_text_lower and skill.lower() not in existing_lower:
            skills_to_promote.append(skill)

    if skills_to_promote:
        optimized.skills.extend(skills_to_promote)

    # 5. SUGERENCIA DE SOFT SKILLS
    existing_soft_lower = {s.lower() for s in optimized.soft_skills}
    soft_to_add = [s for s in missing_soft if s.lower() not in existing_soft_lower][:3]

    return optimized, skills_to_promote, soft_to_add

def improve_bullet_narrative(bullet: str, weak_verbs: list, strong_verbs: list) -> str:
    """
    Busca verbos débiles en un bullet y los reemplaza por uno de alto impacto.
    """
    new_bullet = bullet
    # Limpieza básica para evitar reemplazar partes de palabras
    for weak in weak_verbs:
        pattern = re.compile(rf"\b{weak}\b", re.IGNORECASE)
        if pattern.search(new_bullet):
            # Tomamos un verbo fuerte aleatorio o el primero de la lista
            replacement = strong_verbs[0] if strong_verbs else "Lideré"
            # Reemplazamos y capitalizamos si es el inicio de la frase
            new_bullet = pattern.sub(replacement.capitalize(), new_bullet)
            break  # Solo reemplazamos el primero para no saturar

    return new_bullet