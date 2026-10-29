# Esports World Cup Database

Base de datos relacional en **PostgreSQL** para explorar torneos, equipos, organizaciones, premios y patrocinios de la Esports World Cup. El proyecto comprende el modelo de datos, su implementación SQL, permisos por rol y consultas.

**García, González, Puentes y Turkie** · Bases de Datos, UdeSA · septiembre de 2026.

[Modelo y decisiones de diseño](informe.pdf) · [Guía de ejecución](COMO_EJECUTAR.md)

## Qué contiene

- 12 tablas con claves y restricciones de integridad.
- Roles para administración, organización, sponsors y prensa.
- 12 consultas con joins, agregaciones y subconsultas.
- Un generador en Python con caché de Liquipedia y datos complementarios del equipo.

La selección de la entrega abarca tres ediciones (2024–2026), tres esports, nueve torneos, 40 organizaciones, 47 equipos y 72 participaciones. Es una selección histórica, no una actualización en vivo.

## Crear y consultar la base

Usar una **instancia PostgreSQL de práctica aislada**. Los scripts recrean tablas y roles, y vacían tablas antes de cargar; los roles afectan a todo el clúster. Las contraseñas del SQL son ejemplos locales.

~~~sh
createdb -U postgres ewc
psql -U postgres -d ewc -v ON_ERROR_STOP=1 -f 01_crear_tablas.sql
psql -U postgres -d ewc -v ON_ERROR_STOP=1 -f 02_usuarios_permisos.sql
psql -U postgres -d ewc -v ON_ERROR_STOP=1 -f 03_carga_datos.sql
psql -U postgres -d ewc -v ON_ERROR_STOP=1 -f 04_consultas.sql
~~~

El grupo utilizó PostgreSQL 14.17 en macOS. Los datos preparados ya están incluidos: no hace falta ejecutar el generador para cargar la base.

En **datos/** están los CSV, la caché y el generador. El [detalle técnico](DOCUMENTACION.md) explica la selección de datos, comprobaciones de carga y regeneración. No se reejecutó PostgreSQL durante la preparación del portfolio.
