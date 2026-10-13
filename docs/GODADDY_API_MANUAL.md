# GoDaddy API Integration & Management Manual

This manual provides complete documentation for managing domains, DNS records, and hosting services using the **GoDaddy REST API** and **Personal Access Tokens (PAT)**.

---

## 1. Overview & Credentials

GoDaddy uses Personal Access Tokens (PAT) for modern API authentication.

### Token Format
- **Format:** `gd_pat_<string>`
- **Token Type:** Personal Access Token (Bearer Authentication)
- **Primary Domain:** `sciencesgates.com` (along with `ijcmit.com`, `marciledu.com`)

### Environment Variables
The credentials are stored in `.env` (and configured in `.env.example` as a template):

```ini
# GODADDY API CONFIGURATION
GODADDY_API_TOKEN=gd_pat_uhVN7P4l3G2PqV6T7fSYxUcwjpSY205RN8e7yB0ghHx_93c25b61
GODADDY_API_URL=https://api.godaddy.com
```

> **Security Note:** Never commit `.env` or raw PAT tokens into public version control. Ensure `.env` remains in `.gitignore`.

---

## 2. API Endpoints & Environments

| Environment | Base URL | Usage |
|---|---|---|
| **Production** | `https://api.godaddy.com` | Live domains and active DNS records |
| **OTE (Test)** | `https://api.ote-godaddy.com` | Sandbox testing with test domains |

### Authentication Header
All REST requests require the `Authorization` header with the Bearer scheme:

```http
Authorization: Bearer gd_pat_uhVN7P4l3G2PqV6T7fSYxUcwjpSY205RN8e7yB0ghHx_93c25b61
Accept: application/json
Content-Type: application/json
```

---

## 3. CLI Helper Tool (`scripts/godaddy_client.py`)

A pre-configured Python utility is available in the repository at [scripts/godaddy_client.py](file:///c:/Users/UTD/Desktop/Sciences%20Gates/scripts/godaddy_client.py). It reads the token automatically from `.env`.

### Commands

#### A. List All Domains
List all domains in the account along with expiration dates and status:
```bash
python scripts/godaddy_client.py list-domains
```

#### B. View Detailed Domain Information
```bash
python scripts/godaddy_client.py domain-info sciencesgates.com
```

#### C. List DNS Records
View all DNS records for a domain:
```bash
python scripts/godaddy_client.py list-dns sciencesgates.com
```

Filter DNS records by record type (e.g. `A`, `CNAME`, `TXT`, `MX`):
```bash
python scripts/godaddy_client.py list-dns sciencesgates.com --type A
```

Filter by record type and sub-record name:
```bash
python scripts/godaddy_client.py list-dns sciencesgates.com --type A --name www
```

#### D. Update or Set a DNS Record
Update the root `@` A record or a subdomain:
```bash
# Update @ A record:
python scripts/godaddy_client.py set-dns sciencesgates.com A @ 160.153.0.203 --ttl 3600

# Update www A record:
python scripts/godaddy_client.py set-dns sciencesgates.com A www 160.153.0.203 --ttl 3600
```

---

## 4. Direct REST API Reference & cURL Examples

### 1. List Registered Domains
```bash
curl -X GET "https://api.godaddy.com/v1/domains" \
  -H "Authorization: Bearer $GODADDY_API_TOKEN" \
  -H "Accept: application/json"
```

### 2. Fetch DNS Records for Domain
```bash
curl -X GET "https://api.godaddy.com/v1/domains/sciencesgates.com/records" \
  -H "Authorization: Bearer $GODADDY_API_TOKEN" \
  -H "Accept: application/json"
```

### 3. Replace Specific Record (`PUT`)
```bash
curl -X PUT "https://api.godaddy.com/v1/domains/sciencesgates.com/records/A/@" \
  -H "Authorization: Bearer $GODADDY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "data": "160.153.0.203",
      "ttl": 3600
    }
  ]'
```

### 4. Append New DNS Records (`PATCH`)
Add verification TXT records or subdomains without overwriting existing entries:
```bash
curl -X PATCH "https://api.godaddy.com/v1/domains/sciencesgates.com/records" \
  -H "Authorization: Bearer $GODADDY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "type": "TXT",
      "name": "_custom-verify",
      "data": "verification-token-value",
      "ttl": 3600
    }
  ]'
```

---

## 5. Python Integration Example

You can import and use the GoDaddy client directly within any Python workflow or management command:

```python
from scripts.godaddy_client import GoDaddyClient

client = GoDaddyClient()

# List domains
domains = client.list_domains()
for item in domains:
    print(f"Domain: {item['domain']}, Status: {item['status']}")

# Check DNS A records
a_records = client.get_records("sciencesgates.com", record_type="A")
print("A Records:", a_records)

# Update a record
client.set_record(
    domain="sciencesgates.com",
    record_type="A",
    name="subdomain",
    value="208.109.79.3",
    ttl=3600,
)
```

---

## 6. Hosting & DNS Architecture Reference

| Record Name | Type | Target / Value | Purpose |
|---|---|---|---|
| `@` | `A` | `160.153.0.203` | Main Website (`sciencesgates.com`) |
| `www` | `A` | `160.153.0.203` | WWW Redirect / Caching |
| `_websec` | `A` | `208.109.79.3` | SSH / cPanel Server Endpoint |
| `ns15.domaincontrol.com` | `NS` | - | Primary GoDaddy Nameserver |
| `ns16.domaincontrol.com` | `NS` | - | Secondary GoDaddy Nameserver |

---

## 7. Troubleshooting & Error Codes

| Status Code | Reason | Resolution |
|---|---|---|
| `401 Unauthorized` | Invalid or expired token | Check `GODADDY_API_TOKEN` in `.env` and verify format starts with `gd_pat_` |
| `403 Forbidden` | Insufficient permissions / scope | Regenerate PAT from GoDaddy Developer Portal with `Domains` read/write permissions |
| `404 Not Found` | Domain or record does not exist | Verify domain name spelling and existing record names |
| `422 Unprocessable Entity` | Invalid record data or syntax | Verify valid IP address format for `A` records or valid host for `CNAME` |
