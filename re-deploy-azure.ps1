$RG_NAME      = "rg-tinytool-iss-usa"
$ACR_NAME     = "acrtinytoolissusa"
$ACA_APP_NAME = "ca-iss-backend-usa"
$IMAGE_NAME   = "iss-backend:v1"

az acr build --registry $ACR_NAME --image $IMAGE_NAME .

# Primero recuperamos el servidor del ACR
$ACR_SERVER = az acr show --name $ACR_NAME --query "loginServer" --output tsv

# Actualizamos la app con el nuevo contenedor
az containerapp update `
  --name $ACA_APP_NAME `
  --resource-group $RG_NAME `
  --image "$ACR_SERVER/$IMAGE_NAME"