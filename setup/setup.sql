drop table alerts;
drop table rules;
drop table events;
drop table users;

drop type processing_status;

CREATE TYPE processing_status AS ENUM ('new', 'in-progress', 'done');

create table users (
    user_id serial primary key,
    first_name varchar(255),
    last_name varchar(255),
    program varchar(20)
);

CREATE TABLE events (
    event_id serial primary key, 
    user_id varchar(20), 
    time timestamp with time zone, 
    type varchar(20), 
    description varchar(255), 
    current_status processing_status default 'new');

CREATE TABLE rules (
    rule_id serial primary key, 
    rule_priority smallint, 
    summary varchar(255), 
    expr text, 
    msg varchar(255));

create table alerts (
    alert_id serial primary key,
    user_id integer references users(user_id),
    time timestamp with time zone,
    rule_id integer references rules(rule_id),
    msg varchar(255)
);
