# 🔧 Manual Fix for n8n Workflow - Financial Rules Node

## Issue
The Financial Rules node is receiving data wrapped in `{claim: {...}}` instead of the FHIR claim directly.

## Root Cause
n8n's HTTP Request node configuration is wrapping the JSON body data.

## Solution: Manual Configuration in n8n UI

### Step 1: Access n8n
Navigate to: `https://n8n.srv791040.hstgr.cloud`

### Step 2: Open the Workflow
1. Click on "Workflows" in the left sidebar
2. Find and open: "SBS Integration - Complete (v10)" or similar

### Step 3: Edit the "Financial Rules" Node
1. Click on the "Financial Rules" HTTP Request node
2. In the parameters panel, configure as follows:

**Method:** POST  
**URL:** `http://sbs-financial-rules:8002/validate`

**Send Body:** YES (toggle on)

**Body Content Type:** Select "JSON"

**Specify Body:** Select "Using Fields Below"

**Body Parameters:**
- Click "Add Parameter"
- For the value field, enter EXACTLY: `{{ $json }}`
- Do NOT enter a parameter name
- OR use "Expression" mode and paste the entire FHIR claim structure

### Alternative Fix: Use Code Node

Insert a "Code" node between "Build FHIR" and "Financial Rules":

```javascript
// Code node to ensure proper format
return items.map(item => {
  return {
    json: item.json  // This passes through the JSON without wrapping
  };
});
```

### Step 4: Save and Test

1. Click "Save" (top right)
2. Click "Execute Workflow"
3. Test with this payload:

```json
{
  "facility_id": 1,
  "service_code": "LAB-CBC-01",
  "service_desc": "Complete Blood Count",
  "patient_id": "Patient/123",
  "quantity": 1,
  "unit_price": 50.00
}
```

## Expected Result

The Financial Rules service should receive:
```json
{
  "resourceType": "Claim",
  "status": "active",
  "facility_id": 1,
  "item": [{
    "sequence": 1,
    "productOrService": {
      "coding": [{
        "system": "http://sbs.sa/coding/services",
        "code": "SBS-LAB-001",
        "display": "Complete Blood Count (CBC)"
      }]
    },
    "quantity": {"value": 1},
    "unitPrice": {"value": 50, "currency": "SAR"}
  }],
  ...
}
```

NOT wrapped in:
```json
{
  "claim": { ... }
}
```

## Verification

After the fix, check the execution log:
1. Click on the "Financial Rules" node
2. Check the "Input" tab - should show the FHIR claim directly
3. Check the "Output" tab - should show the validated claim with pricing

---

If this doesn't work, the alternative is to modify the Financial Rules service to accept `{claim: {...}}` format, but that's not recommended as it breaks the API contract.
