"""
Production Server and Database Audit Script via Paramiko SSH
"""
import os
import sys
import paramiko
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_env():
    env_file = Path('.env')
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

def audit_production():
    env = load_env()
    host = env.get('SSH_HOST', '208.109.79.3')
    port = int(env.get('SSH_PORT', 22))
    username = env.get('SSH_USER', 's2jbje0ncqbo')
    key_path = env.get('SSH_KEY_PATH', 'id_rsa')
    passphrase = env.get('SSH_KEY_PASSPHRASE')
    remote_path = env.get('REMOTE_PATH', '/home/s2jbje0ncqbo/science')
    python_bin = f"/home/{username}/virtualenv/science/3.11/bin/python"

    print("=" * 80)
    print(f"PRODUCTION SERVER AUDIT: {username}@{host}:{port}")
    print("=" * 80)

    key = paramiko.RSAKey.from_private_key_file(key_path, password=passphrase)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, port=port, username=username, pkey=key, timeout=15)

    # 1. Check Python & Virtual Environment
    print("\n[1] PYTHON & ENVIRONMENT CHECK:")
    cmd = f"{python_bin} --version && {python_bin} -c 'import django; print(\"Django Version:\", django.__version__)'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode().strip())

    # 2. Check Production Database for WPTB Shortcodes
    print("\n[2] PRODUCTION DATABASE WPTB AUDIT:")
    python_cmd = (
        f"cd {remote_path} && "
        f"{python_bin} manage.py shell --settings=config.settings.production -c \""
        f"from apps.articles.models import Article; "
        f"total = Article.objects.count(); "
        f"wptb_count = Article.objects.filter(content__icontains='wptb').count(); "
        f"print(f'Total Prod Articles: {{total}} | Articles with WPTB: {{wptb_count}}')"
        f"\""
    )
    stdin, stdout, stderr = ssh.exec_command(python_cmd)
    res_out = stdout.read().decode().strip()
    res_err = stderr.read().decode().strip()
    print("DB Result:", res_out if res_out else f"ERR: {res_err}")

    # 3. Check Contact Page Status in Production Routes
    print("\n[3] PRODUCTION ROUTE CHECK (/contact/):")
    python_cmd_urls = (
        f"cd {remote_path} && "
        f"{python_bin} manage.py shell --settings=config.settings.production -c \""
        f"from django.urls import resolve; "
        f"match = resolve('/contact/'); "
        f"print(f'Contact Route Match: {{match.func}}')"
        f"\""
    )
    stdin, stdout, stderr = ssh.exec_command(python_cmd_urls)
    res_out_url = stdout.read().decode().strip()
    print("Route Check:", res_out_url if res_out_url else "Failed route resolve")

    # 4. Check Static & Media Directories
    print("\n[4] STATIC & MEDIA DIRECTORIES:")
    cmd_dirs = f"ls -ld {remote_path}/staticfiles {remote_path}/media"
    stdin, stdout, stderr = ssh.exec_command(cmd_dirs)
    print(stdout.read().decode().strip())

    # 5. Check Production Settings (.env / passenger_wsgi)
    print("\n[5] PRODUCTION .ENV / CONFIGURATION CHECK:")
    cmd_env = f"grep -E 'DEBUG|ALLOWED_HOSTS|SITE_URL|DATABASE_URL' {remote_path}/.env"
    stdin, stdout, stderr = ssh.exec_command(cmd_env)
    print(stdout.read().decode().strip())

    ssh.close()
    print("\n" + "=" * 80)

if __name__ == '__main__':
    audit_production()
