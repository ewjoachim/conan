<?php
function get_db(): PDO {
    $path = __DIR__ . '/data/conan.db';
    $db = new PDO('sqlite:' . $path);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    // WAL mode pour meilleures performances en lecture concurrente
    $db->exec('PRAGMA journal_mode=WAL');

    // Schéma
    $db->exec("
        CREATE TABLE IF NOT EXISTS concerts (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL DEFAULT '',
            date        TEXT NOT NULL DEFAULT '',
            respo       TEXT NOT NULL DEFAULT '',
            mandataire  TEXT NOT NULL DEFAULT '',
            state       TEXT NOT NULL DEFAULT '{}',
            progress    INTEGER NOT NULL DEFAULT 0,
            created_at  INTEGER NOT NULL,
            updated_at  INTEGER NOT NULL
        )
    ");

    return $db;
}
