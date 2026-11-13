from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from ops.automatizaciones.resumen_busquedas_precios import (
    _cuantos,
    fetch_report,
    format_html,
    format_text,
    normalize_query,
    parse_date,
    resolve_window,
)

ARG = ZoneInfo("America/Argentina/Buenos_Aires")


def test_normalize_query_collapses_spaces():
    assert normalize_query("  angulo   3/4  ") == "angulo 3/4"
    assert normalize_query(None) == ""
    assert normalize_query("045") == "045"


def test_cuantos_singular_y_plural():
    assert _cuantos(1, "usuario", "usuarios") == "1 usuario"
    assert _cuantos(2, "usuario", "usuarios") == "2 usuarios"
    assert _cuantos(0, "vez", "veces") == "0 veces"


def test_parse_date_rejects_bad_format():
    with pytest.raises(ValueError):
        parse_date("12-11-2026")
    with pytest.raises(ValueError):
        parse_date("no-fecha")


def test_resolve_window_today_ends_now():
    now = datetime(2026, 11, 13, 20, 0, tzinfo=ARG)
    start, end = resolve_window(datetime(2026, 11, 13, 10, 0, tzinfo=ARG), now=now)
    assert (start.hour, start.minute) == (0, 0)
    assert end == now


def test_resolve_window_past_day_is_full_day():
    start, end = resolve_window(
        datetime(2026, 11, 12, 15, 0, tzinfo=ARG),
        now=datetime(2026, 11, 13, 20, 0, tzinfo=ARG),
    )
    assert (end - start).total_seconds() == 86400


def _fake_runtime():
    def query(sql, params):
        if "FROM api_busqueda WHERE" in sql and "TRIM(query)" in sql and "GROUP BY" in sql:
            return [("  angulo 3/4 ", 5, 3), ("045", 2, 2)]
        if "FROM api_busqueda WHERE" in sql:
            return [(7, 4, 2)]
        if "FROM api_busqueda b" in sql:
            return [("06166", "Cliente Uno", "00040", 4)]
        if "FROM api_consultaprecio WHERE" in sql:
            return [(9, 3, 2)]
        if "LEFT JOIN api_articulos" in sql:
            return [("0800057", "CHAPA CANAL", 4, 2)]
        if "FROM api_consultaprecio cp" in sql and "GROUP BY au.username" in sql:
            return [("06166", "Cliente Uno", "00040", 6, 3),
                    ("invitado1", "", "", 3, 2)]
        if "ac.id IS NULL" in sql:
            return [("invitado1",)]
        raise AssertionError(sql)
    return {"query": query}


def test_fetch_report_shapes_sections():
    start = datetime(2026, 11, 13, 0, 0, tzinfo=ARG)
    end = datetime(2026, 11, 13, 20, 0, tzinfo=ARG)
    report = fetch_report(start, end, runtime=_fake_runtime())
    assert report["busquedas"]["total"] == 7
    assert report["busquedas"]["top"][0]["query"] == "angulo 3/4"
    assert report["precios"]["total"] == 9
    assert report["precios"]["top"][0]["clave"] == "0800057"
    assert report["precios"]["sin_cliente"] == ["invitado1"]
    text = format_text(report)
    assert "angulo 3/4" in text
    assert "0800057" in text
    assert "SIN ficha de cliente" in text
    html = format_html(report)
    assert "0800057" in html
    assert "invitado1" in html


def test_fetch_report_empty_period():
    runtime = {"query": lambda sql, params: [(0, 0, 0)] if "COUNT" in sql and "GROUP" not in sql else []}
    start = datetime(2026, 11, 13, 0, 0, tzinfo=ARG)
    end = datetime(2026, 11, 13, 20, 0, tzinfo=ARG)
    report = fetch_report(start, end, runtime=runtime)
    assert "Sin búsquedas" in format_text(report)
    assert "Sin clics" in format_text(report)
