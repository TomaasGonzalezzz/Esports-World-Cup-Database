DO $$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['admin_ewc','organizacion','sponsor','prensa',
                           'u_coordinador','u_liquid','u_redbull','u_periodista'] LOOP
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      EXECUTE format('DROP OWNED BY %I', r);
    END IF;
  END LOOP;
END $$;

DROP ROLE IF EXISTS
  u_coordinador, u_liquid, u_redbull, u_periodista,
  admin_ewc, organizacion, sponsor, prensa;

CREATE ROLE admin_ewc    NOLOGIN;
CREATE ROLE organizacion NOLOGIN;
CREATE ROLE sponsor      NOLOGIN;
CREATE ROLE prensa       NOLOGIN;

GRANT USAGE ON SCHEMA public TO admin_ewc, organizacion, sponsor, prensa;

GRANT SELECT, INSERT, UPDATE, DELETE
  ON ALL TABLES IN SCHEMA public
  TO admin_ewc;

GRANT SELECT ON
    esports, ediciones, torneos, organizaciones, equipos,
    participaciones, tabla_puntos, sponsors,
    patrocinios_edicion, patrocinios_equipo
  TO prensa;

GRANT SELECT ON
    esports, ediciones, torneos, organizaciones, sponsors,
    participaciones, tabla_puntos,
    patrocinios_edicion, patrocinios_equipo
  TO organizacion;

GRANT SELECT, INSERT, UPDATE ON equipos TO organizacion;

GRANT SELECT (nombre_sponsor, espacio_camiseta)
  ON sponsors_equipo TO organizacion;

GRANT SELECT ON
    esports, ediciones, torneos, organizaciones, equipos,
    participaciones, tabla_puntos, sponsors,
    sponsors_edicion, sponsors_equipo,
    patrocinios_edicion, patrocinios_equipo
  TO sponsor;

CREATE ROLE u_coordinador LOGIN PASSWORD 'ewc_admin_2026';
CREATE ROLE u_liquid      LOGIN PASSWORD 'liquid_2026';
CREATE ROLE u_redbull     LOGIN PASSWORD 'redbull_2026';
CREATE ROLE u_periodista  LOGIN PASSWORD 'prensa_2026';

GRANT admin_ewc    TO u_coordinador;
GRANT organizacion TO u_liquid;
GRANT sponsor      TO u_redbull;
GRANT prensa       TO u_periodista;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO admin_ewc;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO prensa;
