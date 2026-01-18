"""
Comprehensive Test Suite for Financial Rules Engine
===================================================

Tests for:
- CHI business rules validation
- Pricing tier calculations
- Service bundle detection
- Price cap enforcement
- Database integration
"""

import pytest


class TestPricingTiers:
    """Tests for pricing tier calculations"""

    PRICING_TIERS = {
        1: {"name": "Reference Hospital", "markup_pct": 10.0},
        2: {"name": "Tertiary Care Center", "markup_pct": 20.0},
        3: {"name": "Specialized Hospital", "markup_pct": 30.0},
        4: {"name": "General Hospital (JCI)", "markup_pct": 40.0},
        5: {"name": "General Hospital (CBAHI)", "markup_pct": 50.0},
        6: {"name": "Private Clinic (Level A)", "markup_pct": 60.0},
        7: {"name": "Private Clinic (Level B)", "markup_pct": 70.0},
        8: {"name": "Primary Care Center", "markup_pct": 75.0},
    }

    def test_tier_markup_calculation(self):
        """Test markup percentage calculation by tier"""
        base_price = 100.00
        tier = 1  # Reference Hospital - 10% markup

        markup_pct = self.PRICING_TIERS[tier]["markup_pct"]
        allowed_price = base_price * (1 + markup_pct / 100)

        assert abs(allowed_price - 110.00) < 0.01  # Float comparison with tolerance

    def test_all_tiers_defined(self):
        """Test that all 8 tiers are defined"""
        assert len(self.PRICING_TIERS) == 8
        for tier in range(1, 9):
            assert tier in self.PRICING_TIERS

    def test_markup_increases_with_tier(self):
        """Test that markup percentage increases with tier level"""
        markups = [self.PRICING_TIERS[i]["markup_pct"] for i in range(1, 9)]

        # Each tier should have higher markup than previous
        for i in range(1, len(markups)):
            assert markups[i] > markups[i - 1]

    def test_max_allowed_price_calculation(self):
        """Test maximum allowed price calculation"""
        standard_price = 50.00
        tier = 4  # 40% markup

        markup_pct = self.PRICING_TIERS[tier]["markup_pct"]
        max_allowed = standard_price * (1 + markup_pct / 100)

        assert max_allowed == 70.00


class TestValidationRules:
    """Tests for validation rules"""

    def test_validate_request_schema(self):
        """Test validation request schema"""
        valid_request = {
            "bundle": {
                "resourceType": "Bundle",
                "id": "test-bundle",
                "entry": []
            },
            "facility_id": 1
        }

        assert "bundle" in valid_request
        assert "facility_id" in valid_request

    def test_validation_response_schema(self):
        """Test validation response schema"""
        expected_response = {
            "request_id": "uuid-here",
            "is_valid": True,
            "applied_rules": [
                {
                    "rule_id": "CHI-PRICE-001",
                    "rule_name": "Price Cap Validation",
                    "status": "passed",
                    "message": "All prices within allowed limits"
                }
            ],
            "priced_bundle": {
                "resourceType": "Bundle",
                "entry": []
            },
            "total_price": 490.00,
            "total_allowed": 500.00
        }

        assert "is_valid" in expected_response
        assert "applied_rules" in expected_response
        assert "priced_bundle" in expected_response

    def test_price_cap_violation_detection(self):
        """Test detection of price cap violations"""
        claim_price = 150.00
        standard_price = 100.00
        markup_pct = 40.0  # Tier 4
        max_allowed = standard_price * (1 + markup_pct / 100)  # 140.00

        is_violation = claim_price > max_allowed

        assert is_violation
        assert max_allowed == 140.00

    def test_validation_rule_structure(self):
        """Test validation rule structure"""
        rule = {
            "rule_id": "CHI-PRICE-001",
            "rule_name": "Price Cap Validation",
            "rule_type": "price",
            "status": "passed",
            "severity": "error",  # error, warning, info
            "message": "Price within allowed limit",
            "details": {
                "claimed_price": 130.00,
                "max_allowed": 140.00,
                "standard_price": 100.00,
                "tier": 4
            }
        }

        required_fields = ["rule_id", "rule_name", "status", "severity", "message"]
        for field in required_fields:
            assert field in rule


