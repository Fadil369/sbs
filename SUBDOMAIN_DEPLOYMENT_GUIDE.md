# 🚀 SBS Subdomain Deployment Guide

**New Domain**: sbs.brainsait.cloud  
**Status**: ✅ Backend configured and running  
**Remaining**: DNS configuration + n8n workflow

---

## ✅ COMPLETED

- [x] Docker Compose updated to sbs.brainsait.cloud
- [x] Service restarted and healthy
- [x] Backend API running on port 3000
- [x] Connected to Traefik for SSL

---

## 📋 STEP 1: Add DNS Record (2 minutes)

### Go to Hostinger DNS Panel

1. Login: https://hpanel.hostinger.com
2. Navigate: Domains → brainsait.cloud → DNS

### Add Subdomain A Record

```
Type: A
Name: sbs
Points to: 82.25.101.65
TTL: 300 (or 14400)
```

**Save the record**

### Verification

After 2-5 minutes:
```bash
host sbs.brainsait.cloud
# Should show: sbs.brainsait.cloud has address 82.25.101.65
```

---

## 📋 STEP 2: Wait for SSL Certificate (2-3 minutes)

### What Happens Automatically

Once DNS propagates:
1. Traefik detects the subdomain
2. Requests Let's Encrypt SSL certificate
3. Certificate is issued and installed
4. HTTPS becomes available

### Monitor SSL Generation

```bash
# Watch Traefik logs
docker logs n8n-traefik-1 -f | grep -i "sbs.brainsait.cloud\|certificate"

# You'll see messages like:
# "Serving default certificate for request: sbs.brainsait.cloud"
# Then: "The ACME certificate has been successfully obtained"
```

### Test Access After SSL

```bash
# Test HTTP → HTTPS redirect
curl -I http://sbs.brainsait.cloud
# Expected: 301 → https://

# Test HTTPS access
curl -I https://sbs.brainsait.cloud
# Expected: HTTP/2 200

# Test health endpoint
curl https://sbs.brainsait.cloud/health
# Expected: {"status":"healthy",...}
```

---

## 📋 STEP 3: Import n8n Workflow (10 minutes)

### 3.1 Download Workflow File to Your Computer

From your server:
```bash
# If you have SCP/SFTP access, download:
# /root/sbs-landing/n8n-workflow-sbs-complete.json

# Or copy the content:
cat /root/sbs-landing/n8n-workflow-sbs-complete.json
```

Copy this file to your local computer.

### 3.2 Access n8n Dashboard

Open in browser:
```
https://n8n.srv791040.hstgr.cloud
```

Login with your n8n credentials.

### 3.3 Import Workflow

1. Click **"Workflows"** in left sidebar
2. Click **"+ Add Workflow"** button (top right)
3. In the workflow editor, click **three dots menu** (⋮) next to workflow name
4. Select **"Import from File"**
5. Upload: `n8n-workflow-sbs-complete.json`
6. Workflow should load with all nodes visible

### 3.4 Verify Workflow Nodes

You should see these nodes:
```
1. Webhook - Claim Submission
2. Validate Input (Function)
3. 1. Normalizer Service (HTTP Request)
4. 2. Financial Rules Engine (HTTP Request)
5. 3. Digital Signer (HTTP Request)
6. 4. NPHIES Submission (HTTP Request)
7. Format Success Response (Function)
8. Respond to Webhook
9. Handle Error (Function)
10. Check for Errors (IF)
```

All nodes should be connected in sequence.

### 3.5 Save and Activate

1. Click **"Save"** button (top right)
2. Toggle switch next to "Active" to **ON** (should turn green)
3. Status should show: **"Active"**

### 3.6 Get Webhook URL

1. Click on the **"Webhook - Claim Submission"** node (first node)
2. In the right panel, look for **"Production URL"**
3. Copy the full URL, example:
   ```
   https://n8n.srv791040.hstgr.cloud/webhook/sbs-claim-submission
   ```
4. **Keep this URL** - you'll need it in the next step

---

## 📋 STEP 4: Update Backend Webhook URL (2 minutes)

### 4.1 Edit Environment File

SSH to your server:
```bash
cd /root/sbs-landing
nano .env
```

### 4.2 Update Webhook URL

Find this line:
```env
N8N_WEBHOOK_URL=https://n8n.srv791040.hstgr.cloud/webhook/sbs-claim-submission
```

Make sure it matches your actual webhook URL from Step 3.6.

If it's different, update it. If it's already correct, you're good!

### 4.3 Save and Restart

```bash
# Save: Ctrl+X, then Y, then Enter

# Restart backend to apply changes
docker compose restart

# Wait 10 seconds
sleep 10

# Verify it's running
docker ps --filter "name=sbs-landing"
```

---

## 📋 STEP 5: Test Complete System (5 minutes)

### 5.1 Test Landing Page

```bash
# Test HTTPS access
curl -I https://sbs.brainsait.cloud

# Test health endpoint
curl https://sbs.brainsait.cloud/health

# Expected:
# {
#   "status": "healthy",
#   "timestamp": "...",
#   "uptime": ...,
#   "services": {...}
# }
```

### 5.2 Test Services Status

```bash
curl https://sbs.brainsait.cloud/api/services/status | jq

# Expected: All services showing "healthy"
```

### 5.3 Submit Test Claim via API

