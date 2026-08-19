import polars as pl
import pytest

from src.pipeline import rules

JURISDICTIONS = pl.DataFrame(
    {"bank": [1, 2, 3], "jurisdiction": ["domestic", "Germany", "domestic"]}
)


def txns(rows: list[dict]) -> pl.DataFrame:
    frame = pl.DataFrame(
        rows,
        schema={
            "txn_id": pl.UInt32,
            "ts": pl.String,
            "from_account": pl.String,
            "to_account": pl.String,
            "from_bank": pl.Int64,
            "to_bank": pl.Int64,
            "amount": pl.Float64,
            "currency": pl.String,
            "format": pl.String,
        },
    )
    return frame.with_columns(
        pl.col("ts").str.to_datetime("%Y/%m/%d %H:%M")
    ).with_columns(pl.col("ts").dt.date().alias(rules.PERIOD)).sort("ts", "txn_id")


def txn(txn_id, hour, sender, receiver, amount, currency="US Dollar", fmt="ACH", day=1):
    return {
        "txn_id": txn_id,
        "ts": f"2022/09/{day:02d} {hour:02d}:00",
        "from_account": f"1|{sender}",
        "to_account": f"1|{receiver}",
        "from_bank": 1,
        "to_bank": 1,
        "amount": amount,
        "currency": currency,
        "format": fmt,
    }


def test_loader_excludes_the_laundering_flag_and_self_transfers(tmp_path):
    source = tmp_path / "trans.csv"
    source.write_text(
        "Timestamp,From Bank,Account,To Bank,Account,Amount Received,Receiving Currency,"
        "Amount Paid,Payment Currency,Payment Format,Is Laundering\n"
        "2022/09/01 00:10,1,AAA,2,BBB,100.00,US Dollar,100.00,US Dollar,ACH,1\n"
        "2022/09/01 00:20,1,CCC,1,CCC,200.00,US Dollar,200.00,US Dollar,Reinvestment,0\n"
        "2022/09/20 00:30,1,DDD,2,EEE,300.00,US Dollar,300.00,US Dollar,ACH,0\n",
        encoding="utf-8",
    )
    loaded = rules.load_transactions(source, rules.Window())
    assert "Is Laundering" not in loaded.columns
    assert not [name for name in loaded.columns if "aunder" in name]
    # The self transfer and the transaction outside the window are both gone.
    assert loaded.height == 1
    assert loaded["from_account"].to_list() == ["1|AAA"]


def test_loader_maps_the_duplicated_account_column_to_both_sides(tmp_path):
    source = tmp_path / "trans.csv"
    source.write_text(
        "Timestamp,From Bank,Account,To Bank,Account,Amount Received,Receiving Currency,"
        "Amount Paid,Payment Currency,Payment Format,Is Laundering\n"
        "2022/09/01 00:10,7,AAA,9,BBB,100.00,US Dollar,100.00,US Dollar,ACH,0\n",
        encoding="utf-8",
    )
    loaded = rules.load_transactions(source, rules.Window())
    assert loaded["from_account"].item() == "7|AAA"
    assert loaded["to_account"].item() == "9|BBB"


def test_r1_fires_only_inside_the_band_below_the_threshold():
    frame = txns(
        [
            txn(0, 1, "A", "X", 9_500.0),
            txn(1, 2, "A", "Y", 9_600.0),
            txn(2, 3, "B", "X", 10_500.0),
            txn(3, 4, "B", "Y", 10_600.0),
            txn(4, 5, "C", "X", 100.0),
            txn(5, 6, "C", "Y", 200.0),
        ]
    )
    fired = rules.r1_structuring(frame, rules.Parameters())
    assert fired[rules.SUBJECT].to_list() == ["1|A"]
    assert '"count":2' in fired[rules.EVIDENCE].item()


def test_r2_requires_the_debit_to_follow_the_credit_within_the_window():
    forward = txns([txn(0, 1, "X", "A", 50_000.0), txn(1, 2, "A", "Y", 50_100.0)])
    assert rules.r2_rapid_movement(forward, rules.Parameters()).height == 1

    backward = txns([txn(0, 5, "A", "Y", 50_100.0), txn(1, 9, "X", "A", 50_000.0)])
    assert rules.r2_rapid_movement(backward, rules.Parameters()).height == 0

    too_late = txns([txn(0, 1, "X", "A", 50_000.0), txn(1, 22, "A", "Y", 50_100.0)])
    assert rules.r2_rapid_movement(too_late, rules.Parameters()).height == 0

    outside_tolerance = txns([txn(0, 1, "X", "A", 50_000.0), txn(1, 2, "A", "Y", 60_000.0)])
    assert rules.r2_rapid_movement(outside_tolerance, rules.Parameters()).height == 0


def test_r3_and_r4_count_distinct_counterparties_not_transactions():
    repeat_sender = txns([txn(i, i + 1, "A", "B", 100.0) for i in range(20)])
    params = rules.Parameters().replace(r3_min_originators=3, r4_min_beneficiaries=3)
    assert rules.r3_fan_in(repeat_sender, params).height == 0
    assert rules.r4_fan_out(repeat_sender, params).height == 0

    fan = txns([txn(i, i + 1, f"S{i}", "B", 100.0) for i in range(4)])
    fired = rules.r3_fan_in(fan, params)
    assert fired[rules.SUBJECT].to_list() == ["1|B"]
    assert '"counterparties":4' in fired[rules.EVIDENCE].item()


