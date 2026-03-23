from pydantic import BaseModel
from typing import Optional

class UsuarioOperarioCreateDTO(BaseModel):
    dni: str
    nombres: str
    movil: str
    correo: str
    login: str
    password: str

class ClienteCreateDTO(BaseModel):
    dni: str
    nombres: str
    movil: str
    correo: str
    placa: str
    marca: str
    modelo: str

class UsuarioUpdateDTO(BaseModel):
    nombres: str
    movil: str
    correo: str
    login: Optional[str] = None
    password: Optional[str] = None

class UsuarioLoginDTO(BaseModel):
    login: str
    password: str
