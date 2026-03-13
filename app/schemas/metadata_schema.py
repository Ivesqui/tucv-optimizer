from pydantic import BaseModel


class PersonalMetadataSchema(BaseModel):
    # Identidad
    id_type: str = "Cédula"
    id_number: str = ""
    birth_date: str = ""
    gender: str = ""
    marital_status: str = ""
    nationality: str = "Ecuatoriana"
    ethnicity: str = ""

    # Salud (Corregido tipos)
    disability_status: bool = False
    disability_percentage: int = 0
    blood_type: str = ""
    catastrophic_illness_family: bool = False

    # Logística (Corregido tipos)
    drivers_license: str = "No"
    owns_vehicle: bool = False
    willing_to_travel: bool = True
    willing_to_relocate: bool = False

    # Ubicación
    province: str = ""
    canton: str = ""
    parish: str = "" # Añadido parroquia
    address_main_street: str = ""
    address_secondary_street: str = ""
    address_reference: str = ""