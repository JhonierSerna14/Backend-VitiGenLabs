from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone

from app.models.user import (
    LoginRequest,
    UserCreate,
    UserResponse,
    SecurityKeyVerify,
    SecurityKeyRequest,
)
from app.services.auth_service import (
    auth_service,  # Instancia de AuthService
    create_user,
    authenticate_user,
    create_access_token,
    get_current_user,
)

router = APIRouter()


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Inicio de sesión de usuario
    - Autentica credenciales
    - Verifica que el email haya sido verificado (solo una vez)
    - Genera token de acceso
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el usuario haya verificado su email (solo la primera vez)
    user_data = await auth_service.get_user_by_email(user.email)
    if not user_data or not getattr(user_data, 'is_verified', False):
        # Solo pedir verificación si el usuario nunca ha verificado su email
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debe verificar su email antes de hacer login. Revise su bandeja de entrada.",
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/register")
async def simple_register(request: LoginRequest):
    username = request.username
    password = request.password
    """
    Registro simple de usuario con solo nombre de usuario y contraseña
    """
    # Validar la longitud de la contraseña antes de crear el modelo
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres.",
        )

    try:
        user_data = UserCreate(email=username, password=password)
        new_user = await create_user(user_data)
        return new_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/verify-security-key")
async def verify_security_key_route(verification: SecurityKeyVerify):
    """
    Verificar clave de seguridad
    """
    try:
        result = await auth_service.verify_security_key(
            verification.email,
            verification.security_key,
        )
        return {"message": "Clave verificada correctamente", "valid": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/request-security-key")
async def request_security_key_route(request: SecurityKeyRequest):
    """
    Solicitar nuevo código de seguridad
    """
    try:
        # Verificar que el usuario existe
        user = await auth_service.get_user_by_email(request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        
        # Generar nuevo código y enviarlo
        new_security_key = auth_service.generate_security_key()
        expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=24)
        
        # Actualizar en base de datos
        await auth_service.users_collection.update_one(
            {"email": request.email},
            {
                "$set": {
                    "security_key": new_security_key,
                    "security_key_expires": expires_at,
                    "is_verified": False
                }
            }
        )
        
        # Enviar email
        auth_service.publish_security_key_email(request.email, new_security_key)
        
        return {"message": "Nuevo código de seguridad enviado a tu email"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al solicitar nuevo código de seguridad",
        )


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Obtener información del usuario actual
    """
    return current_user
