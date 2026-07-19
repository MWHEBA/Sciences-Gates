#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests

def load_env():
    """Loads environment variables from .env file manually to avoid dependency issues."""
    # Find .env in current directory or parent directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    env_paths = [
        os.path.join(project_dir, '.env'),
        os.path.join(script_dir, '.env'),
        '.env'
    ]
    
    env_vars = {}
    for path in env_paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, val = line.split('=', 1)
                        # Remove quotes if present
                        val = val.strip().strip('"').strip("'")
                        env_vars[key.strip()] = val
            break
            
    # Fallback to system environment variables
    for key in ['CLOUDFLARE_EMAIL', 'CLOUDFLARE_API_KEY', 'CLOUDFLARE_ZONE_ID', 'CLOUDFLARE_ACCOUNT_ID']:
        if key not in env_vars and key in os.environ:
            env_vars[key] = os.environ[key]
            
    return env_vars

def get_headers(env):
    """Returns headers for Cloudflare API. Supports both Global API Key and API Token formats."""
    email = env.get('CLOUDFLARE_EMAIL')
    api_key = env.get('CLOUDFLARE_API_KEY')
    
    if not api_key:
        print("Error: CLOUDFLARE_API_KEY is not defined in .env or environment.", file=sys.stderr)
        sys.exit(1)
        
    headers = {"Content-Type": "application/json"}
    
    # Check if the API key is a token (typically starts with cfk_ or does not fit Global API key format)
    # Global API Key is traditionally 37 hex characters, but token is longer or differently formatted.
    # We will try Bearer authentication if requested or if it looks like a token,
    # but we can try Global API Key auth first since they explicitly called it "Global API".
    # Let's support trying both by testing with a fast request or default to Global API Key if email is present.
    if email and not api_key.startswith('Bearer '):
        headers["X-Auth-Email"] = email
        headers["X-Auth-Key"] = api_key
    else:
        # Fallback/alternative: Use as Bearer Token
        token = api_key.replace('Bearer ', '')
        headers["Authorization"] = f"Bearer {token}"
        
    return headers

def make_request(method, url, headers, data=None):
    """Executes HTTP request to Cloudflare API and handles response."""
    try:
        if method.upper() == 'GET':
            resp = requests.get(url, headers=headers, timeout=15)
        elif method.upper() == 'POST':
            resp = requests.post(url, headers=headers, json=data, timeout=15)
        elif method.upper() == 'PATCH':
            resp = requests.patch(url, headers=headers, json=data, timeout=15)
        elif method.upper() == 'PUT':
            resp = requests.put(url, headers=headers, json=data, timeout=15)
        elif method.upper() == 'DELETE':
            resp = requests.delete(url, headers=headers, json=data, timeout=15)
        else:
            print(f"Error: Unsupported HTTP method: {method}", file=sys.stderr)
            sys.exit(1)
            
        # If we got authentication error and we didn't try the other method, let's try fallback
        if resp.status_code == 403 and 'X-Auth-Key' in headers:
            # Try switching to Bearer Token
            fallback_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {headers['X-Auth-Key']}"
            }
            if method.upper() == 'GET':
                resp = requests.get(url, headers=fallback_headers, timeout=15)
            elif method.upper() == 'POST':
                resp = requests.post(url, headers=fallback_headers, json=data, timeout=15)
            elif method.upper() == 'PATCH':
                resp = requests.patch(url, headers=fallback_headers, json=data, timeout=15)
            elif method.upper() == 'PUT':
                resp = requests.put(url, headers=fallback_headers, json=data, timeout=15)
            elif method.upper() == 'DELETE':
                resp = requests.delete(url, headers=fallback_headers, json=data, timeout=15)
                
        return resp.json()
    except Exception as e:
        print(f"HTTP Request failed: {e}", file=sys.stderr)
        return {"success": False, "errors": [{"message": str(e)}]}

