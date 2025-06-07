from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, date

from app.database import get_db
from app.models.Respuestas import Respuesta
from app.models.Test import Test
from app.models.Segmentacion import Segmentacion
from app.schemas.Respuestas import RespuestaCreate, RespuestaOut

router = APIRouter(prefix="/Respuestas", tags=["Respuestas"])

@router.post("/", response_model=RespuestaOut)
def enviar_respuesta(respuesta: RespuestaCreate, db: Session = Depends(get_db)):
    """
    Recibe y guarda una respuesta a un test.

    - Verifica si ya existe una respuesta para el mismo test y fingerprint (previene duplicados).
    - Si no existe, guarda la nueva respuesta en la base de datos.
    - Calcula la categoría del usuario según sus respuestas y la actualiza en el test correspondiente.
    - Retorna la respuesta guardada.

    Args:
        respuesta (RespuestaCreate): Datos de la respuesta enviada por el usuario.
        db (Session): Sesión de base de datos proporcionada por FastAPI.

    Returns:
        RespuestaOut: Objeto con la información de la respuesta guardada.

    Raises:
        HTTPException: Si ya existe una respuesta para ese test y fingerprint.
    """
    existente = db.query(Respuesta).filter_by(
        test_id=respuesta.test_id,
        fingerprint=respuesta.fingerprint
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya se ha respondido este test desde esta sesión."
        )
    nueva = Respuesta(
        test_id=respuesta.test_id,
        respuestas=[r.dict() for r in respuesta.respuestas],
        caracterizacion_datos=respuesta.caracterizacion_datos,
        fecha=respuesta.fecha,
        fingerprint = respuesta.fingerprint
    )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    categoria = Segmentacion.calcular_categoria(nueva.respuestas)

    test = db.query(Test).filter_by(id=respuesta.test_id).first()
    if test:
        test.categoria = categoria
        db.commit()

    return nueva

# GET general para ver todas las respuestas
@router.get("/", response_model=list[RespuestaOut])
def listar_respuestas(db: Session = Depends(get_db)):
    return db.query(Respuesta).all()