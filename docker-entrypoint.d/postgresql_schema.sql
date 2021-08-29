BEGIN TRANSACTION;
CREATE TABLE users (
    id integer primary key,
    username varchar(64),
    public_key text,
    challenge varchar(64),
    created timestamp,
    verified timestamp,
    deleted timestamp,
    modified timestamp
);
CREATE TABLE follows (
    id integer primary key,
    user_id1 integer,
    user_id2 integer,
    created timestamp,
    deleted timestamp,
    modified timestamp,
    foreign key(user_id1) references users(id),
    foreign key(user_id2) references users(id)
);
CREATE TABLE ratings (
    id integer primary key,
    user_id integer,
    uri varchar(1024),
    value integer,
    created timestamp,
    deleted timestamp,
    modified timestamp,
    foreign key(user_id) references users(id)
);
CREATE TABLE log (
    created text,
    ip varchar(45),  /* max length of ipv6 address */
    action varchar(10),
    bytes integer,
    user_id varchar(64),
    message text,
    foreign key(user_id) references (address)
);
COMMIT;
