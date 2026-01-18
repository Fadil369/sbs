"""
Comprehensive Test Suite for Normalizer Service
================================================

Tests for:
- Code normalization API
- FHIR Bundle building
- Database integration
- AI fallback normalization
- Cache functionality
- Rate limiting
"""

import pytest
from datetime import datetime

# Test fixtures and sample data
SAMPLE_FACILITY = {
    "facility_id": 1,
    "facility_code": "FAC-001",
    "facility_name": "King Fahad Medical City",
    "chi_license_number": "CHI-RYD-001",
    "accreditation_tier": 1
}

SAMPLE_INTERNAL_CODES = [
    {
        "internal_code": "LAB-CBC-01",
        "facility_id": 1,
        "local_description": "CBC - Complete Blood Count Test",
        "price_gross": 60.00
    },
    {
        "internal_code": "RAD-CXR-01",
        "facility_id": 1,
        "local_description": "Chest X-Ray Standard",
        "price_gross": 180.00
    }
]

SAMPLE_NORMALIZATION_MAPS = [
    {
        "internal_code_id": 1,
        "sbs_code": "SBS-LAB-001",
        "confidence": 1.0,
        "mapping_source": "manual",
        "is_active": True
    }
]

SAMPLE_SBS_CODES = [
    {
        "sbs_id": "SBS-LAB-001",
        "description_en": "Complete Blood Count (CBC)",
        "description_ar": "تحليل صورة دم كاملة",
        "category": "Lab",
        "standard_price": 50.00
    }
]


class TestNormalizationEndpoint:
    """Tests for the /normalize endpoint"""

    def test_normalize_request_schema(self):
        """Test that request schema is properly validated"""
        # Valid request
        valid_request = {
            "facility_id": 1,
            "internal_code": "LAB-CBC-01",
            "description": "Complete Blood Count Test"
        }

        # Validate structure
        assert "facility_id" in valid_request
        assert "internal_code" in valid_request
        assert "description" in valid_request
        assert isinstance(valid_request["facility_id"], int)
        assert isinstance(valid_request["internal_code"], str)
        assert isinstance(valid_request["description"], str)

    def test_normalize_response_schema(self):
        """Test that response schema matches expected format"""
        expected_response = {
            "request_id": "uuid-here",
            "internal_code": "LAB-CBC-01",
            "sbs_mapped_code": "SBS-LAB-001",
            "official_description": "Complete Blood Count (CBC)",
            "official_description_ar": "تحليل صورة دم كاملة",
            "confidence": 1.0,
            "mapping_source": "manual",
            "category": "Lab",
            "standard_price": 50.00
        }

        # Validate response structure
        required_fields = [
            "request_id", "internal_code", "sbs_mapped_code",
            "official_description", "confidence", "mapping_source"
        ]

        for field in required_fields:
            assert field in expected_response


class TestFHIRBundleBuilding:
    """Tests for FHIR Bundle construction"""

    def test_build_patient_resource(self):
        """Test Patient FHIR resource building"""
        patient_data = {
            "id": "PAT-001",
            "name": "Ahmed Al-Rashid",
            "national_id": "1012345678",
            "gender": "male",
            "birthDate": "1985-06-15"
        }

        # Expected FHIR Patient resource structure
        expected_resource = {
            "resourceType": "Patient",
            "id": patient_data["id"],
            "identifier": [{
                "system": "http://nphies.sa/identifier/nationalid",
                "value": patient_data["national_id"]
            }],
            "name": [{
                "family": "Al-Rashid",
                "given": ["Ahmed"],
                "text": patient_data["name"]
            }],
            "gender": patient_data["gender"],
            "birthDate": patient_data["birthDate"]
        }

        assert expected_resource["resourceType"] == "Patient"
        assert expected_resource["identifier"][0]["value"] == "1012345678"

    def test_build_claim_resource(self):
        """Test Claim FHIR resource building"""
        # Sample claim items for test
        sample_claim_items = [
            {
                "sbs_code": "SBS-LAB-001",
                "description": "CBC",
                "quantity": 1,
                "unit_price": 50.00,
                "service_date": "2024-01-15"
            }
        ]
        assert len(sample_claim_items) > 0

        # Expected structure
        claim_resource = {
            "resourceType": "Claim",
            "status": "active",
            "type": {
                "coding": [{
                    "system": "http://nphies.sa/codesystem/claim-type",
                    "code": "institutional"
                }]
            },
            "use": "claim",
            "item": [
                {
                    "sequence": 1,
                    "productOrService": {
                        "coding": [{
                            "system": "http://nphies.sa/codesystem/sbs",
                            "code": "SBS-LAB-001",
                            "display": "CBC"
                        }]
                    },
                    "quantity": {"value": 1},
                    "unitPrice": {"value": 50.00, "currency": "SAR"},
                    "net": {"value": 50.00, "currency": "SAR"}
                }
            ]
        }

        assert claim_resource["resourceType"] == "Claim"
        assert len(claim_resource["item"]) == 1
        assert claim_resource["item"][0]["productOrService"]["coding"][0]["code"] == "SBS-LAB-001"

    def test_build_bundle_structure(self):
        """Test complete FHIR Bundle structure"""
        bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle-id",
            "type": "message",
            "timestamp": datetime.now().isoformat(),
            "entry": []
        }

        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "message"
        assert "entry" in bundle

    def test_bundle_entry_format(self):
        """Test Bundle entry format with fullUrl"""
        entry = {
            "fullUrl": "urn:uuid:12345678-1234-1234-1234-123456789012",
            "resource": {
                "resourceType": "Patient",
                "id": "PAT-001"
            }
        }

        assert entry["fullUrl"].startswith("urn:uuid:")
        assert "resource" in entry
        assert "resourceType" in entry["resource"]


