from fastapi import FastAPI, Depends
from app.database import Base, engine
from app.routes import auth
from app.models.user import User
from app.core.deps import get_current_user
from app.models.profile import MedicalProfile
from app.routes import profile
from app.models.emergency import Emergency
from app.routes import emergency





app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth")
app.include_router(profile.router)
app.include_router(emergency.router)


@app.get("/")
def root():
    return {"message": "MedRoute API running"}


@app.get("/protected")
def protected_route(user_id: str = Depends(get_current_user)):
    return {"message": "Access granted", "user_id": user_id}