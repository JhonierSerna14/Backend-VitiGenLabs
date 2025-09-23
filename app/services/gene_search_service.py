import re
import asyncio
from typing import Optional
from fastapi import HTTPException
from app.models.gene import GeneSearchResult, GeneCreate
from app.db.mongodb import get_async_database


class GeneSearchService:
    def __init__(self):
        self.db = get_async_database()

    async def verify_user_access(self, collection_name: str, user_email: str):
        """Verificar que el usuario tiene acceso al archivo"""
        uploaded_files = self.db["uploaded_files"]
        file_record = await uploaded_files.find_one({
            "collection_name": collection_name,
            "user_email": user_email
        })
        
        if not file_record:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para acceder a este archivo"
            )

    async def build_sort_criteria(self, sort_by: Optional[str], sort_order: str):
        """Construir criterios de ordenamiento"""
        if not sort_by:
            return {"_id": 1}  # Ordenamiento por defecto
        
        # Mapear nombres de columnas del frontend a campos de la base de datos
        field_mapping = {
            "chrom": "chromosome",
            "pos": "position", 
            "id": "id",
            "ref": "reference",
            "alt": "alternate",
            "qual": "quality",
            "filter": "filter_status",
            "info": "info",
            "format": "format"
        }
        
        field = field_mapping.get(sort_by, sort_by)
        order = 1 if sort_order.lower() == "asc" else -1
        return {field: order}

    async def parallel_search(
        self, 
        query, 
        skip, 
        limit, 
        collection_name: str,
        sort_criteria: dict
    ):
        """Búsqueda paralela con ordenamiento"""
        pipeline = [
            {"$match": query},
            {"$sort": sort_criteria},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "chromosome": 1,
                    "position": 1,
                    "id": 1,
                    "reference": 1,
                    "alternate": 1,
                    "quality": 1,
                    "filter_status": 1,
                    "info": 1,
                    "format": 1,
                    "outputs": 1,
                }
            },
        ]
        cursor = self.db[collection_name].aggregate(pipeline)
        return await cursor.to_list(length=limit)

    async def search(
        self, 
        criteria, 
        page=1, 
        per_page=25, 
        timeout=30, 
        collection_name: str = "genes",
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        user_email: Optional[str] = None
    ):
        """
        Búsqueda de genes con soporte para:
        - Filtros de búsqueda opcionales
        - Ordenamiento por columnas
        - Paginación
        - Verificación de acceso por usuario
        - Procesamiento paralelo
        """
        
        # Verificar acceso del usuario al archivo
        if user_email:
            await self.verify_user_access(collection_name, user_email)
        
        # Construir criterios de ordenamiento
        sort_criteria = await self.build_sort_criteria(sort_by, sort_order)
        
        # Construir query de búsqueda
        if criteria.search and criteria.search.strip():
            search_term = re.escape(criteria.search.strip())
            query = {
                "$or": [
                    {"chromosome": {"$regex": search_term, "$options": "i"}},
                    {"filter_status": {"$regex": search_term, "$options": "i"}},
                    {"info": {"$regex": search_term, "$options": "i"}},
                    {"format": {"$regex": search_term, "$options": "i"}},
                    {"id": {"$regex": search_term, "$options": "i"}},
                    {"reference": {"$regex": search_term, "$options": "i"}},
                    {"alternate": {"$regex": search_term, "$options": "i"}},
                ]
            }
        else:
            # Sin filtros, obtener todos los datos
            query = {}
        
        # Calcular total de resultados
        total_count = await self.db[collection_name].count_documents(query)
        total_pages = (total_count + per_page - 1) // per_page
        
        skip = (page - 1) * per_page
        
        # Realizar búsqueda paralela en chunks
        tasks = []
        partition_size = max(1, per_page // 4)  # Dividir en 4 subconsultas paralelas
        
        for i in range(4):
            chunk_skip = skip + i * partition_size
            chunk_limit = min(partition_size, per_page - i * partition_size)
            if chunk_limit > 0:
                tasks.append(
                    self.parallel_search(
                        query, chunk_skip, chunk_limit, collection_name, sort_criteria
                    )
                )
        
        try:
            async with asyncio.timeout(timeout):
                results = await asyncio.gather(*tasks)
                flattened_results = [item for sublist in results for item in sublist]

                # Mapear los campos del backend a los nombres esperados por el frontend
                genes = []
                for doc in flattened_results:
                    gene = {
                        "chrom": doc.get("chromosome", ""),
                        "pos": doc.get("position", 0),
                        "id": doc.get("id", ""),
                        "ref": doc.get("reference", ""),
                        "alt": doc.get("alternate", ""),
                        "qual": doc.get("quality", 0.0),
                        "filter": doc.get("filter_status", ""),
                        "info": doc.get("info", ""),
                        "format": doc.get("format", "")
                    }
                    # Agregar las columnas dinámicas (outputs)
                    outputs = doc.get("outputs", {})
                    if isinstance(outputs, dict):
                        gene.update(outputs)
                    
                    genes.append(gene)

                return GeneSearchResult(
                    genes=genes,
                    total=total_count,
                    page=page,
                    per_page=per_page,
                    total_pages=total_pages
                )

        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408,
                detail="La búsqueda tomó demasiado tiempo.",
            )
