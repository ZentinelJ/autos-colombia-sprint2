from pydantic import BaseModel

class CeldaCreateDTO(BaseModel):
    identificador: str

class CeldaRangoDTO(BaseModel):
    prefijo: str
    desde: int
    hasta: int
