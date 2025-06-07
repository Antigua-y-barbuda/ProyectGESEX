from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Carga las variables de entorno desde un archivo .env
load_dotenv()

# Configuración (usa variables de entorno en producción!)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") 
SECRET_KEY = os.getenv("SECRET_KEY")  # Cambia esto!
ALGORITHM = "HS256"

# Para extraer el token desde Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # tokenUrl no se usa, pero es requerido por FastAPI


def verify_google_token(token: str):
    """Verifica el token de Google y devuelve datos del usuario"""
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Validación adicional (opcional)
        if not idinfo.get("email_verified", False):
            raise HTTPException(400, "Email no verificado por Google")

        return {
            "email": idinfo["email"],
            "name": idinfo.get("name", "Usuario"),
            "picture": idinfo.get("picture")
        }

    except ValueError as e:
        raise HTTPException(401, f"Token inválido: {str(e)}")


def create_jwt_token(email: str):
    """Crea un JWT para sesiones en tu sistema"""
    expires = datetime.utcnow() + timedelta(hours=2)
    payload = {
        "sub": email,
        "exp": expires
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_email(token: str = Depends(oauth2_scheme)) -> str:
    """Extrae el email del usuario desde el JWT en la cabecera Authorization"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido: email no encontrado")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")