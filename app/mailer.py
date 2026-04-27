import smtplib
from email.message import EmailMessage
import os
import logging
import time
from dotenv import load_dotenv

load_dotenv()

# Configuração de Logging
logger = logging.getLogger(__name__)

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Configurações de retry
MAX_RETRIES = 3
RETRY_DELAY = 5  # segundos


def enviar_email(destinatario: str, assunto: str, mensagem: str, anexo: str = None) -> bool:
    """
    Envia um email com suporte a retry automático.
    
    Args:
        destinatario: Email do destinatário
        assunto: Assunto do email
        mensagem: Corpo do email
        anexo: Caminho do arquivo anexo (opcional)
        
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    
    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Tentativa {tentativa}/{MAX_RETRIES}: Enviando email para {destinatario}")
            
            msg = EmailMessage()
            msg["From"] = EMAIL_USER
            msg["To"] = destinatario
            msg["Subject"] = assunto
            msg.set_content(mensagem)

            # Adiciona anexo se fornecido
            if anexo:
                if not os.path.exists(anexo):
                    logger.error(f"Arquivo anexo não encontrado: {anexo}")
                    return False
                    
                with open(anexo, "rb") as f:
                    file_data = f.read()
                    file_name = os.path.basename(anexo)
                msg.add_attachment(file_data, maintype="application", 
                                 subtype="octet-stream", filename=file_name)
                logger.debug(f"Anexo adicionado: {file_name}")

            # Conecta e envia
            with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
                smtp.starttls()
                smtp.login(EMAIL_USER, EMAIL_PASSWORD)
                smtp.send_message(msg)
            
            logger.info(f"✓ Email enviado com sucesso para {destinatario}")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Erro: Arquivo não encontrado - {e}")
            return False
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Erro de autenticação SMTP - Verifique EMAIL_USER e EMAIL_PASSWORD")
            return False
            
        except smtplib.SMTPException as e:
            logger.warning(f"Erro SMTP na tentativa {tentativa}/{MAX_RETRIES}: {e}")
            if tentativa < MAX_RETRIES:
                logger.info(f"Aguardando {RETRY_DELAY}s antes de retry...")
                time.sleep(RETRY_DELAY)
                continue
            else:
                logger.error(f"Falha ao enviar email para {destinatario} após {MAX_RETRIES} tentativas")
                return False
                
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar email para {destinatario}: {e}")
            return False
    
    return False