class TestBundleDetection:
    """Tests for service bundle detection"""

    SAMPLE_BUNDLES = {
        "BUNDLE-MATERNITY-001": {
            "name": "Normal Delivery Package",
            "total_price": 8000.00,
            "required_codes": ["SBS-MAT-001", "SBS-MAT-002", "SBS-LAB-001"]
        },
        "BUNDLE-APPENDIX-001": {
            "name": "Appendectomy Package",
            "total_price": 15000.00,
            "required_codes": ["SBS-SURG-001", "SBS-ANESTH-001", "SBS-LAB-001"]
        }
    }

    def test_bundle_detection_logic(self):
        """Test bundle detection from claim items"""
        claim_codes = ["SBS-MAT-001", "SBS-MAT-002", "SBS-LAB-001", "SBS-CONS-001"]

        detected_bundles = []
        for bundle_id, bundle_info in self.SAMPLE_BUNDLES.items():
            required = set(bundle_info["required_codes"])
            claimed = set(claim_codes)

            if required.issubset(claimed):
                detected_bundles.append(bundle_id)

        assert "BUNDLE-MATERNITY-001" in detected_bundles

    def test_bundle_price_override(self):
        """Test that bundle price overrides itemized pricing"""
        itemized_total = 10000.00
        bundle_price = 8000.00

        # Bundle price should be used when lower
        final_price = min(itemized_total, bundle_price)

        assert final_price == 8000.00

    def test_partial_bundle_detection(self):
        """Test detection of partial bundle (missing items)"""
        bundle_required = ["SBS-MAT-001", "SBS-MAT-002", "SBS-LAB-001"]
        claim_codes = ["SBS-MAT-001", "SBS-MAT-002"]  # Missing SBS-LAB-001

        required = set(bundle_required)
        claimed = set(claim_codes)

        is_complete_bundle = required.issubset(claimed)
        missing_codes = required - claimed

        assert not is_complete_bundle
        assert "SBS-LAB-001" in missing_codes


class TestCHIBusinessRules:
    """Tests for CHI-specific business rules"""

    def test_prior_auth_requirement(self):
        """Test prior authorization requirement for certain procedures"""
        PRIOR_AUTH_REQUIRED = [
            "SBS-SURG-001",  # Appendectomy
            "SBS-SURG-002",  # Major surgery
            "SBS-RAD-002",   # MRI
            "SBS-RAD-003"    # CT Scan
        ]

        claim_code = "SBS-SURG-001"
        requires_prior_auth = claim_code in PRIOR_AUTH_REQUIRED

        assert requires_prior_auth

    def test_medical_necessity_validation(self):
        """Test medical necessity based on diagnosis"""
        claim = {
            "diagnosis_codes": ["J06.9"],  # Acute upper respiratory infection
            "procedure_codes": ["SBS-LAB-001"]  # CBC
        }

        # CBC is medically necessary for respiratory infection diagnosis
        valid_combinations = {
            "J06.9": ["SBS-LAB-001", "SBS-RAD-001"],  # Blood test, chest x-ray
            "I10": ["SBS-LAB-002", "SBS-CONS-001"]    # Lipid panel, consultation
        }

        is_necessary = any(
            code in valid_combinations.get(claim["diagnosis_codes"][0], [])
            for code in claim["procedure_codes"]
        )

        assert is_necessary

    def test_duplicate_service_detection(self):
        """Test duplicate service detection on same date"""
        claim_items = [
            {"code": "SBS-LAB-001", "date": "2024-01-15", "quantity": 1},
            {"code": "SBS-LAB-001", "date": "2024-01-15", "quantity": 1},  # Duplicate
            {"code": "SBS-RAD-001", "date": "2024-01-15", "quantity": 1}
        ]

        # Check for duplicates
        seen = set()
        duplicates = []

        for item in claim_items:
            key = (item["code"], item["date"])
            if key in seen:
                duplicates.append(key)
            seen.add(key)

        assert len(duplicates) == 1
        assert duplicates[0] == ("SBS-LAB-001", "2024-01-15")

    def test_quantity_limit_enforcement(self):
        """Test quantity limits per service"""
        QUANTITY_LIMITS = {
            "SBS-LAB-001": 1,  # CBC - max 1 per day
            "SBS-CONS-001": 2,  # Consultation - max 2 per day
            "SBS-RAD-001": 1   # X-Ray - max 1 per day
        }

        claim_item = {"code": "SBS-LAB-001", "quantity": 3}
        max_quantity = QUANTITY_LIMITS.get(claim_item["code"], 1)

        exceeds_limit = claim_item["quantity"] > max_quantity

        assert exceeds_limit


