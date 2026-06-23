<?php
header('Content-Type: application/json');
require_once __DIR__ . '/../db.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$body = json_decode(file_get_contents('php://input'), true);
$id   = $body['id'] ?? null;

if (!$id) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing concert id']);
    exit;
}

$db = get_db();

$stmt = $db->prepare("
    UPDATE concerts SET
        name       = :name,
        date       = :date,
        respo      = :respo,
        mandataire = :mandataire,
        state      = :state,
        progress   = :progress,
        updated_at = :now
    WHERE id = :id
");

$affected = $stmt->execute([
    ':id'          => $id,
    ':name'        => $body['name']       ?? '',
    ':date'        => $body['date']       ?? '',
    ':respo'       => $body['respo']      ?? '',
    ':mandataire'  => $body['mandataire'] ?? '',
    ':state'       => json_encode($body['state'] ?? [], JSON_UNESCAPED_UNICODE),
    ':progress'    => $body['progress']   ?? 0,
    ':now'         => time(),
]);

if ($stmt->rowCount() === 0) {
    http_response_code(404);
    echo json_encode(['error' => 'Concert not found']);
    exit;
}

echo json_encode(['ok' => true]);
