# Welcome Message
Write-Host "====================================================="
Write-Host "Welcome to the setup. This will set up the local virtual environment."
Write-Host "And then it will install all the required Python libraries."
Write-Host "You can rerun this without any issues."
Write-Host "-----------------------------------------------------"

# Check if .env folder exists
if (Test-Path ".env") {
    Write-Host "Enabling virtual environment"
} else {
    Write-Host "No virtual environment found. Please run setup.ps1 first."
    exit 1
}

# Activate virtual environment
Write-Host "Activating the virtual environment..."
& .\.env\Scripts\Activate.ps1

# Set environment variable
Write-Host "Setting environment variable..."
$ENV:ENV = "development"

# Run the Python script
Write-Host "Running main.py..."
python main.py

# Deactivate the virtual environment
Write-Host "Deactivating the virtual environment..."
Deactivate