```bash
curl -X POST https://sbs.brainsait.cloud/api/submit-claim \
  -F "patientName=Ahmed Hassan" \
  -F "patientId=1234567890" \
  -F "memberId=MEM123456" \
  -F "claimType=professional" \
  -F "userEmail=test@example.com"

# Expected:
# {
#   "success": true,
#   "message": "Claim submitted successfully",
#   "claimId": "CLM-1737013200000",
#   "workflowExecutionId": "..."
# }
```

### 5.4 Test in Web Browser

1. Open: https://sbs.brainsait.cloud
2. You should see the bilingual SBS landing page
3. Try changing language (EN/AR toggle)
4. Fill out the claim submission form:
   - Patient Name: Test Patient
   - Patient ID: 1234567890
   - Member ID: MEM123
   - Claim Type: Professional
   - Email: test@example.com
5. Click **"Submit Claim"**
6. Should see success message

### 5.5 Verify in n8n Dashboard

1. Open: https://n8n.srv791040.hstgr.cloud
2. Click **"Executions"** in left sidebar
3. You should see your workflow execution (most recent at top)
4. Click on it to see execution details
5. All nodes should have green checkmarks ✅
6. Click on each node to see input/output data

### 5.6 Check Service Logs (Optional)

```bash
# Landing page logs
docker logs sbs-landing --tail 50

# SBS services logs
docker logs sbs-normalizer --tail 20
docker logs sbs-financial-rules --tail 20
docker logs sbs-signer --tail 20
docker logs sbs-nphies-bridge --tail 20
```

---

## 🎉 SUCCESS CRITERIA

All of these should work:

- [ ] DNS: `host sbs.brainsait.cloud` shows 82.25.101.65
- [ ] SSL: `curl -I https://sbs.brainsait.cloud` returns HTTP/2 200
- [ ] Health: `curl https://sbs.brainsait.cloud/health` returns healthy
- [ ] Landing page loads in browser
- [ ] Claim submission form works
- [ ] n8n workflow execution appears in dashboard
- [ ] All 4 SBS services were called
- [ ] No errors in logs

---

## 📊 System Architecture

```
User Browser
    ↓
https://sbs.brainsait.cloud (SSL via Traefik)
    ↓
Landing Page (sbs-landing:3000)
    ↓
n8n Workflow (webhook)
    ↓
┌──────────────────────────────┐
│  SBS Microservices Pipeline  │
│  1. Normalizer (8000)        │
│  2. Financial Rules (8002)   │
│  3. Signer (8001)            │
│  4. NPHIES Bridge (8003)     │
└──────────────────────────────┘
    ↓
NPHIES (Saudi Health Platform)
```

---

## 🔧 Troubleshooting

### DNS Not Propagating

```bash
# Check if record exists
dig sbs.brainsait.cloud +short

# Try different DNS servers
nslookup sbs.brainsait.cloud 8.8.8.8

# Clear local DNS cache (on your computer)
# Windows: ipconfig /flushdns
# Mac: sudo dscacheutil -flushcache
# Linux: sudo systemd-resolve --flush-caches
```

### SSL Certificate Not Generated

```bash
# Check Traefik logs for errors
docker logs n8n-traefik-1 2>&1 | grep -i "sbs.brainsait.cloud" | tail -20

# Common issues:
# - DNS not propagated yet (wait 5 more minutes)
# - Port 80/443 blocked (check firewall)
# - Rate limit reached (try again in 1 hour)
```

### n8n Webhook Not Triggering

```bash
# Check if workflow is active
# In n8n dashboard, verify toggle is green

# Check backend .env has correct webhook URL
cat /root/sbs-landing/.env | grep N8N_WEBHOOK_URL

# Test webhook directly
curl -X POST https://n8n.srv791040.hstgr.cloud/webhook/sbs-claim-submission \
  -H "Content-Type: application/json" \
  -d '{"body":{"patientName":"Test"}}'
```

### Service Timeout

```bash
# Check all services are healthy
docker ps --filter "name=sbs-" --format "table {{.Names}}\t{{.Status}}"

# Restart unhealthy services
docker restart sbs-normalizer sbs-signer sbs-financial-rules sbs-nphies-bridge

# Check service health directly
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

---

## 📚 Important URLs

After deployment:

```
Landing Page:    https://sbs.brainsait.cloud
Health Check:    https://sbs.brainsait.cloud/health
API Endpoint:    https://sbs.brainsait.cloud/api/submit-claim
Services Status: https://sbs.brainsait.cloud/api/services/status
n8n Dashboard:   https://n8n.srv791040.hstgr.cloud
Documentation:   https://brainsait369.blogspot.com/
```

---

## 📞 Quick Commands

```bash
# Check all services
docker ps --filter "name=sbs-"

# Restart landing page
cd /root/sbs-landing && docker compose restart

# View logs
docker logs sbs-landing -f

# Check DNS
host sbs.brainsait.cloud

# Test API
curl https://sbs.brainsait.cloud/health
```

---

## 🎯 Timeline

- **Step 1**: Add DNS record (2 min)
- **Wait**: DNS propagation (2-5 min)
- **Wait**: SSL generation (2-3 min)
- **Step 2**: Import n8n workflow (10 min)
- **Step 3**: Update webhook URL (2 min)
- **Step 4**: Test everything (5 min)

**Total**: ~20-25 minutes

---

**Status**: Configuration complete, waiting for DNS  
**Next**: Add sbs A record to DNS  
**Generated**: January 16, 2026

**Powered by BrainSAIT برينسايت**  
**Author**: Dr. Mohamed El Fadil

