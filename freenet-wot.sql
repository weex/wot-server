PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE trusts (
    source integer,
    target integer,
    value float
);
COMMIT;
