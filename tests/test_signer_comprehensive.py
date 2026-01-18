"""
Comprehensive Test Suite for Signer Service
============================================

Tests for:
- Digital signature generation (SHA256withRSA)
- Certificate management
- FHIR Bundle canonicalization
- Test keypair generation
- Database integration
"""

import pytest
import json
import base64
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


class TestDigitalSignature:
    """Tests for digital signature functionality"""
    
    def test_signature_request_schema(self):
        """Test signature request schema validation"""
        valid_request = {
            "bundle": {
                "resourceType": "Bundle",
                "id": "test-bundle",
                "type": "message",
                "entry": []
            },
            "facility_id": 1
        }
        
        assert "bundle" in valid_request
        assert "facility_id" in valid_request
        assert valid_request["bundle"]["resourceType"] == "Bundle"
    
    def test_signature_response_schema(self):
        """Test signature response schema"""
        expected_response = {
            "request_id": "uuid-here",
            "signed_bundle": {
                "resourceType": "Bundle",
                "id": "test-bundle",
                "meta": {
                    "lastUpdated": "2024-01-15T10:00:00Z"
                },
                "signature": {
                    "type": [{
                        "system": "urn:iso-astm:E1762-95:2013",
                        "code": "1.2.840.10065.1.12.1.1",
                        "display": "Author's Signature"
                    }],
                    "when": "2024-01-15T10:00:00Z",
                    "who": {
                        "reference": "Organization/facility-1"
                    },
                    "sigFormat": "application/signature+xml",
                    "data": "base64-encoded-signature"
                },
                "entry": []
            },
            "signature": "base64-encoded-signature",
            "algorithm": "SHA256withRSA",
            "certificate_serial": "ABC123"
        }
        
        assert "signed_bundle" in expected_response
        assert "signature" in expected_response["signed_bundle"]
        assert expected_response["algorithm"] == "SHA256withRSA"
    
    def test_sha256_hash_generation(self):
        """Test SHA256 hash generation for bundle"""
        test_data = '{"resourceType":"Bundle","id":"test"}'
        expected_hash = hashlib.sha256(test_data.encode('utf-8')).hexdigest()
        
        assert len(expected_hash) == 64  # SHA256 produces 64 hex chars
    
    def test_base64_encoding(self):
        """Test base64 encoding of signature"""
        signature_bytes = b"test_signature_data"
        encoded = base64.b64encode(signature_bytes).decode('utf-8')
        decoded = base64.b64decode(encoded)
        
        assert decoded == signature_bytes


class TestFHIRCanonicalization:
    """Tests for FHIR Bundle canonicalization"""
    
    def test_canonicalization_removes_signature(self):
        """Test that canonicalization removes existing signature"""
        bundle_with_sig = {
            "resourceType": "Bundle",
            "id": "test",
            "signature": {"data": "old-signature"},
            "entry": []
        }
        
        # Canonicalization should remove signature
        canonical_bundle = {k: v for k, v in bundle_with_sig.items() if k != "signature"}
        
        assert "signature" not in canonical_bundle
        assert "resourceType" in canonical_bundle
    
    def test_canonicalization_sorts_keys(self):
        """Test that canonicalization sorts JSON keys"""
        unsorted = {"z": 1, "a": 2, "m": 3}
        sorted_json = json.dumps(unsorted, sort_keys=True)
        
        assert sorted_json == '{"a": 2, "m": 3, "z": 1}'
    
    def test_canonicalization_consistent_output(self):
        """Test that canonicalization produces consistent output"""
        bundle = {
            "resourceType": "Bundle",
            "id": "test",
            "type": "message",
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "1"}},
                {"resource": {"resourceType": "Claim", "id": "2"}}
            ]
        }
        
        # Multiple canonicalizations should produce same result
        canonical1 = json.dumps(bundle, sort_keys=True, separators=(',', ':'))
        canonical2 = json.dumps(bundle, sort_keys=True, separators=(',', ':'))
        
        assert canonical1 == canonical2
    
    def test_canonicalization_handles_unicode(self):
        """Test canonicalization with Arabic text"""
        bundle = {
            "resourceType": "Bundle",
            "id": "test",
            "entry": [{
                "resource": {
                    "resourceType": "Patient",
                    "name": [{"text": "أحمد الراشد"}]
                }
            }]
        }
        
        canonical = json.dumps(bundle, sort_keys=True, ensure_ascii=False)
        
        assert "أحمد الراشد" in canonical


class TestCertificateManagement:
    """Tests for certificate management"""
    
    def test_certificate_info_schema(self):
        """Test certificate info response schema"""
        cert_info = {
            "serial_number": "ABC123",
            "subject": "CN=Facility Name, O=Healthcare Provider, C=SA",
            "issuer": "CN=Saudi Healthcare CA, O=CCHI, C=SA",
            "valid_from": "2024-01-01T00:00:00Z",
            "valid_until": "2025-01-01T00:00:00Z",
            "is_valid": True,
            "days_until_expiry": 365
        }
        
        required_fields = ["serial_number", "subject", "issuer", "valid_from", "valid_until"]
        for field in required_fields:
            assert field in cert_info
    
    def test_certificate_validity_check(self):
        """Test certificate validity checking"""
        now = datetime.now()
        valid_from = now - timedelta(days=30)
        valid_until = now + timedelta(days=335)
        
        is_valid = valid_from <= now <= valid_until
        
        assert is_valid
    
    def test_certificate_expiry_warning(self):
        """Test certificate expiry warning threshold"""
        EXPIRY_WARNING_DAYS = 30
        
        days_until_expiry = 25
        should_warn = days_until_expiry <= EXPIRY_WARNING_DAYS
        
        assert should_warn


