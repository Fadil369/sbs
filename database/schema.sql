-- ============================================================================
-- Saudi Billing System (SBS) Integration Engine - Database Schema
-- Version: 1.0
-- Description: Complete database schema for SBS integration platform
-- ============================================================================

-- ============================================================================
-- 1. SBS Master Catalogue (Official CHI Reference)
-- ============================================================================

CREATE TABLE sbs_master_catalogue (
    sbs_id VARCHAR(50) PRIMARY KEY,
    description_ar TEXT NOT NULL,
    description_en TEXT NOT NULL,
    version VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('Lab', 'Radiology', 'Surgery', 'Consultation', 'Pharmacy', 'Procedure', 'Emergency', 'ICU', 'Dental', 'Maternity')),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    unit_type VARCHAR(20),
    standard_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster category lookups
CREATE INDEX idx_sbs_category ON sbs_master_catalogue(category);
CREATE INDEX idx_sbs_active ON sbs_master_catalogue(is_active, effective_date);

-- ============================================================================
-- 2. Facilities (Multi-Tenancy Support)
-- ============================================================================

CREATE TABLE facilities (
    facility_id SERIAL PRIMARY KEY,
    facility_code VARCHAR(50) UNIQUE NOT NULL,
    facility_name VARCHAR(255) NOT NULL,
    facility_name_ar VARCHAR(255),
    chi_license_number VARCHAR(100) UNIQUE NOT NULL,
    accreditation_tier INT CHECK (accreditation_tier BETWEEN 1 AND 8),
    region VARCHAR(50),
    city VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    nphies_payer_id VARCHAR(100),
    certificate_serial_number VARCHAR(255),
    certificate_expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_facility_active ON facilities(is_active);

-- ============================================================================
-- 3. Facility Internal Codes (Hospital-Specific Codes)
-- ============================================================================

CREATE TABLE facility_internal_codes (
    internal_code_id SERIAL PRIMARY KEY,
    internal_code VARCHAR(100) NOT NULL,
    facility_id INT NOT NULL REFERENCES facilities(facility_id) ON DELETE CASCADE,
    local_description TEXT NOT NULL,
    local_description_ar TEXT,
    price_gross DECIMAL(10,2),
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(facility_id, internal_code)
);

CREATE INDEX idx_internal_code_lookup ON facility_internal_codes(facility_id, internal_code, is_active);

-- ============================================================================
-- 4. SBS Normalization Map (Core Mapping Engine)
-- ============================================================================

CREATE TABLE sbs_normalization_map (
    map_id BIGSERIAL PRIMARY KEY,
    internal_code_id INT NOT NULL REFERENCES facility_internal_codes(internal_code_id) ON DELETE CASCADE,
    sbs_code VARCHAR(50) NOT NULL REFERENCES sbs_master_catalogue(sbs_id),
    confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
    mapping_source VARCHAR(20) CHECK (mapping_source IN ('manual', 'ai', 'rule_based')),
    is_active BOOLEAN DEFAULT TRUE,
    validated_by VARCHAR(100),
    validation_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(internal_code_id, sbs_code)
);

CREATE INDEX idx_normalization_active ON sbs_normalization_map(internal_code_id, is_active);
CREATE INDEX idx_normalization_confidence ON sbs_normalization_map(confidence DESC);

-- ============================================================================
-- 5. Pricing Tier Rules (Financial Compliance)
-- ============================================================================

CREATE TABLE pricing_tier_rules (
    tier_level INT PRIMARY KEY CHECK (tier_level BETWEEN 1 AND 8),
    tier_description VARCHAR(255) NOT NULL,
    tier_description_ar VARCHAR(255),
    markup_pct FLOAT NOT NULL CHECK (markup_pct >= 0 AND markup_pct <= 100),
    base_coverage_limit DECIMAL(12,2),
    annual_coverage_limit DECIMAL(12,2),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO pricing_tier_rules (tier_level, tier_description, tier_description_ar, markup_pct, effective_date) VALUES
(1, 'Reference Hospital', 'مستشفى مرجعي', 10.0, '2024-01-01'),
(2, 'Tertiary Care Center', 'مركز رعاية ثالثي', 20.0, '2024-01-01'),
(3, 'Specialized Hospital', 'مستشفى متخصص', 30.0, '2024-01-01'),
(4, 'General Hospital (JCI)', 'مستشفى عام (JCI)', 40.0, '2024-01-01'),
(5, 'General Hospital (CBAHI)', 'مستشفى عام (CBAHI)', 50.0, '2024-01-01'),
(6, 'Private Clinic (Level A)', 'عيادة خاصة (مستوى أ)', 60.0, '2024-01-01'),
(7, 'Private Clinic (Level B)', 'عيادة خاصة (مستوى ب)', 70.0, '2024-01-01'),
(8, 'Primary Care Center', 'مركز رعاية أولية', 75.0, '2024-01-01');

-- ============================================================================
-- 6. Service Bundles (CHI Bundle Rules)
-- ============================================================================

CREATE TABLE service_bundles (
    bundle_id SERIAL PRIMARY KEY,
    bundle_code VARCHAR(50) UNIQUE NOT NULL,
    bundle_name VARCHAR(255) NOT NULL,
    bundle_name_ar VARCHAR(255),
    bundle_description TEXT,
    total_allowed_price DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bundle_items (
    bundle_item_id SERIAL PRIMARY KEY,
    bundle_id INT NOT NULL REFERENCES service_bundles(bundle_id) ON DELETE CASCADE,
    sbs_code VARCHAR(50) NOT NULL REFERENCES sbs_master_catalogue(sbs_id),
    quantity INT DEFAULT 1,
    is_mandatory BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bundle_id, sbs_code)
);

-- ============================================================================
-- 7. NPHIES Transaction Log (Audit Trail)
-- ============================================================================

CREATE TABLE nphies_transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(facility_id),
    transaction_uuid UUID DEFAULT gen_random_uuid(),
    request_type VARCHAR(50) NOT NULL CHECK (request_type IN ('Claim', 'PreAuth', 'Eligibility', 'ClaimResponse')),
    fhir_payload JSONB NOT NULL,
    signature TEXT NOT NULL,
    nphies_transaction_id VARCHAR(255),
    http_status_code INT,
    response_payload JSONB,
    submission_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_timestamp TIMESTAMP,
    status VARCHAR(50) CHECK (status IN ('pending', 'submitted', 'accepted', 'rejected', 'error')),
    error_message TEXT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transaction_facility ON nphies_transactions(facility_id, submission_timestamp DESC);
CREATE INDEX idx_transaction_status ON nphies_transactions(status, submission_timestamp DESC);
CREATE INDEX idx_transaction_uuid ON nphies_transactions(transaction_uuid);

-- ============================================================================
-- 8. AI Normalization Cache (Performance Optimization)
-- ============================================================================

CREATE TABLE ai_normalization_cache (
    cache_id BIGSERIAL PRIMARY KEY,
    description_hash VARCHAR(64) UNIQUE NOT NULL,
    original_description TEXT NOT NULL,
    suggested_sbs_code VARCHAR(50) REFERENCES sbs_master_catalogue(sbs_id),
    confidence_score FLOAT,
    hit_count INT DEFAULT 1,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cache_hash ON ai_normalization_cache(description_hash);
CREATE INDEX idx_cache_hits ON ai_normalization_cache(hit_count DESC);

-- ============================================================================
-- 9. Certificate Management
-- ============================================================================

CREATE TABLE facility_certificates (
    cert_id SERIAL PRIMARY KEY,
    facility_id INT NOT NULL REFERENCES facilities(facility_id) ON DELETE CASCADE,
    cert_type VARCHAR(20) CHECK (cert_type IN ('mtls', 'signing', 'both')),
    serial_number VARCHAR(255) NOT NULL,
    issuer VARCHAR(255),
    subject VARCHAR(255),
    valid_from DATE NOT NULL,
    valid_until DATE NOT NULL,
    thumbprint VARCHAR(255),
    private_key_path VARCHAR(500),
    public_cert_path VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(facility_id, cert_type, serial_number)
);

CREATE INDEX idx_cert_expiry ON facility_certificates(valid_until, is_active);

-- ============================================================================
-- 10. System Audit Log
-- ============================================================================

CREATE TABLE system_audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INT,
    user_id VARCHAR(100),
    facility_id INT REFERENCES facilities(facility_id),
    event_description TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_timestamp ON system_audit_log(created_at DESC);
CREATE INDEX idx_audit_entity ON system_audit_log(entity_type, entity_id);

-- ============================================================================
-- Triggers for updated_at timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sbs_master_modtime BEFORE UPDATE ON sbs_master_catalogue FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_facilities_modtime BEFORE UPDATE ON facilities FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_internal_codes_modtime BEFORE UPDATE ON facility_internal_codes FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_normalization_map_modtime BEFORE UPDATE ON sbs_normalization_map FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- ============================================================================
-- Sample Data for Testing
-- ============================================================================

-- Sample SBS Codes
INSERT INTO sbs_master_catalogue (sbs_id, description_ar, description_en, version, category, effective_date, standard_price) VALUES
('SBS-LAB-001', 'تحليل صورة دم كاملة', 'Complete Blood Count (CBC)', 'V3.0', 'Lab', '2024-01-01', 50.00),
('SBS-RAD-001', 'أشعة سينية للصدر', 'Chest X-Ray', 'V3.0', 'Radiology', '2024-01-01', 150.00),
('SBS-CONS-001', 'استشارة طبية عامة', 'General Medical Consultation', 'V3.0', 'Consultation', '2024-01-01', 200.00),
('SBS-SURG-001', 'عملية استئصال الزائدة الدودية', 'Appendectomy', 'V3.0', 'Surgery', '2024-01-01', 5000.00);

-- Sample Facility
INSERT INTO facilities (facility_code, facility_name, facility_name_ar, chi_license_number, accreditation_tier, region, city) VALUES
('FAC-001', 'King Fahad Medical City', 'مدينة الملك فهد الطبية', 'CHI-RYD-001', 1, 'Riyadh', 'Riyadh');

-- Sample Internal Codes
INSERT INTO facility_internal_codes (internal_code, facility_id, local_description, price_gross) VALUES
('LAB-CBC-01', 1, 'CBC - Complete Blood Count Test', 60.00),
('RAD-CXR-01', 1, 'Chest X-Ray Standard', 180.00),
('CONS-GEN-01', 1, 'General Consultation - First Visit', 250.00);

-- Sample Normalization Mappings
INSERT INTO sbs_normalization_map (internal_code_id, sbs_code, confidence, mapping_source, is_active) VALUES
(1, 'SBS-LAB-001', 1.0, 'manual', TRUE),
(2, 'SBS-RAD-001', 1.0, 'manual', TRUE),
(3, 'SBS-CONS-001', 1.0, 'manual', TRUE);

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

CREATE VIEW v_active_mappings AS
SELECT 
    fic.facility_id,
    f.facility_name,
    fic.internal_code,
    fic.local_description,
    snm.sbs_code,
    smc.description_en as sbs_description,
    snm.confidence,
    snm.mapping_source
FROM sbs_normalization_map snm
JOIN facility_internal_codes fic ON snm.internal_code_id = fic.internal_code_id
JOIN facilities f ON fic.facility_id = f.facility_id
JOIN sbs_master_catalogue smc ON snm.sbs_code = smc.sbs_id
WHERE snm.is_active = TRUE 
  AND fic.is_active = TRUE 
  AND f.is_active = TRUE;

CREATE VIEW v_recent_transactions AS
SELECT 
    nt.transaction_id,
    nt.transaction_uuid,
    f.facility_name,
    nt.request_type,
    nt.status,
    nt.submission_timestamp,
    nt.response_timestamp,
    nt.nphies_transaction_id,
    nt.http_status_code
FROM nphies_transactions nt
JOIN facilities f ON nt.facility_id = f.facility_id
ORDER BY nt.submission_timestamp DESC;

-- ============================================================================
-- End of Schema
-- ============================================================================
