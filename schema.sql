PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (
    id integer primary key,
    username varchar(64),
    public_key varchar(64),
    challenge varchar(32),
    created text,
    verified text,
    deleted text,
    modified text
);
CREATE TABLE follows (
    id integer primary key,
    user_id integer,
    user_id2 integer,
    created text,
    deleted text,
    modified text
);
CREATE TABLE ratings (
    id integer primary key,
    user_id integer,
    uri varchar(1024),
    value integer,
    created text,
    deleted text,
    modified text,
    foreign key(user_id) references users(user_id)
);
CREATE TABLE log (
    created text,
    ip varchar(45),  /* max length of ipv6 address */
    action varchar(10),
    bytes integer,
    user_id integer(64),
    message text,
    foreign key(user_id) references users(user_id)
);
COMMIT;
