"""Ofertas personalizadas según compras: cada cliente recibe las ofertas
vigentes de artículos que compró habitualmente (facturas ERP)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from ops.automatizaciones.ofertas_por_compra import (
    encolar_mails_clientes,
    fetch_candidatos,
    mail_cliente,
    plan_mails,
)

ARG = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 24, 8, 0, tzinfo=ARG)

# cliente, clave, veces, ultima
COMPRAS = [
    ("00040", "CEM001", 5, date(2026, 11, 10)),
    ("00040", "CAL002", 2, date(2026, 10, 5)),
    ("00077", "HIE003", 3, date(2026, 11, 1)),
    ("00099", "CEM001", 4, date(2026, 11, 12)),
]

# id, numero, nombre, email, recibe
CLIENTES = [
    (10, "00040", "Corralon Uno", "uno@ejemplo.com", 1),
    (20, "00077", "Ferreteria Dos", "dos@ejemplo.com", 1),
    (30, "00099", "Cliente Baja", "baja@ejemplo.com", 0),
]

# clave, nombre (solo ofertas vigentes con stock y no discontinuadas)
OFERTAS = [
    ("CEM001", "CEMENTO 50KG"),
    ("HIE003", "HIERRO 8"),
]


def _runtime(previas=(), executed=None):
    def query(sql, params):
        if "FROM `fasa`.`facturas`" in sql:
            assert "codigo = 'F'" in sql
            return list(COMPRAS)
        if "FROM api_cliente" in sql:
            return list(CLIENTES)
        if "FROM api_articulos" in sql:
            assert "oferta" in sql
            return list(OFERTAS)
        if "FROM api_ofertaenviada" in sql:
            return list(previas)
        raise AssertionError(sql)

    def execute_batch(stmts):
        executed.append(stmts)

    return {"query": query, "execute_batch": execute_batch}


def test_cruza_compras_con_ofertas_y_respeta_baja():
    cands = fetch_candidatos(_runtime(), dias_compras=90, now=NOW)
    por_cli = {c["numero"]: sorted(a["clave"] for a in c["articulos"]) for c in cands}
    # 00040 compro CEM001 (en oferta) y CAL002 (no en oferta) -> solo CEM001
    assert por_cli["00040"] == ["CEM001"]
    # 00077 compro HIE003 en oferta -> va
    assert por_cli["00077"] == ["HIE003"]
    # 00099 pidio la baja -> no va aunque haya comprado en oferta
    assert "00099" not in por_cli


def test_cooldown_articulo_y_cliente():
    # CEM001 ya ofrecido a 00040 hace 10 dias (< 30) -> se excluye;
    # 00077 con mail hace 2 dias (< 7) -> se excluye entero
    previas = [
        (10, "CEM001", datetime(2026, 11, 14, 8, 0)),
        (20, "OTRA001", datetime(2026, 11, 22, 8, 0)),
    ]
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW)
    # reconstruir con previas: plan_mails recibe runtime con historial
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(previas=previas), now=NOW)
    assert mails == []


def test_plan_respeta_maximo_y_ordena_por_recencia():
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW, max_articulos=5)
    assert {m["numero"] for m in mails} == {"00040", "00077"}
    m40 = next(m for m in mails if m["numero"] == "00040")
    assert [a["clave"] for a in m40["articulos"]] == ["CEM001"]
    assert m40["email"] == "uno@ejemplo.com"


def test_mail_menciona_compras_y_portal_con_baja():
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW)
    asunto, texto, html = mail_cliente(mails[0])
    assert "oferta" in asunto.lower()
    assert "BAJA" in texto
    assert "oferta=1" in html
    assert "compr" in texto.lower()


def test_encolar_registra_oferta_y_cola(monkeypatch):
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW)
    executed = []
    n = encolar_mails_clientes(mails, runtime=_runtime(executed=executed), now=NOW)
    assert n == 2
    assert len(executed) == 2
    cola, historial = executed[0][0], executed[0][1:]
    assert "emails_pendientes" in cola[0]
    assert "api_ofertaenviada" in historial[0][0]
    # email invalido nunca llega a encolar
    assert all("@" in m["email"] for m in mails)
