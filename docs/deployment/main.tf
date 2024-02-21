provider "azurerm" {
  skip_provider_registration = true
  features {
  }
}

# Define variables

variable "environment_prefix" {
  description = "Prefix for the Azure Container Registry and WebApp as well as all other relevant resources"
  type        = string
}

variable "tags" {
  description = "The tags to associate with your Azure Container Registry and WebApp."
  type        = map(string)
}

variable "location" {
  description = "The location of the Azure Container Registry and WebApp."
  type        = string
}

locals {
  container_name = "${var.environment_prefix}-app"
}

# Authenticate Docker client with ACR
resource "null_resource" "acr_login" {

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<EOT
      az acr login \
        --name ${azurerm_container_registry.acr.name} \
        --username ${azurerm_container_registry.acr.admin_username} \
        --password ${azurerm_container_registry.acr.admin_password}
    EOT
  }
}

# Build and upload Docker image to ACR
resource "null_resource" "build_and_upload" {
  triggers = {
    always_run = timestamp()
  }
  depends_on = [null_resource.acr_login]
  # note the dots below are relative to the location of this file
  # we need to go 2 levels up, therefore ../..
  provisioner "local-exec" {
    command = <<EOT
      docker build \
        --no-cache \
        --platform=linux/amd64 \
        -t ${azurerm_container_registry.acr.login_server}/${local.container_name}:latest \
        -f ../Dockerfile.docs ../.. && \
      docker push ${azurerm_container_registry.acr.login_server}/${local.container_name}:latest
    EOT
  }
}


# Create resource group
resource "azurerm_resource_group" "rg" {
  name     = "${var.environment_prefix}-rg"
  location = var.location
  tags     = var.tags
}

# Create Azure Container Registry
resource "azurerm_container_registry" "acr" {
  name                = "${replace(var.environment_prefix, "-", "")}acr"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Standard"
  admin_enabled       = true
  tags                = var.tags
}

resource "azurerm_service_plan" "asp" {
  name                = "${var.environment_prefix}-asp"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = var.tags
  os_type             = "Linux"
  sku_name            = "B1"
}

# Create Azure WebApp from container
resource "azurerm_linux_web_app" "webapp" {
  name                = "${var.environment_prefix}-webapp"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = var.tags
  service_plan_id     = azurerm_service_plan.asp.id

  app_settings = {
    WEBSITES_PORT = "4444"
    DOCKER_ENABLE_CI = "true"
  }

  site_config {
    health_check_path = "/health"

    application_stack {
      docker_image_name        = "${local.container_name}:latest"
      docker_registry_url      = "https://${azurerm_container_registry.acr.login_server}"
      docker_registry_username = azurerm_container_registry.acr.admin_username
      docker_registry_password = azurerm_container_registry.acr.admin_password
    }
  }

}