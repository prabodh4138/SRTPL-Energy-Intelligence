import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from core.db_sync import (
    get_all_consumer_accounts,
    get_consumer_mapping_dict,
    save_consumer_account,
    batch_save_consumer_accounts,
    delete_consumer_account,
    get_correlated_consumer_reconciliation,
)


def test_default_consumer_accounts_contain_user_master_rows():
    df = get_all_consumer_accounts()
    assert not df.empty
    ac_list = df["consumer_account_no"].astype(str).tolist()

    # User specified accounts
    assert "411001070208" in ac_list
    assert "413001070099" in ac_list

    row_tp01 = df[df["consumer_account_no"] == "411001070208"].iloc[0]
    assert row_tp01["toll_plaza_id"] == "TP01"
    assert row_tp01["bill_type"] == "HT"
    assert row_tp01["asset_code"] == "SR-E-EM-EB-5-200"
    assert row_tp01["consumer_scope"] == "HIGHWAY"
    assert row_tp01["division_name"] == "SED"
    assert row_tp01["usage_type"] == "Street Light"
    assert float(row_tp01["sanctioned_load_kw"]) == 10.0
    assert row_tp01["location"] == "Ainthapalli"

    row_tp02 = df[df["consumer_account_no"] == "413001070099"].iloc[0]
    assert row_tp02["toll_plaza_id"] == "TP02"
    assert row_tp02["bill_type"] == "HT"
    assert row_tp02["asset_code"] == "SR-E-EM-EB-62-600"
    assert row_tp02["consumer_scope"] == "HIGHWAY"
    assert row_tp02["division_name"] == "JED"
    assert row_tp02["usage_type"] == "Street Light"
    assert float(row_tp02["sanctioned_load_kw"]) == 18.0
    assert row_tp02["location"] == "TANGARPALI"


def test_consumer_mapping_dict():
    mapping = get_consumer_mapping_dict()
    assert "411001070208" in mapping
    assert mapping["411001070208"]["asset_code"] == "SR-E-EM-EB-5-200"
    assert mapping["411001070208"]["location"] == "Ainthapalli"
    assert mapping["411001070208"]["toll_plaza_id"] == "TP01"


def test_save_and_delete_consumer_account():
    new_acc = {
        "consumer_account_no": "999001079999",
        "toll_plaza_id": "TP03",
        "bill_type": "HT",
        "asset_code": "SR-E-EM-EB-TEST",
        "consumer_scope": "HIGHWAY",
        "division_name": "RED",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 25.0,
        "location": "Rourkela Incomer",
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
        "bill_type": "HT",
        "asset_code": "SR-E-EM-EB-TEST2",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 30.0,
        "location": "Sambalpur Incomer",
        "is_active": True,
    }

    with patch("core.db_sync.get_supabase_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_table = MagicMock()
        mock_instance.table.return_value = mock_table
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
    assert "consumer_account_no" in corr_df.columns
    assert "discom_billed_kwh" in corr_df.columns
    assert "juno_meter_kwh" in corr_df.columns
    assert "kwh_variance" in corr_df.columns
    assert "variance_percentage" in corr_df.columns
