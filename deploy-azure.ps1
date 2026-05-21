# -------------------------------------------------------------------------
# VARIABLES ADAPTADAS PARA USA (La región más BBB)
# -------------------------------------------------------------------------
$RG_NAME      = "rg-tinytool-iss-usa"               # Nuevo nombre para evitar esperas
$LOCATION     = "eastus"                            # La región reina del "bueno, bonito y barato"
$ACR_NAME     = "acrtinytoolissusa"                 # Nombre único para el registro
$ACA_ENV_NAME = "cae-tinytool-backend-usa"
$ACA_APP_NAME = "ca-iss-backend-usa"
$SWA_NAME     = "swa-iss-frontend-usa"
$IMAGE_NAME   = "iss-backend:v1"

Write-Host "🇺🇸 Desplegando en la región BBB [$LOCATION]..." -ForegroundColor Cyan

# 1. Asegurar extensión de Container Apps
az extension add --name containerapp --upgrade --yes

# 2. Crear el nuevo Grupo de Recursos
Write-Host "📦 Creando Grupo de Recursos [$RG_NAME]..." -ForegroundColor Green
az group create --name $RG_NAME --location $LOCATION

# 3. Crear Azure Container Registry (ACR)
Write-Host "🔒 Creando Azure Container Registry [$ACR_NAME]..." -ForegroundColor Green
az acr create --resource-group $RG_NAME --name $ACR_NAME --sku Basic --admin-enabled true

# --- 🔥 COMPILACIÓN AUTOMÁTICA EN LA NUBE ---
Write-Host "🚀 Subiendo tus archivos y compilando el Docker en los servidores de USA..." -ForegroundColor Green
az acr build --registry $ACR_NAME --image $IMAGE_NAME .

# Obtener credenciales del registro para conectar la app
$ACR_SERVER = az acr show --name $ACR_NAME --query "loginServer" --output tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" --output tsv

# 4. Crear Entorno de Container Apps
Write-Host "☁️ Creando entorno Serverless de Container Apps..." -ForegroundColor Green
az containerapp env create --name $ACA_ENV_NAME --resource-group $RG_NAME --location $LOCATION

# 5. Crear la Container App (Con tu código y escala a 0 para que no cueste nada)
Write-Host "🐳 Desplegando el contenedor con escala a 0..." -ForegroundColor Green
az containerapp create `
  --name $ACA_APP_NAME `
  --resource-group $RG_NAME `
  --environment $ACA_ENV_NAME `
  --image "$ACR_SERVER/$IMAGE_NAME" `
  --target-port 8080 `
  --ingress external `
  --registry-server $ACR_SERVER `
  --registry-username $ACR_NAME `
  --registry-password $ACR_PASSWORD `
  --cpu 0.25 `
  --memory 0.5Gi `
  --min-replicas 0 `
  --max-replicas 5

# Obtener URL del Backend
$BACKEND_URL = az containerapp show --name $ACA_APP_NAME --resource-group $RG_NAME --query "properties.configuration.ingress.fqdn" --output tsv

# 6. Crear la Azure Static Web App para el Frontend (100% Gratis)
Write-Host "🌐 Creando Azure Static Web App..." -ForegroundColor Green
az staticwebapp create `
  --name $SWA_NAME `
  --resource-group $RG_NAME `
  --location $LOCATION `
  --sku Free

# Obtener Token del Frontend para subir los archivos después
$SWA_TOKEN = az staticwebapp secrets list --name $SWA_NAME --resource-group $RG_NAME --query "properties.apiKey" --output tsv

Write-Host "🎉 ¡Estructura y backend desplegados con éxito en USA!" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "👇 COPIA ESTOS DATOS AL TERMINAR:" -ForegroundColor White
Write-Host "🔗 URL Backend API: https://$BACKEND_URL" -ForegroundColor Yellow
Write-Host "🔑 Token Static Web App: $SWA_TOKEN" -ForegroundColor Yellow