def check_status(env, headers):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    if not zone_id:
        print("Error: CLOUDFLARE_ZONE_ID is not defined in .env", file=sys.stderr)
        sys.exit(1)
        
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
    res = make_request('GET', url, headers)
    if res.get('success'):
        zone_info = res.get('result', {})
        print(json.dumps({
            "status": "Connected Successfully",
            "domain": zone_info.get('name'),
            "status_in_cloudflare": zone_info.get('status'),
            "original_name_servers": zone_info.get('original_name_servers'),
            "name_servers": zone_info.get('name_servers'),
            "development_mode": zone_info.get('development_mode')
        }, indent=2, ensure_ascii=False))
    else:
        print("Error connecting to Cloudflare API:", file=sys.stderr)
        print(json.dumps(res, indent=2), file=sys.stderr)
        sys.exit(1)

def list_dns(env, headers):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?per_page=100"
    res = make_request('GET', url, headers)
    if res.get('success'):
        records = []
        for r in res.get('result', []):
            records.append({
                "id": r.get('id'),
                "type": r.get('type'),
                "name": r.get('name'),
                "content": r.get('content'),
                "proxied": r.get('proxied'),
                "ttl": r.get('ttl')
            })
        print(json.dumps(records, indent=2))
    else:
        print("Error fetching DNS records:", file=sys.stderr)
        print(json.dumps(res, indent=2), file=sys.stderr)

def set_dns(env, headers, name, record_type, value, proxied=True, ttl=1):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    
    # First, check if record already exists
    list_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={name}&type={record_type}"
    check_res = make_request('GET', list_url, headers)
    
    data = {
        "type": record_type,
        "name": name,
        "content": value,
        "ttl": ttl,
        "proxied": proxied
    }
    
    existing = check_res.get('result', []) if check_res.get('success') else []
    
    # For A and CNAME, we overwrite the first match (usually unique)
    # For TXT, MX, SRV, etc., we only overwrite if content matches (i.e. update TTL or proxied status of that exact record),
    # otherwise we create a new one to allow multiple records of the same type (like multiple verification records).
    target_record = None
    if record_type.upper() in ['A', 'CNAME']:
        if existing:
            target_record = existing[0]
    else:
        for r in existing:
            # Strip quotes for TXT content comparison to avoid double-quoting mismatch
            existing_content = r.get('content', '').strip('"').strip("'")
            new_content = value.strip('"').strip("'")
            if existing_content == new_content:
                target_record = r
                break
                
    if target_record:
        record_id = target_record['id']
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
        res = make_request('PUT', url, headers, data)
        action = "Updated"
    else:
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        res = make_request('POST', url, headers, data)
        action = "Created"
        
    print(json.dumps(res, indent=2))


def delete_dns(env, headers, record_id):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    res = make_request('DELETE', url, headers)
    print(json.dumps(res, indent=2))

def get_settings(env, headers):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/settings"
    res = make_request('GET', url, headers)
    if res.get('success'):
        settings = {}
        for s in res.get('result', []):
            settings[s.get('id')] = s.get('value')
        print(json.dumps(settings, indent=2))
    else:
        print("Error fetching settings:", file=sys.stderr)
        print(json.dumps(res, indent=2), file=sys.stderr)

def set_setting(env, headers, setting_name, value):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/{setting_name}"
    
    # Try parsing value as JSON if it looks like JSON
    if isinstance(value, str):
        try:
            if value.startswith('{') or value.startswith('['):
                value = json.loads(value)
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.lower() == 'on':
                value = 'on'
            elif value.lower() == 'off':
                value = 'off'
            elif value.isdigit():
                value = int(value)
        except Exception:
            pass
            
    data = {"value": value}
    res = make_request('PATCH', url, headers, data)
    print(json.dumps(res, indent=2))

def list_rules(env, headers):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    
    # Page Rules
    page_rules_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules"
    page_rules_res = make_request('GET', page_rules_url, headers)
    
    # Cache Rules (Rulesets)
    # Cloudflare's Cache Rules are part of Rulesets. Let's query them.
    rulesets_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets"
    rulesets_res = make_request('GET', rulesets_url, headers)
    
    output = {
        "page_rules": page_rules_res.get('result', []) if page_rules_res.get('success') else [],
        "rulesets": rulesets_res.get('result', []) if rulesets_res.get('success') else []
    }
    print(json.dumps(output, indent=2))

