from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do banco de dados
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', '135420')
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
DB_HOST = os.getenv('POSTGRES_HOST', 'db')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(DATABASE_URL, echo=False, future=True)
metadata = MetaData()

# Definição da tabela
messages = Table(
    'messages', metadata,
    Column('id', Integer, primary_key=True),
    Column('author', String(100)),
    Column('content', Text, nullable=False),
    Column('created_at', TIMESTAMP(timezone=True), server_default=func.now())
)

# Criar a tabela se não existir
metadata.create_all(engine)

# Configuração do FastAPI
app = FastAPI(title="Mensagens da Aula")

# Configuração do CORS
FRONT_URL = os.getenv("FRONT_URL", "http://localhost:8080")
origins = [
    FRONT_URL,
    "https://mensagens.lipwfellipe.site",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de entrada
class MessageIn(BaseModel):
    author: str | None = None
    content: str

# Rota POST
@app.post("/api/messages")
def create_message(data: MessageIn):
    try:
        with engine.connect() as conn:
            result = conn.execute(messages.insert().values(**data.dict()))
            conn.commit()
            return {"id": result.inserted_primary_key[0], **data.dict()}
    except SQLAlchemyError as e:
        return {"error": str(e)}

# Rota GET
@app.get("/api/messages")
def list_messages():
    try:
        with engine.connect() as conn:
            # ✅ usar mappings() para retornar dicionários diretamente
            rows = conn.execute(
                messages.select().order_by(messages.c.created_at.desc())
            ).mappings().all()
            return rows  # já é uma lista de dicts, não precisa de dict(r)
    except SQLAlchemyError as e:
        return {"error": str(e)}
    
