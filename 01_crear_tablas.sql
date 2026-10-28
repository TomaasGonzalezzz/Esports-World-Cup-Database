DROP TABLE IF EXISTS
  participaciones, patrocinios_equipo, patrocinios_edicion, tabla_puntos,
  sponsors_equipo, sponsors_edicion, torneos, equipos,
  sponsors, esports, ediciones, organizaciones CASCADE;

create table esports (
	nombre_esport varchar(80) primary key,
	genero varchar(80) not null,
	desarrolladora varchar(80) not null,
	jugadores_por_equipo smallint not null check (jugadores_por_equipo > 0)
);

create table ediciones (
	anio_edicion smallint primary key,
	ciudad varchar(80) not null,
	fecha_inicio date unique not null,
	fecha_fin date,
	pozo_total numeric not null check (pozo_total > 0),
	
	constraint chk_fechas_inicio_fin check (fecha_fin > fecha_inicio),
	constraint chk_anio_edicion check (extract(year from fecha_inicio) = anio_edicion)
);

create table organizaciones (
	nombre_org varchar(80) primary key,
	pais varchar(80) not null,
	fecha_fundacion date
);

create table sponsors (
	nombre_sponsor varchar(80) primary key,
	rubro varchar(80) not null,
	pais varchar(80) not null
);

create table equipos (
	nombre_org varchar(80) not null,
	nombre_esport varchar(80) not null,
	fecha_creacion date,
	
	constraint pk_equipos primary key (nombre_org, nombre_esport),
	
	constraint fk_equipos_org foreign key (nombre_org)
		references organizaciones (nombre_org)
		on delete restrict on update cascade,
	
	constraint fk_equipos_esport foreign key (nombre_esport)
		references esports (nombre_esport)
		on delete restrict on update cascade
	);

create table torneos (
	anio_edicion smallint not null,
	nombre_esport varchar(80) not null,
	fecha_inicio date not null,
	fecha_fin date not null,
	pozo numeric not null check (pozo > 0),
	formato varchar(80),
	cantidad_equipos smallint not null check (cantidad_equipos > 0),
	
	constraint chk_fecha_inicio_fin check (fecha_fin > fecha_inicio),
	
	constraint pk_torneos primary key (anio_edicion, nombre_esport),
	
	constraint fk_torneos_ediciones foreign key (anio_edicion)
		references ediciones (anio_edicion)
		on delete restrict on update cascade,
	
	constraint fk_torneos_esports foreign key (nombre_esport)
		references esports (nombre_esport)
		on delete restrict on update cascade
);

create table sponsors_equipo (
	nombre_sponsor varchar(80) primary key,
	monto_anual numeric not null check (monto_anual > 0),
	duracion_contrato smallint not null check (duracion_contrato > 0),
	espacio_camiseta varchar(80) not null,
	
	constraint fk_sponsors_equipo_sponsors foreign key (nombre_sponsor)
		references sponsors (nombre_sponsor)
		on delete restrict on update cascade
);

create table sponsors_edicion (
	nombre_sponsor varchar(80) primary key,
	monto_anual numeric not null check (monto_anual > 0),
	duracion_contrato smallint not null check (duracion_contrato > 0),
	categoria varchar(80) not null,
	
	constraint fk_sponsors_edicion_sponsors foreign key (nombre_sponsor)
		references sponsors (nombre_sponsor)
		on delete restrict on update cascade
);

create table patrocinios_edicion (
	nombre_sponsor varchar(80) not null,
	anio_edicion smallint not null,
	
	constraint pk_patrocinios_edicion primary key (nombre_sponsor, anio_edicion),
	
	constraint fk_patrocinios_edicion_sponsors_edicion foreign key (nombre_sponsor)
		references sponsors_edicion (nombre_sponsor)
		on delete restrict on update cascade,
	
	constraint fk_patrocinios_edicion_ediciones foreign key (anio_edicion)
		references ediciones (anio_edicion)
		on delete restrict on update cascade
);

create table patrocinios_equipo (
	nombre_sponsor varchar(80) not null,
	nombre_org varchar(80) not null,
	nombre_esport varchar(80) not null,
	
	constraint pk_patrocinios_equipo primary key (nombre_sponsor, nombre_org, nombre_esport),
	
	constraint fk_patrocinios_equipo_sponsors_equipo foreign key (nombre_sponsor)
		references sponsors_equipo (nombre_sponsor)
		on delete restrict on update cascade,
	
	constraint fk_patrocinios_equipo_equipos foreign key (nombre_org, nombre_esport)
		references equipos (nombre_org, nombre_esport)
		on delete restrict on update cascade
);

create table tabla_puntos (
	anio_edicion smallint not null,
	nombre_esport varchar(80) not null,
	posicion_final smallint not null check (posicion_final > 0),
	puntos integer not null,
	premio numeric not null,
	
	constraint pk_tabla_puntos primary key (anio_edicion, nombre_esport, posicion_final),
	
	constraint fk_tabla_puntos_torneos foreign key (anio_edicion, nombre_esport)
		references torneos (anio_edicion, nombre_esport)
		on delete restrict on update cascade
);

create table participaciones (
	nombre_org varchar(80) not null,
	nombre_esport varchar(80) not null,
	anio_edicion smallint not null,
	posicion_final smallint not null check (posicion_final > 0),
	
	constraint pk_participaciones primary key (nombre_org, nombre_esport, anio_edicion),
	
	constraint fk_participaciones_tabla_puntos foreign key (anio_edicion, nombre_esport, posicion_final)
		references tabla_puntos (anio_edicion, nombre_esport, posicion_final)
		on delete restrict on update cascade,
	
	constraint fk_participaciones_equipos foreign key (nombre_org, nombre_esport)
		references equipos (nombre_org, nombre_esport)
		on delete restrict on update cascade,
	
	constraint fk_participaciones_torneos foreign key (anio_edicion, nombre_esport)
		references torneos (anio_edicion, nombre_esport)
		on delete restrict on update cascade
);