def add_page_rule(env, headers, target_url, actions_json):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules"
    
    actions = json.loads(actions_json)
    data = {
        "targets": [
            {
                "target": "url",
                "constraint": {
                    "operator": "matches",
                    "value": target_url
                }
            }
        ],
        "actions": actions,
        "status": "active"
    }
    res = make_request('POST', url, headers, data)
    print(json.dumps(res, indent=2))

def delete_page_rule(env, headers, rule_id):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules/{rule_id}"
    res = make_request('DELETE', url, headers)
    print(json.dumps(res, indent=2))

def create_cache_rule(env, headers, name, expression, bypass=True):
    """Creates a Cache Rule (Ruleset API) to bypass or cache specific paths."""
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    
    # First, find the entry_point ruleset for cache_rules
    rulesets_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets"
    res = make_request('GET', rulesets_url, headers)
    
    phase_ruleset_id = None
    if res.get('success'):
        for rs in res.get('result', []):
            if rs.get('phase') == 'http_request_cache_control':
                phase_ruleset_id = rs.get('id')
                break
                
    if not phase_ruleset_id:
        # Create a new ruleset for http_request_cache_control phase if it doesn't exist
        create_rs_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets"
        rs_data = {
            "name": "default",
            "phase": "http_request_cache_control",
            "kind": "zone",
            "rules": []
        }
        res_new = make_request('POST', create_rs_url, headers, rs_data)
        if res_new.get('success'):
            phase_ruleset_id = res_new.get('result', {}).get('id')
        else:
            print("Error creating http_request_cache_control ruleset:", file=sys.stderr)
            print(json.dumps(res_new, indent=2), file=sys.stderr)
            sys.exit(1)
            
    # Now get the existing rules in this ruleset
    get_rs_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets/{phase_ruleset_id}"
    rs_details = make_request('GET', get_rs_url, headers)
    
    rules = rs_details.get('result', {}).get('rules', []) if rs_details.get('success') else []
    
    # Build the new rule
    new_rule = {
        "action": "set_cache_settings",
        "action_parameters": {
            "cache": not bypass
        },
        "expression": expression,
        "description": name,
        "enabled": True
    }
    
    # Append or insert rule
    rules.append(new_rule)
    
    # Update ruleset
    update_data = {
        "rules": rules
    }
    update_res = make_request('PUT', get_rs_url, headers, update_data)
    print(json.dumps(update_res, indent=2))

def purge_cache(env, headers, purge_all=True, files=None):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
    
    if purge_all:
        data = {"purge_everything": True}
    elif files:
        data = {"files": files}
    else:
        print("Error: Must specify either purge_all or files list.", file=sys.stderr)
        sys.exit(1)
        
    res = make_request('POST', url, headers, data)
    print(json.dumps(res, indent=2))

