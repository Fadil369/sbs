"""
Integration Test Fixtures for SBS Integration Engine
=====================================================

Sample data for end-to-end testing including:
- FHIR Claims
- Patient data
- Provider data
- Service codes
- Insurance coverage
"""

import uuid
from datetime import date, datetime
from typing import Dict, Any, List
import json


class SampleData:
    """Factory for generating sample test data"""

    # ==========================================================================
    # SBS Master Codes (CHI Official Codes)
    # ==========================================================================

    SBS_CODES = {
        "SBS-LAB-001": {
            "description_en": "Complete Blood Count (CBC)",
            "description_ar": "تحليل صورة دم كاملة",
            "category": "Lab",
            "standard_price": 50.00
        },
        "SBS-LAB-002": {
            "description_en": "Comprehensive Metabolic Panel",
            "description_ar": "لوحة الأيض الشاملة",
            "category": "Lab",
            "standard_price": 120.00
        },
        "SBS-RAD-001": {
            "description_en": "Chest X-Ray",
            "description_ar": "أشعة سينية للصدر",
            "category": "Radiology",
            "standard_price": 150.00
        },
        "SBS-RAD-002": {
            "description_en": "MRI Brain",
            "description_ar": "رنين مغناطيسي للدماغ",
            "category": "Radiology",
            "standard_price": 1500.00
        },
        "SBS-CONS-001": {
            "description_en": "General Medical Consultation",
            "description_ar": "استشارة طبية عامة",
            "category": "Consultation",
            "standard_price": 200.00
        },
        "SBS-CONS-002": {
            "description_en": "Specialist Consultation",
            "description_ar": "استشارة تخصصية",
            "category": "Consultation",
            "standard_price": 350.00
        },
        "SBS-SURG-001": {
            "description_en": "Appendectomy",
            "description_ar": "عملية استئصال الزائدة الدودية",
            "category": "Surgery",
            "standard_price": 5000.00
        },
        "SBS-PHARM-001": {
            "description_en": "Antibiotic Dispensing",
            "description_ar": "صرف مضاد حيوي",
            "category": "Pharmacy",
            "standard_price": 45.00
        }
    }

    # ==========================================================================
    # Sample Patients
    # ==========================================================================

    PATIENTS = [
        {
            "id": "PAT-001",
            "name": "Ahmed Al-Rashid",
            "name_ar": "أحمد الراشد",
            "national_id": "1012345678",
            "gender": "male",
            "birthDate": "1985-06-15",
            "phone": "+966500001111",
            "email": "ahmed@example.com",
            "address": {
                "city": "Riyadh",
                "district": "Al Olaya",
                "postal_code": "12211"
            }
        },
        {
            "id": "PAT-002",
            "name": "Fatima Al-Zahrani",
            "name_ar": "فاطمة الزهراني",
            "national_id": "1098765432",
            "gender": "female",
            "birthDate": "1990-03-22",
            "phone": "+966500002222",
            "email": "fatima@example.com",
            "address": {
                "city": "Jeddah",
                "district": "Al Rawdah",
                "postal_code": "21452"
            }
        },
        {
            "id": "PAT-003",
            "name": "Mohammed Al-Ghamdi",
            "name_ar": "محمد الغامدي",
            "national_id": "1055667788",
            "gender": "male",
            "birthDate": "1978-11-08",
            "phone": "+966500003333",
            "email": "mohammed@example.com",
            "address": {
                "city": "Dammam",
                "district": "Al Faisaliyah",
                "postal_code": "31411"
            }
        }
    ]

    # ==========================================================================
    # Sample Insurance Coverage
    # ==========================================================================

    INSURANCE_POLICIES = [
        {
            "policy_number": "POL-2024-001234",
            "payer_id": "PAYER-BUPA",
            "payer_name": "BUPA Arabia",
            "class": "VIP",
            "class_name": "VIP Class A",
            "effective_date": "2024-01-01",
            "termination_date": "2024-12-31",
            "annual_limit": 500000.00,
            "remaining_balance": 450000.00,
            "copay_percentage": 0,
            "deductible": 0
        },
        {
            "policy_number": "POL-2024-005678",
            "payer_id": "PAYER-MEDGULF",
            "payer_name": "MedGulf Insurance",
            "class": "B",
            "class_name": "Class B Standard",
            "effective_date": "2024-01-01",
            "termination_date": "2024-12-31",
            "annual_limit": 250000.00,
            "remaining_balance": 200000.00,
            "copay_percentage": 20,
            "deductible": 500.00
        },
        {
            "policy_number": "POL-2024-009999",
            "payer_id": "PAYER-TAWUNIYA",
            "payer_name": "Tawuniya",
            "class": "C",
            "class_name": "Class C Basic",
            "effective_date": "2024-01-01",
            "termination_date": "2024-12-31",
            "annual_limit": 100000.00,
            "remaining_balance": 85000.00,
            "copay_percentage": 30,
            "deductible": 1000.00
        }
    ]

    # ==========================================================================
    # Sample Facilities
    # ==========================================================================

    FACILITIES = [
        {
            "facility_id": 1,
            "facility_code": "FAC-001",
            "facility_name": "King Fahad Medical City",
            "facility_name_ar": "مدينة الملك فهد الطبية",
            "chi_license_number": "CHI-RYD-001",
            "accreditation_tier": 1,
            "region": "Riyadh",
            "city": "Riyadh",
            "nphies_payer_id": "NPHIES-FAC-001"
        },
        {
            "facility_id": 2,
            "facility_code": "FAC-002",
            "facility_name": "King Faisal Specialist Hospital",
            "facility_name_ar": "مستشفى الملك فيصل التخصصي",
            "chi_license_number": "CHI-RYD-002",
            "accreditation_tier": 1,
            "region": "Riyadh",
            "city": "Riyadh",
            "nphies_payer_id": "NPHIES-FAC-002"
        },
        {
            "facility_id": 3,
            "facility_code": "FAC-003",
            "facility_name": "Al Mouwasat Hospital",
            "facility_name_ar": "مستشفى المواساة",
            "chi_license_number": "CHI-DMM-001",
            "accreditation_tier": 3,
            "region": "Eastern",
            "city": "Dammam",
            "nphies_payer_id": "NPHIES-FAC-003"
        }
    ]

    # ==========================================================================
    # Sample Diagnosis Codes (ICD-10)
    # ==========================================================================

    DIAGNOSIS_CODES = {
        "J06.9": "Acute upper respiratory infection, unspecified",
        "R05": "Cough",
        "I10": "Essential (primary) hypertension",
        "E11.9": "Type 2 diabetes mellitus without complications",
        "K35.9": "Acute appendicitis, unspecified",
        "M54.5": "Low back pain",
        "J18.9": "Pneumonia, unspecified organism"
    }

    # ==========================================================================
    # Sample Claims
    # ==========================================================================

    @classmethod
    def generate_claim(
        cls,
        patient_idx: int = 0,
        facility_idx: int = 0,
        insurance_idx: int = 0,
        services: List[str] = None,
        diagnosis_codes: List[str] = None
    ) -> Dict[str, Any]:
        """Generate a sample claim"""

        patient = cls.PATIENTS[patient_idx]
        facility = cls.FACILITIES[facility_idx]
        insurance = cls.INSURANCE_POLICIES[insurance_idx]

        if services is None:
            services = ["SBS-LAB-001", "SBS-RAD-001", "SBS-CONS-001"]

        if diagnosis_codes is None:
            diagnosis_codes = ["J06.9", "R05"]

        claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
        service_date = date.today().isoformat()

        claim_items = []
        total_amount = 0

        for idx, sbs_code in enumerate(services, 1):
            sbs_info = cls.SBS_CODES.get(sbs_code, {})
            unit_price = sbs_info.get("standard_price", 100.00)
            quantity = 1

            claim_items.append({
                "sequence": idx,
                "sbs_code": sbs_code,
                "description": sbs_info.get("description_en", "Unknown Service"),
                "description_ar": sbs_info.get("description_ar", "خدمة غير معروفة"),
                "category": sbs_info.get("category", "Other"),
                "quantity": quantity,
                "unit_price": unit_price,
                "net_amount": unit_price * quantity,
                "service_date": service_date
            })
            total_amount += unit_price * quantity

        return {
            "claim_id": claim_id,
            "claim_type": "institutional",
            "claim_use": "claim",
            "status": "active",
            "created": datetime.now().isoformat(),
            "facility": facility,
            "patient": {
                **patient,
                "insurance": insurance
            },
            "provider": {
                "id": facility["facility_code"],
                "name": facility["facility_name"],
                "license_number": facility["chi_license_number"]
            },
            "diagnosis": [
                {
                    "sequence": idx,
                    "code": code,
                    "description": cls.DIAGNOSIS_CODES.get(code, "Unknown"),
                    "type": "principal" if idx == 1 else "secondary"
                }
                for idx, code in enumerate(diagnosis_codes, 1)
            ],
            "items": claim_items,
            "total_amount": total_amount,
            "currency": "SAR"
        }

    @classmethod
    def generate_fhir_bundle(cls, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a FHIR R4 Bundle from claim data"""

        bundle_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Patient resource
        patient = claim["patient"]
        patient_resource = {
            "resourceType": "Patient",
            "id": patient["id"],
            "identifier": [{
                "system": "http://nphies.sa/identifier/nationalid",
                "value": patient["national_id"]
            }],
            "name": [{
                "family": patient["name"].split()[-1],
                "given": patient["name"].split()[:-1],
                "text": patient["name"]
            }],
            "gender": patient["gender"],
            "birthDate": patient["birthDate"],
            "telecom": [
                {"system": "phone", "value": patient.get("phone", "")},
                {"system": "email", "value": patient.get("email", "")}
            ]
        }

        # Coverage resource
        insurance = patient["insurance"]
        coverage_resource = {
            "resourceType": "Coverage",
            "id": f"coverage-{insurance['policy_number']}",
            "status": "active",
            "beneficiary": {
                "reference": f"Patient/{patient['id']}"
            },
            "payor": [{
                "identifier": {
                    "system": "http://nphies.sa/identifier/payer",
                    "value": insurance["payer_id"]
                },
                "display": insurance["payer_name"]
            }],
            "class": [{
                "type": {
                    "coding": [{
                        "system": "http://nphies.sa/codesystem/coverage-class",
                        "code": insurance["class"]
                    }]
                },
                "value": insurance["policy_number"],
                "name": insurance["class_name"]
            }],
            "period": {
                "start": insurance["effective_date"],
                "end": insurance["termination_date"]
            }
        }

        # Organization resource (Facility)
        facility = claim["facility"]
        organization_resource = {
            "resourceType": "Organization",
            "id": facility["facility_code"],
            "identifier": [{
                "system": "http://nphies.sa/identifier/chi-license",
                "value": facility["chi_license_number"]
            }],
            "name": facility["facility_name"],
            "type": [{
                "coding": [{
                    "system": "http://nphies.sa/codesystem/organization-type",
                    "code": "prov",
                    "display": "Healthcare Provider"
                }]
            }]
        }

        # Build claim items
        fhir_items = []
        for item in claim["items"]:
            fhir_items.append({
                "sequence": item["sequence"],
                "productOrService": {
                    "coding": [{
                        "system": "http://nphies.sa/codesystem/sbs",
                        "code": item["sbs_code"],
                        "display": item["description"]
                    }]
                },
                "servicedDate": item["service_date"],
                "quantity": {"value": item["quantity"]},
                "unitPrice": {
                    "value": item["unit_price"],
                    "currency": "SAR"
                },
                "net": {
                    "value": item["net_amount"],
                    "currency": "SAR"
                }
            })

        # Diagnosis entries
        fhir_diagnosis = []
        for diag in claim["diagnosis"]:
            fhir_diagnosis.append({
                "sequence": diag["sequence"],
                "diagnosisCodeableConcept": {
                    "coding": [{
                        "system": "http://hl7.org/fhir/sid/icd-10",
                        "code": diag["code"],
                        "display": diag["description"]
                    }]
                },
                "type": [{
                    "coding": [{
                        "system": "http://nphies.sa/codesystem/diagnosis-type",
                        "code": diag["type"]
                    }]
                }]
            })

        # Claim resource
        claim_resource = {
            "resourceType": "Claim",
            "id": claim["claim_id"],
            "status": claim["status"],
            "type": {
                "coding": [{
                    "system": "http://nphies.sa/codesystem/claim-type",
                    "code": claim["claim_type"]
                }]
            },
            "use": claim["claim_use"],
            "patient": {
                "reference": f"Patient/{patient['id']}"
            },
            "created": claim["created"],
            "insurer": {
                "identifier": {
                    "system": "http://nphies.sa/identifier/payer",
                    "value": insurance["payer_id"]
                }
            },
            "provider": {
                "reference": f"Organization/{facility['facility_code']}",
                "display": facility["facility_name"]
            },
            "priority": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/processpriority",
                    "code": "normal"
                }]
            },
            "insurance": [{
                "sequence": 1,
                "focal": True,
                "coverage": {
                    "reference": f"Coverage/{coverage_resource['id']}"
                }
            }],
            "diagnosis": fhir_diagnosis,
            "item": fhir_items,
            "total": {
                "value": claim["total_amount"],
                "currency": "SAR"
            }
        }

        # Build Bundle
        bundle = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "message",
            "timestamp": timestamp,
            "entry": [
                {"fullUrl": f"urn:uuid:{uuid.uuid4()}", "resource": patient_resource},
                {"fullUrl": f"urn:uuid:{uuid.uuid4()}", "resource": coverage_resource},
                {"fullUrl": f"urn:uuid:{uuid.uuid4()}", "resource": organization_resource},
                {"fullUrl": f"urn:uuid:{uuid.uuid4()}", "resource": claim_resource}
            ]
        }

        return bundle


# =============================================================================
# Pre-generated test fixtures
# =============================================================================

SAMPLE_CLAIM_SIMPLE = SampleData.generate_claim(
    patient_idx=0,
    facility_idx=0,
    insurance_idx=0,
    services=["SBS-LAB-001", "SBS-CONS-001"],
    diagnosis_codes=["J06.9"]
)

SAMPLE_CLAIM_COMPLEX = SampleData.generate_claim(
    patient_idx=1,
    facility_idx=1,
    insurance_idx=1,
    services=["SBS-LAB-001", "SBS-LAB-002", "SBS-RAD-001", "SBS-CONS-002"],
    diagnosis_codes=["I10", "E11.9"]
)

SAMPLE_CLAIM_SURGERY = SampleData.generate_claim(
    patient_idx=2,
    facility_idx=2,
    insurance_idx=2,
    services=["SBS-SURG-001", "SBS-LAB-001", "SBS-RAD-001"],
    diagnosis_codes=["K35.9"]
)

SAMPLE_FHIR_BUNDLE_SIMPLE = SampleData.generate_fhir_bundle(SAMPLE_CLAIM_SIMPLE)
SAMPLE_FHIR_BUNDLE_COMPLEX = SampleData.generate_fhir_bundle(SAMPLE_CLAIM_COMPLEX)
SAMPLE_FHIR_BUNDLE_SURGERY = SampleData.generate_fhir_bundle(SAMPLE_CLAIM_SURGERY)


# =============================================================================
# Utility functions
# =============================================================================

def save_fixture(data: Dict[str, Any], filename: str):
    """Save fixture data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_fixture(filename: str) -> Dict[str, Any]:
    """Load fixture data from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    # Generate and save sample fixtures
    import os

    fixtures_dir = os.path.dirname(__file__)

    fixtures = {
        "sample_claim_simple.json": SAMPLE_CLAIM_SIMPLE,
        "sample_claim_complex.json": SAMPLE_CLAIM_COMPLEX,
        "sample_claim_surgery.json": SAMPLE_CLAIM_SURGERY,
        "sample_fhir_bundle_simple.json": SAMPLE_FHIR_BUNDLE_SIMPLE,
        "sample_fhir_bundle_complex.json": SAMPLE_FHIR_BUNDLE_COMPLEX,
        "sample_fhir_bundle_surgery.json": SAMPLE_FHIR_BUNDLE_SURGERY,
    }

    for filename, data in fixtures.items():
        filepath = os.path.join(fixtures_dir, "fixtures", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        save_fixture(data, filepath)
        print(f"✅ Saved: {filepath}")

    print("\n📦 All fixtures generated successfully!")
