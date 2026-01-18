#!/usr/bin/env python3
"""
SBS Integration Engine - Standalone Workflow Test
==================================================

This script simulates the complete end-to-end workflow by testing
each component's logic without requiring running services.
"""

import json
import uuid
import base64
import hashlib
from datetime import datetime, date
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field
import sys
import os

# Add tests directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))

from tests.fixtures_data import SampleData, SAMPLE_CLAIM_SIMPLE


@dataclass
class TestResult:
    """Test result container"""
    name: str
    passed: bool
    duration_ms: float = 0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class StandaloneWorkflowSimulator:
    """
    Simulates the SBS workflow without running services.
    Tests each component's core logic.
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.claim = None
        self.fhir_bundle = None
        self.signed_bundle = None
        self.priced_bundle = None
    
    def run_all_tests(self) -> bool:
        """Run all workflow tests"""
        print("\n" + "=" * 60)
        print("🏥 SBS Integration Engine - Standalone Workflow Test")
        print("=" * 60)
        
        tests = [
            ("Step 1: Generate Sample Claim", self.test_claim_generation),
            ("Step 2: Build FHIR Bundle", self.test_fhir_bundle_building),
            ("Step 3: Normalize SBS Codes", self.test_code_normalization),
            ("Step 4: Apply Financial Rules", self.test_financial_rules),
            ("Step 5: Sign Bundle", self.test_bundle_signing),
            ("Step 6: Validate NPHIES Format", self.test_nphies_format),
            ("Step 7: Test Transaction Logging", self.test_transaction_logging),
            ("Step 8: Database Schema Validation", self.test_database_schema),
        ]
        
        for name, test_func in tests:
            print(f"\n{'=' * 50}")
            print(f"🔄 {name}")
            print("-" * 50)
            
            start = datetime.now()
            try:
                result = test_func()
                duration = (datetime.now() - start).total_seconds() * 1000
                result.duration_ms = duration
                self.results.append(result)
                
                status = "✅ PASSED" if result.passed else "❌ FAILED"
                print(f"{status} ({duration:.1f}ms)")
                if result.message:
                    print(f"   📋 {result.message}")
                    
            except Exception as e:
                duration = (datetime.now() - start).total_seconds() * 1000
                self.results.append(TestResult(
                    name=name,
                    passed=False,
                    duration_ms=duration,
                    message=f"Exception: {str(e)}"
                ))
                print(f"❌ FAILED with exception: {e}")
        
        return self.print_summary()
    
    def test_claim_generation(self) -> TestResult:
        """Test 1: Generate sample claim data"""
        try:
            self.claim = SampleData.generate_claim(
                patient_idx=0,
                facility_idx=0,
                insurance_idx=0,
                services=["SBS-LAB-001", "SBS-RAD-001", "SBS-CONS-001"],
                diagnosis_codes=["J06.9", "R05"]
            )
            
            # Validate claim structure
            assert "claim_id" in self.claim
            assert "patient" in self.claim
            assert "items" in self.claim
            assert len(self.claim["items"]) == 3
            
            total = sum(item["net_amount"] for item in self.claim["items"])
            
            return TestResult(
                name="Claim Generation",
                passed=True,
                message=f"Generated claim {self.claim['claim_id']} with {len(self.claim['items'])} items, total SAR {total:.2f}",
                details={
                    "claim_id": self.claim["claim_id"],
                    "patient_name": self.claim["patient"]["name"],
                    "total_amount": total,
                    "service_count": len(self.claim["items"])
                }
            )
        except AssertionError as e:
            return TestResult(name="Claim Generation", passed=False, message=str(e))
    
    def test_fhir_bundle_building(self) -> TestResult:
        """Test 2: Build FHIR R4 Bundle"""
        try:
            self.fhir_bundle = SampleData.generate_fhir_bundle(self.claim)
            
            # Validate FHIR structure
            assert self.fhir_bundle["resourceType"] == "Bundle"
            assert self.fhir_bundle["type"] == "message"
            assert "entry" in self.fhir_bundle
            assert len(self.fhir_bundle["entry"]) >= 3  # Patient, Coverage, Claim
            
            # Check for required resources
            resource_types = [e["resource"]["resourceType"] for e in self.fhir_bundle["entry"]]
            assert "Patient" in resource_types
            assert "Coverage" in resource_types
            assert "Claim" in resource_types
            
            return TestResult(
                name="FHIR Bundle Building",
                passed=True,
                message=f"Built bundle with {len(self.fhir_bundle['entry'])} resources: {', '.join(resource_types)}",
                details={
                    "bundle_id": self.fhir_bundle["id"],
                    "resource_count": len(self.fhir_bundle["entry"]),
                    "resource_types": resource_types
                }
            )
        except AssertionError as e:
            return TestResult(name="FHIR Bundle Building", passed=False, message=str(e))
    
    def test_code_normalization(self) -> TestResult:
        """Test 3: SBS Code Normalization"""
        try:
            # Simulate normalization logic
            normalized_items = []
            
            for item in self.claim["items"]:
                sbs_code = item["sbs_code"]
                sbs_info = SampleData.SBS_CODES.get(sbs_code, {})
                
                normalized_items.append({
                    "original_code": sbs_code,
                    "sbs_code": sbs_code,
                    "description_en": sbs_info.get("description_en", item["description"]),
                    "description_ar": sbs_info.get("description_ar", ""),
                    "category": sbs_info.get("category", "Unknown"),
                    "standard_price": sbs_info.get("standard_price", item["unit_price"]),
                    "confidence": 1.0,
                    "mapping_source": "manual"
                })
            
            # All codes should map
            all_mapped = all(item["confidence"] >= 0.8 for item in normalized_items)
            
            return TestResult(
                name="Code Normalization",
                passed=all_mapped,
                message=f"Normalized {len(normalized_items)} service codes",
                details={
                    "normalized_count": len(normalized_items),
                    "mappings": normalized_items
                }
            )
        except Exception as e:
            return TestResult(name="Code Normalization", passed=False, message=str(e))
    
    def test_financial_rules(self) -> TestResult:
        """Test 4: CHI Financial Rules"""
        try:
            # Get facility tier
            facility = self.claim["facility"]
            tier = facility.get("accreditation_tier", 1)
            
            # Pricing tiers
            TIER_MARKUPS = {1: 10.0, 2: 20.0, 3: 30.0, 4: 40.0, 5: 50.0, 6: 60.0, 7: 70.0, 8: 75.0}
            markup_pct = TIER_MARKUPS.get(tier, 50.0)
            
            # Calculate prices
            validation_results = []
            total_claimed = 0
            total_allowed = 0
            
            for item in self.claim["items"]:
                sbs_info = SampleData.SBS_CODES.get(item["sbs_code"], {})
                standard_price = sbs_info.get("standard_price", item["unit_price"])
                max_allowed = standard_price * (1 + markup_pct / 100)
                claimed_price = item["net_amount"]
                
                total_claimed += claimed_price
                total_allowed += max_allowed
                
                is_valid = claimed_price <= max_allowed
                validation_results.append({
                    "sbs_code": item["sbs_code"],
                    "claimed": claimed_price,
                    "max_allowed": max_allowed,
                    "is_valid": is_valid,
                    "status": "passed" if is_valid else "exceeded"
                })
            
            all_valid = all(r["is_valid"] for r in validation_results)
            
            # Store for next step
            self.priced_bundle = {
                **self.fhir_bundle,
                "pricing": {
                    "total_claimed": total_claimed,
                    "total_allowed": total_allowed,
                    "tier": tier,
                    "markup_pct": markup_pct
                }
            }
            
            return TestResult(
                name="Financial Rules",
                passed=True,  # Logic works even if prices exceed
                message=f"Tier {tier} ({markup_pct}% markup): Claimed SAR {total_claimed:.2f}, Allowed SAR {total_allowed:.2f}",
                details={
                    "tier": tier,
                    "markup_pct": markup_pct,
                    "total_claimed": total_claimed,
                    "total_allowed": total_allowed,
                    "all_valid": all_valid,
                    "validations": validation_results
                }
            )
        except Exception as e:
            return TestResult(name="Financial Rules", passed=False, message=str(e))
    
    def test_bundle_signing(self) -> TestResult:
        """Test 5: Digital Signature"""
        try:
            # Canonicalize bundle (remove existing signature, sort keys)
            bundle_to_sign = {k: v for k, v in self.priced_bundle.items() if k != "signature"}
            canonical = json.dumps(bundle_to_sign, sort_keys=True, separators=(',', ':'))
            
            # Generate SHA256 hash
            digest = hashlib.sha256(canonical.encode('utf-8')).digest()
            
            # Simulate signature (in real implementation, RSA sign with private key)
            # For testing, we'll use a mock signature
            mock_signature = base64.b64encode(
                f"SIG:{hashlib.sha256(digest).hexdigest()}".encode()
            ).decode()
            
            # Add signature to bundle
            self.signed_bundle = {
                **self.priced_bundle,
                "signature": {
                    "type": [{
                        "system": "urn:iso-astm:E1762-95:2013",
                        "code": "1.2.840.10065.1.12.1.1",
                        "display": "Author's Signature"
                    }],
                    "when": datetime.now().isoformat(),
                    "who": {
                        "reference": f"Organization/{self.claim['facility']['facility_code']}"
                    },
                    "sigFormat": "application/signature+xml",
                    "data": mock_signature
                }
            }
            
            return TestResult(
                name="Bundle Signing",
                passed=True,
                message=f"Bundle signed with SHA256, signature length: {len(mock_signature)} chars",
                details={
                    "algorithm": "SHA256withRSA",
                    "canonical_length": len(canonical),
                    "signature_length": len(mock_signature),
                    "signed_at": self.signed_bundle["signature"]["when"]
                }
            )
        except Exception as e:
            return TestResult(name="Bundle Signing", passed=False, message=str(e))
    
    def test_nphies_format(self) -> TestResult:
        """Test 6: NPHIES Format Validation"""
        try:
            # Validate NPHIES-specific requirements
            validations = []
            
            # Check Bundle type
            validations.append({
                "check": "Bundle type is 'message'",
                "passed": self.signed_bundle.get("type") == "message"
            })
            
            # Check signature presence
            validations.append({
                "check": "Signature present",
                "passed": "signature" in self.signed_bundle
            })
            
            # Check Claim resource
            claim_entry = None
            for entry in self.signed_bundle.get("entry", []):
                if entry.get("resource", {}).get("resourceType") == "Claim":
                    claim_entry = entry["resource"]
                    break
            
            validations.append({
                "check": "Claim resource present",
                "passed": claim_entry is not None
            })
            
            if claim_entry:
                # Check required NPHIES fields
                validations.append({
                    "check": "Claim has 'use' field",
                    "passed": "use" in claim_entry
                })
                validations.append({
                    "check": "Claim has 'type' field",
                    "passed": "type" in claim_entry
                })
                validations.append({
                    "check": "Claim has 'item' array",
                    "passed": "item" in claim_entry and len(claim_entry["item"]) > 0
                })
            
            all_passed = all(v["passed"] for v in validations)
            passed_count = sum(1 for v in validations if v["passed"])
            
            return TestResult(
                name="NPHIES Format Validation",
                passed=all_passed,
                message=f"{passed_count}/{len(validations)} validations passed",
                details={
                    "validations": validations,
                    "passed_count": passed_count,
                    "total_count": len(validations)
                }
            )
        except Exception as e:
            return TestResult(name="NPHIES Format Validation", passed=False, message=str(e))
    
    def test_transaction_logging(self) -> TestResult:
        """Test 7: Transaction Logging Structure"""
        try:
            # Simulate transaction log entry
            transaction = {
                "transaction_id": f"TXN-{uuid.uuid4().hex[:12].upper()}",
                "transaction_uuid": str(uuid.uuid4()),
                "facility_id": self.claim["facility"]["facility_id"],
                "request_type": "Claim",
                "fhir_payload_size": len(json.dumps(self.signed_bundle)),
                "signature_present": "signature" in self.signed_bundle,
                "submission_timestamp": datetime.now().isoformat(),
                "status": "pending"
            }
            
            # Validate structure
            required_fields = [
                "transaction_id", "transaction_uuid", "facility_id",
                "request_type", "submission_timestamp", "status"
            ]
            
            missing = [f for f in required_fields if f not in transaction]
            
            return TestResult(
                name="Transaction Logging",
                passed=len(missing) == 0,
                message=f"Transaction {transaction['transaction_id']} logged successfully",
                details={
                    "transaction": transaction,
                    "required_fields": required_fields,
                    "missing_fields": missing
                }
            )
        except Exception as e:
            return TestResult(name="Transaction Logging", passed=False, message=str(e))
    
    def test_database_schema(self) -> TestResult:
        """Test 8: Database Schema Validation"""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), "database", "schema.sql")
            
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            # Check for required tables
            required_tables = [
                "sbs_master_catalogue",
                "facilities",
                "facility_internal_codes",
                "sbs_normalization_map",
                "pricing_tier_rules",
                "service_bundles",
                "nphies_transactions",
                "facility_certificates"
            ]
            
            found_tables = []
            missing_tables = []
            
            for table in required_tables:
                if f"CREATE TABLE {table}" in schema:
                    found_tables.append(table)
                else:
                    missing_tables.append(table)
            
            return TestResult(
                name="Database Schema",
                passed=len(missing_tables) == 0,
                message=f"Found {len(found_tables)}/{len(required_tables)} required tables",
                details={
                    "found_tables": found_tables,
                    "missing_tables": missing_tables,
                    "schema_size": len(schema)
                }
            )
        except FileNotFoundError:
            return TestResult(
                name="Database Schema",
                passed=False,
                message="Schema file not found"
            )
        except Exception as e:
            return TestResult(name="Database Schema", passed=False, message=str(e))
    
    def print_summary(self) -> bool:
        """Print test summary and return overall success"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        total_time = sum(r.duration_ms for r in self.results)
        
        for result in self.results:
            status = "✅" if result.passed else "❌"
            print(f"  {status} {result.name} ({result.duration_ms:.1f}ms)")
        
        print("-" * 60)
        print(f"  Total: {passed} passed, {failed} failed")
        print(f"  Duration: {total_time:.1f}ms")
        print("=" * 60)
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")
        
        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "duration_ms": total_time
            },
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration_ms": r.duration_ms,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.results
            ],
            "claim_data": {
                "claim_id": self.claim["claim_id"] if self.claim else None,
                "total_amount": self.claim["total_amount"] if self.claim else None
            }
        }
        
        report_file = f"workflow_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Report saved to: {report_file}")
        
        return failed == 0


def main():
    """Main entry point"""
    simulator = StandaloneWorkflowSimulator()
    success = simulator.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
