# Docker Installation Guide for UEBA System on Windows

## Quick Installation Steps

### Option 1: Docker Desktop (Recommended)
1. **Download Docker Desktop for Windows:**
   - Visit: https://www.docker.com/products/docker-desktop/
   - Download the Windows installer

2. **Install Docker Desktop:**
   - Run the installer as Administrator
   - Enable WSL 2 integration (recommended)
   - Restart your computer when prompted

3. **Verify Installation:**
   ```powershell
   docker --version
   docker run hello-world
   ```

### Option 2: Docker Engine (Command Line Only)
1. **Install via PowerShell (as Administrator):**
   ```powershell
   # Enable Hyper-V and Containers features
   Enable-WindowsOptionalFeature -Online -FeatureName containers -All
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
   
   # Install Docker
   Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/microsoft/Windows-Containers/Main/helpful_tools/Install-DockerCE/install-docker-ce.ps1" -o install-docker-ce.ps1
   .\install-docker-ce.ps1
   ```

## System Requirements
- **Windows 10/11 Pro, Enterprise, or Education** (64-bit)
- **4GB RAM minimum** (8GB recommended)
- **Virtualization enabled** in BIOS
- **WSL 2** (Windows Subsystem for Linux)

## After Docker Installation

### Test Docker is Working:
```powershell
# Check Docker version
docker --version

# Test with hello-world
docker run hello-world

# Check if Docker daemon is running
docker info
```

### Ready for UEBA Deployment:
Once Docker is installed, you can run:
```powershell
# Navigate to UEBA directory
cd d:\ueba-system

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Deploy UEBA system
.\ueba-v1-windows.ps1 deploy
```

## Troubleshooting

### Common Issues:
1. **"Docker daemon not running"**
   - Start Docker Desktop application
   - Or run: `Start-Service docker`

2. **"WSL 2 installation incomplete"**
   - Install WSL 2 kernel update: https://aka.ms/wsl2kernel

3. **"Virtualization not enabled"**
   - Enable Hyper-V in Windows Features
   - Enable virtualization in BIOS settings

### Alternative: Podman
If Docker doesn't work, you can use Podman:
```powershell
# Install Podman
winget install RedHat.Podman
```

## Next Steps After Installation
1. ✅ **Python Dependencies** - Already installed
2. 🔧 **Docker Installation** - In progress
3. 🚀 **UEBA Deployment** - Ready to go once Docker is available

---
*Updated: October 6, 2025*