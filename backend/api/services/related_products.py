from django.db import connections


def get_related_products_for_article(article_code, limit=3):
    code = str(article_code or "").strip()
    if not code:
        return []

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 3
    limit = max(1, min(limit, 10))

    sql = """
        WITH sugerencias AS (
            SELECT
                prm.producto_relacionado AS clave,
                CAST(999999 - prm.prioridad AS DECIMAL(18,6)) AS score,
                CAST(1.000000 AS DECIMAL(18,6)) AS confianza,
                0 AS origen_orden,
                prm.prioridad AS prioridad,
                'MANUAL' AS origen
            FROM productos_relacionados_manual prm
            WHERE prm.producto_base = %s
              AND prm.activo = 1

            UNION ALL

            SELECT
                pr.producto_relacionado AS clave,
                pr.score,
                COALESCE(NULLIF(pr.confianza_ponderada, 0), pr.confianza) AS confianza,
                1 AS origen_orden,
                100000 AS prioridad,
                'AUTO' AS origen
            FROM productos_relacionados pr
            WHERE pr.producto_base = %s
              AND pr.activo = 1
        ),
        deduplicadas AS (
            SELECT
                s.clave,
                s.score,
                s.confianza,
                s.origen,
                s.origen_orden,
                s.prioridad,
                ROW_NUMBER() OVER (
                    PARTITION BY s.clave
                    ORDER BY s.origen_orden ASC, s.prioridad ASC, s.score DESC
                ) AS rn
            FROM sugerencias s
        )
        SELECT
            d.clave,
            st.UNIDAD AS unidad,
            st.DETALLE AS detalle,
            d.origen
        FROM deduplicadas d
        JOIN stock st ON TRIM(st.CLAVE) = d.clave
        JOIN articulo ar ON TRIM(ar.CLAVE) = d.clave
        WHERE d.rn = 1
          AND st.VISIBLE = 'S'
          AND COALESCE(ar.FISICO, 'S') <> 'N'
        ORDER BY d.origen_orden ASC, d.prioridad ASC, d.score DESC, d.clave ASC
        LIMIT %s
    """

    try:
        with connections["fasa"].cursor() as cursor:
            cursor.execute(sql, [code, code, limit])
            rows = cursor.fetchall()
    except Exception:
        return []

    return [
        {
            "clave": str(row[0]).strip(),
            "unidad": str(row[1] or "").strip(),
            "detalle": str(row[2] or "").strip(),
            "origen": str(row[3] or "").strip(),
        }
        for row in rows
    ]
