from pydantic import BaseModel

class PagoCreateDTO(BaseModel):
    criterio: str
    monto: float

class PagoBuscarDTO(BaseModel):
    criterio: str
