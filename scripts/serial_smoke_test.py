#!/usr/bin/env python3
"""
Open a serial port and optionally capture output for a few seconds.
"""
import argparse, time, sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--seconds', type=float, default=5.0)
    ap.add_argument('--out', default='data/board_runs/serial_smoke.log')
    args = ap.parse_args()
    try:
        import serial
    except Exception as e:
        print('[FAIL] pyserial is not installed:', e)
        sys.exit(1)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f'[INFO] Opening {args.port} at {args.baud} for {args.seconds}s')
    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.2)
    except Exception as e:
        print('[FAIL] Cannot open serial port:', e)
        sys.exit(1)
    end = time.time() + args.seconds
    data = bytearray()
    try:
        while time.time() < end:
            chunk = ser.read(1024)
            if chunk:
                data.extend(chunk)
                try:
                    print(chunk.decode('utf-8', errors='replace'), end='')
                except Exception:
                    pass
    finally:
        ser.close()
    out.write_bytes(data)
    print(f'\n[OK] Serial port opened. Captured {len(data)} bytes to {out}')

if __name__ == '__main__':
    main()
