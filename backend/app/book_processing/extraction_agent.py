"""Information extraction agent for agricultural entities and relations."""

from __future__ import annotations

from collections import defaultdict

from app.book_processing.parser_agent import ParsedBook


class InformationExtractionAgent:
    """Extract diseases, treatments, techniques, and relations from sections."""

    _diseases = {
        "نقص النيتروجين": "Nitrogen Deficiency",
        "البياض الدقيقي": "Powdery Mildew",
        "تبقع الأوراق": "Leaf Spot",
        "nitrogen deficiency": "Nitrogen Deficiency",
        "powdery mildew": "Powdery Mildew",
        "leaf spot": "Leaf Spot",
    }

    _treatments = {
        "سماد اليوريا": "Urea Fertilizer",
        "المبيد الفطري": "Fungicide",
        "urea": "Urea Fertilizer",
        "fungicide": "Fungicide",
    }

    _techniques = {
        "الري بالتنقيط": "Drip Irrigation Technique",
        "drip irrigation": "Drip Irrigation Technique",
    }

    _crops = ["طماطم", "قمح", "ذرة", "tomato", "wheat", "corn"]

    def extract(self, parsed_books: list[ParsedBook]) -> dict:
        diseases: dict[str, dict] = {}
        treatments: dict[str, dict] = {}
        techniques: dict[str, dict] = {}
        relationships: list[dict] = []

        disease_treat_map: defaultdict[str, set[str]] = defaultdict(set)

        for parsed in parsed_books:
            for section in parsed.sections:
                section_text = section.text.lower()
                sources = [f"{parsed.file_name}:p.{section.page_start}"]
                crops = [crop for crop in self._crops if crop.lower() in section_text]

                found_diseases = self._find_matches(section_text, self._diseases)
                found_treatments = self._find_matches(section_text, self._treatments)
                found_techniques = self._find_matches(section_text, self._techniques)

                for disease_ar, disease_en in found_diseases:
                    key = disease_en.lower()
                    diseases.setdefault(
                        key,
                        {
                            "id": f"disease_{len(diseases) + 1:03d}",
                            "name_ar": disease_ar,
                            "name_en": disease_en,
                            "symptoms": [],
                            "symptoms_en": [],
                            "causes": [],
                            "treatments": [],
                            "severity": 0.7,
                            "affected_crops": [],
                            "book_sources": [],
                            "confidence": 0.9,
                        },
                    )
                    diseases[key]["book_sources"] = sorted(
                        set(diseases[key]["book_sources"] + sources)
                    )
                    diseases[key]["affected_crops"] = sorted(
                        set(diseases[key]["affected_crops"] + crops)
                    )

                for treatment_ar, treatment_en in found_treatments:
                    key = treatment_en.lower()
                    treatments.setdefault(
                        key,
                        {
                            "id": f"treatment_{len(treatments) + 1:03d}",
                            "name_ar": treatment_ar,
                            "name_en": treatment_en,
                            "dosage": "",
                            "frequency": "",
                            "application_method": "",
                            "results": [],
                            "suitable_for": [],
                            "book_sources": [],
                            "effectiveness": 0.85,
                        },
                    )
                    treatments[key]["book_sources"] = sorted(
                        set(treatments[key]["book_sources"] + sources)
                    )

                for technique_ar, technique_en in found_techniques:
                    key = technique_en.lower()
                    techniques.setdefault(
                        key,
                        {
                            "id": f"technique_{len(techniques) + 1:03d}",
                            "name_ar": technique_ar,
                            "name_en": technique_en,
                            "description_ar": section.text[:280],
                            "description_en": section.text[:280],
                            "benefits": [],
                            "best_crops": crops,
                            "book_sources": [],
                            "difficulty_level": "متوسط",
                        },
                    )
                    techniques[key]["book_sources"] = sorted(
                        set(techniques[key]["book_sources"] + sources)
                    )

                for disease_ar, disease_en in found_diseases:
                    for treatment_ar, treatment_en in found_treatments:
                        disease_treat_map[disease_en.lower()].add(treatment_en.lower())

        for disease_key, treatment_keys in disease_treat_map.items():
            disease_id = diseases[disease_key]["id"]
            for treatment_key in sorted(treatment_keys):
                treatment_id = treatments[treatment_key]["id"]
                diseases[disease_key]["treatments"].append(treatments[treatment_key]["name_ar"])
                treatments[treatment_key]["suitable_for"].append(diseases[disease_key]["name_ar"])
                relationships.append(
                    {
                        "from": disease_id,
                        "to": treatment_id,
                        "type": "cured_by",
                        "confidence": 0.9,
                    }
                )

        return {
            "diseases": list(diseases.values()),
            "treatments": list(treatments.values()),
            "techniques": list(techniques.values()),
            "relationships": relationships,
        }

    @staticmethod
    def _find_matches(text: str, dictionary: dict[str, str]) -> list[tuple[str, str]]:
        matches: list[tuple[str, str]] = []
        for key, english in dictionary.items():
            if key.lower() in text:
                matches.append((key, english))
        return matches
