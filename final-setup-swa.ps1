# -------------------------------------------------------------------------
# FINAL SETUP FOR AZURE STATIC WEB APP
# -------------------------------------------------------------------------
# Configura las app settings de la SWA para que la Function pueda
# reenviar peticiones al backend Container App.

$RG_NAME    = "rg-tinytool-iss-usa"
$LOCATION   = "eastus2"
$SWA_NAME   = "swa-iss-frontend-usa"
$BACKEND_URL = "https://ca-iss-backend-usa.orangeriver-813e879f.eastus.azurecontainerapps.io"

Write-Host "🌐 Configurando Static Web App [$SWA_NAME]..." -ForegroundColor Cyan

# 1. Verificar que Azure CLI tenga soporte para Static Web Apps
Write-Host "🔧 Comprobando soporte de Static Web Apps en Azure CLI..." -ForegroundColor Green
az staticwebapp -h | Out-Null

# 2. Crear la Static Web App si todavía no existe.
Write-Host "🔎 Comprobando si existe la Static Web App..." -ForegroundColor Green
$SWA_EXISTS = az staticwebapp show `
  --name $SWA_NAME `
  --resource-group $RG_NAME `
  --query "name" `
  --output tsv 2>$null

if (-not $SWA_EXISTS) {
  Write-Host "🆕 Creando Static Web App [$SWA_NAME] en [$LOCATION]..." -ForegroundColor Green
  az staticwebapp create `
    --name $SWA_NAME `
    --resource-group $RG_NAME `
    --location $LOCATION `
    --sku Free
}

# 3. Aplicar la variable de entorno que usará la Azure Function
Write-Host "🔑 Configurando BACKEND_API_URL..." -ForegroundColor Green
az staticwebapp appsettings set `
  --name $SWA_NAME `
  --resource-group $RG_NAME `
  --setting-names BACKEND_API_URL=$BACKEND_URL

$SWA_HOST = az staticwebapp show `
  --name $SWA_NAME `
  --resource-group $RG_NAME `
  --query "defaultHostname" `
  --output tsv

$SWA_TOKEN = az staticwebapp secrets list `
  --name $SWA_NAME `
  --resource-group $RG_NAME `
  --query "properties.apiKey" `
  --output tsv

Write-Host "✅ Configuración aplicada." -ForegroundColor Cyan
Write-Host "   SWA: $SWA_NAME" -ForegroundColor White
Write-Host "   URL: https://$SWA_HOST" -ForegroundColor White
Write-Host "   BACKEND_API_URL: $BACKEND_URL" -ForegroundColor White
Write-Host "   GitHub secret AZURE_STATIC_WEB_APPS_API_TOKEN: $SWA_TOKEN" -ForegroundColor Yellow
