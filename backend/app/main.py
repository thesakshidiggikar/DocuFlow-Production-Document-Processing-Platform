import os, uuid
from datetime import datetime, timedelta, timezone
import boto3
from botocore.client import Config
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, String, Text, DateTime, Integer, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

DB=os.environ["DATABASE_URL"]
engine=create_engine(DB,pool_pre_ping=True)
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")
SECRET=os.environ["JWT_SECRET"]
S3=boto3.client("s3",endpoint_url=os.getenv("S3_ENDPOINT_URL"),region_name=os.getenv("S3_REGION"),aws_access_key_id=os.getenv("S3_ACCESS_KEY"),aws_secret_access_key=os.getenv("S3_SECRET_KEY"),config=Config(signature_version="s3v4"))
SQS=boto3.client("sqs",endpoint_url=os.getenv("SQS_ENDPOINT_URL"),region_name=os.getenv("S3_REGION"),aws_access_key_id=os.getenv("S3_ACCESS_KEY"),aws_secret_access_key=os.getenv("S3_SECRET_KEY"))
BUCKET=os.getenv("S3_BUCKET","docuflow")
QUEUE=os.environ["SQS_QUEUE_URL"]

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    email:Mapped[str]=mapped_column(String(255),unique=True,index=True)
    password_hash:Mapped[str]=mapped_column(String(255))
class Document(Base):
    __tablename__="documents"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    filename:Mapped[str]=mapped_column(String(255))
    object_key:Mapped[str]=mapped_column(String(500),unique=True)
    status:Mapped[str]=mapped_column(String(30),default="PENDING",index=True)
    extracted_text:Mapped[str|None]=mapped_column(Text,nullable=True)
    error_message:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
Base.metadata.create_all(engine)
app=FastAPI(title="DocuFlow API",version="1.0.0")
class Auth(BaseModel): email:EmailStr; password:str

def token(uid): return jwt.encode({"sub":str(uid),"exp":datetime.now(timezone.utc)+timedelta(hours=12)},SECRET,algorithm="HS256")
def user(authorization:str=Header(...),db:Session=Depends(lambda:Session(engine))):
    if not authorization.startswith("Bearer "): raise HTTPException(401,"Bearer token required")
    try: uid=int(jwt.decode(authorization[7:],SECRET,algorithms=["HS256"])["sub"])
    except Exception: raise HTTPException(401,"Invalid token")
    u=db.get(User,uid)
    if not u: raise HTTPException(401,"User not found")
    return u
@app.get("/health")
def health(): return {"status":"ok","service":"docuflow-api"}
@app.post("/api/auth/register")
def register(a:Auth):
    with Session(engine) as db:
        if db.scalar(select(User).where(User.email==a.email)): raise HTTPException(409,"Email already registered")
        u=User(email=a.email,password_hash=pwd.hash(a.password)); db.add(u); db.commit(); db.refresh(u); return {"access_token":token(u.id)}
@app.post("/api/auth/login")
def login(a:Auth):
    with Session(engine) as db:
        u=db.scalar(select(User).where(User.email==a.email))
        if not u or not pwd.verify(a.password,u.password_hash): raise HTTPException(401,"Invalid credentials")
        return {"access_token":token(u.id)}
@app.post("/api/documents")
async def upload(file:UploadFile=File(...),u=Depends(user)):
    data=await file.read()
    if len(data)>10*1024*1024: raise HTTPException(413,"Maximum file size is 10MB")
    key=f"{u.id}/{uuid.uuid4()}-{file.filename}"
    S3.put_object(Bucket=BUCKET,Key=key,Body=data,ContentType=file.content_type or "application/octet-stream")
    with Session(engine) as db:
        d=Document(user_id=u.id,filename=file.filename,object_key=key); db.add(d); db.commit(); db.refresh(d)
        SQS.send_message(QueueUrl=QUEUE,MessageBody=str(d.id)); return {"id":d.id,"filename":d.filename,"status":d.status}
@app.get("/api/documents")
def documents(u=Depends(user)):
    with Session(engine) as db:
        return [{"id":d.id,"filename":d.filename,"status":d.status,"error":d.error_message} for d in db.scalars(select(Document).where(Document.user_id==u.id).order_by(Document.id.desc()))]