def test_r5_counts_whole_dollar_amounts_only():
    frame = txns([txn(0, 1, "A", "X", 500.0), txn(1, 2, "A", "Y", 700.0), txn(2, 3, "B", "X", 500.55)])
    fired = rules.r5_round_dollar(frame, rules.Parameters())
    assert fired[rules.SUBJECT].to_list() == ["1|A"]


def test_r6_cannot_fire_before_a_full_lookback_exists():
    burst = [txn(i, i, "A", f"X{i}", 100.0, day=1) for i in range(8)]
    params = rules.Parameters().replace(r6_lookback_periods=3, r6_activation_count=6)
    assert rules.r6_dormant_then_active(txns(burst), params).height == 0

    later = [txn(i + 100, i, "A", f"X{i}", 100.0, day=5) for i in range(8)]
    fired = rules.r6_dormant_then_active(txns(burst + later), params)
    assert fired.height == 1
    assert '"prior_count":0' in fired[rules.EVIDENCE].item()


def test_r7_requires_a_cross_jurisdiction_payment_in_a_corridor_instrument():
    same = txns(
        [
            {**txn(i, i, "A", "B", 5_000.0, fmt="Cash"), "from_bank": 1, "to_bank": 3}
            for i in range(4)
        ]
    )
    assert rules.r7_high_risk_corridor(same, JURISDICTIONS, rules.Parameters()).height == 0

    crossing = txns(
        [
            {**txn(i, i, "A", "B", 5_000.0, fmt="Cash"), "from_bank": 1, "to_bank": 2}
            for i in range(4)
        ]
    )
    assert rules.r7_high_risk_corridor(crossing, JURISDICTIONS, rules.Parameters()).height == 1

    wrong_instrument = txns(
        [
            {**txn(i, i, "A", "B", 5_000.0, fmt="Cheque"), "from_bank": 1, "to_bank": 2}
            for i in range(4)
        ]
    )
    assert rules.r7_high_risk_corridor(wrong_instrument, JURISDICTIONS, rules.Parameters()).height == 0


def test_r8_needs_prior_periods_and_uses_them_only():
    quiet = [txn(i, 1, "A", f"X{i}", 100.0, day=day) for i, day in enumerate((1, 2, 3))]
    spike = [txn(i + 50, i, "A", f"Y{i}", 100.0, day=4) for i in range(6)]
    noise = [txn(i + 200, 1, f"P{i}", f"Q{i}", 100.0, day=4) for i in range(3)]
    fired = rules.r8_peer_velocity(txns(quiet + spike + noise), JURISDICTIONS, rules.Parameters())
    assert fired[rules.SUBJECT].to_list() == ["1|A"]
    assert '"prior_periods":3' in fired[rules.EVIDENCE].item()

    without_history = rules.r8_peer_velocity(txns(spike + noise), JURISDICTIONS, rules.Parameters())
    assert without_history.height == 0


def test_run_rules_emits_the_alert_row_schema_and_is_deterministic():
    frame = txns(
        [txn(0, 1, "X", "A", 50_000.0), txn(1, 2, "A", "Y", 50_100.0), txn(2, 3, "A", "Z", 9_500.0)]
    )
    first = rules.run_rules(frame, JURISDICTIONS)
    second = rules.run_rules(frame, JURISDICTIONS)
    assert first.columns == rules.ALERT_COLUMNS
    assert first.equals(second)
    assert set(first[rules.RULE].to_list()) <= {f"R{n}" for n in range(1, 9)}


def test_alert_volume_counts_subject_periods_not_rule_rows():
    frame = txns([txn(0, 1, "X", "A", 50_000.0), txn(1, 2, "A", "Y", 50_100.0)])
    rows = pl.concat(
        [
            rules.r2_rapid_movement(frame, rules.Parameters()),
            rules.r2_rapid_movement(frame, rules.Parameters()).with_columns(
                pl.lit("R3").alias(rules.RULE)
            ),
        ]
    )
    volume = rules.alert_volume(rows)
    assert volume["alerts"].to_list() == [1]
    assert volume["rule_rows"].to_list() == [2]


def test_parameters_json_is_stable_and_order_independent():
    params = rules.Parameters()
    assert rules.parameters_json(params) == rules.parameters_json(rules.Parameters())
    assert rules.parameters_json(params) != rules.parameters_json(params.replace(r1_band=0.2))


@pytest.mark.parametrize("rule", ["r1_structuring", "r5_round_dollar"])
def test_threshold_rules_ignore_other_currencies(rule):
    frame = txns(
        [
            txn(0, 1, "A", "X", 9_500.0, currency="Euro"),
            txn(1, 2, "A", "Y", 9_600.0, currency="Euro"),
        ]
    )
    assert getattr(rules, rule)(frame, rules.Parameters()).height == 0