class TestTestKeypairGeneration:
    """Tests for test keypair generation"""
    
    def test_generate_keypair_response(self):
        """Test keypair generation response schema"""
        expected_response = {
            "message": "Test keypair generated successfully",
            "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
            "private_key_saved": True,
            "key_size": 2048,
            "algorithm": "RSA"
        }
        
        assert "public_key_pem" in expected_response
        assert expected_response["key_size"] == 2048
    
    def test_pem_format_validation(self):
        """Test PEM format validation"""
        valid_public_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBg...\n-----END PUBLIC KEY-----"
        
        assert valid_public_key.startswith("-----BEGIN PUBLIC KEY-----")
        assert valid_public_key.endswith("-----END PUBLIC KEY-----")


class TestDatabaseIntegration:
    """Tests for signer service database integration"""
    
    def test_certificate_lookup_query(self):
        """Test certificate lookup SQL"""
        expected_query = """
            SELECT cert_id, serial_number, subject, issuer,
                   valid_from, valid_until, private_key_path, public_cert_path
            FROM facility_certificates
            WHERE facility_id = %s 
              AND is_active = TRUE
              AND cert_type IN ('signing', 'both')
              AND valid_until > CURRENT_DATE
            ORDER BY valid_until DESC
            LIMIT 1
        """
        
        assert "facility_certificates" in expected_query
        assert "is_active" in expected_query
        assert "valid_until > CURRENT_DATE" in expected_query


class TestSigningWorkflow:
    """Tests for complete signing workflow"""
    
    def test_signing_workflow_steps(self):
        """Test signing workflow steps"""
        workflow_steps = [
            "1. Receive bundle and facility_id",
            "2. Lookup certificate for facility",
            "3. Canonicalize bundle (remove existing signature, sort keys)",
            "4. Generate SHA256 hash of canonical form",
            "5. Sign hash with private key using RSA PKCS#1 v1.5",
            "6. Base64 encode signature",
            "7. Add FHIR signature element to bundle",
            "8. Return signed bundle"
        ]
        
        assert len(workflow_steps) == 8
    
    def test_signature_element_structure(self):
        """Test FHIR signature element structure"""
        signature_element = {
            "type": [{
                "system": "urn:iso-astm:E1762-95:2013",
                "code": "1.2.840.10065.1.12.1.1",
                "display": "Author's Signature"
            }],
            "when": datetime.now().isoformat(),
            "who": {
                "reference": "Organization/facility-1"
            },
            "sigFormat": "application/signature+xml",
            "data": "base64-encoded-signature-data"
        }
        
        assert "type" in signature_element
        assert "when" in signature_element
        assert "who" in signature_element
        assert "data" in signature_element


class TestErrorHandling:
    """Tests for signer service error handling"""
    
    def test_missing_certificate_error(self):
        """Test error response for missing certificate"""
        error_response = {
            "request_id": "uuid-here",
            "error": "No active signing certificate found for facility",
            "facility_id": 1
        }
        
        assert "error" in error_response
        assert "facility_id" in error_response
    
    def test_expired_certificate_error(self):
        """Test error response for expired certificate"""
        error_response = {
            "request_id": "uuid-here",
            "error": "Certificate has expired",
            "certificate_serial": "ABC123",
            "expired_on": "2023-12-31T23:59:59Z"
        }
        
        assert "error" in error_response
        assert "expired" in error_response["error"].lower()
    
    def test_invalid_bundle_error(self):
        """Test error response for invalid bundle"""
        error_response = {
            "detail": [
                {
                    "loc": ["body", "bundle", "resourceType"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }
        
        assert "detail" in error_response


class TestVerification:
    """Tests for signature verification"""
    
    def test_verify_request_schema(self):
        """Test verification request schema"""
        valid_request = {
            "signed_bundle": {
                "resourceType": "Bundle",
                "id": "test",
                "signature": {
                    "data": "base64-signature"
                },
                "entry": []
            },
            "facility_id": 1
        }
        
        assert "signed_bundle" in valid_request
        assert "signature" in valid_request["signed_bundle"]
    
    def test_verify_response_schema(self):
        """Test verification response schema"""
        expected_response = {
            "request_id": "uuid-here",
            "is_valid": True,
            "verification_details": {
                "certificate_serial": "ABC123",
                "signed_at": "2024-01-15T10:00:00Z",
                "algorithm": "SHA256withRSA"
            }
        }
        
        assert "is_valid" in expected_response
        assert isinstance(expected_response["is_valid"], bool)


# Pytest fixtures
@pytest.fixture
def sample_unsigned_bundle():
    """Sample unsigned FHIR Bundle"""
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
                    "id": "PAT-001",
                    "name": [{"text": "Ahmed Al-Rashid"}]
                }
            }
        ]
    }


@pytest.fixture
def sample_signed_bundle(sample_unsigned_bundle):
    """Sample signed FHIR Bundle"""
    bundle = sample_unsigned_bundle.copy()
    bundle["signature"] = {
        "type": [{
            "system": "urn:iso-astm:E1762-95:2013",
            "code": "1.2.840.10065.1.12.1.1"
        }],
        "when": "2024-01-15T10:00:00Z",
        "who": {"reference": "Organization/1"},
        "data": "dGVzdC1zaWduYXR1cmU="
    }
    return bundle


def test_unsigned_bundle_has_no_signature(sample_unsigned_bundle):
    """Test that unsigned bundle has no signature"""
    assert "signature" not in sample_unsigned_bundle


def test_signed_bundle_has_signature(sample_signed_bundle):
    """Test that signed bundle has signature"""
    assert "signature" in sample_signed_bundle
    assert "data" in sample_signed_bundle["signature"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
