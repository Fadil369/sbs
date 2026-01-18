"""
Pytest Configuration and Shared Fixtures
========================================

Provides shared fixtures and configuration for all test modules.
"""

import pytest
import json
import os
import sys
from typing import Dict, Any
from datetime import datetime, date

# Add tests directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import sample data generators
from fixtures_data import (
    SampleData,
    SAMPLE_CLAIM_SIMPLE,
    SAMPLE_CLAIM_COMPLEX,
    SAMPLE_CLAIM_SURGERY,
    SAMPLE_FHIR_BUNDLE_SIMPLE,
    SAMPLE_FHIR_BUNDLE_COMPLEX,
    SAMPLE_FHIR_BUNDLE_SURGERY
)


# =============================================================================
# Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# =============================================================================
# Service URL Fixtures
# =============================================================================

@pytest.fixture
def service_urls():
    """Get service URLs from environment or defaults"""
    return {
        "normalizer": os.getenv("NORMALIZER_URL", "http://localhost:8000"),
        "signer": os.getenv("SIGNER_URL", "http://localhost:8001"),
        "financial": os.getenv("FINANCIAL_URL", "http://localhost:8002"),
        "nphies": os.getenv("NPHIES_URL", "http://localhost:8003")
    }


# =============================================================================
# Sample Claim Fixtures
# =============================================================================

@pytest.fixture
def simple_claim():
    """Simple claim with basic services"""
    return SAMPLE_CLAIM_SIMPLE.copy()


@pytest.fixture
def complex_claim():
    """Complex claim with multiple services"""
    return SAMPLE_CLAIM_COMPLEX.copy()


@pytest.fixture
def surgery_claim():
    """Surgery claim requiring prior authorization"""
    return SAMPLE_CLAIM_SURGERY.copy()


@pytest.fixture
def claim_generator():
    """Factory fixture for generating custom claims"""
    return SampleData.generate_claim


# =============================================================================
# FHIR Bundle Fixtures
# =============================================================================

@pytest.fixture
def simple_fhir_bundle():
    """Simple FHIR bundle"""
    return SAMPLE_FHIR_BUNDLE_SIMPLE.copy()


@pytest.fixture
def complex_fhir_bundle():
    """Complex FHIR bundle"""
    return SAMPLE_FHIR_BUNDLE_COMPLEX.copy()


@pytest.fixture
def surgery_fhir_bundle():
    """Surgery FHIR bundle"""
    return SAMPLE_FHIR_BUNDLE_SURGERY.copy()


@pytest.fixture
def fhir_bundle_generator():
    """Factory fixture for generating FHIR bundles"""
    return SampleData.generate_fhir_bundle


# =============================================================================
# Patient Fixtures
# =============================================================================

@pytest.fixture
def sample_patient():
    """Single sample patient"""
    return SampleData.PATIENTS[0].copy()


@pytest.fixture
def all_sample_patients():
    """All sample patients"""
    return [p.copy() for p in SampleData.PATIENTS]


# =============================================================================
# Facility Fixtures
# =============================================================================

@pytest.fixture
def sample_facility():
    """Single sample facility"""
    return SampleData.FACILITIES[0].copy()


@pytest.fixture
def all_sample_facilities():
    """All sample facilities"""
    return [f.copy() for f in SampleData.FACILITIES]


# =============================================================================
# Insurance Fixtures
# =============================================================================

@pytest.fixture
def vip_insurance():
    """VIP class insurance policy"""
    return SampleData.INSURANCE_POLICIES[0].copy()


@pytest.fixture
def standard_insurance():
    """Standard class insurance policy"""
    return SampleData.INSURANCE_POLICIES[1].copy()


@pytest.fixture
def basic_insurance():
    """Basic class insurance policy"""
    return SampleData.INSURANCE_POLICIES[2].copy()


# =============================================================================
# SBS Code Fixtures
# =============================================================================

@pytest.fixture
def sbs_codes():
    """All SBS codes"""
    return SampleData.SBS_CODES.copy()


