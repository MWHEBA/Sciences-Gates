"""
Run sanitize_seo_synonyms on production via SSH and print report
"""
import os
import sys
import paramiko
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


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


def run_remote_command(cmd_args=""):
    env = load_env()
    host = env.get('SSH_HOST', '208.109.79.3')
    port = int(env.get('SSH_PORT', 22))
    username = env.get('SSH_USER', 's2jbje0ncqbo')
    key_path = env.get('SSH_KEY_PATH', 'id_rsa')
    passphrase = env.get('SSH_KEY_PASSPHRASE')
    remote_path = env.get('REMOTE_PATH', '/home/s2jbje0ncqbo/science')
    python_bin = f"/home/{username}/virtualenv/science/3.11/bin/python"

    print("=" * 80)
    print(f"CONNECTING TO PRODUCTION SERVER: {username}@{host}:{port}")
    print("=" * 80)

    key = paramiko.RSAKey.from_private_key_file(key_path, password=passphrase)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, port=port, username=username, pkey=key, timeout=15)

    full_cmd = (
        f"cd {remote_path} && "
        f"PYTHONIOENCODING=utf-8 {python_bin} manage.py sanitize_seo_synonyms {cmd_args} --settings=config.settings.production"
    )
    print(f"Running command: {full_cmd}\n")

    stdin, stdout, stderr = ssh.exec_command(full_cmd, timeout=300)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')

    if out:
        print(out)
    if err:
        print("\n--- STDERR ---")
        print(err)

    code = "from apps.universities.models import University; " \
           "unis = University.objects.filter(pk__in=[322, 339]); " \
           "print('\\n'.join([str(u.id) + ' | ' + str(u.name) + ' | KW: ' + str(u.focus_keyword) + ' | SYNS: ' + str(u.keyphrase_synonyms) for u in unis]))"
    verify_cmd = f"cd {remote_path} && PYTHONIOENCODING=utf-8 {python_bin} manage.py shell --settings=config.settings.production -c \"{code}\""
    stdin, stdout, stderr = ssh.exec_command(verify_cmd, timeout=60)
    print(stdout.read().decode('utf-8', errors='replace'))

    ssh.close()


if __name__ == '__main__':
    args = " ".join(sys.argv[1:])
    run_remote_command(args)
