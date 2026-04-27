from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from .database import Base

class EmailTask(Base):
    __tablename__ = "email_tasks"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    nome = Column(String)
    assunto = Column(String)
    mensagem = Column(String)
    anexo = Column(String, nullable=True)
    data_envio = Column(DateTime, index=True)  # Data agendada para envio
    enviado = Column(Boolean, default=False, index=True)  # Status
    data_envio_real = Column(DateTime, nullable=True)  # Quando foi realmente enviado
    data_criacao = Column(DateTime, default=datetime.now)  # Quando a tarefa foi criada
    tentativas = Column(Integer, default=0)  # Contador de tentativas
    erro_mensagem = Column(String, nullable=True)  # Última mensagem de erro