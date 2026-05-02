#!/usr/bin/env python3
"""
Sanity check for local project environment.
健全性检查：确认 Python、路径、串口、Vivado/Vitis 命令基本可用。
"""
from pathlib import Path
import argparse, os, shutil, subprocess, sys, re

REQUIRED_KEYS = [
    'PROJECT_ROOT', 'FIR_REFERENCE_REPO', 'BOARD_DOCS_ROOT', 'GITHUB_URL',
    'VIVADO_SETTINGS', 'VITIS_SETTINGS', 'SERIAL_PORT', 'UART_BAUD',
    'BOARD_NAME', 'FPGA_PART', 'ALLOW_BOARD_RUN', 'ALLOW_FLASH_WRITE'
]

def parse_env(path: Path):
    data = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def check_python_pkg(pkg):
    try:
        __import__(pkg)
        return True, ''
    except Exception as e:
        return False, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--env', default='config/local.env')
    args = ap.parse_args()
    env_path = Path(args.env)
    if not env_path.exists():
        print(f'[FAIL] env file not found: {env_path}')
        sys.exit(1)
    env = parse_env(env_path)

    ok = True
    print('[CHECK] Required keys')
    for k in REQUIRED_KEYS:
        if k not in env or not env[k]:
            print(f'  [FAIL] {k} missing')
            ok = False
        else:
            print(f'  [OK] {k}={env[k]}')

    print('[CHECK] Paths')
    for k in ['PROJECT_ROOT', 'FIR_REFERENCE_REPO', 'BOARD_DOCS_ROOT']:
        p = Path(env.get(k, '')).expanduser()
        if p.exists():
            print(f'  [OK] {k}: {p}')
        else:
            print(f'  [WARN] {k} path does not exist: {p}')
            if k == 'PROJECT_ROOT':
                ok = False

    print('[CHECK] Tool setup files')
    for k in ['VIVADO_SETTINGS', 'VITIS_SETTINGS']:
        p = Path(env.get(k, '')).expanduser()
        if p.exists():
            print(f'  [OK] {k}: {p}')
        else:
            print(f'  [FAIL] {k} file does not exist: {p}')
            ok = False

    print('[CHECK] Python packages')
    for pkg in ['json', 'subprocess', 'numpy', 'pandas', 'matplotlib', 'pytest', 'serial']:
        name = 'serial' if pkg == 'serial' else pkg
        good, err = check_python_pkg(name)
        print(f'  [{"OK" if good else "WARN"}] {pkg}' + ('' if good else f' -> {err}'))

    print('[CHECK] Commands in PATH')
    for cmd in ['git', 'python', 'vivado', 'xsct']:
        found = shutil.which(cmd)
        print(f'  [{"OK" if found else "WARN"}] {cmd}: {found}')

    print('[CHECK] Flash policy')
    if env.get('ALLOW_FLASH_WRITE', '0') != '0':
        print('  [FAIL] ALLOW_FLASH_WRITE must stay 0 unless user explicitly authorizes flash programming.')
        ok = False
    else:
        print('  [OK] flash write disabled')

    print('[SUMMARY]', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