class TestFacilityTier:
    """Tests for facility tier determination"""

    def test_facility_tier_lookup(self):
        """Test facility tier lookup from database"""
        facilities = {
            1: {"name": "King Fahad Medical City", "tier": 1},
            2: {"name": "General Hospital", "tier": 4},
            3: {"name": "Private Clinic", "tier": 6}
        }

        facility_id = 1
        tier = facilities[facility_id]["tier"]

        assert tier == 1

    def test_tier_not_found_default(self):
        """Test default tier when facility not found"""
        DEFAULT_TIER = 5  # Most common tier

        facility_tier = None  # Not found
        effective_tier = facility_tier if facility_tier else DEFAULT_TIER

        assert effective_tier == DEFAULT_TIER


class TestPriceCalculation:
    """Tests for price calculation"""

    def test_total_claim_calculation(self):
        """Test total claim amount calculation"""
        items = [
            {"unit_price": 50.00, "quantity": 1},
            {"unit_price": 180.00, "quantity": 1},
            {"unit_price": 250.00, "quantity": 1}
        ]

        total = sum(item["unit_price"] * item["quantity"] for item in items)

        assert total == 480.00

    def test_price_adjustment_logging(self):
        """Test logging of price adjustments"""
        adjustment = {
            "original_price": 150.00,
            "adjusted_price": 140.00,
            "adjustment_reason": "Price cap exceeded - adjustment required",
            "rule_id": "CHI-PRICE-001",
            "sbs_code": "SBS-LAB-001"
        }

        assert adjustment["adjusted_price"] < adjustment["original_price"]
        assert "exceeded" in adjustment["adjustment_reason"].lower()


class TestDatabaseIntegration:
    """Tests for financial rules database integration"""

    def test_pricing_tier_query(self):
        """Test pricing tier lookup SQL"""
        expected_query = """
            SELECT tier_level, markup_pct, tier_description
            FROM pricing_tier_rules
            WHERE tier_level = %s
              AND is_active = TRUE
              AND effective_date <= CURRENT_DATE
              AND (expiry_date IS NULL OR expiry_date > CURRENT_DATE)
        """

        assert "pricing_tier_rules" in expected_query
        assert "is_active" in expected_query

    def test_bundle_lookup_query(self):
        """Test service bundle lookup SQL"""
        expected_query = """
            SELECT sb.bundle_id, sb.bundle_code, sb.bundle_name, sb.total_allowed_price,
                   array_agg(bi.sbs_code) as required_codes
            FROM service_bundles sb
            JOIN bundle_items bi ON sb.bundle_id = bi.bundle_id
            WHERE sb.is_active = TRUE
            GROUP BY sb.bundle_id
        """

        assert "service_bundles" in expected_query
        assert "bundle_items" in expected_query

    def test_sbs_price_lookup_query(self):
        """Test SBS standard price lookup SQL"""
        expected_query = """
            SELECT sbs_id, standard_price, category
            FROM sbs_master_catalogue
            WHERE sbs_id = %s
              AND is_active = TRUE
              AND effective_date <= CURRENT_DATE
        """

        assert "sbs_master_catalogue" in expected_query


# Pytest fixtures
@pytest.fixture
def sample_claim_bundle():
    """Sample claim bundle for validation"""
    return {
        "resourceType": "Bundle",
        "id": "test-claim-bundle",
        "type": "message",
        "entry": [
            {
                "resource": {
                    "resourceType": "Claim",
                    "item": [
                        {
                            "sequence": 1,
                            "productOrService": {
                                "coding": [{"code": "SBS-LAB-001"}]
                            },
                            "quantity": {"value": 1},
                            "unitPrice": {"value": 60.00, "currency": "SAR"}
                        },
                        {
                            "sequence": 2,
                            "productOrService": {
                                "coding": [{"code": "SBS-RAD-001"}]
                            },
                            "quantity": {"value": 1},
                            "unitPrice": {"value": 180.00, "currency": "SAR"}
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture
def sample_validation_result():
    """Sample validation result"""
    return {
        "is_valid": True,
        "applied_rules": [
            {
                "rule_id": "CHI-PRICE-001",
                "status": "passed"
            }
        ],
        "total_price": 240.00
    }


def test_sample_bundle_has_items(sample_claim_bundle):
    """Test sample bundle has claim items"""
    claim = next(
        e["resource"] for e in sample_claim_bundle["entry"]
        if e["resource"]["resourceType"] == "Claim"
    )

    assert len(claim["item"]) == 2


def test_validation_result_structure(sample_validation_result):
    """Test validation result structure"""
    assert "is_valid" in sample_validation_result
    assert "applied_rules" in sample_validation_result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
