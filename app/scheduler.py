import schedule
import time
import logging
import threading
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import EmailTask
from .mailer import enviar_email

# Configuração de Logging
logger = logging.getLogger(__name__)

# Flag para controlar o scheduler
scheduler_ativo = False


def processar_envios():
    """
    Processa todas as tarefas de email agendadas.
    Envia emails cuja data_envio já passou.
    """
    try:
        db: Session = SessionLocal()
        
        # Busca tarefas não enviadas
        tarefas = db.query(EmailTask).filter(EmailTask.enviado == False).all()
        
        if not tarefas:
            logger.debug("Nenhuma tarefa pendente para processar")
            return
        
        logger.info(f"Processando {len(tarefas)} tarefas pendentes")
        
        for tarefa in tarefas:
            # Verifica se chegou a hora de enviar
            if tarefa.data_envio <= datetime.now():
                logger.info(f"Enviando email para: {tarefa.email}")
                
                # Tenta enviar
                sucesso = enviar_email(
                    destinatario=tarefa.email,
                    assunto=tarefa.assunto,
                    mensagem=tarefa.mensagem,
                    anexo=tarefa.anexo
                )
                
                if sucesso:
                    tarefa.enviado = True
                    tarefa.data_envio_real = datetime.now()  # Registra hora real de envio
                    db.commit()
                    logger.info(f"✓ Tarefa {tarefa.id} marcada como enviada")
                else:
                    logger.warning(f"✗ Falha ao enviar tarefa {tarefa.id}")
                    # Tarefa mantém estado de não enviada para retry posterior
                    
    except Exception as e:
        logger.error(f"Erro crítico ao processar envios: {e}", exc_info=True)
    finally:
        db.close()


def iniciar_scheduler():
    """
    Inicia o agendador de tarefas.
    Executa processar_envios a cada 1 minuto.
    """
    global scheduler_ativo
    
    logger.info("=== SCHEDULER INICIADO ===")
    scheduler_ativo = True
    
    # Agenda a verificação a cada 1 minuto
    schedule.every(1).minutes.do(processar_envios)
    
    try:
        while scheduler_ativo:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro no loop do scheduler: {e}", exc_info=True)
    finally:
        scheduler_ativo = False
        logger.info("=== SCHEDULER FINALIZADO ===")


def parar_scheduler():
    """Sinaliza o scheduler para parar."""
    global scheduler_ativo
    scheduler_ativo = False
    logger.info("Comando para parar scheduler enviado")


def iniciar_scheduler_thread():
    """
    Inicia o scheduler em uma thread separada (daemon).
    Ideal para aplicações web como FastAPI.
    """
    logger.info("Iniciando scheduler em thread separada (daemon)...")
    thread = threading.Thread(target=iniciar_scheduler, daemon=True)
    thread.start()
    logger.info("Thread do scheduler iniciada")
    return thread