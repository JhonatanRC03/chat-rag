"""
Script principal para cargar datos a Azure Cosmos DB
Usa las variables de entorno ya configuradas en tu .env
"""
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

from cosmos_helper import CosmosDBHelper

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cosmos_etl.log')
    ]
)
logger = logging.getLogger(__name__)


def load_environment_variables():
    """Carga las variables de entorno desde el archivo .env"""
    try:
        # Buscar archivo .env
        env_path = Path('.env')
        if not env_path.exists():
            raise FileNotFoundError("Archivo .env no encontrado")
        
        load_dotenv(env_path)
        
        # Obtener variables de Cosmos DB
        cosmos_config = {
            'endpoint': os.getenv('COSMOS_ENDPOINT'),
            'key': os.getenv('COSMOS_KEY'),
            'database_name': os.getenv('DATABASE_NAME'),
            'container_name': os.getenv('CONTAINER_NAME'),
            'partition_key': os.getenv('PARTITION_KEY', '/id')  # Default a /id
        }
        
        # Validar que todas las variables requeridas estén presentes
        missing_vars = []
        for key, value in cosmos_config.items():
            if not value and key != 'partition_key':
                missing_vars.append(key.upper())
        
        if missing_vars:
            raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
        
        logger.info("✅ Variables de entorno cargadas exitosamente")
        logger.info(f"   Database: {cosmos_config['database_name']}")
        logger.info(f"   Container: {cosmos_config['container_name']}")
        
        return cosmos_config
        
    except Exception as e:
        logger.error(f"❌ Error cargando variables de entorno: {str(e)}")
        raise


def find_data_files():
    """Busca archivos de datos en la carpeta app/data/"""
    try:
        data_folder = Path('./app/data')
        
        if not data_folder.exists():
            logger.warning("⚠️ Carpeta 'app/data' no existe, creándola...")
            data_folder.mkdir(parents=True)
            return []
        
        # Buscar archivos soportados
        supported_extensions = ['.csv', '.json', '.xlsx', '.xls']
        data_files = []
        
        for ext in supported_extensions:
            files = list(data_folder.glob(f'*{ext}'))
            data_files.extend(files)
        
        if data_files:
            logger.info(f"📁 Archivos encontrados en './app/data/':")
            for file in data_files:
                logger.info(f"   - {file.name}")
        else:
            logger.warning("⚠️ No se encontraron archivos de datos en './app/data/'")
        
        return data_files
        
    except Exception as e:
        logger.error(f"❌ Error buscando archivos: {str(e)}")
        return []


async def process_data_file(cosmos_helper: CosmosDBHelper, file_path: Path, batch_size: int = 100):
    """
    Procesa un archivo de datos específico
    
    Args:
        cosmos_helper: Helper de Cosmos DB
        file_path: Ruta del archivo
        batch_size: Tamaño del batch para carga
    """
    try:
        logger.info(f"🚀 Iniciando procesamiento de: {file_path.name}")
        
        # Cargar archivo a DataFrame
        df = cosmos_helper.load_file_to_dataframe(str(file_path))
        
        # Cargar datos a Cosmos DB
        result = await cosmos_helper.load_data_from_dataframe(df, batch_size)
        
        if result['success']:
            logger.info(f"🎉 Archivo '{file_path.name}' procesado exitosamente:")
            logger.info(f"   📊 Total registros: {result['total_records']}")
            logger.info(f"   ✅ Exitosos: {result['successful_inserts']}")
            logger.info(f"   ❌ Errores: {result['failed_inserts']}")
            logger.info(f"   📈 Tasa de éxito: {result['success_rate']:.2f}%")
        else:
            logger.error(f"❌ Error procesando '{file_path.name}': {result.get('error', 'Error desconocido')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error procesando archivo {file_path.name}: {str(e)}")
        return {'success': False, 'error': str(e)}


