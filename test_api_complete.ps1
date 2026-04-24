# test_api_complete.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Flask API Test Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$BASE_URL = "http://127.0.0.1:5000/api/v1"
$ADMIN_EMAIL = "admin@example.com"
$ADMIN_PASSWORD = "admin123"

$TOTAL_TESTS = 0
$PASSED_TESTS = 0
$FAILED_TESTS = 0

function Test-Result {
    param(
        [string]$TestName,
        [int]$ExpectedStatus,
        [int]$ActualStatus,
        [string]$Description = ""
    )

    $script:TOTAL_TESTS++

    if ($ActualStatus -eq $ExpectedStatus) {
        $script:PASSED_TESTS++
        Write-Host "[PASS] $TestName" -ForegroundColor Green
        if ($Description) {
            Write-Host "       $Description" -ForegroundColor Gray
        }
        return $true
    } else {
        $script:FAILED_TESTS++
        Write-Host "[FAIL] $TestName" -ForegroundColor Red
        Write-Host "       Expected: $ExpectedStatus, Got: $ActualStatus" -ForegroundColor Red
        if ($Description) {
            Write-Host "       $Description" -ForegroundColor Gray
        }
        return $false
    }
}

function Show-Separator {
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
}

Show-Separator
Write-Host "1. Test Public Endpoints" -ForegroundColor Yellow
Show-Separator

Write-Host "Test 1.1: Get posts list..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/posts/" -Method GET -UseBasicParsing
    $status = $response.StatusCode
    $data = $response.Content | ConvertFrom-Json
    Test-Result "Get posts" 200 $status "Count: $($data.count)"
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Test-Result "Get posts" 200 $status
}

Write-Host "Test 1.2: Get users list..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/users/" -Method GET -UseBasicParsing
    $status = $response.StatusCode
    $data = $response.Content | ConvertFrom-Json
    Test-Result "Get users" 200 $status "Count: $($data.count)"
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Test-Result "Get users" 200 $status
}

Show-Separator
Write-Host "2. Test Authentication" -ForegroundColor Yellow
Show-Separator

Write-Host "Test 2.1: Get Token..." -ForegroundColor Cyan
$TOKEN = $null
try {
    $pair = "${ADMIN_EMAIL}:${ADMIN_PASSWORD}"
    $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
    $base64 = [System.Convert]::ToBase64String($bytes)
    $headers = @{ Authorization = "Basic $base64" }

    $response = Invoke-WebRequest -Uri "$BASE_URL/tokens/" -Method POST -Headers $headers -UseBasicParsing
    $status = $response.StatusCode
    $tokenData = $response.Content | ConvertFrom-Json
    $TOKEN = $tokenData.token

    if ($TOKEN) {
        Test-Result "Get Token" 200 $status "Token: $($TOKEN.Substring(0, 20))..."
    } else {
        Test-Result "Get Token" 200 $status "Token is empty"
    }
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Test-Result "Get Token" 200 $status "Check admin account exists"
}

Show-Separator
Write-Host "3. Test CRUD Operations" -ForegroundColor Yellow
Show-Separator

Write-Host "Test 3.1: Create post..." -ForegroundColor Cyan
$NEW_POST_ID = $null
try {
    $pair = "${ADMIN_EMAIL}:${ADMIN_PASSWORD}"
    $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
    $base64 = [System.Convert]::ToBase64String($bytes)
    $headers = @{
        Authorization = "Basic $base64"
        "Content-Type" = "application/json"
    }
    $body = @{ body = "Test post from script" } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$BASE_URL/posts/" -Method POST -Headers $headers -Body $body -UseBasicParsing
    $status = $response.StatusCode
    $postData = $response.Content | ConvertFrom-Json
    $NEW_POST_ID = $postData.id

    Test-Result "Create post" 201 $status "Post ID: $NEW_POST_ID"
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Test-Result "Create post" 201 $status
}

if ($NEW_POST_ID) {
    Write-Host "Test 3.2: Edit post..." -ForegroundColor Cyan
    try {
        $pair = "${ADMIN_EMAIL}:${ADMIN_PASSWORD}"
        $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
        $base64 = [System.Convert]::ToBase64String($bytes)
        $headers = @{
            Authorization = "Basic $base64"
            "Content-Type" = "application/json"
        }
        $body = @{ body = "Updated content" } | ConvertTo-Json

        $response = Invoke-WebRequest -Uri "$BASE_URL/posts/$NEW_POST_ID" -Method PUT -Headers $headers -Body $body -UseBasicParsing
        $status = $response.StatusCode
        Test-Result "Edit post" 200 $status
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        Test-Result "Edit post" 200 $status
    }

    Write-Host "Test 3.3: Delete post..." -ForegroundColor Cyan
    try {
        $pair = "${ADMIN_EMAIL}:${ADMIN_PASSWORD}"
        $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
        $base64 = [System.Convert]::ToBase64String($bytes)
        $headers = @{ Authorization = "Basic $base64" }

        $response = Invoke-WebRequest -Uri "$BASE_URL/posts/$NEW_POST_ID" -Method DELETE -Headers $headers -UseBasicParsing
        $status = $response.StatusCode
        Test-Result "Delete post" 200 $status
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        Test-Result "Delete post" 200 $status
    }
}

Show-Separator
Write-Host "4. Test Security" -ForegroundColor Yellow
Show-Separator

if ($TOKEN) {
    Write-Host "Test 4.1: Token cannot exchange for new token..." -ForegroundColor Cyan
    try {
        $pair = "${TOKEN}:"
        $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
        $base64 = [System.Convert]::ToBase64String($bytes)
        $headers = @{ Authorization = "Basic $base64" }

        $response = Invoke-WebRequest -Uri "$BASE_URL/tokens/" -Method POST -Headers $headers -UseBasicParsing
        $status = $response.StatusCode
        Test-Result "Token exchange limit" 401 $status "Should return 401"
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        Test-Result "Token exchange limit" 401 $status
    }
}

Write-Host "Test 4.2: Access protected endpoint without auth..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/comments/" -Method GET -UseBasicParsing
    $status = $response.StatusCode
    Test-Result "Unauth access" 401 $status "Should return 401"
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Test-Result "Unauth access" 401 $status
}

Write-Host "Test 4.3: Access non-existent resource..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/posts/99999" -Method GET -UseBasicParsing
    $status = $response.StatusCode
    Test-Result "404 handling" 404 $status
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Test-Result "404 handling" 404 $status
}

Show-Separator
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total: $TOTAL_TESTS" -ForegroundColor White
Write-Host "Passed: $PASSED_TESTS" -ForegroundColor Green
Write-Host "Failed: $FAILED_TESTS" -ForegroundColor $(if ($FAILED_TESTS -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($FAILED_TESTS -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed, check output above" -ForegroundColor Yellow
}

Write-Host ""
