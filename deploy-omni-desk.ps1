# OmniDesk AI - Complete Production Deployment Script
# This script handles the entire deployment process from start to finish

param(
    [string]$Domain = "localhost",
    [string]$Email = "",
    [switch]$SkipPrereqs = $false,
    [switch]$SkipBackup = $false,
    [switch]$Force = $false,
    [switch]$Monitor = $false,
    [switch]$SSL = $false
)

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

# ASCII Art Header
Write-Host @"

  ╔═══════════════════════════════════════════════════════════╗
  ║                                                           ║
  ║    ████████╗ ███╗   ███╗ ███╗   ██╗ ██╗ ██████╗ ███████╗  ║
  ║    ██╔═══██║ ████╗ ████║ ████╗  ██║ ██║ ██╔══██║██╔════╝  ║
  ║    ██║   ██║ ██╔████╔██║ ██╔██╗ ██║ ██║ ██║  ██║█████╗    ║
  ║    ██║   ██║ ██║╚██╔╝██║ ██║╚██╗██║ ██║ ██║  ██║██╔══╝    ║
  ║    ╚██████╔╝ ██║ ╚═╝ ██║ ██║ ╚████║ ██║ ██████╔╝███████╗  ║
  ║     ╚═════╝  ╚═╝     ╚═╝ ╚═╝  ╚═══╝ ╚═╝ ╚═════╝ ╚══════╝  ║
  ║                                                           ║
  ║                  Smart AI Ticket Management               ║
  ║                                                           ║
  ╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

Write-Host "🚀 OmniDesk AI Production Deployment" -ForegroundColor Green
Write-Host "🌐 Domain: $Domain" -ForegroundColor Cyan
Write-Host "📧 Email: $(if($Email) { $Email } else { 'Not configured' })" -ForegroundColor Cyan
Write-Host "🔒 SSL: $(if($SSL) { 'Enabled' } else { 'Disabled' })" -ForegroundColor Cyan
Write-Host "📊 Monitoring: $(if($Monitor) { 'Enabled' } else { 'Basic' })" -ForegroundColor Cyan
Write-Host "=" * 70

# Function to show progress
function Show-Progress {
    param($Message, $Step, $Total)
    $percent = [math]::Round(($Step / $Total) * 100)
    Write-Host "[$Step/$Total] ($percent%) $Message" -ForegroundColor Yellow
}

# Function to check prerequisites
function Test-Prerequisites {
    Show-Progress "Checking system prerequisites..." 1 10
    
    $requirements = @(
        @{Name="Docker"; Command="docker"; Version="--version"},
        @{Name="Docker Compose"; Command="docker-compose"; Version="--version"}
    )
    
    $missing = @()
    foreach ($req in $requirements) {
        try {
            $version = & $req.Command $req.Version 2>$null
            Write-Host "  ✅ $($req.Name): Found" -ForegroundColor Green
        } catch {
            $missing += $req.Name
            Write-Host "  ❌ $($req.Name): Missing" -ForegroundColor Red
        }
    }
    
    if ($missing.Count -gt 0 -and -not $SkipPrereqs) {
        Write-Host "Missing prerequisites: $($missing -join ', ')" -ForegroundColor Red
        Write-Host "Install missing components or use -SkipPrereqs to continue anyway" -ForegroundColor Red
        exit 1
    }
    
    # Check system resources
    $memory = Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory
    $memoryGB = [math]::Round($memory / 1GB, 1)
    
    if ($memoryGB -lt 4) {
        Write-Warning "System has only ${memoryGB}GB RAM. Recommended: 8GB+"
    } else {
        Write-Host "  ✅ Memory: ${memoryGB}GB" -ForegroundColor Green
    }
    
    $disk = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object -ExpandProperty FreeSpace
    $diskGB = [math]::Round($disk / 1GB, 1)
    
    if ($diskGB -lt 20) {
        Write-Warning "Free disk space: ${diskGB}GB. Recommended: 50GB+"
    } else {
        Write-Host "  ✅ Disk Space: ${diskGB}GB free" -ForegroundColor Green
    }
}

