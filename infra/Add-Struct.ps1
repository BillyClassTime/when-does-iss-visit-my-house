# Nombre del proyecto
$project = "ttt-iss-above-home"

# Crear carpeta raíz
New-Item -ItemType Directory -Path $project -Force | Out-Null

# Subcarpetas estándar Flask
New-Item -ItemType Directory -Path "$project\templates" -Force | Out-Null
New-Item -ItemType Directory -Path "$project\static" -Force | Out-Null

# Archivos base
New-Item -ItemType File -Path "$project\app.py" -Force | Out-Null
New-Item -ItemType File -Path "$project\requirements.txt" -Force | Out-Null
New-Item -ItemType File -Path "$project\Dockerfile" -Force | Out-Null

# Archivos frontend
New-Item -ItemType File -Path "$project\templates\index.html" -Force | Out-Null
New-Item -ItemType File -Path "$project\static\script.js" -Force | Out-Null
New-Item -ItemType File -Path "$project\static\style.css" -Force | Out-Null

Write-Host "Estructura creada:"
Write-Host ""
Write-Host "$project\"
Write-Host " ├── app.py"
Write-Host " ├── requirements.txt"
Write-Host " ├── Dockerfile"
Write-Host " ├── templates\index.html"
Write-Host " └── static\script.js, style.css"
