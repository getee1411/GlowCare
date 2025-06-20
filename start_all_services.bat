@echo off
echo Starting GlowCare Microservices...

echo Starting User Service on port 5001...
start cmd /k "cd user-service && python app.py"

echo Starting Appointment Service on port 5002...
start cmd /k "cd appointment-service && python app.py"

echo Starting Treatment Service on port 5003...
start cmd /k "cd treatment-service && python app.py"

echo Starting Payment Service on port 5004...
start cmd /k "cd payment-service && python app.py"

echo Waiting for services to start...
timeout /t 5

echo Starting Frontend HTTP Server on port 8000...
start cmd /k "python -m http.server 8000"

echo.   
echo =========================================
echo All GlowCare Services Started!
echo =========================================
echo Frontend: http://localhost:8000
echo User Service: http://localhost:5001
echo Appointment Service: http://localhost:5002  
echo Treatment Service: http://localhost:5003
echo Payment Service: http://localhost:5004
echo =========================================
echo.
echo Press any key to stop all services...
pause

echo Stopping all services...
taskkill /f /im python.exe
echo All services stopped.
pause