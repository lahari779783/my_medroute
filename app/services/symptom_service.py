SYMPTOM_MAP = {
    "chest pain": "cardiology",
    "breathing difficulty": "pulmonology",
    "head injury": "trauma",
    "fracture": "orthopedic",
    "burn": "emergency",
    "fever": "general"
}


def map_symptoms_to_specialization(symptoms: str):

    symptoms = symptoms.lower()

    matched = []

    for key in SYMPTOM_MAP:

        if key in symptoms:
            matched.append(SYMPTOM_MAP[key])

    if not matched:
        return ["general"]

    return list(set(matched))