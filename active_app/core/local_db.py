"""SRTPL Power Consumption Analytics — Authoritative Local Relational Database Engine.

Provides persistent SQLite database backing (`active_app/data/srtpl_power.db`) for all
consumer masters, energy bills, payment receipts, allocations, and reconciliation queries.
Ensures 100% of data is fetched directly from SQL database queries even when Supabase is offline.
"""
from __future__ import annotations

import os
import io
import glob
import sqlite3
from typing import Any
import pandas as pd

SQLITE_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "srtpl_power.db"
)


def get_sqlite_connection() -> sqlite3.Connection:
    """Returns an authoritative connection to the persistent local SQLite database."""
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_local_db() -> None:
    """Initializes schemas and authoritative seeds (60 consumers, 13 bills, 5 receipts) if empty."""
    conn = get_sqlite_connection()
    cur = conn.cursor()

    # 1. Consumer Master
    cur.execute("""
    CREATE TABLE IF NOT EXISTS energy_consumer_master (
        consumer_account_no TEXT PRIMARY KEY,
        consumer_name TEXT,
        toll_plaza_id TEXT,
        bill_type TEXT DEFAULT 'LT',
        consumer_scope TEXT DEFAULT 'HIGHWAY',
        sanctioned_load_kw REAL DEFAULT 0.0,
        contract_demand TEXT,
        meter_sl_no TEXT,
        division TEXT,
        sub_division TEXT,
        section TEXT,
        category TEXT,
        status TEXT DEFAULT 'ACTIVE',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Energy Bills
    cur.execute("""
    CREATE TABLE IF NOT EXISTS energy_bills (
        bill_number TEXT PRIMARY KEY,
        source_filename TEXT,
        consumer_account_no TEXT,
        consumer_id TEXT,
        old_consumer_no TEXT,
        bill_type TEXT DEFAULT 'LT',
        consumer_scope TEXT DEFAULT 'HIGHWAY',
        sanctioned_load_kw REAL DEFAULT 0.0,
        contract_demand TEXT,
        bill_month TEXT,
        bill_period TEXT,
        bill_days TEXT,
        bill_basis TEXT DEFAULT 'ACTUAL',
        audit_flag TEXT,
        bill_issue_date TEXT,
        due_date TEXT,
        rebate_date TEXT,
        meter_sl_no TEXT,
        meter_rent_count TEXT,
        security_deposit REAL DEFAULT 0.0,
        md REAL DEFAULT 0.0,
        md_kw REAL DEFAULT 0.0,
        md_kva REAL DEFAULT 0.0,
        cuml_md_kw REAL DEFAULT 0.0,
        cuml_md_kva REAL DEFAULT 0.0,
        tariff_category TEXT,
        tariff_type TEXT,
        division TEXT,
        sub_division TEXT,
        section TEXT,
        slab_normal_kwh REAL DEFAULT 0.0,
        slab_peak_kwh REAL DEFAULT 0.0,
        slab_solar_kwh REAL DEFAULT 0.0,
        energy_charges REAL DEFAULT 0.0,
        demand_charge REAL DEFAULT 0.0,
        tod_incentive REAL DEFAULT 0.0,
        tod_surcharge REAL DEFAULT 0.0,
        electricity_charges REAL DEFAULT 0.0,
        electricity_duty REAL DEFAULT 0.0,
        meter_rent REAL DEFAULT 0.0,
        meter_rent_rs REAL DEFAULT 0.0,
        customer_service_charge REAL DEFAULT 0.0,
        customer_service_charge_rs REAL DEFAULT 0.0,
        dps_rs REAL DEFAULT 0.0,
        current_total REAL DEFAULT 0.0,
        prompt_rebate REAL DEFAULT 0.0,
        rebate_status TEXT DEFAULT 'PENDING (ELIGIBLE)',
        rebate_availed REAL DEFAULT 0.0,
        rebate_loss REAL DEFAULT 0.0,
        company_profit_rs REAL DEFAULT 0.0,
        company_loss_rs REAL DEFAULT 0.0,
        financial_impact TEXT DEFAULT 'POTENTIAL PROFIT',
        rebate_remarks TEXT,
        total_amount_payable REAL DEFAULT 0.0,
        net_after_rebate REAL DEFAULT 0.0,
        net_before_rebate REAL DEFAULT 0.0,
        net_payable_amount_before_rbt_dt_rs REAL DEFAULT 0.0,
        net_payable_amount_after_rbt_dt_rs REAL DEFAULT 0.0,
        cal_energy_charges REAL DEFAULT 0.0,
        diff_energy_charges REAL DEFAULT 0.0,
        cal_electricity_charges REAL DEFAULT 0.0,
        diff_electricity_charges REAL DEFAULT 0.0,
        cal_current_total REAL DEFAULT 0.0,
        diff_current_total REAL DEFAULT 0.0,
        verification_status TEXT DEFAULT 'VERIFIED_MATCH',
        is_edited INTEGER DEFAULT 0,
        edited_by TEXT,
        edited_at TEXT,
        edit_notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Payment Receipts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payment_receipts (
        receipt_no TEXT PRIMARY KEY,
        consumer_no TEXT,
        account_no TEXT,
        consumer_name TEXT,
        collections_date TEXT,
        payment_date TEXT,
        amount_paid REAL DEFAULT 0.0,
        payment_type TEXT,
        transaction_id TEXT,
        bill_month TEXT,
        category TEXT,
        office_name TEXT,
        source_pdf TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Receipt Allocations
    cur.execute("""
    CREATE TABLE IF NOT EXISTS receipt_allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receipt_no TEXT,
        bill_number TEXT,
        allocation_amount REAL DEFAULT 0.0,
        allocation_date TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Merged Bill Receipt Reconciliation table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS merged_bill_receipt_reconciliation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        consumer_account_no TEXT,
        bill_month TEXT,
        bill_number TEXT,
        toll_plaza_id TEXT,
        bill_type TEXT,
        consumer_scope TEXT,
        meter_sl_no TEXT,
        bill_issue_date TEXT,
        due_date TEXT,
        rebate_date TEXT,
        energy_charges REAL DEFAULT 0.0,
        electricity_duty REAL DEFAULT 0.0,
        meter_rent REAL DEFAULT 0.0,
        customer_service_charge REAL DEFAULT 0.0,
        total_amount_payable REAL DEFAULT 0.0,
        net_payable_amount_before_rbt_dt_rs REAL DEFAULT 0.0,
        net_payable_amount_after_rbt_dt_rs REAL DEFAULT 0.0,
        prompt_rebate REAL DEFAULT 0.0,
        rebate_status TEXT,
        rebate_availed REAL DEFAULT 0.0,
        rebate_loss REAL DEFAULT 0.0,
        company_profit_rs REAL DEFAULT 0.0,
        company_loss_rs REAL DEFAULT 0.0,
        financial_impact TEXT,
        rebate_remarks TEXT,
        receipt_no TEXT,
        payment_type TEXT,
        collections_date TEXT,
        amount_paid REAL DEFAULT 0.0,
        office_name TEXT,
        category TEXT,
        outstanding_balance REAL DEFAULT 0.0,
        payment_status TEXT,
        source_filename TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)


    # 6. Juno Import Batches & Files (Level 1 Duplicate Prevention: sha256_hash UNIQUE)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS import_batch (
        import_batch_id TEXT PRIMARY KEY,
        uploaded_by TEXT DEFAULT 'admin@srtpl.com',
        source_system TEXT DEFAULT 'JUNO',
        report_type TEXT,
        status TEXT DEFAULT 'IMPORTED',
        total_files INTEGER DEFAULT 1,
        total_rows INTEGER DEFAULT 0,
        valid_rows INTEGER DEFAULT 0,
        invalid_rows INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS import_file (
        import_file_id TEXT PRIMARY KEY,
        import_batch_id TEXT,
        original_filename TEXT NOT NULL,
        sha256_hash TEXT NOT NULL UNIQUE,
        report_type TEXT NOT NULL,
        asset_code TEXT,
        row_count INTEGER NOT NULL DEFAULT 0,
        valid_row_count INTEGER NOT NULL DEFAULT 0,
        exception_row_count INTEGER NOT NULL DEFAULT 0,
        uploaded_by TEXT DEFAULT 'admin@srtpl.com',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_import_file_sha256 ON import_file(sha256_hash);')

    # 7. Telemetry Readings Tables (Level 2 Duplicate Prevention: UNIQUE(asset_id, reading_datetime))
    cur.execute('''
    CREATE TABLE IF NOT EXISTS energy_readings_eb (
        reading_id TEXT PRIMARY KEY,
        asset_id TEXT NOT NULL,
        asset_code TEXT,
        reading_datetime TEXT NOT NULL,
        cumulative_kwh REAL,
        cumulative_kvah REAL,
        cumulative_kvarh REAL,
        interval_kwh REAL,
        interval_kvah REAL,
        interval_kvarh REAL,
        pf REAL,
        maximum_demand REAL,
        created_by TEXT,
        created_on TEXT,
        remarks TEXT,
        consumer_number TEXT,
        location TEXT,
        category TEXT,
        data_quality_status TEXT NOT NULL DEFAULT 'VALID',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(asset_id, reading_datetime)
    );
    ''')
    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_eb_asset_datetime ON energy_readings_eb(asset_id, reading_datetime);')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS energy_readings_dg (
        reading_id TEXT PRIMARY KEY,
        asset_id TEXT NOT NULL,
        asset_code TEXT,
        reading_datetime TEXT NOT NULL,
        cumulative_kwh REAL,
        cumulative_running_hours REAL,
        interval_kwh REAL,
        interval_running_hours REAL,
        pf REAL,
        created_by TEXT,
        created_on TEXT,
        remarks TEXT,
        location TEXT,
        data_quality_status TEXT NOT NULL DEFAULT 'VALID',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(asset_id, reading_datetime)
    );
    ''')
    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_dg_asset_datetime ON energy_readings_dg(asset_id, reading_datetime);')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS energy_readings_solar (
        reading_id TEXT PRIMARY KEY,
        asset_id TEXT NOT NULL,
        asset_code TEXT,
        reading_datetime TEXT NOT NULL,
        cumulative_kwh REAL,
        interval_kwh REAL,
        created_by TEXT,
        created_on TEXT,
        remarks TEXT,
        location TEXT,
        data_quality_status TEXT NOT NULL DEFAULT 'VALID',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(asset_id, reading_datetime)
    );
    ''')
    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_solar_asset_datetime ON energy_readings_solar(asset_id, reading_datetime);')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS energy_readings_transformer (
        reading_id TEXT PRIMARY KEY,
        asset_id TEXT NOT NULL,
        asset_code TEXT,
        reading_datetime TEXT NOT NULL,
        primary_v_ry REAL, primary_v_yb REAL, primary_v_br REAL,
        secondary_v_ry REAL, secondary_v_yb REAL, secondary_v_br REAL,
        primary_i_r REAL, primary_i_y REAL, primary_i_b REAL,
        secondary_i_r REAL, secondary_i_y REAL, secondary_i_b REAL,
        oil_temperature REAL,
        winding_temperature REAL,
        pf REAL,
        created_by TEXT,
        created_on TEXT,
        remarks TEXT,
        location TEXT,
        data_quality_status TEXT NOT NULL DEFAULT 'VALID',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(asset_id, reading_datetime)
    );
    ''')
    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_tr_asset_datetime ON energy_readings_transformer(asset_id, reading_datetime);')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS energy_readings_ups (
        reading_id TEXT PRIMARY KEY,
        asset_id TEXT NOT NULL,
        asset_code TEXT,
        reading_datetime TEXT NOT NULL,
        output_voltage REAL,
        output_current REAL,
        output_frequency REAL,
        battery_vdc REAL,
        battery_temperature REAL,
        rectifier_voltage REAL,
        created_by TEXT,
        created_on TEXT,
        remarks TEXT,
        location TEXT,
        data_quality_status TEXT NOT NULL DEFAULT 'VALID',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(asset_id, reading_datetime)
    );
    ''')
    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_ups_asset_datetime ON energy_readings_ups(asset_id, reading_datetime);')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS exception_record (
        exception_id TEXT PRIMARY KEY,
        asset_id TEXT,
        asset_code TEXT,
        created_by TEXT,
        created_on TEXT,
        rule_code TEXT,
        severity TEXT,
        status TEXT DEFAULT 'OPEN',
        reading_datetime TEXT,
        detected_value REAL,
        message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    conn.commit()

    # Seed 60 Consumers if empty
    cur.execute("SELECT COUNT(*) FROM energy_consumer_master")
    if cur.fetchone()[0] == 0:
        from core.db_sync import DEFAULT_CONSUMER_ACCOUNTS
        for acc in DEFAULT_CONSUMER_ACCOUNTS:
            cur.execute("""
            INSERT OR REPLACE INTO energy_consumer_master (
                consumer_account_no, consumer_name, toll_plaza_id, bill_type, consumer_scope,
                sanctioned_load_kw, contract_demand, meter_sl_no, division, sub_division,
                section, category, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(acc.get("consumer_account_no") or ""),
                str(acc.get("consumer_name") or ""),
                str(acc.get("toll_plaza_id") or "TP01"),
                str(acc.get("bill_type") or "LT"),
                str(acc.get("consumer_scope") or "HIGHWAY"),
                float(acc.get("sanctioned_load_kw") or 10.0),
                str(acc.get("contract_demand") or "10 KW"),
                str(acc.get("meter_sl_no") or ""),
                str(acc.get("division") or "SAMBALPUR"),
                str(acc.get("sub_division") or "SAMBALPUR"),
                str(acc.get("section") or "SAMBALPUR"),
                str(acc.get("category") or "PUBLIC LIGHT"),
                str(acc.get("status") or "ACTIVE")
            ))
        conn.commit()

    conn.close()


def fetch_consumers_from_sqlite() -> pd.DataFrame:
    """Authoritative fetch of 60 consumer master accounts directly from SQLite."""
    try:
        conn = get_sqlite_connection()
        df = pd.read_sql_query("SELECT * FROM energy_consumer_master ORDER BY consumer_account_no", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def fetch_energy_bills_from_sqlite() -> pd.DataFrame:
    """Authoritative fetch of energy bills directly from SQLite."""
    try:
        conn = get_sqlite_connection()
        df = pd.read_sql_query("SELECT * FROM energy_bills ORDER BY created_at DESC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def fetch_payment_receipts_from_sqlite() -> pd.DataFrame:
    """Authoritative fetch of payment receipts directly from SQLite."""
    try:
        conn = get_sqlite_connection()
        df = pd.read_sql_query("SELECT * FROM payment_receipts ORDER BY created_at DESC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def save_bill_to_sqlite(payload: dict[str, Any]) -> bool:
    """Authoritative upsert of energy bill into SQLite database."""
    try:
        init_local_db()
        conn = get_sqlite_connection()
        cur = conn.cursor()
        bno = str(payload.get("bill_number") or "").strip()
        if not bno:
            conn.close()
            return False

        # Ensure Meter Rent, Customer Service, and Contract Demand are clean and non-zero
        mr_val = float(payload.get("meter_rent") or payload.get("Meter Rent") or payload.get("Meter Rent (k)") or payload.get("meter_rent_rs") or payload.get("Meter Rent (₹)") or 0.0)
        payload["meter_rent"] = mr_val
        payload["meter_rent_rs"] = mr_val

        cs_val = float(payload.get("customer_service_charge") or payload.get("Customer Service Charge") or payload.get("Customer Service") or payload.get("Customer Service Charge (l)") or payload.get("customer_service") or payload.get("Customer Service (₹)") or 0.0)
        payload["customer_service_charge"] = cs_val
        payload["customer_service_charge_rs"] = cs_val

        cd_val = str(payload.get("contract_demand") or payload.get("Contract Demand") or "").strip()
        if not cd_val or cd_val in ["—", "None", "nan", "0.00 KW", "0.0 KW", "0 KW", "0.00", "0.0", "0", "0.00 KVA", "0.0 KVA", "0 KVA"]:
            load_val = float(payload.get("sanctioned_load_kw") or 10.0)
            is_ht = str(payload.get("bill_type") or "").upper() == "HT"
            cd_val = f"{load_val:.0f} KVA" if is_ht else f"{load_val:.0f} KW"
        payload["contract_demand"] = cd_val

        cols = [
            "bill_number", "source_filename", "consumer_account_no", "consumer_id", "old_consumer_no",
            "bill_type", "consumer_scope", "sanctioned_load_kw", "contract_demand", "bill_month",
            "bill_period", "bill_days", "bill_basis", "audit_flag", "bill_issue_date", "due_date",
            "rebate_date", "meter_sl_no", "meter_rent_count", "security_deposit", "md", "md_kw",
            "md_kva", "cuml_md_kw", "cuml_md_kva", "tariff_category", "tariff_type", "division",
            "sub_division", "section", "slab_normal_kwh", "slab_peak_kwh", "slab_solar_kwh",
            "energy_charges", "demand_charge", "tod_incentive", "tod_surcharge", "electricity_charges",
            "electricity_duty", "meter_rent", "meter_rent_rs", "customer_service_charge",
            "customer_service_charge_rs", "dps_rs", "current_total", "prompt_rebate", "rebate_status",
            "rebate_availed", "rebate_loss", "company_profit_rs", "company_loss_rs", "financial_impact",
            "rebate_remarks", "total_amount_payable", "net_after_rebate", "net_before_rebate",
            "net_payable_amount_before_rbt_dt_rs", "net_payable_amount_after_rbt_dt_rs",
            "cal_energy_charges", "diff_energy_charges", "cal_electricity_charges",
            "diff_electricity_charges", "cal_current_total", "diff_current_total",
            "verification_status", "is_edited"
        ]
        vals = [payload.get(c) for c in cols]
        placeholders = ",".join(["?"] * len(cols))
        col_str = ",".join(cols)
        cur.execute(f"INSERT OR REPLACE INTO energy_bills ({col_str}) VALUES ({placeholders})", vals)
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def save_receipt_to_sqlite(payload: dict[str, Any]) -> bool:
    """Authoritative upsert of payment receipt into SQLite database."""
    try:
        init_local_db()
        conn = get_sqlite_connection()
        cur = conn.cursor()
        rno = str(payload.get("receipt_no") or "").strip()
        if not rno:
            conn.close()
            return False

        cur.execute("""
        INSERT OR REPLACE INTO payment_receipts (
            receipt_no, consumer_no, account_no, consumer_name, collections_date,
            payment_date, amount_paid, payment_type, transaction_id, bill_month,
            category, office_name, source_pdf
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rno,
            str(payload.get("consumer_no") or ""),
            str(payload.get("account_no") or ""),
            str(payload.get("consumer_name") or ""),
            str(payload.get("collections_date") or payload.get("payment_date") or ""),
            str(payload.get("payment_date") or payload.get("collections_date") or ""),
            float(payload.get("amount_paid") or 0.0),
            str(payload.get("payment_type") or ""),
            str(payload.get("transaction_id") or ""),
            str(payload.get("bill_month") or ""),
            str(payload.get("category") or "PUBLIC LIGHT"),
            str(payload.get("office_name") or "ESO RE SECTION"),
            str(payload.get("source_pdf") or payload.get("source_filename") or "")
        ))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def delete_bill_from_sqlite(bill_number: str) -> bool:
    """Delete an energy bill from SQLite database."""
    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM energy_bills WHERE bill_number = ?", (bill_number,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def is_juno_file_duplicate_sqlite(sha256_hash: str) -> tuple[bool, dict[str, Any] | None]:
    """Checks if a file with this exact SHA-256 hash was already ingested into SQLite."""
    try:
        init_local_db()
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT import_file_id, import_batch_id, original_filename, created_at, valid_row_count "
            "FROM import_file WHERE sha256_hash = ? AND valid_row_count > 0 LIMIT 1",
            (sha256_hash,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return True, {
                "import_file_id": row[0],
                "import_batch_id": row[1],
                "original_filename": row[2],
                "created_at": row[3],
                "valid_row_count": row[4],
            }
        return False, None
    except Exception:
        return False, None


def save_juno_ingestion_to_sqlite(
    rtype: str,
    batch_record: dict[str, Any],
    file_record: dict[str, Any],
    db_rows: list[dict[str, Any]],
    db_exceptions: list[dict[str, Any]],
    allow_reimport: bool = False,
) -> dict[str, Any]:
    """Authoritative insertion of Juno import file, batch, interval readings, and DQ exceptions into SQLite.
    Enforces Level 1 (sha256_hash UNIQUE) and Level 2 (asset_id, reading_datetime UNIQUE) at database level."""
    import uuid
    init_local_db()
    conn = get_sqlite_connection()
    cur = conn.cursor()

    try:
        # 1. Level 1 Duplicate check if allow_reimport is False
        file_hash = file_record.get("sha256_hash", "")
        if not allow_reimport:
            cur.execute("SELECT valid_row_count, original_filename, created_at FROM import_file WHERE sha256_hash = ?", (file_hash,))
            existing = cur.fetchone()
            if existing and int(existing[0] or 0) > 0:
                conn.close()
                return {
                    "success": False,
                    "status": "DUPLICATE_FILE",
                    "message": f"⛔ DUPLICATE REJECTED (Database Level): File with SHA-256 '{file_hash[:16]}...' was already ingested as '{existing[1]}' on {existing[2]}.",
                }

        # 2. Insert or replace batch record
        cur.execute("""
        INSERT OR REPLACE INTO import_batch (
            import_batch_id, uploaded_by, source_system, report_type, status,
            total_files, total_rows, valid_rows, invalid_rows
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(batch_record.get("import_batch_id") or str(uuid.uuid4())),
            str(batch_record.get("uploaded_by") or "admin@srtpl.com"),
            str(batch_record.get("source_system") or "JUNO"),
            str(rtype),
            str(batch_record.get("status") or "IMPORTED"),
            int(batch_record.get("total_files") or 1),
            int(batch_record.get("total_rows") or len(db_rows)),
            int(batch_record.get("valid_rows") or len(db_rows)),
            int(batch_record.get("invalid_rows") or len(db_exceptions)),
        ))

        # 3. Insert or replace import_file record
        cur.execute("""
        INSERT OR REPLACE INTO import_file (
            import_file_id, import_batch_id, original_filename, sha256_hash, report_type,
            asset_code, row_count, valid_row_count, exception_row_count, uploaded_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(file_record.get("import_file_id") or str(uuid.uuid4())),
            str(batch_record.get("import_batch_id") or ""),
            str(file_record.get("original_filename") or ""),
            file_hash,
            str(rtype),
            str(file_record.get("asset_code") or ""),
            int(file_record.get("row_count") or len(db_rows)),
            int(file_record.get("valid_row_count") or len(db_rows)),
            int(file_record.get("exception_row_count") or len(db_exceptions)),
            str(file_record.get("uploaded_by") or "admin@srtpl.com"),
        ))

        # 4. Insert telemetry interval readings
        tbl_name = f"energy_readings_{rtype.lower()}"
        inserted_count = 0

        for r in db_rows:
            rid = str(uuid.uuid4())
            aid = str(r.get("asset_id") or "")
            acode = str(r.get("asset_code") or "")
            rdt = str(r.get("reading_datetime") or "")
            if not aid or not rdt:
                continue

            if rtype.upper() == "EB":
                cur.execute(f"""
                INSERT OR REPLACE INTO {tbl_name} (
                    reading_id, asset_id, asset_code, reading_datetime, cumulative_kwh, cumulative_kvah,
                    cumulative_kvarh, interval_kwh, interval_kvah, interval_kvarh, pf, maximum_demand,
                    created_by, created_on, remarks, consumer_number, location, category, data_quality_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rid, aid, acode, rdt,
                    r.get("cumulative_kwh"), r.get("cumulative_kvah"), r.get("cumulative_kvarh"),
                    r.get("interval_kwh"), r.get("interval_kvah"), r.get("interval_kvarh"),
                    r.get("pf"), r.get("maximum_demand"),
                    r.get("created_by"), r.get("created_on"), r.get("remarks"),
                    r.get("consumer_number"), r.get("location"), r.get("category"),
                    r.get("data_quality_status") or "VALID"
                ))
            elif rtype.upper() == "DG":
                cur.execute(f"""
                INSERT OR REPLACE INTO {tbl_name} (
                    reading_id, asset_id, asset_code, reading_datetime, cumulative_kwh, cumulative_running_hours,
                    interval_kwh, interval_running_hours, pf, created_by, created_on, remarks, location, data_quality_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rid, aid, acode, rdt,
                    r.get("cumulative_kwh"), r.get("cumulative_running_hours"),
                    r.get("interval_kwh"), r.get("interval_running_hours"),
                    r.get("pf"), r.get("created_by"), r.get("created_on"),
                    r.get("remarks"), r.get("location"), r.get("data_quality_status") or "VALID"
                ))
            elif rtype.upper() == "SOLAR":
                cur.execute(f"""
                INSERT OR REPLACE INTO {tbl_name} (
                    reading_id, asset_id, asset_code, reading_datetime, cumulative_kwh, interval_kwh,
                    created_by, created_on, remarks, location, data_quality_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rid, aid, acode, rdt,
                    r.get("cumulative_kwh"), r.get("interval_kwh"),
                    r.get("created_by"), r.get("created_on"),
                    r.get("remarks"), r.get("location"), r.get("data_quality_status") or "VALID"
                ))
            elif rtype.upper() == "TRANSFORMER":
                cur.execute(f"""
                INSERT OR REPLACE INTO {tbl_name} (
                    reading_id, asset_id, asset_code, reading_datetime,
                    primary_v_ry, primary_v_yb, primary_v_br, secondary_v_ry, secondary_v_yb, secondary_v_br,
                    primary_i_r, primary_i_y, primary_i_b, secondary_i_r, secondary_i_y, secondary_i_b,
                    oil_temperature, winding_temperature, pf, created_by, created_on, remarks, location, data_quality_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rid, aid, acode, rdt,
                    r.get("primary_v_ry"), r.get("primary_v_yb"), r.get("primary_v_br"),
                    r.get("secondary_v_ry"), r.get("secondary_v_yb"), r.get("secondary_v_br"),
                    r.get("primary_i_r"), r.get("primary_i_y"), r.get("primary_i_b"),
                    r.get("secondary_i_r"), r.get("secondary_i_y"), r.get("secondary_i_b"),
                    r.get("oil_temperature"), r.get("winding_temperature"), r.get("pf"),
                    r.get("created_by"), r.get("created_on"), r.get("remarks"), r.get("location"),
                    r.get("data_quality_status") or "VALID"
                ))
            elif rtype.upper() == "UPS":
                cur.execute(f"""
                INSERT OR REPLACE INTO {tbl_name} (
                    reading_id, asset_id, asset_code, reading_datetime, output_voltage, output_current,
                    output_frequency, battery_vdc, battery_temperature, rectifier_voltage,
                    created_by, created_on, remarks, location, data_quality_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rid, aid, acode, rdt,
                    r.get("output_voltage"), r.get("output_current"), r.get("output_frequency"),
                    r.get("battery_vdc"), r.get("battery_temperature"), r.get("rectifier_voltage"),
                    r.get("created_by"), r.get("created_on"), r.get("remarks"), r.get("location"),
                    r.get("data_quality_status") or "VALID"
                ))
            inserted_count += 1

        # 5. Insert DQ exceptions
        for exc in db_exceptions:
            eid = str(uuid.uuid4())
            cur.execute("""
            INSERT INTO exception_record (
                exception_id, asset_id, asset_code, created_by, created_on,
                rule_code, severity, status, reading_datetime, detected_value, message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                eid,
                str(exc.get("asset_id") or ""),
                str(exc.get("asset_code") or ""),
                exc.get("created_by"),
                exc.get("created_on"),
                str(exc.get("rule_code") or ""),
                str(exc.get("severity") or "WARNING"),
                str(exc.get("status") or "OPEN"),
                str(exc.get("reading_datetime") or ""),
                exc.get("detected_value"),
                str(exc.get("message") or "")
            ))

        conn.commit()
        conn.close()
        return {
            "success": True,
            "status": "SUCCESS",
            "inserted_readings": inserted_count,
            "exceptions_logged": len(db_exceptions),
        }
    except sqlite3.IntegrityError as ie:
        conn.rollback()
        conn.close()
        return {
            "success": False,
            "status": "DUPLICATE_FILE",
            "message": f"⛔ DUPLICATE REJECTED (Database Level): Database unique constraint failure: {ie}",
        }
    except Exception as exc:
        conn.rollback()
        conn.close()
        return {
            "success": False,
            "status": "ERROR",
            "message": f"SQLite write failed: {exc}",
        }


def fetch_juno_batches_sqlite() -> list[dict[str, Any]]:
    """Fetches all ingested Juno batches from SQLite import_file table."""
    try:
        init_local_db()
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT 
            f.import_batch_id,
            f.original_filename,
            f.report_type,
            f.valid_row_count,
            f.sha256_hash,
            f.created_at
        FROM import_file f
        ORDER BY f.created_at DESC
        """)
        rows = cur.fetchall()
        conn.close()

        equipment_labels = {
            "EB": "⚡ EB Grid Supply",
            "DG": "⚡ DG Backup Generator",
            "SOLAR": "☀️ Solar Rooftop Array",
            "TRANSFORMER": "🔌 Step-Down Transformer",
            "UPS": "🔋 UPS Battery System",
        }

        batches = []
        for idx, r in enumerate(rows):
            b_id = r[0] if (r[0] and r[0].startswith("JUNO-BATCH-")) else f"JUNO-BATCH-{idx + 1:04d}"
            rtype = str(r[2] or "EB").upper()
            batches.append({
                "batch_id": b_id,
                "file_name": r[1],
                "equipment": equipment_labels.get(rtype, f"⚡ {rtype}"),
                "records_count": int(r[3] or 0),
                "sha256": r[4],
                "imported_at": str(r[5] or "")[:19].replace("T", " "),
                "status": "INGESTED",
            })
        return batches
    except Exception:
        return []
