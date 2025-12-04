# routers/auth.py — Rotas de autenticação

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.auth import (
    LoginRequest, 
    LoginResponse, 
    UserInfo,
    login_user,
    get_current_user,
    get_current_user_optional
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticação"]
)

# ============================================================================
# SCHEMAS DE RESPOSTA
# ============================================================================

class StatusResponse(BaseModel):
    authenticated: bool
    user: Optional[str] = None
    message: str

# ============================================================================
# ROTAS
# ============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Realiza login e retorna um token JWT.
    
    **Credenciais padrão:**
    - Usuário: `atlas.admin@performance`
    - Senha: Definida via variável de ambiente ou padrão seguro
    
    **Retorna:**
    - `access_token`: Token JWT para autenticação
    - `token_type`: Tipo do token (sempre "bearer")
    - `expires_in`: Tempo de expiração em segundos
    """
    result = login_user(request.username, request.password)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.message or "Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result

@router.get("/status", response_model=StatusResponse)
async def auth_status(user: Optional[UserInfo] = Depends(get_current_user_optional)):
    """
    Verifica o status de autenticação do usuário atual.
    
    **Headers necessários:**
    - `Authorization: Bearer <token>`
    
    **Retorna:**
    - `authenticated`: Se o usuário está autenticado
    - `user`: Nome do usuário (se autenticado)
    """
    if user:
        return StatusResponse(
            authenticated=True,
            user=user.username,
            message="Usuário autenticado"
        )
    
    return StatusResponse(
        authenticated=False,
        message="Não autenticado"
    )

@router.post("/logout")
async def logout(user: UserInfo = Depends(get_current_user)):
    """
    Realiza logout (invalida o token no cliente).
    
    **Nota:** Como usamos JWT stateless, o logout é feito no cliente
    removendo o token do armazenamento local.
    
    **Headers necessários:**
    - `Authorization: Bearer <token>`
    """
    return {
        "success": True,
        "message": "Logout realizado com sucesso. Remova o token do cliente."
    }

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(user: UserInfo = Depends(get_current_user)):
    """
    Retorna informações do usuário atual.
    
    **Headers necessários:**
    - `Authorization: Bearer <token>`
    """
    return user
