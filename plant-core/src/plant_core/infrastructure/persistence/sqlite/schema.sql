pragma foreign_keys = ON;

create table if not exists nodes (
    node_id text primary key,
    node_kind text not null,
    display_name text not null,
    serial_no text unique,
    status text not null,
    last_seen_at text,
    created_at text not null,
    updated_at text not null
);

create table if not exists device_states (
    node_id text not null,
    device_type text not null,
    is_active integer not null,
    level real,
    reason text,
    updated_at text not null,
    primary key (node_id, device_type),
    foreign key (node_id) references nodes(node_id) on delete cascade
);

create table if not exists sensors (
    sensor_id text primary key,
    node_id text not null,
    sensor_type text not null,
    channel text,
    unit text not null,
    display_name text,
    created_at text not null,
    unique (node_id, sensor_type, channel),
    foreign key (node_id) references nodes(node_id) on delete cascade
);

create table if not exists sensor_readings (
    reading_id text primary key,
    sensor_id text not null,
    node_id text not null,
    sensor_type text not null,
    value real not null,
    unit text not null,
    status text not null,
    recorded_at text not null,
    foreign key (sensor_id) references sensors(sensor_id) on delete cascade,
    foreign key (node_id) references nodes(node_id) on delete cascade
);

create table if not exists latest_sensor_readings (
    sensor_id text primary key,
    reading_id text not null,
    node_id text not null,
    sensor_type text not null,
    value real not null,
    unit text not null,
    status text not null,
    recorded_at text not null,
    foreign key (sensor_id) references sensors(sensor_id) on delete cascade,
    foreign key (reading_id) references sensor_readings(reading_id) on delete cascade
);

create table if not exists command_logs (
    command_id text primary key,
    node_id text not null,
    command_type text not null,
    device_type text,
    correlation_id text,
    requested_by text not null,
    payload_json text not null,
    status text not null,
    message text,
    requested_at text not null,
    accepted_at text,
    finished_at text,
    foreign key (node_id) references nodes(node_id) on delete restrict
);

create table if not exists event_logs (
    event_id text primary key,
    node_id text not null,
    event_type text not null,
    correlation_id text,
    command_id text,
    payload_json text not null,
    recorded_at text not null,
    foreign key (node_id) references nodes(node_id) on delete restrict,
    foreign key (command_id) references command_logs(command_id) on delete set null
);

create index if not exists idx_nodes_status
on nodes(status);

create index if not exists idx_sensors_node
on sensors(node_id);

create index if not exists idx_sensor_readings_sensor_time
on sensor_readings(sensor_id, recorded_at desc);

create index if not exists idx_latest_sensor_readings_node
on latest_sensor_readings(node_id);

create index if not exists idx_command_logs_node_time
on command_logs(node_id, requested_at desc);

create index if not exists idx_command_logs_correlation
on command_logs(correlation_id);

create index if not exists idx_event_logs_node_time
on event_logs(node_id, recorded_at desc);

create index if not exists idx_event_logs_command
on event_logs(command_id);
