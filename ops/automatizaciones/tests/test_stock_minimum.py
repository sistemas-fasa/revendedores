from decimal import Decimal

import pytest

from ops.automatizaciones.stock_minimum import (
    apply_formula,
    calculate_minimum,
    child_minimum,
    compute_minima,
    formula_factor,
    net_sales_from_rows,
    parse_coverage_days,
    run_update,
)


def test_parse_coverage_days_accepts_positive_int_and_string():
    assert parse_coverage_days(14) == 14
    assert parse_coverage_days("7") == 7


def test_parse_coverage_days_rejects_zero_negative_and_text():
    for bad in (0, -3, "0", "abc", "", None, 2.5):
        with pytest.raises(ValueError):
            parse_coverage_days(bad)


def test_calculate_minimum_scales_with_coverage_days():
    net = Decimal("2048")
    assert calculate_minimum(net, 7) == 160  # 2048/90*7 = 159.3
    assert calculate_minimum(net, 14) == 319  # 2048/90*14 = 318.6
    assert calculate_minimum(net, 30) == 683  # 2048/90*30 = 682.7


def test_calculate_minimum_floor_one_and_none_without_sales():
    assert calculate_minimum(Decimal("0.2"), 14) == 1
    assert calculate_minimum(Decimal("0"), 14) is None
    assert calculate_minimum(Decimal("-5"), 14) is None


def test_calculate_minimum_rejects_bad_coverage():
    with pytest.raises(ValueError):
        calculate_minimum(Decimal("10"), 0)


def test_formula_factor_and_child_minimum():
    assert formula_factor("*0.5") == Decimal("0.5")
    assert formula_factor("/2.000") == Decimal("0.5")
    assert formula_factor("*3") == Decimal("3")
    assert formula_factor("") == Decimal("1")
    assert formula_factor("zzz") is None
    assert child_minimum(319, "*0.5") == 638
    assert child_minimum(319, "/2.000") == 638
    assert child_minimum(319, "*3") == 107
    assert child_minimum(None, "*0.5") is None
    assert child_minimum(10, "zzz") is None


def test_net_sales_from_rows_nets_credits_and_ignores_other_codes():
    rows = [
        ("0800247", "FS", Decimal("1905")),
        ("0800247", "F", Decimal("1609")),
        ("0800247", "C", Decimal("2096.75")),
        ("0800247", "X", Decimal("999")),
        ("0800247", None, Decimal("1")),
    ]
    assert net_sales_from_rows(rows) == {"0800247": Decimal("1417.25")}


def test_compute_minima_resolves_children_from_parent():
    net = {"0800247": Decimal("2048")}
    children = {"0800201": ("0800247", "*0.5"), "0800211": ("0800247", "*3")}
    result = compute_minima(net, children, 14)
    assert result["0800247"] == 319
    assert result["0800201"] == 638
    assert result["0800211"] == 107


def test_compute_minima_child_without_parent_sales_is_none():
    result = compute_minima({}, {"0800201": ("0800247", "*0.5")}, 14)
    assert result["0800201"] is None


def test_compute_minima_ignores_self_reference():
    result = compute_minima(
        {"5400014": Decimal("900")}, {"5400014": ("5400014", "/5.000")}, 14
    )
    assert result["5400014"] == 140


def test_run_update_dry_run_reports_without_writing():
    saved = {}

    def fake_save(minima, children):
        saved.update(minima)
        return len(minima)

    runtime = {
        "fetch_net_sales": lambda: {"A": Decimal("900")},  # 900/90*14 = 140
        "fetch_children": lambda: {"H": ("A", "*0.5")},  # 140/0.5 = 280
        "fetch_current": lambda keys: {"A": (Decimal("1"), ""), "H": (None, "")},
        "save_minima": fake_save,
    }
    result = run_update(14, dry_run=True, runtime=runtime)
    assert result["status"] == "dry_run"
    assert result["coverage_days"] == 14
    assert result["con_rotacion"] == 2
    assert result["cambiados"] == 2
    assert result["actualizados"] == 0
    assert saved == {}
    assert {item["articulo"]: item["nuevo"] for item in result["muestras"]} == {
        "A": 140,
        "H": 280,
    }


def test_run_update_writes_when_not_dry_run():
    runtime = {
        "fetch_net_sales": lambda: {"A": Decimal("900")},
        "fetch_children": lambda: {},
        "fetch_current": lambda keys: {},
        "save_minima": lambda minima, children: len(minima),
    }
    result = run_update(7, dry_run=False, runtime=runtime)
    assert result["status"] == "ok"
    assert result["coverage_days"] == 7
    assert result["actualizados"] == 1


def test_run_update_honours_custom_coverage_days():
    runtime = {
        "fetch_net_sales": lambda: {"A": Decimal("900")},  # 900/90*30 = 300
        "fetch_children": lambda: {},
        "fetch_current": lambda keys: {},
        "save_minima": lambda minima, children: 0,
    }
    result = run_update(30, dry_run=True, runtime=runtime)
    assert result["muestras"][0]["nuevo"] == 300
