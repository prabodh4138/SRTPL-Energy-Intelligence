#!/usr/bin/env python3
"""SRTPL Power Consumption Analytics — Database CLI Manager.

Usage:
    python scripts/supabase_manager.py --status
    python scripts/supabase_manager.py --network
    python scripts/supabase_manager.py --inject
    python scripts/supabase_manager.py --reset
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "active_app"))

from core.supabase_manager import (
    get_database_status,
    get_network_info,
    inject_master_and_sample_data,
    remove_all_database_data,
    test_database_connection,
)


def main():
    parser = argparse.ArgumentParser(description="SRTPL Supabase & Database Manager")
    parser.add_argument("--status", action="store_true", help="Check database connection status")
    parser.add_argument("--network", action="store_true", help="Show local & network URLs for mobile/laptop")
    parser.add_argument("--inject", action="store_true", help="Inject master data, CSV logs, bills, and receipts")
    parser.add_argument("--reset", action="store_true", help="Remove all data from database (clean production wipe)")

    args = parser.parse_args()

    if not any([args.status, args.network, args.inject, args.reset]):
        parser.print_help()
        sys.exit(0)

    if args.network or args.status:
        net = get_network_info()
        print("=" * 60)
        print("SRTPL APPLICATION ACCESS LINKS:")
        print(f"  Local PC Link      : {net['local_url']}")
        print(f"  Mobile/Laptop Link : {net['network_url']}")
        print(f"  Local Network IP   : {net['ip']}")
        print("=" * 60)

    if args.status:
        conn = test_database_connection()
        print("DATABASE STATUS:")
        print(f"  Connected : {conn['connected']}")
        print(f"  Status    : {conn['status']}")
        print(f"  Message   : {conn['message']}")
        print("=" * 60)

    if args.inject:
        print("[*] Starting data injection into Supabase / operational store...")
        def _cb(msg, progress):
            print(f"  [{int(progress * 100):3d}%] {msg}")

        result = inject_master_and_sample_data(_cb)
        print("\n[OK] Injection Complete!")
        print(f"  Mode           : {result['mode']}")
        print(f"  Plazas         : {result['plazas']}")
        print(f"  Assets         : {result['assets']}")
        print(f"  Meter Readings : {result['meter_readings']}")
        print(f"  Energy Bills   : {result['bills']}")
        print(f"  Receipts       : {result['receipts']}")
        print("=" * 60)

    if args.reset:
        print("[!] Wiping all operational data from database...")
        res = remove_all_database_data()
        print("[OK] Database Reset Complete!")
        print(f"  Message : {res['message']}")
        print(f"  Tables  : {len(res['cleared_tables'])} cleared")
        print("=" * 60)


if __name__ == "__main__":
    main()
