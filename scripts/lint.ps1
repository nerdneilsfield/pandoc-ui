# Lint Python code using multiple tools
# This script runs ruff, mypy, and other linting tools to check code quality

$ErrorActionPreference = "Stop"

Write-Host "🔍 Linting Python code..." -ForegroundColor Yellow

# Check if uv is available
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: uv is not installed. Please install uv first." -ForegroundColor Red
    exit 1
}

# Track if any linting issues were found
$IssuesFound = $false

try {
    # Run ruff for linting
    Write-Host "🦀 Running ruff linting..." -ForegroundColor Cyan
    $RuffResult = uv run ruff check pandoc_ui tests scripts
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Ruff found issues" -ForegroundColor Yellow
        $IssuesFound = $true
    } else {
        Write-Host "✅ Ruff: No issues found" -ForegroundColor Green
    }
    
    Write-Host ""
    
    # Run mypy for type checking
    Write-Host "🔍 Running mypy type checking..." -ForegroundColor Cyan
    $MypyResult = uv run mypy pandoc_ui
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  MyPy found type issues" -ForegroundColor Yellow
        $IssuesFound = $true
    } else {
        Write-Host "✅ MyPy: No type issues found" -ForegroundColor Green
    }
    
    Write-Host ""
    
    # Run pytest in multiple sessions to organize test output
    Write-Host "🧪 Running tests in multiple sessions..." -ForegroundColor Cyan
    
    # Session 1: Infrastructure layer tests
    Write-Host "📚 Session 1: Infrastructure layer tests..." -ForegroundColor Magenta
    $Session1Result = uv run pytest tests/test_pandoc_detector.py tests/test_pandoc_runner.py -v --tb=short
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Session 1: Infrastructure tests failed" -ForegroundColor Yellow
        $IssuesFound = $true
    } else {
        Write-Host "✅ Session 1: Infrastructure tests passed" -ForegroundColor Green
    }
    
    Write-Host ""
    
    # Session 2: Application and config layer tests
    Write-Host "⚙️  Session 2: Application and config layer tests..." -ForegroundColor Magenta
    $Session2Result = uv run pytest tests/test_conversion_service.py tests/test_folder_scanner.py tests/test_profile_repository.py tests/test_config_manager.py tests/test_settings_store.py -v --tb=short
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Session 2: Application/config tests failed" -ForegroundColor Yellow
        $IssuesFound = $true
    } else {
        Write-Host "✅ Session 2: Application/config tests passed" -ForegroundColor Green
    }
    
    Write-Host ""
    
    # Session 3: Integration tests (excluding GUI)
    Write-Host "🔗 Session 3: Integration tests..." -ForegroundColor Magenta
    $Session3Result = uv run pytest tests/test_phase4_acceptance.py tests/test_batch_performance.py -v --tb=short
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Session 3: Integration tests failed" -ForegroundColor Yellow
        $IssuesFound = $true
    } else {
        Write-Host "✅ Session 3: Integration tests passed" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "📋 Linting Summary:" -ForegroundColor White
    
    if (-not $IssuesFound) {
        Write-Host "✅ All checks passed! Code is ready for commit." -ForegroundColor Green
        Write-Host ""
        Write-Host "💡 Great job! Your code meets all quality standards:" -ForegroundColor White
        Write-Host "  - No linting issues (ruff)" -ForegroundColor Gray
        Write-Host "  - No type issues (mypy)" -ForegroundColor Gray
        Write-Host "  - All tests passing (pytest)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Issues found. Please address them before committing." -ForegroundColor Red
        Write-Host ""
        Write-Host "🔧 Quick fixes:" -ForegroundColor White
        Write-Host "  - Run .\scripts\format.ps1 to auto-fix formatting issues" -ForegroundColor Gray
        Write-Host "  - Check mypy output for type hints and corrections" -ForegroundColor Gray
        Write-Host "  - Review failing tests and fix underlying issues" -ForegroundColor Gray
        exit 1
    }
}
catch {
    Write-Host "❌ Error occurred during linting: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}