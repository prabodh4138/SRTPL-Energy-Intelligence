import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import streamlit as st
from core.db_sync import (
    get_all_consumer_accounts,
    get_consumer_mapping_dict,
    save_consumer_account,
    batch_save_consumer_accounts,
    delete_consumer_account,
    get_correlated_consumer_reconciliation,
)


@pytest.fixture(autouse=True)
def clean_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


def test_default_consumer_accounts_60_total_and_ht_lt_split():
    df = get_all_consumer_accounts()
    assert not df.empty
    assert len(df) == 60, f"Expected exactly 60 consumers, found {len(df)}"

    # Assert exactly 3 HT and 57 LT accounts
    ht_df = df[df["bill_type"] == "HT"]
    lt_df = df[df["bill_type"] == "LT"]
    assert len(ht_df) == 3, f"Expected exactly 3 HT accounts, found {len(ht_df)}"
    assert len(lt_df) == 57, f"Expected exactly 57 LT accounts, found {len(lt_df)}"

    # Assert plaza distribution: 20 each (1 HT, 19 LT)
    for plz in ["TP01", "TP02", "TP03"]:
        plz_df = df[df["toll_plaza_id"] == plz]
        assert len(plz_df) == 20, f"Expected 20 accounts for {plz}, found {len(plz_df)}"
        assert len(plz_df[plz_df["bill_type"] == "HT"]) == 1, f"Expected 1 HT account for {plz}"
        assert len(plz_df[plz_df["bill_type"] == "LT"]) == 19, f"Expected 19 LT accounts for {plz}"

    # Verify the 3 specific HT Substation Incomers
    ht_ac_list = ht_df["consumer_account_no"].astype(str).tolist()
    assert "416000000110" in ht_ac_list, "TP01 HT incomer missing"
    assert "413000000002" in ht_ac_list, "TP02 HT incomer missing"
    assert "813000000281" in ht_ac_list, "TP03 HT incomer missing"

    row_tp01_ht = df[df["consumer_account_no"] == "416000000110"].iloc[0]
    assert row_tp01_ht["toll_plaza_id"] == "TP01"
    assert row_tp01_ht["bill_type"] == "HT"
    assert row_tp01_ht["consumer_scope"] in ["PLAZA", "TOLL_PLAZA"]
    assert float(row_tp01_ht["sanctioned_load_kw"]) == 120.0

    row_tp02_ht = df[df["consumer_account_no"] == "413000000002"].iloc[0]
    assert row_tp02_ht["toll_plaza_id"] == "TP02"
    assert row_tp02_ht["bill_type"] == "HT"
    assert row_tp02_ht["consumer_scope"] in ["PLAZA", "TOLL_PLAZA"]
    assert float(row_tp02_ht["sanctioned_load_kw"]) == 120.0

    row_tp03_ht = df[df["consumer_account_no"] == "813000000281"].iloc[0]
    assert row_tp03_ht["toll_plaza_id"] == "TP03"
    assert row_tp03_ht["bill_type"] == "HT"
    assert row_tp03_ht["consumer_scope"] in ["PLAZA", "TOLL_PLAZA"]
    assert float(row_tp03_ht["sanctioned_load_kw"]) == 120.0

    # Verify key LT accounts (Street Lighting connections are LT)
    row_tp01_lt = df[df["consumer_account_no"] == "411001070208"].iloc[0]
    assert row_tp01_lt["toll_plaza_id"] == "TP01"
    assert row_tp01_lt["bill_type"] == "LT"
    assert row_tp01_lt["asset_code"] == "SR-E-EM-EB-5-200"
    assert row_tp01_lt["consumer_scope"] == "HIGHWAY"
    assert row_tp01_lt["division_name"] == "SED SAMBALPUR"
    assert row_tp01_lt["usage_type"] == "Street Light"
    assert float(row_tp01_lt["sanctioned_load_kw"]) == 10.0

    row_tp02_lt = df[df["consumer_account_no"] == "413001070099"].iloc[0]
    assert row_tp02_lt["toll_plaza_id"] == "TP02"
    assert row_tp02_lt["bill_type"] == "LT"
    assert row_tp02_lt["asset_code"] == "SR-E-EM-EB-62-600"
    assert row_tp02_lt["consumer_scope"] == "HIGHWAY"
    assert row_tp02_lt["division_name"] == "JED JHARSUGUDA"
    assert row_tp02_lt["usage_type"] == "Street Light"
    assert float(row_tp02_lt["sanctioned_load_kw"]) == 18.0

    row_tp03_lt = df[df["consumer_account_no"] == "812001070018"].iloc[0]
    assert row_tp03_lt["toll_plaza_id"] == "TP03"
    assert row_tp03_lt["bill_type"] == "LT"
    assert row_tp03_lt["division_name"] == "SED SUNDARAGADA"
    assert float(row_tp03_lt["sanctioned_load_kw"]) == 28.0


def test_consumer_mapping_dict():
    mapping = get_consumer_mapping_dict()
    assert "411001070208" in mapping
    assert mapping["411001070208"]["asset_code"] == "SR-E-EM-EB-5-200"
    assert mapping["411001070208"]["toll_plaza_id"] == "TP01"
    assert mapping["411001070208"]["bill_type"] == "LT"

    assert "416000000110" in mapping
    assert mapping["416000000110"]["bill_type"] == "HT"


def test_save_and_delete_consumer_account():
    new_acc = {
        "consumer_account_no": "999001079999",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-TEST",
        "consumer_scope": "HIGHWAY",
        "division_name": "RED",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 25.0,
        "location": "Rourkela Corridor",
        "is_active": True,
    }

    # Test local / session state persistence
    with patch("core.db_sync.get_supabase_client", return_value=None):
        res = save_consumer_account(new_acc)
        assert res["status"] == "SUCCESS"
        assert res["payload"]["consumer_account_no"] == "999001079999"

        # Check it is in get_all_consumer_accounts
        df = get_all_consumer_accounts()
        assert "999001079999" in df["consumer_account_no"].astype(str).tolist()

        # Delete it
        del_res = delete_consumer_account("999001079999")
        assert del_res["status"] == "DELETED"
        df_after = get_all_consumer_accounts()
        assert "999001079999" not in df_after["consumer_account_no"].astype(str).tolist()


def test_save_consumer_account_cloud():
    cloud_acc = {
        "consumer_account_no": "888001078888",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-TEST2",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 30.0,
        "location": "Sambalpur Corridor",
        "is_active": True,
    }

    with patch("core.db_sync.get_supabase_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_table = MagicMock()
        mock_instance.table.return_value = mock_table
        mock_instance.schema.return_value.table.return_value = mock_table
        mock_table.upsert.return_value.execute.return_value = MagicMock()
        mock_table.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[cloud_acc]
        )

        res = save_consumer_account(cloud_acc)
        assert res["status"] == "SUCCESS"
        assert res["cloud_synced"] is True

        df = get_all_consumer_accounts()
        assert "888001078888" in df["consumer_account_no"].astype(str).tolist()


def test_correlated_consumer_reconciliation():
    corr_df = get_correlated_consumer_reconciliation()
    assert not corr_df.empty
    assert len(corr_df) == 60, f"Expected 60 accounts in reconciliation, found {len(corr_df)}"
    assert "consumer_account_no" in corr_df.columns
    assert "discom_billed_kwh" in corr_df.columns
    assert "juno_meter_kwh" in corr_df.columns
    assert "kwh_variance" in corr_df.columns
    assert "variance_percentage" in corr_df.columns
