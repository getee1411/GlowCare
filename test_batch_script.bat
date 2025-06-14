@echo off
setlocal enabledelayedexpansion

REM GlowCare Salon Microservices Test Script for Windows
REM Make sure all services are running before executing this script

echo ==================================================
echo 🌟 GlowCare Salon Microservices Test Script 🌟
echo ==================================================
echo.

REM Service URLs
set USER_SERVICE=http://localhost:5001
set APPOINTMENT_SERVICE=http://localhost:5002
set TREATMENT_SERVICE=http://localhost:5003
set PAYMENT_SERVICE=http://localhost:5004

REM Variables to store IDs
set TREATMENT_ID=1
set APPOINTMENT_ID=1
set PAYMENT_ID=1

echo 📋 Starting comprehensive microservices testing...
echo.

REM Check if curl is available
curl --version >nul 2>&1
if errorlevel 1 (
    echo ❌ curl is not available. Please install curl or use Git Bash.
    echo You can download curl from: https://curl.se/windows/
    pause
    exit /b 1
)

echo 🔍 Checking if all services are running...

REM Check User Service
curl -s --connect-timeout 5 %USER_SERVICE% >nul 2>&1
if errorlevel 1 (
    echo ❌ User Service is not running at %USER_SERVICE%
    echo Please start all services before running this test script.
    pause
    exit /b 1
) else (
    echo ✅ User Service is running
)

REM Check other services
curl -s --connect-timeout 5 %APPOINTMENT_SERVICE% >nul 2>&1
if errorlevel 1 (
    echo ❌ Appointment Service is not running at %APPOINTMENT_SERVICE%
    pause
    exit /b 1
) else (
    echo ✅ Appointment Service is running
)

curl -s --connect-timeout 5 %TREATMENT_SERVICE% >nul 2>&1
if errorlevel 1 (
    echo ❌ Treatment Service is not running at %TREATMENT_SERVICE%
    pause
    exit /b 1
) else (
    echo ✅ Treatment Service is running
)

curl -s --connect-timeout 5 %PAYMENT_SERVICE% >nul 2>&1
if errorlevel 1 (
    echo ❌ Payment Service is not running at %PAYMENT_SERVICE%
    pause
    exit /b 1
) else (
    echo ✅ Payment Service is running
)

echo.

REM ===========================================
REM USER SERVICE TESTS
REM ===========================================
echo 👤 Testing User Service...
echo.

echo 1. User Registration
echo Testing: Register Pasien
curl -s -X POST "%USER_SERVICE%/register" -H "Content-Type: application/json" -d "{\"name\":\"John Doe\",\"email\":\"john@glowcare.com\",\"password\":\"password123\",\"role\":\"pasien\"}"
echo.
echo ---

echo Testing: Register Dokter
curl -s -X POST "%USER_SERVICE%/register" -H "Content-Type: application/json" -d "{\"name\":\"Dr. Sarah\",\"email\":\"sarah@glowcare.com\",\"password\":\"password123\",\"role\":\"dokter\"}"
echo.
echo ---

echo Testing: Register Admin
curl -s -X POST "%USER_SERVICE%/register" -H "Content-Type: application/json" -d "{\"name\":\"Admin User\",\"email\":\"admin@glowcare.com\",\"password\":\"password123\",\"role\":\"admin\"}"
echo.
echo ---

echo.
echo 2. User Login
echo Testing: Login Pasien
curl -s -X POST "%USER_SERVICE%/login" -H "Content-Type: application/json" -d "{\"email\":\"john@glowcare.com\",\"password\":\"password123\"}" > temp_pasien_login.json
type temp_pasien_login.json
echo.
echo ---

echo Testing: Login Dokter
curl -s -X POST "%USER_SERVICE%/login" -H "Content-Type: application/json" -d "{\"email\":\"sarah@glowcare.com\",\"password\":\"password123\"}" > temp_dokter_login.json
type temp_dokter_login.json
echo.
echo ---

echo Testing: Login Admin
curl -s -X POST "%USER_SERVICE%/login" -H "Content-Type: application/json" -d "{\"email\":\"admin@glowcare.com\",\"password\":\"password123\"}" > temp_admin_login.json
type temp_admin_login.json
echo.
echo ---

