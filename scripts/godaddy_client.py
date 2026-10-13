"""GoDaddy API Client Utility.

Provides programmatic access to GoDaddy REST APIs using Personal Access Tokens (PAT).
Can be used as a CLI tool or imported as a Python module.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def load_env_variables(env_path: Path | None = None) -> None:
    """Load variables from .env file into os.environ if not already set."""
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent / ".env"

    if not env_path.exists():
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception as exc:
        print(f"[WARN] Failed to read .env: {exc}", file=sys.stderr)


class GoDaddyClient:
    """GoDaddy REST API Client with Personal Access Token (PAT) authentication."""

    def __init__(self, token: str | None = None, base_url: str | None = None):
        load_env_variables()
        self.token = token or os.environ.get("GODADDY_API_TOKEN")
        self.base_url = (base_url or os.environ.get("GODADDY_API_URL") or "https://api.godaddy.com").rstrip("/")

        if not self.token:
            raise ValueError("GODADDY_API_TOKEN not found in environment or .env file.")

    def _request(self, method: str, path: str, data: dict | list | None = None) -> dict | list | None:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                content = resp.read().decode("utf-8")
                if not content:
                    return {"status": status, "message": "Success (No Content)"}
                return json.loads(content)
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
                raise RuntimeError(f"HTTP {err.code}: {err_json}") from err
            except json.JSONDecodeError:
                raise RuntimeError(f"HTTP {err.code}: {err_body}") from err

    def list_domains(self) -> list:
        """List all domains under the account."""
        return self._request("GET", "/v1/domains")

    def get_domain(self, domain: str) -> dict:
        """Retrieve details of a single domain."""
        return self._request("GET", f"/v1/domains/{domain}")

    def get_records(self, domain: str, record_type: str | None = None, name: str | None = None) -> list:
        """Get DNS records for a domain, optionally filtering by type and name."""
        path = f"/v1/domains/{domain}/records"
        if record_type and name:
            path = f"/v1/domains/{domain}/records/{record_type}/{name}"
        elif record_type:
            path = f"/v1/domains/{domain}/records/{record_type}"
        return self._request("GET", path)

    def set_record(self, domain: str, record_type: str, name: str, value: str, ttl: int = 3600) -> dict | list | None:
        """Set / replace DNS record(s) of a specific type and name."""
        path = f"/v1/domains/{domain}/records/{record_type}/{name}"
        data = [{"data": value, "ttl": ttl}]
        return self._request("PUT", path, data=data)

    def add_records(self, domain: str, records: list) -> dict | list | None:
        """Add new DNS record(s) to a domain."""
        path = f"/v1/domains/{domain}/records"
        return self._request("PATCH", path, data=records)


def main():
    parser = argparse.ArgumentParser(description="GoDaddy API Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: list-domains
    subparsers.add_parser("list-domains", help="List all registered domains")

    # Command: domain-info
    domain_parser = subparsers.add_parser("domain-info", help="Get domain details")
    domain_parser.add_argument("domain", help="Domain name (e.g. sciencesgates.com)")

    # Command: list-dns
    dns_parser = subparsers.add_parser("list-dns", help="List DNS records for a domain")
    dns_parser.add_argument("domain", help="Domain name (e.g. sciencesgates.com)")
    dns_parser.add_argument("--type", dest="record_type", help="Filter by type (A, CNAME, TXT, etc.)")
    dns_parser.add_argument("--name", help="Filter by name (@, www, etc.)")

    # Command: set-dns
    set_parser = subparsers.add_parser("set-dns", help="Set / update a DNS record")
    set_parser.add_argument("domain", help="Domain name")
    set_parser.add_argument("type", help="Record type (A, CNAME, TXT)")
    set_parser.add_argument("name", help="Record name (@, www, subdomain)")
    set_parser.add_argument("value", help="Record value (e.g. IP address or host)")
    set_parser.add_argument("--ttl", type=int, default=3600, help="TTL in seconds (default: 3600)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        client = GoDaddyClient()

        if args.command == "list-domains":
            domains = client.list_domains()
            print(f"Found {len(domains)} domain(s):")
            for d in domains:
                status = d.get("status")
                expires = d.get("expires")
                print(f" - {d.get('domain')} | Status: {status} | Expires: {expires}")

        elif args.command == "domain-info":
            info = client.get_domain(args.domain)
            print(json.dumps(info, indent=2))

        elif args.command == "list-dns":
            records = client.get_records(args.domain, args.record_type, args.name)
            print(json.dumps(records, indent=2))

        elif args.command == "set-dns":
            res = client.set_record(args.domain, args.type, args.name, args.value, args.ttl)
            print(f"Successfully updated {args.type} record for {args.name}.{args.domain} -> {args.value}")

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
