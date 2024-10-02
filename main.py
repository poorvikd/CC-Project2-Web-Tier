from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import Base, Face
from schemas import FaceSchema
from database import SessionLocal, engine
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/hello")
async def root():
    return {"message": "Hello World"}

@app.post('/add_face')
async def add_face(request: FaceSchema, db: Session = Depends(get_db)):
    face = Face(name=request.name, image_name=request.image_name)
    db.add(face)
    db.commit()
    db.refresh(face)
    return face

@app.post('/')
async def get_face(inputFile: UploadFile = File(...), db: Session = Depends(get_db)):

    filename = inputFile.filename.split('.')[0]

    print(filename)
    face = db.query(Face).filter(Face.image_name == filename).first()
    if face is None:
        raise HTTPException(status_code=404, detail="Face not found")
    return JSONResponse(status_code=200, content = {filename: face.name})