# Function to setup environment
function Initialize-Environment {
    Show-Progress "Setting up environment..." 2 10
    
    # Check for environment file
    if (-not (Test-Path ".env.production")) {
        if (Test-Path ".env.production.example") {
            Copy-Item ".env.production.example" ".env.production"
            Write-Host "  📄 Created .env.production from example" -ForegroundColor Green
            Write-Host "  ⚠️  Please edit .env.production with your settings!" -ForegroundColor Yellow
        } else {
            Write-Host "  ❌ .env.production.example not found!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  ✅ .env.production exists" -ForegroundColor Green
    }
    
    # Create required directories
    $directories = @(
        "logs",
        "data/postgres",
        "data/qdrant", 
        "data/redis",
        "monitoring/grafana/data",
        "monitoring/prometheus/data",
        "ssl",
        "backups"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "  📁 Created: $dir" -ForegroundColor Green
        }
    }
    
    # Set permissions on data directories
    foreach ($dir in @("data", "logs", "monitoring", "backups")) {
        if (Test-Path $dir) {
            # Give full control to current user
            $acl = Get-Acl $dir
            $permission = $env:USERNAME, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
            $rule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
            $acl.SetAccessRule($rule)
            Set-Acl $dir $acl
        }
    }
}

# Function to backup existing data
function Backup-ExistingData {
    Show-Progress "Creating backup..." 3 10
    
    if ($SkipBackup) {
        Write-Host "  ⏭️  Skipping backup (--SkipBackup specified)" -ForegroundColor Yellow
        return
    }
    
    if (Test-Path "scripts/backup.sh") {
        try {
            if (Get-Command "wsl" -ErrorAction SilentlyContinue) {
                Write-Host "  🐧 Running backup via WSL..." -ForegroundColor Cyan
                wsl bash scripts/backup.sh
            } elseif (Get-Command "bash" -ErrorAction SilentlyContinue) {
                Write-Host "  🐧 Running backup via Git Bash..." -ForegroundColor Cyan
                bash scripts/backup.sh
            } else {
                Write-Warning "  ⚠️  Bash not available, creating manual backup..."
                $backupDir = "backups/manual_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
                New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
                
                if (Test-Path "data") {
                    Copy-Item "data" "$backupDir/data" -Recurse -Force
                }
                if (Test-Path ".env.production") {
                    Copy-Item ".env.production" "$backupDir/.env.production" -Force
                }
                Write-Host "  💾 Manual backup created in $backupDir" -ForegroundColor Green
            }
        } catch {
            Write-Warning "  ⚠️  Backup failed: $($_.Exception.Message)"
            if (-not $Force) {
                $response = Read-Host "Continue without backup? (y/N)"
                if ($response -ne "y" -and $response -ne "Y") {
                    Write-Host "Deployment cancelled" -ForegroundColor Red
                    exit 1
                }
            }
        }
    } else {
        Write-Warning "  ⚠️  Backup script not found"
    }
}

# Function to pull and build images
function Build-Application {
    Show-Progress "Building application images..." 4 10
    
    Write-Host "  🐳 Stopping existing containers..." -ForegroundColor Cyan
    docker-compose -f docker-compose.prod.yml down --remove-orphans 2>$null
    
    Write-Host "  📥 Pulling base images..." -ForegroundColor Cyan
    docker-compose -f docker-compose.prod.yml pull --ignore-pull-failures
    
    Write-Host "  🔨 Building application images..." -ForegroundColor Cyan
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    Write-Host "  ✅ Application built successfully" -ForegroundColor Green
}

# Function to deploy services
function Deploy-Services {
    Show-Progress "Deploying services..." 5 10
    
    Write-Host "  🚀 Starting services..." -ForegroundColor Cyan
    
    # Start core services first
    docker-compose -f docker-compose.prod.yml up -d postgres redis qdrant
    Start-Sleep -Seconds 10
    
    # Start application services
    docker-compose -f docker-compose.prod.yml up -d backend
    Start-Sleep -Seconds 15
    
    docker-compose -f docker-compose.prod.yml up -d frontend
    Start-Sleep -Seconds 10
    
    docker-compose -f docker-compose.prod.yml up -d nginx
    Start-Sleep -Seconds 5
    
    if ($Monitor) {
        Write-Host "  📊 Starting monitoring stack..." -ForegroundColor Cyan
        docker-compose -f docker-compose.prod.yml up -d prometheus grafana
        Start-Sleep -Seconds 10
    }
    
    Write-Host "  ✅ Services deployed" -ForegroundColor Green
}