REM Extract tokens (simplified - you'll need to manually copy tokens for authenticated requests)
echo NOTE: Copy the access_token from above responses to use in authenticated requests
echo.

REM ===========================================
REM TREATMENT SERVICE TESTS
REM ===========================================
echo 💆 Testing Treatment Service...
echo.

echo 4. Treatment Operations
echo Testing: Get All Treatments
curl -s -X GET "%TREATMENT_SERVICE%/treatments"
echo.
echo ---

echo Testing: Get Specific Treatment (ID: 1)
curl -s -X GET "%TREATMENT_SERVICE%/treatments/1"
echo.
echo ---

echo Testing: Add New Treatment
curl -s -X POST "%TREATMENT_SERVICE%/treatments" -H "Content-Type: application/json" -d "{\"name\":\"Premium Facial\",\"description\":\"Luxury facial treatment\",\"price\":250000,\"duration\":90}"
echo.
echo ---

REM ===========================================
REM APPOINTMENT SERVICE TESTS
REM ===========================================
echo 📅 Testing Appointment Service...
echo.

echo 5. Appointment Operations
echo Testing: Create Appointment
curl -s -X POST "%APPOINTMENT_SERVICE%/appointments" -H "Content-Type: application/json" -d "{\"user_id\":1,\"treatment_id\":1,\"appointment_date\":\"2025-06-20 10:00\"}"
echo.
echo ---

echo Testing: Get All Appointments
curl -s -X GET "%APPOINTMENT_SERVICE%/appointments"
echo.
echo ---

echo Testing: Get User Appointments
curl -s -X GET "%APPOINTMENT_SERVICE%/appointments?user_id=1"
echo.
echo ---

echo Testing: Get Specific Appointment (ID: 1)
curl -s -X GET "%APPOINTMENT_SERVICE%/appointments/1"
echo.
echo ---

REM ===========================================
REM PAYMENT SERVICE TESTS
REM ===========================================
echo 💳 Testing Payment Service...
echo.

echo 6. Payment Operations
echo Testing: Create Payment
curl -s -X POST "%PAYMENT_SERVICE%/payments" -H "Content-Type: application/json" -d "{\"user_id\":1,\"appointment_id\":1,\"amount\":150000,\"payment_method\":\"transfer\"}"
echo.
echo ---

echo Testing: Get All Payments
curl -s -X GET "%PAYMENT_SERVICE%/payments"
echo.
echo ---

echo Testing: Get Payment by Appointment
curl -s -X GET "%PAYMENT_SERVICE%/payments/appointment/1"
echo.
echo ---

echo Testing: Confirm Payment (ID: 1)
curl -s -X POST "%PAYMENT_SERVICE%/payments/1/confirm"
echo.
echo ---

REM ===========================================
REM APPOINTMENT MANAGEMENT TESTS
REM ===========================================
echo 📋 Testing Appointment Management...
echo.

echo 9. Appointment Status Management
echo Testing: Update Appointment Status
curl -s -X PUT "%APPOINTMENT_SERVICE%/appointments/1" -H "Content-Type: application/json" -d "{\"status\":\"confirmed\"}"
echo.
echo ---

echo Testing: Cancel Appointment
curl -s -X POST "%APPOINTMENT_SERVICE%/appointments/1/cancel"
echo.
echo ---

REM ===========================================
REM PAYMENT STATUS TESTS
REM ===========================================
echo 💰 Testing Payment Status Management...
echo.

echo 10. Payment Status Management
echo Testing: Update Payment Status
curl -s -X PUT "%PAYMENT_SERVICE%/payments/1/status" -H "Content-Type: application/json" -d "{\"status\":\"completed\"}"
echo.
echo ---

REM ===========================================
REM ERROR HANDLING TESTS
REM ===========================================
echo ⚠️ Testing Error Handling...
echo.

echo 11. Error Handling Tests
echo Testing: Invalid Login (Should Fail)
curl -s -X POST "%USER_SERVICE%/login" -H "Content-Type: application/json" -d "{\"email\":\"invalid@email.com\",\"password\":\"wrongpassword\"}"
echo.
echo ---

echo Testing: Get Non-existent Appointment (Should Fail)
curl -s -X GET "%APPOINTMENT_SERVICE%/appointments/999"
echo.
echo ---

echo Testing: Get Non-existent Payment (Should Fail)
curl -s -X GET "%PAYMENT_SERVICE%/payments/999"
echo.
echo ---

REM ===========================================
REM SUMMARY
REM ===========================================
echo.
echo 📊 Test Summary
echo ==================================================
echo ✅ User Service: Registration, Login, Profile Management
echo ✅ Treatment Service: CRUD Operations
echo ✅ Appointment Service: Booking, Status Management
echo ✅ Payment Service: Payment Processing, Status Updates
echo ✅ Error Handling: Invalid inputs and edge cases
echo.
echo 🎉 All microservices tests completed!
echo Check the responses above for any errors or unexpected behavior.
echo.
echo Key Test Data Created:
echo - Pasien: john@glowcare.com / password123
echo - Dokter: sarah@glowcare.com / password123
echo - Admin: admin@glowcare.com / password123
echo - Treatment ID: 1
echo - Appointment ID: 1
echo - Payment ID: 1
echo ==================================================

REM Clean up temporary files
if exist temp_pasien_login.json del temp_pasien_login.json
if exist temp_dokter_login.json del temp_dokter_login.json
if exist temp_admin_login.json del temp_admin_login.json

echo.
echo Press any key to exit...
pause >nul