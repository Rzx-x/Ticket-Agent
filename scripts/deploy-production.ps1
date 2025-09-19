# PowerShell Deployment Script for OmniDesk AI (Windows)
# This script deploys the OmniDesk AI solution in production mode

param(
    [string]$Domain = "localhost",
    [string]$Email = "",
    [switch]$SkipBackup = $false,
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting OmniDesk AI Production Deployment" -ForegroundColor Green
Write-Host "Domain: $Domain" -ForegroundColor Cyan
Write-Host "=" * 50

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow
    
    $missing = @()
    
    if (-not (Test-Command "docker")) {
        $missing += "Docker"
    }
    
    if (-not (Test-Command "docker-compose")) {
        $missing += "Docker Compose"
    }
    
    if ($missing.Count -gt 0) {
        Write-Host "❌ Missing prerequisites: $($missing -join ', ')" -ForegroundColor Red
        Write-Host "Please install the missing components and try again." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ All prerequisites found" -ForegroundColor Green
}

# Function to setup environment
function Setup-Environment {
    Write-Host "🔧 Setting up environment..." -ForegroundColor Yellow
    
    if (-not (Test-Path ".env.production")) {
        Write-Host "❌ .env.production file not found!" -ForegroundColor Red
        Write-Host "Please copy .env.production.example to .env.production and configure it." -ForegroundColor Red
        exit 1
    }
    
    # Create necessary directories
    $dirs = @("logs", "data/postgres", "data/qdrant", "data/redis", "monitoring/grafana/data")
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "📁 Created directory: $dir" -ForegroundColor Green
        }
    }
    
    Write-Host "✅ Environment setup complete" -ForegroundColor Green
}

# Function to backup existing data
function Backup-Data {
    if ($SkipBackup) {
        Write-Host "⏭️ Skipping backup (--SkipBackup flag used)" -ForegroundColor Yellow
        return
    }
    
    Write-Host "💾 Creating backup..." -ForegroundColor Yellow
    
    if (Test-Path "scripts/backup.sh") {
        Write-Host "Running backup script..." -ForegroundColor Cyan
        # Convert to Unix-style path for WSL or Git Bash
        if (Test-Command "wsl") {
            wsl bash scripts/backup.sh
        } elseif (Test-Command "bash") {
            bash scripts/backup.sh
        } else {
            Write-Host "⚠️ Bash not available, skipping automated backup" -ForegroundColor Yellow
            Write-Host "Please manually backup your data before proceeding" -ForegroundColor Yellow
            if (-not $Force) {
                $response = Read-Host "Continue without backup? (y/N)"
                if ($response -ne "y" -and $response -ne "Y") {
                    Write-Host "Deployment cancelled" -ForegroundColor Red
                    exit 1
                }
            }
        }
    } else {
        Write-Host "⚠️ Backup script not found, skipping..." -ForegroundColor Yellow
    }
}

# Function to deploy services
function Deploy-Services {
    Write-Host "🐳 Deploying services..." -ForegroundColor Yellow
    
    # Stop existing services
    Write-Host "Stopping existing services..." -ForegroundColor Cyan
    docker-compose -f docker-compose.prod.yml down --remove-orphans 2>$null
    
    # Pull latest images
    Write-Host "Pulling latest images..." -ForegroundColor Cyan
    docker-compose -f docker-compose.prod.yml pull
    
    # Build and start services
    Write-Host "Building and starting services..." -ForegroundColor Cyan
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # Wait for services to be ready
    Write-Host "Waiting for services to be ready..." -ForegroundColor Cyan
    Start-Sleep -Seconds 30
    
    Write-Host "✅ Services deployed" -ForegroundColor Green
}

# Function to verify deployment
function Test-Deployment {
    Write-Host "🔍 Verifying deployment..." -ForegroundColor Yellow
    
    if (Test-Path "scripts/verify-deployment.sh") {
        if (Test-Command "wsl") {
            $env:DOMAIN = $Domain
            $env:PROTOCOL = "http"
            wsl bash scripts/verify-deployment.sh
        } elseif (Test-Command "bash") {
            $env:DOMAIN = $Domain
            $env:PROTOCOL = "http"
            bash scripts/verify-deployment.sh
        } else {
            Write-Host "⚠️ Verification script requires Bash, running basic checks..." -ForegroundColor Yellow
            Test-BasicEndpoints
        }
    } else {
        Write-Host "⚠️ Verification script not found, running basic checks..." -ForegroundColor Yellow
        Test-BasicEndpoints
    }
}

# Function to test basic endpoints
function Test-BasicEndpoints {
    $endpoints = @(
        @{url="http://$Domain/"; name="Frontend"},
        @{url="http://$Domain/api/health"; name="Backend Health"},
        @{url="http://$Domain/api/docs"; name="API Docs"}
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            Write-Host "Testing $($endpoint.name)..." -ForegroundColor Cyan
            $response = Invoke-WebRequest -Uri $endpoint.url -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $($endpoint.name): OK" -ForegroundColor Green
            } else {
                Write-Host "⚠️ $($endpoint.name): HTTP $($response.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "❌ $($endpoint.name): Failed - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Function to show deployment status
function Show-DeploymentStatus {
    Write-Host ""
    Write-Host "📊 Deployment Status" -ForegroundColor Green
    Write-Host "=" * 30
    
    try {
        $containers = docker-compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}"
        Write-Host $containers
    } catch {
        Write-Host "❌ Could not retrieve container status" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "🌐 Application URLs:" -ForegroundColor Green
    Write-Host "  Frontend: http://$Domain/" -ForegroundColor Cyan
    Write-Host "  API Docs: http://$Domain/api/docs" -ForegroundColor Cyan
    Write-Host "  Health: http://$Domain/api/health" -ForegroundColor Cyan
    
    if ($Email) {
        Write-Host ""
        Write-Host "📧 SSL Certificate (Let's Encrypt):" -ForegroundColor Green
        Write-Host "  Email: $Email" -ForegroundColor Cyan
        Write-Host "  Note: Configure Nginx for HTTPS in production" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "📝 Next Steps:" -ForegroundColor Green
    Write-Host "  1. Configure your domain DNS to point to this server" -ForegroundColor Cyan
    Write-Host "  2. Set up SSL certificates for production" -ForegroundColor Cyan
    Write-Host "  3. Configure monitoring alerts" -ForegroundColor Cyan
    Write-Host "  4. Set up regular backups" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎉 OmniDesk AI deployment completed successfully!" -ForegroundColor Green
}

# Main deployment flow
try {
    Test-Prerequisites
    Setup-Environment
    Backup-Data
    Deploy-Services
    Test-Deployment
    Show-DeploymentStatus
} catch {
    Write-Host ""
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔍 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check logs: docker-compose -f docker-compose.prod.yml logs" -ForegroundColor Cyan
    Write-Host "  2. Check container status: docker-compose -f docker-compose.prod.yml ps" -ForegroundColor Cyan
    Write-Host "  3. Check environment variables in .env.production" -ForegroundColor Cyan
    Write-Host "  4. Ensure all required services are available" -ForegroundColor Cyan
    exit 1
}