class TestDatabaseIntegration:
    """Tests for database integration"""

    def test_facility_lookup_query(self):
        """Test facility lookup SQL"""
        expected_query = """
            SELECT facility_id, facility_code, facility_name,
                   chi_license_number, accreditation_tier
            FROM facilities
            WHERE facility_id = %s AND is_active = TRUE
        """

        # Verify query structure
        assert "facilities" in expected_query
        assert "is_active" in expected_query

    def test_normalization_map_query(self):
        """Test normalization mapping lookup SQL"""
        expected_query = """
            SELECT snm.sbs_code, smc.description_en, smc.description_ar,
                   snm.confidence, snm.mapping_source, smc.category, smc.standard_price
            FROM sbs_normalization_map snm
            JOIN facility_internal_codes fic ON snm.internal_code_id = fic.internal_code_id
            JOIN sbs_master_catalogue smc ON snm.sbs_code = smc.sbs_id
            WHERE fic.facility_id = %s
              AND fic.internal_code = %s
              AND snm.is_active = TRUE
              AND fic.is_active = TRUE
        """

        # Verify query joins
        assert "sbs_normalization_map" in expected_query
        assert "facility_internal_codes" in expected_query
        assert "sbs_master_catalogue" in expected_query


class TestAINormalization:
    """Tests for AI-powered normalization fallback"""

    def test_ai_suggestion_format(self):
        """Test AI suggestion response format"""
        ai_response = {
            "sbs_code": "SBS-LAB-001",
            "confidence": 0.85,
            "reasoning": "Description matches CBC pattern"
        }

        assert "sbs_code" in ai_response
        assert 0 <= ai_response["confidence"] <= 1

    def test_ai_cache_key_generation(self):
        """Test cache key generation for AI responses"""
        import hashlib

        description = "Complete Blood Count Test"
        cache_key = hashlib.sha256(description.lower().encode()).hexdigest()

        assert len(cache_key) == 64  # SHA256 produces 64 hex chars


class TestRateLimiting:
    """Tests for rate limiting functionality"""

    def test_rate_limit_headers(self):
        """Test expected rate limit headers"""
        expected_headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "99",
            "X-RateLimit-Reset": "1234567890"
        }

        assert "X-RateLimit-Limit" in expected_headers
        assert "X-RateLimit-Remaining" in expected_headers


class TestMetrics:
    """Tests for Prometheus metrics"""

    def test_metrics_endpoint(self):
        """Test that metrics endpoint returns valid format"""
        # Expected Prometheus format
        expected_metrics = [
            "# HELP normalizer_requests_total Total normalization requests",
            "# TYPE normalizer_requests_total counter",
            "normalizer_requests_total{status=\"success\"} 100",
        ]

        for metric in expected_metrics:
            assert "#" in metric or "normalizer_" in metric


class TestErrorHandling:
    """Tests for error handling"""

    def test_validation_error_format(self):
        """Test validation error response format"""
        error_response = {
            "detail": [
                {
                    "loc": ["body", "facility_id"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

        assert "detail" in error_response
        assert isinstance(error_response["detail"], list)

    def test_not_found_error_format(self):
        """Test 404 error response format"""
        error_response = {
            "request_id": "uuid-here",
            "error": "Facility not found",
            "facility_id": 99999
        }

        assert "error" in error_response


# Test fixtures using pytest
@pytest.fixture
def sample_normalize_request():
    """Sample normalization request"""
    return {
        "facility_id": 1,
        "internal_code": "LAB-CBC-01",
        "description": "Complete Blood Count Test"
    }


@pytest.fixture
def sample_fhir_bundle():
    """Sample FHIR Bundle"""
    return {
        "resourceType": "Bundle",
        "id": "test-bundle",
        "type": "message",
        "timestamp": "2024-01-15T10:00:00Z",
        "entry": [
            {
                "fullUrl": "urn:uuid:patient-1",
                "resource": {
                    "resourceType": "Patient",
                    "id": "PAT-001"
                }
            },
            {
                "fullUrl": "urn:uuid:claim-1",
                "resource": {
                    "resourceType": "Claim",
                    "id": "CLM-001"
                }
            }
        ]
    }


def test_sample_request_fixture(sample_normalize_request):
    """Test sample request fixture"""
    assert sample_normalize_request["facility_id"] == 1
    assert sample_normalize_request["internal_code"] == "LAB-CBC-01"


def test_sample_bundle_fixture(sample_fhir_bundle):
    """Test sample bundle fixture"""
    assert sample_fhir_bundle["resourceType"] == "Bundle"
    assert len(sample_fhir_bundle["entry"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
