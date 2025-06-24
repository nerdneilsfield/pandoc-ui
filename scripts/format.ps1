# Format Python code using multiple tools
# This script runs ruff, black, and isort to format the codebase

$ErrorActionPreference = "Stop"

Write-Host "🔧 Formatting Python code..." -ForegroundColor Yellow

# Check if uv is available
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: uv is not installed. Please install uv first." -ForegroundColor Red
    exit 1
}

try {
    # Run isort to sort imports
    Write-Host "📦 Sorting imports with isort..." -ForegroundColor Cyan
    uv run isort pandoc_ui tests scripts
    
    # Run black to format code
    Write-Host "🖤 Formatting code with black..." -ForegroundColor Cyan
    uv run black pandoc_ui tests scripts
    
    # Run ruff to fix auto-fixable issues
    Write-Host "🦀 Running ruff auto-fixes..." -ForegroundColor Cyan
    uv run ruff check --fix pandoc_ui tests scripts
    
    # Run ruff format as well (alternative to black)
    Write-Host "🦀 Running ruff format..." -ForegroundColor Cyan
    uv run ruff format pandoc_ui tests scripts
    
    Write-Host "✅ Code formatting completed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Summary:" -ForegroundColor White
    Write-Host "  - Imports sorted with isort" -ForegroundColor Gray
    Write-Host "  - Code formatted with black" -ForegroundColor Gray
    Write-Host "  - Auto-fixable issues resolved with ruff" -ForegroundColor Gray
    Write-Host "  - Code formatted with ruff format" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Next steps:" -ForegroundColor White
    Write-Host "  - Run .\scripts\lint.ps1 to check for remaining issues" -ForegroundColor Gray
    Write-Host "  - Review changes before committing" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Error occurred during formatting: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}