drop index if exists idx_readings_sensor_timestamp;
drop index if exists idx_sensors_module;

drop table if exists sensor_readings;
drop table if exists sensors;
drop table if exists modules;

pragma foreign_keys = ON;

create table if not exists modules (
    id text primary key,
    serial_no text unique not null,
    name text,
    created_at text not null
);

create table if not exists sensors (
    id integer primary key autoincrement,
    module_id text not null,
    sensor_type text not null,
    unit text,
    created_at text not null,
    serial_no text,

    foreign key (module_id)
        references modules(id)
        on delete cascade
);

create table if not exists sensor_readings (
    id integer primary key autoincrement,
    sensor_id text not null,
    value real not null,
    timestamp real not null,

    foreign key (sensor_id)
        references sensors(id)
        on delete cascade
);

create index if not exists idx_sensors_module
on sensors(module_id);

create index if not exists idx_readings_sensor_timestamp
on sensor_readings(sensor_id, timestamp desc);