def custom_request(env, headers, method, endpoint, data_str=None):
    zone_id = env.get('CLOUDFLARE_ZONE_ID')
    account_id = env.get('CLOUDFLARE_ACCOUNT_ID')
    
    # Replace placeholders in endpoint
    endpoint = endpoint.strip('/')
    endpoint = endpoint.replace('{zone_id}', zone_id if zone_id else '')
    endpoint = endpoint.replace('{account_id}', account_id if account_id else '')
    
    url = f"https://api.cloudflare.com/client/v4/{endpoint}"
    
    data = None
    if data_str:
        try:
            data = json.loads(data_str)
        except Exception as e:
            print(f"Error parsing custom JSON data: {e}", file=sys.stderr)
            sys.exit(1)
            
    res = make_request(method, url, headers, data)
    print(json.dumps(res, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Sciences Gates Cloudflare Management CLI Tool")
    parser.add_argument('--action', required=True, choices=[
        'status', 'list_dns', 'set_dns', 'delete_dns', 
        'get_settings', 'set_setting', 'list_rules', 
        'add_page_rule', 'delete_page_rule', 'add_cache_rule',
        'purge_cache', 'custom'
    ], help="Action to execute on Cloudflare.")
    
    # Arguments for DNS
    parser.add_argument('--name', help="DNS record name (e.g. sciencesgates.com)")
    parser.add_argument('--type', help="DNS record type (e.g. A, CNAME, TXT)")
    parser.add_argument('--value', help="DNS record value/content (e.g. 208.109.79.3)")
    parser.add_argument('--proxied', action='store_true', default=True, help="Proxy status (orange/grey cloud). Defaults to True.")
    parser.add_argument('--no-proxied', dest='proxied', action='store_false', help="Set proxy status to False.")
    parser.add_argument('--ttl', type=int, default=1, help="DNS TTL value (1 for auto).")
    parser.add_argument('--id', help="ID of DNS record or Page/Cache Rule to delete/operate on.")
    
    # Arguments for Settings
    parser.add_argument('--setting', help="Name of setting to modify.")
    
    # Arguments for Page/Cache Rules
    parser.add_argument('--target', help="URL target pattern for Page Rule.")
    parser.add_argument('--behavior', help="JSON string for page rule actions or 'bypass'/'cache' for cache rules.")
    parser.add_argument('--expression', help="Expression syntax for cache rule (e.g. http.request.uri.path contains \"/admin\").")
    
    # Arguments for Purge Cache
    parser.add_argument('--all', action='store_true', help="Purge all cached resources.")
    parser.add_argument('--urls', help="Comma-separated list of URLs to purge.")
    
    # Arguments for Custom Request
    parser.add_argument('--method', default='GET', help="HTTP method for custom request (GET, POST, etc.)")
    parser.add_argument('--endpoint', help="Cloudflare API endpoint path (e.g. zones/{zone_id}/settings)")
    parser.add_argument('--data', help="JSON data string for custom request POST/PATCH/PUT payload.")
    
    args = parser.parse_args()
    
    env = load_env()
    headers = get_headers(env)
    
    if args.action == 'status':
        check_status(env, headers)
    elif args.action == 'list_dns':
        list_dns(env, headers)
    elif args.action == 'set_dns':
        if not all([args.name, args.type, args.value]):
            parser.error("--action set_dns requires --name, --type, and --value")
        set_dns(env, headers, args.name, args.type, args.value, args.proxied, args.ttl)
    elif args.action == 'delete_dns':
        if not args.id:
            parser.error("--action delete_dns requires --id")
        delete_dns(env, headers, args.id)
    elif args.action == 'get_settings':
        get_settings(env, headers)
    elif args.action == 'set_setting':
        if not all([args.setting, args.value]):
            parser.error("--action set_setting requires --setting and --value")
        set_setting(env, headers, args.setting, args.value)
    elif args.action == 'list_rules':
        list_rules(env, headers)
    elif args.action == 'add_page_rule':
        if not all([args.target, args.behavior]):
            parser.error("--action add_page_rule requires --target and --behavior (JSON actions)")
        add_page_rule(env, headers, args.target, args.behavior)
    elif args.action == 'delete_page_rule':
        if not args.id:
            parser.error("--action delete_page_rule requires --id")
        delete_page_rule(env, headers, args.id)
    elif args.action == 'add_cache_rule':
        if not all([args.name, args.expression, args.behavior]):
            parser.error("--action add_cache_rule requires --name, --expression, and --behavior ('bypass' or 'cache')")
        bypass = args.behavior.lower() == 'bypass'
        create_cache_rule(env, headers, args.name, args.expression, bypass)
    elif args.action == 'purge_cache':
        purge_all = args.all
        files = args.urls.split(',') if args.urls else None
        if not purge_all and not files:
            parser.error("--action purge_cache requires either --all or --urls")
        purge_cache(env, headers, purge_all, files)
    elif args.action == 'custom':
        if not args.endpoint:
            parser.error("--action custom requires --endpoint")
        custom_request(env, headers, args.method, args.endpoint, args.data)

if __name__ == '__main__':
    main()
