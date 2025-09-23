from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Depends,
)
from app.services.file_processor import FileProcessorService
from app.db.mongodb import get_async_database

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
):
    """
    Endpoint para subir archivos vía CURL
    """
    # Obtener el tamaño del archivo
    file_content = await file.read()
    file_size = len(file_content)
    await file.seek(0)  # Regresar al inicio del archivo
    
    
    processor = FileProcessorService()
    result = await processor.process_file(file)
    
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
        "processing_stats": result.get('stats', {})
    }


@router.get("/uploaded-files")
async def get_uploaded_files():
    """
    Endpoint para consultar los nombres de los archivos en la colección 'upload_files'.
    """
    database = get_async_database()
    upload_files_collection = database.uploaded_files

    try:
        uploaded_files = await upload_files_collection.find().to_list(
            length=100
        )  # Limitar a 100 archivos
        file_names = [
            file["collection_name"] for file in uploaded_files
        ]  # Obtener solo los nombres de los archivos
        return file_names
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al consultar archivos subidos: {str(e)}"
        )