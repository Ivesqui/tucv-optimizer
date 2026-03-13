from app.core.knowledge.db_loader import _AREA_PATTERNS, clean_text
from app.domain.cv_model import CVProfile

class IdentityService:
    def get_all_platform_mappings(self, profile: CVProfile):
        return {
            "multitrabajos": self._map_multitrabajos(profile),
            "encuentra_empleo": self._map_encuentra_empleo(profile),
            "linkedin": self._map_linkedin(profile)
        }
    def _map_multitrabajos(self, p: CVProfile):
        return {
            "seccion_datos": {
                "Nombre Completo": p.contact.name,
                "Nacionalidad": p.metadata.nationality,
                "Estado Civil": p.metadata.marital_status,
                "Dirección": f"{p.metadata.address_main_street} y {p.metadata.address_secondary_street}"
            },
            "seccion_educacion": [
                {
                    "Titulo": e.degree,
                    "Institucion": e.institution,
                    "Area": self._guess_area(e.field_of_study) # Lógica simple de mapeo
                } for e in p.education
            ]
        }

    def _map_encuentra_empleo(self, p: CVProfile):
        m = p.metadata
        return {
            "informacion_personal": {
                "Cédula": m.id_number,
                "Tipo de Sangre": m.blood_type,
                "Etnia": m.ethnicity,
                "Género": m.gender
            },
            "residencia": {
                "Provincia": m.province,
                "Cantón": m.canton,
                "Parroquia": m.parish,
                "Calle Principal": m.address_main_street,
                "Calle Secundaria": m.address_secondary_street
            }
        }

    def _map_linkedin(self, p: CVProfile):
        return {
            "contact_info": {
                "email": p.contact.email,
                "phone": p.contact.phone,
                "linkedin_url": p.contact.linkedin
            },
            "summary_snippet": p.summary[:2000] if p.summary else "",
            "skills_flat": ", ".join(p.skills[:10])
        }

    def _guess_area(self, field: str):
        if not field:
            return "Otras áreas"
        normalized_field = clean_text(field)
        for area_key, formal_name, pattern in _AREA_PATTERNS:
            if pattern.search(normalized_field):
                return formal_name
        return "Otras áreas"