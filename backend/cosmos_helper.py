"""
Azure Cosmos DB Helper para operaciones de base de datos
Maneja la conexión, creación de recursos y operaciones de datos
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey, exceptions
import pandas as pd

logger = logging.getLogger(__name__)

class CosmosDBHelper:
    """Helper para operaciones con Azure Cosmos DB"""
    
    def __init__(self, endpoint: str, key: str, database_name: str, container_name: str):
        """
        Inicializa el helper de Cosmos DB
        
        Args:
            endpoint: Endpoint de Cosmos DB
            key: Clave de acceso
            database_name: Nombre de la base de datos
            container_name: Nombre del contenedor
        """
        self.endpoint = endpoint
        self.key = key
        self.database_name = database_name
        self.container_name = container_name
        self.client = None
        self.database = None
        self.container = None
        
    async def connect(self):
        """Conecta al cliente de Cosmos DB"""
        try:
            self.client = CosmosClient(self.endpoint, self.key)
            logger.info("✓ Conexión a Cosmos DB establecida")
            return True
        except Exception as e:
            logger.error(f"Error conectando a Cosmos DB: {e}")
            return False
    
    async def setup_cosmos_resources(self):
        """Configura la base de datos y contenedor si no existen"""
        try:
            # Crear base de datos si no existe
            try:
                self.database = await self.client.create_database_if_not_exists(
                    id=self.database_name
                )
                logger.info(f"✓ Base de datos '{self.database_name}' configurada")
            except exceptions.CosmosResourceExistsError:
                self.database = self.client.get_database_client(self.database_name)
                logger.info(f"✓ Base de datos '{self.database_name}' ya existe")
            
            # Crear contenedor si no existe
            try:
                self.container = await self.database.create_container_if_not_exists(
                    id=self.container_name,
                    partition_key=PartitionKey(path="/id"),
                    offer_throughput=400
                )
                logger.info(f"✓ Contenedor '{self.container_name}' configurado")
            except exceptions.CosmosResourceExistsError:
                self.container = self.database.get_container_client(self.container_name)
                logger.info(f"✓ Contenedor '{self.container_name}' ya existe")
                
            return True
            
        except Exception as e:
            logger.error(f"Error configurando recursos de Cosmos DB: {e}")
            return False
    
    async def upsert_item(self, item: Dict[str, Any]) -> bool:
        """
        Inserta o actualiza un item en el contenedor
        
        Args:
            item: Diccionario con los datos del item
            
        Returns:
            bool: True si fue exitoso, False en caso de error
        """
        try:
            await self.container.upsert_item(item)
            return True
        except Exception as e:
            logger.error(f"Error insertando item {item.get('id', 'unknown')}: {e}")
            return False
    
    async def batch_upsert(self, items: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, int]:
        """
        Inserta múltiples items en lotes
        
        Args:
            items: Lista de items a insertar
            batch_size: Tamaño del lote
            
        Returns:
            Dict con estadísticas de inserción
        """
        total_items = len(items)
        successful = 0
        failed = 0
        
        logger.info(f"Iniciando inserción de {total_items} items en lotes de {batch_size}")
        
        # Procesar en lotes
        for i in range(0, total_items, batch_size):
            batch = items[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_items + batch_size - 1) // batch_size
            
            logger.info(f"Procesando lote {batch_num}/{total_batches}: {len(batch)} items")
            
            # Procesar lote usando tareas concurrentes
            tasks = [self.upsert_item(item) for item in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Contar resultados del lote
            batch_successful = sum(1 for result in results if result is True)
            batch_failed = len(batch) - batch_successful
            
            successful += batch_successful
            failed += batch_failed
            
            logger.info(f"Lote {batch_num}/{total_batches}: {batch_successful} exitosos, {batch_failed} fallidos")
        
        stats = {
            'total': total_items,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total_items) * 100 if total_items > 0 else 0
        }
        
        logger.info(f"Inserción completada: {successful}/{total_items} items exitosos ({stats['success_rate']:.1f}%)")
        return stats
    
    def load_file_to_dataframe(self, file_path: str) -> pd.DataFrame:
        """
        Carga un archivo a DataFrame según su extensión
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            pd.DataFrame: DataFrame con los datos del archivo
        """
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()
        
        try:
            if file_ext == '.csv':
                return pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                return pd.read_excel(file_path)
            elif file_ext == '.json':
                return pd.read_json(file_path)
            else:
                raise ValueError(f"Formato de archivo no soportado: {file_ext}")
        except Exception as e:
            logger.error(f"Error cargando archivo {file_path}: {e}")
            raise

    def generate_item_id(self, row_data: Dict[str, Any], row_index: int) -> str:
        """
        Genera un ID único para el item
        
        Args:
            row_data: Datos de la fila
            row_index: Índice de la fila
            
        Returns:
            str: ID único generado
        """
        # Intentar usar campos comunes como ID
        potential_id_fields = ['id', 'ID', 'obra_id', 'proyecto_id', 'codigo', 'referencia']
        
        for field in potential_id_fields:
            if field in row_data and row_data[field]:
                return str(row_data[field]).strip()
        
        # Si no hay campo ID, generar uno basado en datos
        if 'obra' in row_data and 'fecha' in row_data:
            obra_clean = str(row_data['obra']).strip().replace(' ', '_')
            fecha_clean = str(row_data['fecha']).strip().replace(' ', '_')
            return f"{obra_clean}_{fecha_clean}_{row_index}"
        elif 'nombre' in row_data:
            nombre_clean = str(row_data['nombre']).strip().replace(' ', '_')
            return f"{nombre_clean}_{row_index}"
        else:
            # Último recurso: usar índice y hash de algunos campos
            key_fields = list(row_data.keys())[:3]  # Primeros 3 campos
            key_values = [str(row_data.get(field, '')).strip().replace(' ', '_') for field in key_fields]
            clean_values = [v for v in key_values if v]  # Filtrar valores vacíos
            if clean_values:
                return f"item_{row_index}_{'_'.join(clean_values)}"[:50].strip()
            else:
                return f"item_{row_index}"
    
    async def load_data_from_dataframe(self, df: pd.DataFrame, batch_size: int = 100) -> Dict[str, Any]:
        """
        Carga datos desde un DataFrame a Cosmos DB
        
        Args:
            df: DataFrame con los datos
            batch_size: Tamaño del lote para procesamiento
            
        Returns:
            Dict con estadísticas de carga
        """
        logger.info(f"Preparando {len(df)} registros para carga")
        
        # Convertir DataFrame a lista de diccionarios
        items = []
        for index, row in df.iterrows():
            # Convertir la fila a diccionario y limpiar valores NaN
            item_data = row.to_dict()
            
            # Reemplazar valores NaN con None
            for key, value in item_data.items():
                if pd.isna(value):
                    item_data[key] = None
                elif isinstance(value, (int, float)):
                    # Mantener números como están
                    item_data[key] = value
                else:
                    # Convertir otros tipos a string
                    item_data[key] = str(value)
            
            # Generar ID único
            item_data['id'] = self.generate_item_id(item_data, index)
            
            # Agregar metadatos
            item_data['_loaded_at'] = pd.Timestamp.now().isoformat()
            
            items.append(item_data)
        
        # Cargar datos en lotes
        batch_stats = await self.batch_upsert(items, batch_size)
        
        # Convertir al formato que espera el ETL
        return {
            'success': True,
            'total_records': len(df),
            'successful_inserts': batch_stats['successful'],
            'failed_inserts': batch_stats['failed'],
            'success_rate': batch_stats['success_rate']
        }
    
    async def get_container_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del contenedor
        
        Returns:
            Dict con estadísticas del contenedor
        """
        try:
            # Realizar una consulta simple para contar documentos
            query = "SELECT VALUE COUNT(1) FROM c"
            items = self.container.query_items(
                query=query
            )
            
            count = 0
            async for item in items:
                count = item
                break
            
            return {
                'success': True,
                'total_documents': count
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del contenedor: {e}")
            return {
                'success': False,
                'total_documents': 0
            }

    async def close(self):
        """Cierra la conexión a Cosmos DB"""
        if self.client:
            await self.client.close()
            logger.info("Conexión a Cosmos DB cerrada")
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.connect()
        await self.setup_cosmos_resources()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()