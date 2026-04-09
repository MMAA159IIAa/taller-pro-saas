from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    taller_id: Optional[int] = None

class EmpleadoBase(BaseModel):
    email: str
    nombre: str
    rol: str

class EmpleadoCreate(EmpleadoBase):
    password: str
    taller_id: int

class TallerBase(BaseModel):
    nombre: str

class TallerCreate(TallerBase):
    pass

class Taller(TallerBase):
    id: int
    suscripcion_activa: bool
    plan: str
    activation_key: Optional[str] = None
    fecha_vencimiento: Optional[datetime] = None

    class Config:
        from_attributes = True

class LicenseCheck(BaseModel):
    taller_id: int
    taller_name: str
    status: str # activo, suspendido
    mensaje: str
    fecha_vencimiento: Optional[datetime] = None