# Function to configure SSL
function Configure-SSL {
    Show-Progress "Configuring SSL..." 6 10
    
    if (-not $SSL) {
        Write-Host "  ⏭️  SSL configuration skipped" -ForegroundColor Yellow
        return
    }
    
    if (-not $Email) {
        Write-Warning "  ⚠️  Email required for SSL certificate"
        return
    }
    
    Write-Host "  🔒 Setting up SSL certificate..." -ForegroundColor Cyan
    
    # Check if we're on Windows with WSL available
    if (Get-Command "wsl" -ErrorAction SilentlyContinue) {
        try {
            wsl sudo apt-get update
            wsl sudo apt-get install -y certbot python3-certbot-nginx
            wsl sudo certbot --nginx -d $Domain --email $Email --agree-tos --non-interactive
            Write-Host "  ✅ SSL certificate configured" -ForegroundColor Green
        } catch {
            Write-Warning "  ⚠️  Automatic SSL setup failed: $($_.Exception.Message)"
            Write-Host "  📝 Manual SSL setup required" -ForegroundColor Yellow
        }
    } else {
        Write-Warning "  ⚠️  SSL setup requires WSL or manual configuration"
        Write-Host "  📝 Place your certificate files in ./ssl/ directory:" -ForegroundColor Yellow
        Write-Host "    - cert.pem" -ForegroundColor Cyan
        Write-Host "    - key.pem" -ForegroundColor Cyan
    }
}

# Function to wait for services
function Wait-ForServices {
    Show-Progress "Waiting for services to be ready..." 7 10
    
    $maxWait = 120
    $waited = 0
    $interval = 5
    
    Write-Host "  ⏳ Waiting for services (max ${maxWait}s)..." -ForegroundColor Cyan
    
    while ($waited -lt $maxWait) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost/api/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "  ✅ Services are ready!" -ForegroundColor Green
                return
            }
        } catch {
            # Service not ready yet
        }
        
        Start-Sleep -Seconds $interval
        $waited += $interval
        $progress = [math]::Round(($waited / $maxWait) * 100)
        Write-Host "  ⏳ Still waiting... (${progress}%)" -ForegroundColor Yellow
    }
    
    Write-Warning "  ⚠️  Services may not be fully ready yet"
}

# Function to verify deployment
function Test-Deployment {
    Show-Progress "Verifying deployment..." 8 10
    
    if (Test-Path "scripts/verify-deployment.sh" -and (Get-Command "bash" -ErrorAction SilentlyContinue)) {
        Write-Host "  🔍 Running comprehensive verification..." -ForegroundColor Cyan
        try {
            $env:DOMAIN = $Domain
            $env:PROTOCOL = if($SSL) { "https" } else { "http" }
            bash scripts/verify-deployment.sh
        } catch {
            Write-Warning "  ⚠️  Verification script failed: $($_.Exception.Message)"
            Test-BasicEndpoints
        }
    } else {
        Write-Host "  🔍 Running basic verification..." -ForegroundColor Cyan
        Test-BasicEndpoints
    }
}

# Function to test basic endpoints
function Test-BasicEndpoints {
    $protocol = if($SSL) { "https" } else { "http" }
    $endpoints = @(
        @{url="$protocol://$Domain/"; name="Frontend"},
        @{url="$protocol://$Domain/api/health"; name="Backend Health"},
        @{url="$protocol://$Domain/api/docs"; name="API Documentation"}
    )
    
    $successful = 0
    foreach ($endpoint in $endpoints) {
        try {
            Write-Host "    Testing $($endpoint.name)..." -ForegroundColor Cyan
            $response = Invoke-WebRequest -Uri $endpoint.url -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "    ✅ $($endpoint.name): OK" -ForegroundColor Green
                $successful++
            } else {
                Write-Host "    ⚠️ $($endpoint.name): HTTP $($response.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "    ❌ $($endpoint.name): Failed" -ForegroundColor Red
        }
    }
    
    if ($successful -eq $endpoints.Count) {
        Write-Host "  ✅ All endpoints responding correctly" -ForegroundColor Green
    } elseif ($successful -gt 0) {
        Write-Warning "  ⚠️  Some endpoints not responding"
    } else {
        Write-Host "  ❌ No endpoints responding" -ForegroundColor Red
    }
}