@pytest.fixture
def lab_codes():
    """Lab category SBS codes"""
    return {k: v for k, v in SampleData.SBS_CODES.items() if v["category"] == "Lab"}


@pytest.fixture
def radiology_codes():
    """Radiology category SBS codes"""
    return {k: v for k, v in SampleData.SBS_CODES.items() if v["category"] == "Radiology"}


# =============================================================================
# Request/Response Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_normalize_response():
    """Mock normalizer service response"""
    return {
        "request_id": "test-request-id",
        "internal_code": "LAB-CBC-01",
        "sbs_mapped_code": "SBS-LAB-001",
        "official_description": "Complete Blood Count (CBC)",
        "official_description_ar": "تحليل صورة دم كاملة",
        "confidence": 1.0,
        "mapping_source": "manual",
        "category": "Lab",
        "standard_price": 50.00
    }


@pytest.fixture
def mock_sign_response():
    """Mock signer service response"""
    return {
        "request_id": "test-request-id",
        "signed_bundle": {
            "resourceType": "Bundle",
            "signature": {
                "type": [{"code": "1.2.840.10065.1.12.1.1"}],
                "when": datetime.now().isoformat(),
                "data": "dGVzdC1zaWduYXR1cmUtZGF0YQ=="
            }
        },
        "signature": "dGVzdC1zaWduYXR1cmUtZGF0YQ==",
        "algorithm": "SHA256withRSA",
        "certificate_serial": "TEST-CERT-001"
    }


@pytest.fixture
def mock_validate_response():
    """Mock financial rules engine response"""
    return {
        "request_id": "test-request-id",
        "is_valid": True,
        "applied_rules": [
            {
                "rule_id": "CHI-PRICE-001",
                "rule_name": "Price Cap Validation",
                "status": "passed"
            }
        ],
        "priced_bundle": {
            "resourceType": "Bundle"
        },
        "total_price": 400.00,
        "total_allowed": 500.00
    }


@pytest.fixture
def mock_submit_response():
    """Mock NPHIES bridge response"""
    return {
        "request_id": "test-request-id",
        "status": "submitted",
        "transaction_id": "TXN-TEST-001",
        "nphies_transaction_id": "NPHIES-TEST-001",
        "submission_timestamp": datetime.now().isoformat(),
        "response": {
            "resourceType": "Bundle",
            "type": "message",
            "entry": [
                {
                    "resource": {
                        "resourceType": "ClaimResponse",
                        "status": "active",
                        "outcome": "complete"
                    }
                }
            ]
        }
    }


# =============================================================================
# Error Response Fixtures
# =============================================================================

@pytest.fixture
def validation_error_response():
    """Validation error response (422)"""
    return {
        "detail": [
            {
                "loc": ["body", "facility_id"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }


@pytest.fixture
def not_found_error_response():
    """Not found error response (404)"""
    return {
        "request_id": "test-request-id",
        "error": "Resource not found",
        "message": "The requested resource does not exist"
    }


@pytest.fixture
def nphies_error_response():
    """NPHIES OperationOutcome error response"""
    return {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "diagnostics": "Invalid claim format",
                "location": ["Bundle.entry[0].resource"]
            }
        ]
    }


# =============================================================================
# Database Fixtures (for integration tests)
# =============================================================================

@pytest.fixture
def db_connection_params():
    """Database connection parameters"""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "sbs_integration"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "changeme")
    }


# =============================================================================
# Helper Functions
# =============================================================================

@pytest.fixture
def json_serializer():
    """JSON serializer for datetime objects"""
    def serialize(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    return serialize


@pytest.fixture
def assert_valid_fhir_bundle():
    """Assert helper for FHIR bundle validation"""
    def _assert(bundle: Dict[str, Any]):
        assert "resourceType" in bundle
        assert bundle["resourceType"] == "Bundle"
        assert "type" in bundle
        assert "entry" in bundle
        assert isinstance(bundle["entry"], list)
    return _assert


@pytest.fixture
def assert_valid_claim_response():
    """Assert helper for claim response validation"""
    def _assert(response: Dict[str, Any]):
        assert "request_id" in response
        assert "status" in response
    return _assert
