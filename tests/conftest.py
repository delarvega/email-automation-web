import pytest
import sys
import os

# Adicionar o diretório pai ao path para importar o app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def test_db():
    """Cria banco de dados de teste"""
    from sqlalchemy import create_engine
    from app.database import Base
    
    # Usar banco de dados em memória para testes
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Configura variáveis de ambiente para teste"""
    monkeypatch.setenv("EMAIL_HOST", "smtp.gmail.com")
    monkeypatch.setenv("EMAIL_PORT", "587")
    monkeypatch.setenv("EMAIL_USER", "test@gmail.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "test_password")