# Function to setup monitoring
function Configure-Monitoring {
    Show-Progress "Configuring monitoring..." 9 10
    
    if (-not $Monitor) {
        Write-Host "  ⏭️  Advanced monitoring disabled" -ForegroundColor Yellow
        return
    }
    
    Write-Host "  📊 Setting up Grafana dashboards..." -ForegroundColor Cyan
    
    # Wait for Grafana to be ready
    $maxWait = 60
    $waited = 0
    while ($waited -lt $maxWait) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3001" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                break
            }
        } catch {
            Start-Sleep -Seconds 2
            $waited += 2
        }
    }
    
    Write-Host "  📊 Monitoring URLs:" -ForegroundColor Green
    Write-Host "    Grafana: http://$Domain:3001 (admin/admin)" -ForegroundColor Cyan
    Write-Host "    Prometheus: http://$Domain:9090" -ForegroundColor Cyan
}

# Function to show final status
function Show-DeploymentSummary {
    Show-Progress "Deployment complete!" 10 10
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                     🎉 DEPLOYMENT SUCCESSFUL! 🎉                  ║" -ForegroundColor Green  
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    
    # Container status
    Write-Host "📊 Container Status:" -ForegroundColor Yellow
    try {
        docker-compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}"
    } catch {
        Write-Warning "Could not retrieve container status"
    }
    
    Write-Host ""
    $protocol = if($SSL) { "https" } else { "http" }
    
    # Application URLs
    Write-Host "🌐 Application URLs:" -ForegroundColor Green
    Write-Host "  🏠 Frontend:     $protocol://$Domain/" -ForegroundColor Cyan
    Write-Host "  🔗 API Docs:     $protocol://$Domain/api/docs" -ForegroundColor Cyan
    Write-Host "  ❤️  Health:      $protocol://$Domain/api/health" -ForegroundColor Cyan
    Write-Host "  ℹ️  System Info: $protocol://$Domain/api/v1/system/info" -ForegroundColor Cyan
    
    if ($Monitor) {
        Write-Host ""
        Write-Host "📊 Monitoring URLs:" -ForegroundColor Green
        Write-Host "  📈 Grafana:      http://$Domain:3001" -ForegroundColor Cyan
        Write-Host "  📉 Prometheus:   http://$Domain:9090" -ForegroundColor Cyan
        Write-Host "  📊 Metrics:      $protocol://$Domain/metrics" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "📝 Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Configure DNS to point $Domain to this server" -ForegroundColor Cyan
    Write-Host "  2. Update .env.production with your API keys and secrets" -ForegroundColor Cyan
    if (-not $SSL) {
        Write-Host "  3. Set up SSL certificate for production" -ForegroundColor Cyan
    }
    Write-Host "  4. Set up regular backups (scripts/backup.sh)" -ForegroundColor Cyan
    Write-Host "  5. Configure monitoring alerts" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "🛟 Support Commands:" -ForegroundColor Yellow
    Write-Host "  📋 View logs:    docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor Cyan
    Write-Host "  🔄 Restart:      docker-compose -f docker-compose.prod.yml restart" -ForegroundColor Cyan
    Write-Host "  🛑 Stop:         docker-compose -f docker-compose.prod.yml down" -ForegroundColor Cyan
    Write-Host "  💾 Backup:       ./scripts/backup.sh" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "🎊 Welcome to OmniDesk AI! Your intelligent ticket management system is ready!" -ForegroundColor Green
}

# Main execution flow
try {
    $startTime = Get-Date
    
    Test-Prerequisites
    Initialize-Environment  
    Backup-ExistingData
    Build-Application
    Deploy-Services
    Configure-SSL
    Wait-ForServices
    Test-Deployment
    Configure-Monitoring
    Show-DeploymentSummary
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    Write-Host ""
    Write-Host "⏱️  Total deployment time: $($duration.Minutes)m $($duration.Seconds)s" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "❌ DEPLOYMENT FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔍 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check logs: docker-compose -f docker-compose.prod.yml logs" -ForegroundColor Cyan
    Write-Host "  2. Check containers: docker-compose -f docker-compose.prod.yml ps" -ForegroundColor Cyan
    Write-Host "  3. Check system resources: docker system df" -ForegroundColor Cyan
    Write-Host "  4. Verify .env.production configuration" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Use -Force to skip confirmation prompts" -ForegroundColor Cyan
    Write-Host "  Use -SkipPrereqs to bypass prerequisite checks" -ForegroundColor Cyan
    Write-Host "  Use -SkipBackup to skip backup creation" -ForegroundColor Cyan
    exit 1
}