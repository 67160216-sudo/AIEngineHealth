<?php
// predict_proxy.php
//   GET  -> ข้อมูลโมเดล (ช่วงค่าฟอร์ม, เกณฑ์สถานะ)  => FastAPI /engine/model-info
//   POST -> ประเมินความเสี่ยงเครื่องยนต์               => FastAPI /engine/predict
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

$fastapi_base_url = 'http://127.0.0.1:8000';

function forward($url, $method, $body = null) {
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    }
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);

    if ($error) {
        http_response_code(502);
        echo json_encode(['detail' => 'เชื่อมต่อ AI Server ไม่ได้: ' . $error]);
    } else {
        http_response_code($http_code);
        echo $response;
    }
    exit();
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    forward($fastapi_base_url . '/engine/model-info', 'GET');
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = json_decode(file_get_contents('php://input'), true);
    if (!is_array($data)) {
        http_response_code(400);
        echo json_encode(['detail' => 'ข้อมูลที่ส่งมาไม่ถูกต้อง (Invalid JSON)']);
        exit();
    }

    $payload = json_encode([
        'user_id'          => intval($data['user_id'] ?? 0),
        'vehicle_name'     => trim($data['vehicle_name'] ?? ''),
        'engine_rpm'       => $data['engine_rpm'] ?? null,
        'lub_oil_pressure' => $data['lub_oil_pressure'] ?? null,
        'fuel_pressure'    => $data['fuel_pressure'] ?? null,
        'coolant_pressure' => $data['coolant_pressure'] ?? null,
        'lub_oil_temp'     => $data['lub_oil_temp'] ?? null,
        'coolant_temp'     => $data['coolant_temp'] ?? null,
    ]);
    forward($fastapi_base_url . '/engine/predict', 'POST', $payload);
}

http_response_code(405);
echo json_encode(['detail' => 'Method not allowed']);
