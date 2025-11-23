# Script ETL para Azure Cosmos DB - Setup Completo

## Archivos Creados
- `etl_cosmos.py`: Script principal para cargar datos automáticamente
- `cosmos_helper.py`: Clase helper para operaciones con Cosmos DB
- `data/`: Carpeta donde debes colocar tus archivos (CSV, Excel, JSON)

## Variables de Entorno (.env)
Confirma que tengas estas variables en tu archivo `.env`:
```
COSMOS_ENDPOINT=your_cosmos_endpoint
COSMOS_KEY=your_cosmos_key
DATABASE_NAME=avance-obras-db
CONTAINER_NAME=obras
```

## Instalación de Dependencias
```bash
pip install azure-cosmos python-dotenv pandas openpyxl
```

## Uso del Script ETL

### 1. Preparar los datos
- Crea la carpeta `data` si no existe:
  ```bash
  mkdir -p data
  ```
- Coloca tus archivos CSV, Excel (.xlsx, .xls) o JSON en la carpeta `data/`

### 2. Ejecutar el script
```bash
python etl_cosmos.py
```

## Características del Script

### Formatos Soportados
- **CSV**: archivos .csv
- **Excel**: archivos .xlsx y .xls
- **JSON**: archivos .json

### Procesamiento Automático
- Detecta automáticamente el formato de archivo
- Carga datos en lotes de 100 registros
- Genera IDs únicos automáticamente si no existen
- Maneja errores y continúa con otros archivos
- Muestra progreso en tiempo real

### Estructura de Datos
El script convertirá tus datos a este formato en Cosmos DB:
```json
{
    "id": "único-generado-automáticamente",
    "obra": "nombre_del_proyecto",
    "fecha": "2024-01-15",
    "avance": 85.5,
    "responsable": "Juan Pérez",
    // ... otros campos de tu archivo original
    "_ts": "timestamp_automatico"
}
```

### Logs y Monitoreo
- Muestra estadísticas de procesamiento
- Registra errores detallados
- Indica progreso de carga por lotes

## Ejemplo de Ejecución
```
Cargando variables de entorno desde: .env
Conectando a Cosmos DB...
✓ Base de datos 'avance-obras-db' configurada
✓ Contenedor 'obras' configurado

Archivos encontrados:
- data/proyecto_1.xlsx (500 registros)
- data/avances.csv (1200 registros)

Procesando proyecto_1.xlsx...
Lote 1/5: 100 registros cargados
Lote 2/5: 100 registros cargados
...

✓ Procesamiento completo:
  - 2 archivos procesados
  - 1700 registros cargados exitosamente
  - 0 errores
```

## Personalización
Si necesitas modificar el mapeo de columnas o la estructura de datos, edita la función `process_data_file()` en `etl_cosmos.py`.

## Troubleshooting
- Verifica que las variables de entorno estén correctas
- Asegúrate de que la carpeta `data/` contenga archivos válidos
- Revisa los logs de error si algún archivo falla