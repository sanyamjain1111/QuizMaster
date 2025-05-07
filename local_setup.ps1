# Welcome Message
Write-Host "====================================================="
Write-Host "Welcome to the setup. This will set up the local virtual environment."
Write-Host "And then it will install all the required Python libraries."
Write-Host "You can rerun this without any issues."
Write-Host "-----------------------------------------------------"

# Check if .env folder exists
if (Test-Path ".env") {
    Write-Host ".env folder exists. Installing using pip"
} else {
    Write-Host "Creating .env folder and setting up virtual environment"
    python -m venv .env
}

# Activate the virtual environment
Write-Host "Activating the virtual environment..."
& .\.env\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..."
pip install --upgrade pip

# Install required libraries
Write-Host "Installing required libraries from requirements.txt..."
pip install -r requirements.txt

# Deactivate the virtual environment
Write-Host "Deactivating the virtual environment..."
Deactivate
