$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is required."
}

python scripts/generate_dataset.py
python experiment_7/spark_sql.py
python experiment_11/data_quality.py
python experiment_8/spark_mllib.py
python -m pytest -q | Tee-Object outputs/test_results.log

if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker info *> $null
    if ($LASTEXITCODE -eq 0) {
        Push-Location experiment_9
        docker compose config *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Airflow Compose configuration is valid. Start it with: docker compose up -d"
        }
        Pop-Location
    } else {
        Write-Warning "Docker is installed but its daemon is unavailable; Airflow was not started."
    }
} else {
    Write-Warning "Docker is unavailable; Airflow was not started."
}

Write-Host "Experiments 7, 11, 8 and tests completed. See outputs/ and reports/."

