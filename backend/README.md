# app-gys-agente-ia-admin

Ruta:

```shell
cd backend
```

## Install

```shell
pip install -r requirements.txt
```

## Config Azure resources

Cosmos DB:

- Add client IP address to the list on: Cosmos DB for MongoDB/Settings/Networking

Storage:

- Create a container in storage named `uploads`
- Create queues

AI Search:

- Create index with JSON
- Go to: Settings/Keys/Access Control and select option "Both"

Web App:

- Impide que se cierre sesión en la aplicación debido a un periodo de inactividad.
  Ruta Azure Web App: app-smartinvierte-admin>Configuración>Siempre activado
- Settings/Configuration/Stack settings/Startup Command

-version sin $PORT

```shell
pip install -r requirements.txt && gunicorn -k uvicorn.workers.UvicornWorker --bind=0.0.0.0 app.main:app
```

-version con $PORT

```shell
pip install -r requirements.txt && gunicorn -k uvicorn.workers.UvicornWorker --bind=0.0.0.0:$PORT --timeout 900 --graceful-timeout 900 --keep-alive 120 --access-logfile - --error-logfile - --log-level info app.main:app
```

La variable $PORT es una variable de entorno que se debe alojada en la nube
ir a api-smartinvierte-admin > Variables de entorno > Agregar
Nombre:PORT
Valor:8081
Al finalizar aplicamos para agregar las variables y guardarlas en Azure.

## Run locally

```shell
cd backend
uvicorn main:app --reload --port 8083
```

With multiple instances:

```shell
uvicorn main:app --reload --port 8083
```

## Deploy

1. Select Azure suscription:

```shell
az account set --subscription "2e8b3ead-8986-42a6-8e05-b8e85e4e47df"
```

2. Go to /backend route:

```shell
cd backend
```

3. Compress the files

```shell
zip -r deploy.zip .
```

4. Deploy to Azure

```shell
az webapp deployment source config-zip --resource-group rg-smartinvierte-admin --name api-smartinvierte-admin --src deploy.zip
```