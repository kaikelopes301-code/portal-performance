# auth.py — Sistema de autenticação seguro com JWT

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÃO DE SEGURANÇA
# ============================================================================

# Contexto de criptografia para senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de autenticação Bearer
security = HTTPBearer(auto_error=False)

# Senha padrão segura (DEVE ser alterada via variável de ambiente em produção)
DEFAULT_ADMIN_PASSWORD = "Atl@s#P3rf0rm@nc3!2025$Secure"

# ============================================================================
# SCHEMAS
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos

class TokenData(BaseModel):
    username: Optional[str] = None
    exp: Optional[datetime] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    access_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None  # segundos
    message: Optional[str] = None

class UserInfo(BaseModel):
    username: str
    is_admin: bool = True

# ============================================================================
# FUNÇÕES DE HASH E VERIFICAÇÃO
# ============================================================================

# Cache do hash da senha admin (gerado uma única vez)
_cached_admin_hash: str | None = None

def get_password_hash(password: str) -> str:
    """Gera o hash bcrypt de uma senha."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Erro ao verificar senha: {e}")
        return False

def get_admin_password_hash() -> str:
    """
    Obtém o hash da senha do admin.
    Se ADMIN_PASSWORD_HASH estiver configurado, usa ele.
    Caso contrário, gera o hash da senha padrão (cacheado).
    """
    global _cached_admin_hash
    
    # Se há hash configurado via variável de ambiente, usa ele
    if settings.admin_password_hash and len(settings.admin_password_hash) > 50:
        return settings.admin_password_hash
    
    # Gera e cacheia o hash da senha padrão
    if _cached_admin_hash is None:
        _cached_admin_hash = get_password_hash(DEFAULT_ADMIN_PASSWORD)
        logger.info(f"Hash da senha admin gerado")
    
    return _cached_admin_hash

# ============================================================================
# FUNÇÕES DE JWT
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT com os dados fornecidos.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt

def decode_token(token: str) -> Optional[TokenData]:
    """
    Decodifica e valida um token JWT.
    Retorna TokenData se válido, None se inválido.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        username: str = payload.get("sub")
        exp: datetime = datetime.fromtimestamp(payload.get("exp", 0))
        
        if username is None:
            return None
            
        return TokenData(username=username, exp=exp)
        
    except JWTError as e:
        logger.warning(f"Erro ao decodificar token: {e}")
        return None

# ============================================================================
# AUTENTICAÇÃO DE USUÁRIO
# ============================================================================

def authenticate_user(username: str, password: str) -> Optional[UserInfo]:
    """
    Autentica o usuário admin.
    Retorna UserInfo se credenciais válidas, None se inválidas.
    """
    # Verifica se é o usuário admin
    if username.lower().strip() != settings.admin_username.lower():
        logger.warning(f"Tentativa de login com usuário inválido: {username}")
        return None
    
    # Obtém o hash da senha do admin
    admin_hash = get_admin_password_hash()
    
    # Verifica a senha
    if not verify_password(password, admin_hash):
        logger.warning(f"Senha incorreta para usuário: {username}")
        return None
    
    logger.info(f"Login bem-sucedido para usuário: {username}")
    return UserInfo(username=username, is_admin=True)

# ============================================================================
# DEPENDÊNCIAS DE AUTENTICAÇÃO
# ============================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserInfo:
    """
    Dependência que extrai e valida o usuário do token JWT.
    Levanta HTTPException 401 se não autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        raise credentials_exception
    
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data is None:
        raise credentials_exception
    
    # Verifica se o token não expirou
    if token_data.exp and token_data.exp < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserInfo(username=token_data.username, is_admin=True)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserInfo]:
    """
    Dependência opcional - não levanta erro se não autenticado.
    Retorna None se não autenticado, UserInfo se autenticado.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

# ============================================================================
# ROTAS PÚBLICAS (sem autenticação)
# ============================================================================

PUBLIC_ROUTES = [
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/auth/login",
    "/api/auth/status",
]

def is_public_route(path: str) -> bool:
    """Verifica se a rota é pública."""
    return any(path.startswith(route) or path == route for route in PUBLIC_ROUTES)

# ============================================================================
# FUNÇÃO DE LOGIN
# ============================================================================

def login_user(username: str, password: str) -> LoginResponse:
    """
    Realiza o login do usuário e retorna o token JWT.
    """
    user = authenticate_user(username, password)
    
    if not user:
        return LoginResponse(
            success=False,
            message="Usuário ou senha inválidos"
        )
    
    # Cria o token JWT
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        success=True,
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60  # em segundos
    )

# ============================================================================
# GERADOR DE HASH PARA CONFIGURAÇÃO INICIAL
# ============================================================================

def generate_password_hash_for_env():
    """
    Gera o hash da senha padrão para ser usado em variáveis de ambiente.
    Execute este script para obter o hash:
    
    python -c "from app.auth import generate_password_hash_for_env; generate_password_hash_for_env()"
    """
    password = DEFAULT_ADMIN_PASSWORD
    hash_value = get_password_hash(password)
    print("=" * 60)
    print("CONFIGURAÇÃO DE SENHA PARA PRODUÇÃO")
    print("=" * 60)
    print(f"\nSenha padrão: {password}")
    print(f"\nHash bcrypt (adicione ao .env como ADMIN_PASSWORD_HASH):")
    print(f"\nADMIN_PASSWORD_HASH={hash_value}")
    print("\n" + "=" * 60)
    return hash_value

if __name__ == "__main__":
    generate_password_hash_for_env()
