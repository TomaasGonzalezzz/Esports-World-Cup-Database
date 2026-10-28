# como ejecutar

esto asume el postgres dockerizado de la guía 0, o sea el container
`servidor_postgresql` con la base `base_tp0`, usuario `admin`, contraseña
`admin123` y el puerto 5440 mapeado al 5432 del container.

si lo tenés levantado con otro nombre o con otra contraseña, cambialos en los
comandos de abajo.

## levantar el container

desde MI CARPETA LOCAL, la que tiene el `docker-compose.yaml`:

```
docker compose up -d
docker ps
```

`docker ps` tiene que mostrar `servidor_postgresql`.

## pasar los scripts al container

la guía mapea `data/tmp` de tu carpeta local a `/tmp` adentro del container, así
que alcanza con copiar los cuatro `.sql` ahí:

```
cp 0*.sql MI_CARPETA_LOCAL/data/tmp/
```

## crear la base y correr todo

los scripts crean sus propias tablas, así que van en una base aparte y no en
`base_tp0`:

```
docker exec servidor_postgresql psql -U admin -d base_tp0 -c "CREATE DATABASE ewc;"
docker exec servidor_postgresql psql -U admin -d ewc -v ON_ERROR_STOP=1 -f /tmp/01_crear_tablas.sql
docker exec servidor_postgresql psql -U admin -d ewc -v ON_ERROR_STOP=1 -f /tmp/02_usuarios_permisos.sql
docker exec servidor_postgresql psql -U admin -d ewc -v ON_ERROR_STOP=1 -f /tmp/03_carga_datos.sql
docker exec servidor_postgresql psql -U admin -d ewc -f /tmp/04_consultas.sql
```

el orden importa: `02` necesita que las tablas existan y `03` necesita las dos
cosas.

los cuatro se pueden correr de nuevo sobre una base ya cargada sin que rompan.
`01` hace `drop table if exists`, `02` borra y recrea los roles, y `03` hace
`truncate` antes de insertar.

## ver que quedó bien

```
docker exec servidor_postgresql psql -U admin -d ewc -c "\dt"
docker exec servidor_postgresql psql -U admin -d ewc -c "select count(*) from participaciones;"
```

tienen que salir 12 tablas y 72 participaciones.

## desde un cliente gráfico

igual que en la guía 0, pero apuntando a la base `ewc` en vez de `base_tp0`:

```
host      localhost
puerto    5440
base      ewc
usuario   admin
password  admin123
```

## probar los permisos

`02_usuarios_permisos.sql` crea cuatro roles. para ver que andan, entrá al psql y
usá `set role`, que cambia el rol sin reconectar:

```
docker exec -it servidor_postgresql psql -U admin -d ewc
```

y adentro:

```sql
set role prensa;
select count(*) from participaciones;   -- anda
select count(*) from sponsors_edicion;  -- permission denied
reset role;

set role organizacion;
select nombre_sponsor, espacio_camiseta from sponsors_equipo;  -- anda
select monto_anual from sponsors_equipo;                       -- permission denied
reset role;
```

la matriz completa de permisos sale con:

```sql
select grantee, table_name, privilege_type
from information_schema.role_table_grants
where grantee in ('admin_ewc','organizacion','sponsor','prensa')
order by grantee, table_name, privilege_type;
```

## regenerar los datos (opcional)

`03_carga_datos.sql` no está escrito a mano, lo genera `datos/generar_datos.py` a
partir de liquipedia. esto corre en tu máquina, no adentro del container:

```
cd datos
python3 generar_datos.py
```

la primera vez baja las páginas de la api y las deja cacheadas en `datos/raw/`.
como la caché va en el zip, no hace falta internet. deja los csv en `datos/csv/` y
reescribe `03_carga_datos.sql`.

los esports que se cargan se eligen en la constante `ESPORTS` del script. con
`ESPORTS = None` carga la competencia entera, 27 esports y 72 torneos.

## si no usás docker

con un postgres instalado local es más corto:

```
createdb ewc
psql -d ewc -v ON_ERROR_STOP=1 -f 01_crear_tablas.sql
psql -d ewc -v ON_ERROR_STOP=1 -f 02_usuarios_permisos.sql
psql -d ewc -v ON_ERROR_STOP=1 -f 03_carga_datos.sql
psql -d ewc -f 04_consultas.sql
```

lo probamos así sobre postgresql 14.17 en macos. no usamos nada que pida una
versión más nueva.

## limpiar

```
docker exec servidor_postgresql psql -U admin -d base_tp0 -c "DROP DATABASE ewc;"
```

los roles no se borran con la base porque son del cluster y no de una base en
particular. para sacarlos:

```
docker exec servidor_postgresql psql -U admin -d base_tp0 -c "DROP ROLE IF EXISTS u_coordinador, u_liquid, u_redbull, u_periodista, admin_ewc, organizacion, sponsor, prensa;"
```
