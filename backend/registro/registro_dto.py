from pydantic import BaseModel

class RegistroCreateDTO(BaseModel):
    placa_vehiculo: str

class RegistroSalidaDTO(BaseModel):
    placa_vehiculo: str
