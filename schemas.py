from pydantic import  BaseModel

class FaceSchema(BaseModel):
    id: int
    name: str
    image_name: str

class FaceQuery(BaseModel):
    name: str
    image_name: str
    class Config:
        orm_mode = True