async def main():
    """Función principal del ETL"""
    try:
        logger.info("🚀 INICIANDO ETL COSMOS DB")
        logger.info("=" * 50)
        
        # 1. Cargar configuración
        logger.info("1️⃣ Cargando configuración...")
        config = load_environment_variables()
        
        # 2. Buscar archivos de datos
        logger.info("2️⃣ Buscando archivos de datos...")
        data_files = find_data_files()
        
        if not data_files:
            logger.error("❌ No se encontraron archivos para procesar")
            logger.info("💡 Coloca tus archivos (.csv, .json, .xlsx) en la carpeta './data/'")
            return
        
        # 3. Inicializar Cosmos DB Helper
        logger.info("3️⃣ Inicializando Cosmos DB...")
        cosmos_helper = CosmosDBHelper(
            endpoint=config['endpoint'],
            key=config['key'],
            database_name=config['database_name'],
            container_name=config['container_name']
        )
        
        # 4. Conectar y configurar recursos de Cosmos DB
        logger.info("4️⃣ Conectando a Cosmos DB...")
        if not await cosmos_helper.connect():
            logger.error("❌ Error conectando a Cosmos DB")
            return
            
        logger.info("5️⃣ Configurando recursos de Cosmos DB...")
        if not await cosmos_helper.setup_cosmos_resources():
            logger.error("❌ Error configurando recursos de Cosmos DB")
            return
        
        # 6. Procesar cada archivo
        logger.info("6️⃣ Procesando archivos de datos...")
        results = []
        
        for file_path in data_files:
            result = await process_data_file(cosmos_helper, file_path)
            results.append({
                'file': file_path.name,
                'result': result
            })
        
        # 7. Resumen final
        logger.info("6️⃣ Generando resumen final...")
        await generate_final_summary(cosmos_helper, results)
        
        # 7. Cerrar conexión
        await cosmos_helper.close()
        
        logger.info("🎉 ETL COMPLETADO EXITOSAMENTE")
        
    except KeyboardInterrupt:
        logger.info("⏹️ ETL interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error inesperado en ETL: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


async def generate_final_summary(cosmos_helper: CosmosDBHelper, results: list):
    """Genera un resumen final del ETL"""
    try:
        logger.info("📊 RESUMEN FINAL")
        logger.info("-" * 30)
        
        total_files = len(results)
        successful_files = sum(1 for r in results if r['result'].get('success', False))
        total_records = sum(r['result'].get('total_records', 0) for r in results)
        total_successful = sum(r['result'].get('successful_inserts', 0) for r in results)
        total_errors = sum(r['result'].get('failed_inserts', 0) for r in results)
        
        logger.info(f"📁 Archivos procesados: {successful_files}/{total_files}")
        logger.info(f"📊 Total registros procesados: {total_records:,}")
        logger.info(f"✅ Registros exitosos: {total_successful:,}")
        logger.info(f"❌ Registros con error: {total_errors:,}")
        
        if total_records > 0:
            success_rate = (total_successful / total_records) * 100
            logger.info(f"📈 Tasa de éxito general: {success_rate:.2f}%")
        
        # Obtener estadísticas del container
        logger.info("\n📊 Estadísticas del Container:")
        stats = await cosmos_helper.get_container_stats()
        if stats['success']:
            logger.info(f"📦 Total documentos en container: {stats['total_documents']:,}")
        
        logger.info("\n🔗 Detalles por archivo:")
        for file_result in results:
            file_name = file_result['file']
            result = file_result['result']
            status = "✅" if result.get('success', False) else "❌"
            records = result.get('total_records', 0)
            logger.info(f"   {status} {file_name}: {records:,} registros")
        
    except Exception as e:
        logger.error(f"❌ Error generando resumen: {str(e)}")


def show_usage():
    """Muestra instrucciones de uso"""
    print("""
🏗️ ETL para Azure Cosmos DB - Avance de Obras

INSTRUCCIONES DE USO:
===================

1. Configurar variables de entorno en .env:
   COSMOS_ENDPOINT=tu_endpoint_aquí
   COSMOS_KEY=tu_clave_aquí
   DATABASE_NAME=avance-obras-db
   CONTAINER_NAME=obras

2. Colocar archivos de datos en la carpeta './data/':
   - Archivos CSV: data/avance_obras.csv
   - Archivos Excel: data/avance_obras.xlsx
   - Archivos JSON: data/avance_obras.json

3. Ejecutar el script:
   python etl_cosmos.py

CARACTERÍSTICAS:
===============
✅ Detección automática de archivos
✅ Carga masiva en batches
✅ Manejo de errores robusto
✅ Logs detallados
✅ Upsert (actualiza si existe)
✅ Soporte para +50,000 registros

ARCHIVOS SOPORTADOS:
==================
• CSV (separado por comas)
• Excel (.xlsx, .xls) 
• JSON (array de objetos)

¡Listo para procesar tu base de datos de avance de obras! 🚀
    """)


if __name__ == "__main__":
    # Mostrar ayuda si no hay archivos
    data_folder = Path('./app/data')
    if not data_folder.exists() or not any(data_folder.glob('*')):
        show_usage()
        
        # Crear carpeta data si no existe
        data_folder.mkdir(parents=True, exist_ok=True)
        print(f"📁 Carpeta 'data' creada. Coloca tus archivos ahí y ejecuta nuevamente.")
    else:
        # Ejecutar ETL
        asyncio.run(main())