from pydantic import BaseModel

class NovedadCreateDTO(BaseModel):
    placa_vehiculo: str
    descripcion: str
