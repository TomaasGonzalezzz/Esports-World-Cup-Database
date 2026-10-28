SELECT p.posicion_final,
       p.nombre_org,
       tp.puntos,
       tp.premio
FROM participaciones p
JOIN tabla_puntos tp
  ON  p.anio_edicion   = tp.anio_edicion
  AND p.nombre_esport  = tp.nombre_esport
  AND p.posicion_final = tp.posicion_final
WHERE p.anio_edicion  = 2024
  AND p.nombre_esport = 'Counter-Strike 2'
ORDER BY p.posicion_final;

SELECT s.nombre_sponsor,
       s.rubro,
       s.pais,
       se.categoria,
       se.monto_anual,
       se.duracion_contrato
FROM patrocinios_edicion pe
JOIN sponsors_edicion se ON pe.nombre_sponsor = se.nombre_sponsor
JOIN sponsors s          ON s.nombre_sponsor  = se.nombre_sponsor
WHERE pe.anio_edicion = 2024
ORDER BY se.monto_anual DESC;

SELECT o.nombre_org,
       o.pais,
       COUNT(*)        AS participaciones,
       SUM(tp.puntos)  AS puntos_totales,
       SUM(tp.premio)  AS premio_total
FROM participaciones p
JOIN organizaciones o ON p.nombre_org = o.nombre_org
JOIN tabla_puntos tp
  ON  p.anio_edicion   = tp.anio_edicion
  AND p.nombre_esport  = tp.nombre_esport
  AND p.posicion_final = tp.posicion_final
GROUP BY o.nombre_org, o.pais
ORDER BY puntos_totales DESC;

SELECT e.anio_edicion,
       e.pozo_total,
       COUNT(*)                     AS torneos,
       SUM(t.pozo)                  AS pozo_en_torneos,
       e.pozo_total - SUM(t.pozo)   AS fuera_de_torneos
FROM ediciones e
JOIN torneos t ON e.anio_edicion = t.anio_edicion
GROUP BY e.anio_edicion, e.pozo_total
ORDER BY e.anio_edicion;

SELECT t.anio_edicion,
       t.nombre_esport,
       t.cantidad_equipos          AS declarados,
       COUNT(p.nombre_org)         AS registrados
FROM torneos t
LEFT JOIN participaciones p
  ON  t.anio_edicion  = p.anio_edicion
  AND t.nombre_esport = p.nombre_esport
GROUP BY t.anio_edicion, t.nombre_esport, t.cantidad_equipos
ORDER BY t.anio_edicion, t.nombre_esport;

SELECT p.nombre_org,
       COUNT(*)                                      AS podios,
       COUNT(*) FILTER (WHERE p.posicion_final = 1)  AS titulos
FROM participaciones p
WHERE p.posicion_final <= 3
GROUP BY p.nombre_org
HAVING COUNT(*) > 1
ORDER BY podios DESC, titulos DESC, p.nombre_org;

SELECT e.nombre_esport,
       e.jugadores_por_equipo,
       COUNT(t.anio_edicion)        AS torneos,
       COALESCE(SUM(t.pozo), 0)     AS pozo_acumulado
FROM esports e
LEFT JOIN torneos t ON e.nombre_esport = t.nombre_esport
GROUP BY e.nombre_esport, e.jugadores_por_equipo
ORDER BY torneos DESC, e.nombre_esport;

SELECT o.nombre_org,
       o.pais,
       o.fecha_fundacion
FROM organizaciones o
LEFT JOIN patrocinios_equipo pe ON o.nombre_org = pe.nombre_org
WHERE pe.nombre_sponsor IS NULL
ORDER BY o.nombre_org;

SELECT s.nombre_sponsor,
       s.rubro,
       SUM(x.monto_anual) AS inversion_anual
FROM sponsors s
JOIN (
    SELECT nombre_sponsor, monto_anual FROM sponsors_equipo
    UNION ALL
    SELECT nombre_sponsor, monto_anual FROM sponsors_edicion
) x ON s.nombre_sponsor = x.nombre_sponsor
GROUP BY s.nombre_sponsor, s.rubro
ORDER BY inversion_anual DESC;

SELECT p.nombre_esport,
       p.nombre_org,
       SUM(tp.puntos) AS puntos_totales
FROM participaciones p
JOIN tabla_puntos tp
  ON  p.anio_edicion   = tp.anio_edicion
  AND p.nombre_esport  = tp.nombre_esport
  AND p.posicion_final = tp.posicion_final
GROUP BY p.nombre_esport, p.nombre_org
HAVING SUM(tp.puntos) > (
    SELECT AVG(sub.total)
    FROM (
        SELECT SUM(tp2.puntos) AS total
        FROM participaciones p2
        JOIN tabla_puntos tp2
          ON  p2.anio_edicion   = tp2.anio_edicion
          AND p2.nombre_esport  = tp2.nombre_esport
          AND p2.posicion_final = tp2.posicion_final
        WHERE p2.nombre_esport = p.nombre_esport
        GROUP BY p2.nombre_org
    ) sub
)
ORDER BY p.nombre_esport, puntos_totales DESC;

SELECT o.nombre_org,
       o.pais
FROM organizaciones o
WHERE NOT EXISTS (
    SELECT 1
    FROM esports e
    WHERE NOT EXISTS (
        SELECT 1
        FROM equipos q
        WHERE q.nombre_org    = o.nombre_org
          AND q.nombre_esport = e.nombre_esport
    )
)
ORDER BY o.nombre_org;

SELECT s.nombre_sponsor,
       pe.nombre_org,
       pe.nombre_esport,
       COUNT(*)              AS participaciones,
       SUM(tp.puntos)        AS puntos,
       MIN(p.posicion_final) AS mejor_puesto
FROM patrocinios_equipo pe
JOIN sponsors s        ON s.nombre_sponsor = pe.nombre_sponsor
JOIN participaciones p ON  p.nombre_org    = pe.nombre_org
                       AND p.nombre_esport = pe.nombre_esport
JOIN tabla_puntos tp
  ON  tp.anio_edicion   = p.anio_edicion
  AND tp.nombre_esport  = p.nombre_esport
  AND tp.posicion_final = p.posicion_final
GROUP BY s.nombre_sponsor, pe.nombre_org, pe.nombre_esport
ORDER BY puntos DESC, s.nombre_sponsor;
