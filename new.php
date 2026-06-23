<?php
require_once __DIR__ . '/db.php';

$db = get_db();
$id = uniqid('c', false);
$now = time();

$stmt = $db->prepare("
    INSERT INTO concerts (id, name, date, respo, mandataire, state, progress, created_at, updated_at)
    VALUES (:id, :name, :date, :respo, '', '{}', 0, :now, :now)
");

$stmt->execute([
    ':id'    => $id,
    ':name'  => trim($_POST['name'] ?? ''),
    ':date'  => trim($_POST['date'] ?? ''),
    ':respo' => trim($_POST['respo'] ?? ''),
    ':now'   => $now,
]);

header("Location: concert/$id");
exit;
