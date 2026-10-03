<?php
// history_proxy.php
//   GET    ?user_id=1                -> ประวัติการประเมิน   => FastAPI /engine/history/{user_id}
//   DELETE ?record_id=5&user_id=1    -> ลบรายการของตัวเอง  => FastAPI /engine/history/{record_id}?user_id=
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

$fastapi_base_url = 'http://127.0.0.1:8000';
$userId = isset($_GET['user_id']) ? intval($_GET['user_id']) : 0;

if ($userId <= 0) {
    http_response_code(400);
    echo json_encode(['detail' => 'ไม่พบ user_id']);
    exit();
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $url = $fastapi_base_url . '/engine/history/' . $userId;
    $method = 'GET';
} elseif ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
    $recordId = isset($_GET['record_id']) ? intval($_GET['record_id']) : 0;
    if ($recordId <= 0) {
        http_response_code(400);
        echo json_encode(['detail' => 'record_id ไม่ถูกต้อง']);
        exit();
    }
    $url = $fastapi_base_url . '/engine/history/' . $recordId . '?user_id=' . $userId;
    $method = 'DELETE';
} else {
    http_response_code(405);
    echo json_encode(['detail' => 'Method not allowed']);
    exit();
}

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
$response = curl_exec($ch);        // เรียกครั้งเดียว (แก้บั๊กเดิมที่เรียกซ้ำ 2 ครั้ง)
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($error) {
    http_response_code(502);
    echo json_encode(['detail' => 'เชื่อมต่อ AI Server ไม่ได้: ' . $error]);
} else {
    http_response_code($httpCode);
    echo $response;
}
