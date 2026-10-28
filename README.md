# Esports World Cup · Base de datos relacional

Trabajo práctico grupal de **I312 — Bases de Datos**, Universidad de San Andrés.
Diseño e implementación de una base de datos PostgreSQL para consultar ediciones,
torneos, organizaciones, equipos, resultados, premios y patrocinios de la Esports World Cup.

**Autores:** García, González, Puentes y Turkie, según la portada del informe original.  
**Fecha de la entrega:** 18 de septiembre de 2026.

## Documentación

- [Consigna de la materia](docs/consigna.pdf).
- [Informe original](informe.pdf): requerimientos, modelo entidad-interrelación,
  modelo relacional, decisiones de diseño y limitaciones.
- [Guía original de ejecución](COMO_EJECUTAR.md): instalación utilizada por el grupo,
  ejecución de scripts y comprobación de permisos.

## Contenido

| Archivo o carpeta | Función |
| --- | --- |
| `01_crear_tablas.sql` | Crea las 12 tablas, claves y restricciones de integridad. |
| `02_usuarios_permisos.sql` | Define roles de administración, organización, sponsor y prensa; incluye usuarios de demostración. |
| `03_carga_datos.sql` | Carga los datos preparados en la entrega. |
| `04_consultas.sql` | 12 consultas con joins, agregaciones, subconsultas y filtros. |
| `datos/generar_datos.py` | Genera CSV y SQL a partir de la caché de Liquipedia y correcciones manuales. |
| `datos/raw/` | Respuestas originales almacenadas de Liquipedia. |
| `datos/manual/` | Datos complementarios, equivalencias y excepciones. |
| `datos/csv/` | Tablas exportadas en formato CSV. |

La selección guardada contiene **3 ediciones (2024–2026), 3 esports, 9 torneos,
40 organizaciones, 47 equipos y 72 participaciones**. Son datos de la entrega,
no una sincronización actual de la competencia. La caché contiene material
adicional; el generador selecciona Counter-Strike 2, League of Legends y Rocket League.

## Ejecutar

El grupo documentó PostgreSQL **14.17** en macOS. Para esta publicación se
preservaron los scripts; no se volvió a ejecutar PostgreSQL.

Usar una instancia PostgreSQL de práctica aislada y un usuario administrador
con permisos para crear bases y roles. Los scripts `01` y `02` eliminan y recrean
tablas y roles; `03` vacía tablas antes de cargar datos. Los roles son del clúster,
por lo que una base nueva en una instancia compartida no los aísla.
Las contraseñas incluidas son ejemplos de la entrega para uso local.

Desde la raíz del repositorio, con PostgreSQL y sus comandos disponibles:

```sh
createdb -U postgres ewc
psql -U postgres -d ewc -v ON_ERROR_STOP=1 -f 01_crear_tablas.sql
psql -U postgres -d ewc -v ON_ERROR_STOP=1 -f 02_usuarios_permisos.sql
psql -U postgres -d ewc -v ON_ERROR_STOP=1 -f 03_carga_datos.sql
psql -U postgres -d ewc -v ON_ERROR_STOP=1 -f 04_consultas.sql
```

Adaptar usuario, host y puerto a la instalación. La guía original también incluye
los comandos para el contenedor de la guía 0 de la materia; ese entorno externo
no forma parte de esta entrega.

Comprobar la carga:

```sh
psql -U postgres -d ewc -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
psql -U postgres -d ewc -c "SELECT count(*) FROM participaciones;"
```

Los resultados esperados son **12 tablas** y **72 participaciones**.
La guía original muestra pruebas de acceso con `SET ROLE` para cada perfil.

## Regenerar los datos (opcional)

El SQL de carga ya está incluido: no hace falta ejecutar Python para crear la base.
El generador utiliza Python 3 y únicamente módulos de su biblioteca estándar:

```sh
python datos/generar_datos.py
```

Este comando reescribe los CSV y `03_carga_datos.sql`. Utiliza los archivos de caché
cuando existen; si se amplía la selección y faltan páginas, puede consultar Liquipedia.
Conviene ejecutarlo en una copia o rama para comparar los cambios con la entrega.

## Conservación y autoría

Los scripts, datos, guía e informe se mantienen con sus bytes originales.
Se agregaron este README, la consigna, reglas para Git y un
[registro de procedencia con hashes SHA-256](docs/procedencia.json).
Se excluyeron archivos auxiliares de macOS. No se reconstruyó un historial previo
ni se atribuyeron aportes individuales que no constan en la entrega.

El código corresponde al trabajo grupal; la consigna pertenece a la cátedra y los
datos de origen provienen de Liquipedia y de los complementos documentados por el grupo.
No se incorpora una licencia adicional sobre estos materiales.
