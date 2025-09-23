from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Depends,
)
from typing import List
from app.services.file_processor import FileProcessorService
from app.db.mongodb import get_async_database
from app.services.auth_service import get_current_user
from app.models.user import UserResponse

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint para subir archivos vía CURL con asociación al usuario
    """
    # Obtener el tamaño del archivo
    file_content = await file.read()
    file_size = len(file_content)
    await file.seek(0)  # Regresar al inicio del archivo
    
    
    processor = FileProcessorService()
    result = await processor.process_file(file, current_user.email)  # Pasar email del usuario
    
    if result['status'] == "error":
        error_message = result.get('message', 'Error desconocido durante el procesamiento')
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el archivo: {error_message}"
        )

    # Handle both old and new response formats
    if 'data' in result:
        # Old format compatibility
        data = result['data']
        total_genes = data.get('total_genes', 0)
        file_path = str(data.get('file_path', ''))
    else:
        # New format
        stats = result.get('stats', {})
        total_genes = stats.get('total_genes', 0)
        file_path = result.get('file_id', '')

    return {
        "message": "Archivo subido exitosamente",
        "file_id": file_path,
        "total_genes": total_genes,
        "file_size": file_size,
        "filename": file.filename,
        "processing_stats": result.get('stats', {}),
        "user_email": current_user.email
    }


@router.get("/uploaded-files")
async def get_uploaded_files(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint para consultar los archivos del usuario actual.
    """
    database = get_async_database()
    upload_files_collection = database.uploaded_files

    try:
        # Filtrar archivos por usuario
        uploaded_files = await upload_files_collection.find(
            {"user_email": current_user.email}
        ).to_list(length=100)  # Limitar a 100 archivos
        
        file_info = []
        for file in uploaded_files:
            file_info.append({
                "collection_name": file["collection_name"],
                "original_filename": file.get("original_filename", file["collection_name"]),
                "upload_date": file.get("upload_date"),
                "file_size": file.get("file_size"),
                "total_genes": file.get("total_genes"),
                "user_email": file.get("user_email")
            })
        
        return file_info
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al consultar archivos subidos: {str(e)}"
        )


@router.delete("/delete-file/{collection_name}")
async def delete_file(
    collection_name: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint para eliminar un archivo específico del usuario.
    """
    database = get_async_database()
    upload_files_collection = database.uploaded_files

    try:
        # Verificar que el archivo pertenece al usuario
        file_record = await upload_files_collection.find_one({
            "collection_name": collection_name,
            "user_email": current_user.email
        })
        
        if not file_record:
            raise HTTPException(
                status_code=404,
                detail="Archivo no encontrado o no tienes permisos para eliminarlo"
            )

        # Eliminar la colección de datos genéticos
        genes_collection = database[collection_name]
        await genes_collection.drop()

        # Eliminar el registro del archivo
        await upload_files_collection.delete_one({
            "collection_name": collection_name,
            "user_email": current_user.email
        })

        return {
            "message": f"Archivo {collection_name} eliminado exitosamente",
            "deleted_collection": collection_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar el archivo: {str(e)}"
        )


@router.delete("/delete-files")
async def delete_multiple_files(
    collection_names: List[str],
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint para eliminar múltiples archivos del usuario.
    """
    database = get_async_database()
    upload_files_collection = database.uploaded_files

    try:
        deleted_files = []
        failed_files = []

        for collection_name in collection_names:
            try:
                # Verificar que el archivo pertenece al usuario
                file_record = await upload_files_collection.find_one({
                    "collection_name": collection_name,
                    "user_email": current_user.email
                })
                
                if not file_record:
                    failed_files.append({
                        "collection_name": collection_name,
                        "error": "Archivo no encontrado o sin permisos"
                    })
                    continue

                # Eliminar la colección de datos genéticos
                genes_collection = database[collection_name]
                await genes_collection.drop()

                # Eliminar el registro del archivo
                await upload_files_collection.delete_one({
                    "collection_name": collection_name,
                    "user_email": current_user.email
                })

                deleted_files.append(collection_name)
            except Exception as e:
                failed_files.append({
                    "collection_name": collection_name,
                    "error": str(e)
                })

        return {
            "message": f"Proceso completado. {len(deleted_files)} archivos eliminados",
            "deleted_files": deleted_files,
            "failed_files": failed_files
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar archivos: {str(e)}"
        )