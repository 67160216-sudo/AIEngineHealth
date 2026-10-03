<?php
// simulate_proxy.php
//   POST {points:[{...6 ค่า...}]} -> FastAPI /engine/simulate (ไม่บันทึกลงฐานข้อมูล)
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['detail' => 'Method not allowed']);
    exit();
}

$body = file_get_contents('php://input');
if (!is_array(json_decode($body, true))) {
    http_response_code(400);
    echo json_encode(['detail' => 'ข้อมูลที่ส่งมาไม่ถูกต้อง (Invalid JSON)']);
    exit();
}

$ch = curl_init('http://127.0.0.1:8000/engine/simulate');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
$response = curl_exec($ch);
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
