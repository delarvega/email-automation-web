from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import os
import logging
from datetime import datetime
from .database import Base, engine, SessionLocal
from .models import EmailTask
from .scheduler import iniciar_scheduler_thread

# Configuração de Logging - Simplificada
os.makedirs("data", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/email_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Criar tabelas no banco se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Email Automation Web")

# Mount dos assets estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# INICIAR SCHEDULER NA APLICAÇÃO
@app.on_event("startup")
async def startup_event():
    """Executa ao iniciar a aplicação"""
    logger.info("Iniciando aplicação Email Automation Web...")
    iniciar_scheduler_thread()
    logger.info("Aplicação iniciada com sucesso!")
    logger.info("=" * 60)
    logger.info("[OK] Servidor pronto! Acesse em:")
    logger.info("   [*] http://localhost:8000")
    logger.info("   [*] http://127.0.0.1:8000")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Executa ao desligar a aplicação"""
    logger.info("Aplicação desligando...")


# ============ ROTAS ============

@app.get("/", response_class=HTMLResponse)
async def index():
    """Página inicial com menu principal"""
    logger.info("Acesso à página inicial")
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Automation Web</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .container { background: white; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); padding: 40px; max-width: 500px; text-align: center; }
            h1 { color: #333; margin-bottom: 10px; font-size: 28px; }
            .subtitle { color: #666; margin-bottom: 30px; }
            nav { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
            a { display: block; padding: 12px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; transition: background 0.3s; font-weight: 500; }
            a:hover { background: #764ba2; }
            .stats { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
            .stat-box { display: inline-block; margin: 0 10px; }
            .stat-value { font-size: 24px; font-weight: bold; color: #667eea; }
            .stat-label { font-size: 12px; color: #999; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📧 Email Automation Web</h1>
            <p class="subtitle">Automatize envio de emails em massa</p>
            
            <nav>
                <a href="/upload">📤 Upload de CSV</a>
                <a href="/create">✏️ Criar Emails (Sem CSV)</a>
                <a href="/logs">📋 Histórico de Emails</a>
                <a href="/stats">📊 Estatísticas</a>
            </nav>
            
            <div class="stats" id="stats">
                <p>Carregando estatísticas...</p>
            </div>
        </div>
        
        <script>
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('stats').innerHTML = `
                        <div class="stat-box">
                            <div class="stat-value">${data.total}</div>
                            <div class="stat-label">Total</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">${data.enviados}</div>
                            <div class="stat-label">Enviados</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">${data.pendentes}</div>
                            <div class="stat-label">Pendentes</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-label">Taxa: ${data.taxa_sucesso}</div>
                        </div>
                    `;
                })
                .catch(e => console.log('Erro ao carregar stats'));
        </script>
    </body>
    </html>
    """
    return html


@app.get("/upload", response_class=HTMLResponse)
async def upload_page():
    """Página de upload de CSV"""
    logger.info("Acesso à página de upload")
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upload - Email Automation</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); padding: 40px; }
            h1 { color: #333; margin-bottom: 20px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
            input[type="file"] { width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 5px; }
            button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.3s; }
            button:hover { background: #764ba2; }
            .message { margin-top: 20px; padding: 10px; border-radius: 5px; display: none; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .info { font-size: 14px; color: #666; margin-top: 10px; }
            a { color: #667eea; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📤 Upload de CSV</h1>
            
            <form id="uploadForm">
                <div class="form-group">
                    <label for="csvFile">Selecione o arquivo CSV:</label>
                    <input type="file" id="csvFile" name="file" accept=".csv" required>
                </div>
                
                <div class="info">
                    <strong>Formato esperado:</strong><br>
                    Colunas: email, nome, assunto, mensagem, data_envio<br>
                    Data: YYYY-MM-DD HH:MM:SS (ex: 2026-05-01 10:00:00)
                </div>
                
                <button type="submit">Enviar CSV</button>
            </form>
            
            <div id="message" class="message"></div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <a href="/">← Voltar</a>
            </div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const fileInput = document.getElementById('csvFile');
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {
                    const response = await fetch('/upload', { method: 'POST', body: formData });
                    const data = await response.json();
                    
                    const messageDiv = document.getElementById('message');
                    messageDiv.style.display = 'block';
                    
                    if (data.status === 'ok') {
                        messageDiv.className = 'message success';
                        messageDiv.innerHTML = `✓ ${data.tarefas_criadas} tarefas criadas com sucesso!`;
                        fileInput.value = '';
                    } else {
                        messageDiv.className = 'message error';
                        messageDiv.innerHTML = `✗ Erro: ${data.erros ? data.erros[0] : 'Erro desconhecido'}`;
                    }
                } catch (err) {
                    const messageDiv = document.getElementById('message');
                    messageDiv.className = 'message error';
                    messageDiv.innerHTML = `✗ Erro ao enviar: ${err.message}`;
                    messageDiv.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """
    return html


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Processa upload de arquivo CSV e cria tarefas de envio.
    
    Esperado: CSV com colunas: email, nome, assunto, mensagem, data_envio, anexo (opcional)
    """
    logger.info(f"Iniciando upload do arquivo: {file.filename}")
    db = SessionLocal()
    
    try:
        # Validar extensão do arquivo
        if not file.filename.endswith('.csv'):
            logger.warning(f"Arquivo rejeitado - não é CSV: {file.filename}")
            raise HTTPException(status_code=400, detail="Apenas arquivos CSV são permitidos")
        
        # Ler CSV
        df = pd.read_csv(file.file)
        
        # Validar colunas obrigatórias
        colunas_obrigatorias = {'email', 'nome', 'assunto', 'mensagem', 'data_envio'}
        colunas_presentes = set(df.columns)
        
        if not colunas_obrigatorias.issubset(colunas_presentes):
            colunas_faltando = colunas_obrigatorias - colunas_presentes
            erro = f"Colunas faltando no CSV: {colunas_faltando}"
            logger.error(erro)
            raise HTTPException(status_code=400, detail=erro)
        
        logger.info(f"CSV validado - {len(df)} linhas encontradas")
        
        tarefas_criadas = 0
        erros = []
        
        # Processar cada linha do CSV
        for idx, row in df.iterrows():
            try:
                # Validar email
                email = str(row["email"]).strip()
                if "@" not in email:
                    erro = f"Linha {idx + 2}: Email inválido: {email}"
                    logger.warning(erro)
                    erros.append(erro)
                    continue
                
                # Validar e converter data_envio
                try:
                    data_envio = pd.to_datetime(row["data_envio"])
                except Exception:
                    erro = f"Linha {idx + 2}: Data inválida: {row['data_envio']}"
                    logger.warning(erro)
                    erros.append(erro)
                    continue
                
                # Criar tarefa
                tarefa = EmailTask(
                    email=email,
                    nome=str(row["nome"]).strip(),
                    assunto=str(row["assunto"]).strip(),
                    mensagem=str(row["mensagem"]).strip(),
                    anexo=row.get("anexo", None) if pd.notna(row.get("anexo")) else None,
                    data_envio=data_envio.to_pydatetime()
                )
                db.add(tarefa)
                tarefas_criadas += 1
                
            except Exception as e:
                erro = f"Linha {idx + 2}: Erro ao processar - {str(e)}"
                logger.error(erro)
                erros.append(erro)
                continue
        
        db.commit()
        logger.info(f"✓ {tarefas_criadas} tarefas criadas com sucesso")
        
        resposta = {
            "status": "ok",
            "tarefas_criadas": tarefas_criadas,
            "erros": erros if erros else None
        }
        
        if tarefas_criadas == 0 and erros:
            resposta["status"] = "erro"
        
        return resposta
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")
    finally:
        db.close()


@app.get("/logs", response_class=HTMLResponse)
async def logs():
    """Página de histórico de emails enviados"""
    logger.info("Acesso à página de logs")
    db = SessionLocal()
    try:
        # Busca emails enviados, ordenados por data mais recente
        enviados = db.query(EmailTask).filter(
            EmailTask.enviado == True
        ).order_by(EmailTask.data_envio_real.desc()).limit(100).all()
        
        # Gerar linhas da tabela
        linhas = ""
        if enviados:
            for email in enviados:
                data_envio = email.data_envio_real.strftime("%d/%m/%Y %H:%M") if email.data_envio_real else "N/A"
                linhas += f"""
                <tr>
                    <td>{email.email}</td>
                    <td>{email.nome}</td>
                    <td>{email.assunto[:30]}</td>
                    <td>{data_envio}</td>
                </tr>
                """
        else:
            linhas = "<tr><td colspan='4' style='text-align:center; padding:20px;'>Nenhum email enviado ainda</td></tr>"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Histórico - Email Automation</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
                .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); padding: 40px; }}
                h1 {{ color: #333; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #667eea; color: white; padding: 12px; text-align: left; font-weight: 600; }}
                td {{ padding: 12px; border-bottom: 1px solid #eee; }}
                tr:hover {{ background: #f9f9f9; }}
                .total {{ color: #666; margin: 20px 0; font-weight: 500; }}
                a {{ color: #667eea; text-decoration: none; font-weight: 500; }}
                .nav {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📋 Histórico de Emails Enviados</h1>
                
                <div class="total">Total de emails enviados: <strong>{len(enviados)}</strong></div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Email</th>
                            <th>Nome</th>
                            <th>Assunto</th>
                            <th>Data de Envio</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas}
                    </tbody>
                </table>
                
                <div class="nav">
                    <a href="/">← Voltar</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    finally:
        db.close()


@app.get("/stats", response_class=HTMLResponse)
async def stats_page():
    """Página de estatísticas com visualização"""
    logger.info("Acesso à página de estatísticas")
    db = SessionLocal()
    try:
        total = db.query(EmailTask).count()
        enviados = db.query(EmailTask).filter(EmailTask.enviado == True).count()
        pendentes = db.query(EmailTask).filter(EmailTask.enviado == False).count()
        taxa = f"{(enviados/total*100):.1f}%" if total > 0 else "0%"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Estatísticas - Email Automation</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); padding: 40px; }}
                h1 {{ color: #333; margin-bottom: 30px; text-align: center; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
                .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
                .stat-card.green {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
                .stat-card.orange {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
                .stat-card.blue {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
                .stat-value {{ font-size: 48px; font-weight: bold; margin-bottom: 10px; }}
                .stat-label {{ font-size: 16px; opacity: 0.9; }}
                .progress-container {{ background: #f0f0f0; border-radius: 20px; height: 30px; margin: 20px 0; overflow: hidden; }}
                .progress-bar {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); height: 100%; border-radius: 20px; transition: width 0.5s; }}
                .progress-text {{ text-align: center; margin-top: 10px; color: #666; }}
                a {{ color: #667eea; text-decoration: none; font-weight: 500; }}
                .nav {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Estatísticas de Emails</h1>
                
                <div class="stats-grid">
                    <div class="stat-card blue">
                        <div class="stat-value">{total}</div>
                        <div class="stat-label">Total de Tarefas</div>
                    </div>
                    <div class="stat-card green">
                        <div class="stat-value">{enviados}</div>
                        <div class="stat-label">Enviados</div>
                    </div>
                    <div class="stat-card orange">
                        <div class="stat-value">{pendentes}</div>
                        <div class="stat-label">Pendentes</div>
                    </div>
                </div>
                
                <div class="progress-container">
                    <div class="progress-bar" style="width: {enviados}%;"></div>
                </div>
                <div class="progress-text">Taxa de sucesso: {taxa}</div>
                
                <div class="nav">
                    <a href="/">← Voltar</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    finally:
        db.close()


@app.get("/api/stats", response_class=JSONResponse)
def stats():
    """
    API: Estatísticas de emails
    """
    db = SessionLocal()
    try:
        total = db.query(EmailTask).count()
        enviados = db.query(EmailTask).filter(EmailTask.enviado == True).count()
        pendentes = db.query(EmailTask).filter(EmailTask.enviado == False).count()
        
        return {
            "total": total,
            "enviados": enviados,
            "pendentes": pendentes,
            "taxa_sucesso": f"{(enviados/total*100):.1f}%" if total > 0 else "0%"
        }
    finally:
        db.close()


@app.get("/create", response_class=HTMLResponse)
async def create_page():
    """Página para criar emails em massa sem CSV"""
    logger.info("Acesso à página de criação de emails")
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Criar Emails - Email Automation</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); padding: 40px; }
            h1 { color: #333; margin-bottom: 20px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
            input[type="text"], input[type="datetime-local"], textarea { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px; }
            input:focus, textarea:focus { border-color: #667eea; outline: none; }
            textarea { height: 150px; resize: vertical; }
            .help { font-size: 12px; color: #888; margin-top: 5px; }
            button { padding: 12px 30px; background: #667eea; color: white; border: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.3s; }
            button:hover { background: #764ba2; }
            .btn-secondary { background: #6c757d; margin-left: 10px; }
            .btn-secondary:hover { background: #5a6268; }
            .message { margin-top: 20px; padding: 15px; border-radius: 5px; display: none; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .nav { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
            a { color: #667eea; text-decoration: none; font-weight: 500; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📧 Criar Emails em Massa</h1>
            
            <div class="info">
                <strong>Como usar:</strong><br>
                - Liste os emails dos destinatários (um por linha)<br>
                - O nome será extraído do email ou use o formato: <code>email|nome</code><br>
                - Todos receberam o mesmo assunto e mensagem<br>
                - O scheduler enviará automaticamente na data/hora definida
            </div>
            
            <form id="emailForm">
                <div class="form-group">
                    <label for="destinatarios">Destinatários (emails):</label>
                    <textarea id="destinatarios" name="destinatarios" required placeholder="exemplo1@email.com
exemplo2@email.com
nome|exemplo3@email.com"></textarea>
                    <div class="help">Um email por linha. Opcional: use o formato "nome|email" para nomes personalizados</div>
                </div>
                
                <div class="form-group">
                    <label for="assunto">Assunto:</label>
                    <input type="text" id="assunto" name="assunto" required placeholder="Ex: Newsletter Abril 2026">
                </div>
                
                <div class="form-group">
                    <label for="mensagem">Mensagem:</label>
                    <textarea id="mensagem" name="mensagem" required placeholder="Digite a mensagem que será enviada para todos..."></textarea>
                </div>
                
                <div class="form-group">
                    <label for="data_envio">Data e Hora para Envio:</label>
                    <input type="datetime-local" id="data_envio" name="data_envio" required>
                    <div class="help">Deixe no passado para enviar imediatamente</div>
                </div>
                
                <button type="submit">Criar Tarefas</button>
                <a href="/" class="btn-secondary" style="display: inline-block; padding: 12px 30px; background: #6c757d; color: white; border-radius: 5px; text-decoration: none;">Cancelar</a>
            </form>
            
            <div id="message" class="message"></div>
        </div>
        
        <script>
            document.getElementById('emailForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData();
                formData.append('destinatarios', document.getElementById('destinatarios').value);
                formData.append('assunto', document.getElementById('assunto').value);
                formData.append('mensagem', document.getElementById('mensagem').value);
                formData.append('data_envio', document.getElementById('data_envio').value);
                
                try {
                    const response = await fetch('/create', { method: 'POST', body: formData });
                    const data = await response.json();
                    
                    const messageDiv = document.getElementById('message');
                    messageDiv.style.display = 'block';
                    
                    if (data.status === 'ok') {
                        messageDiv.className = 'message success';
                        messageDiv.innerHTML = `✓ ${data.tarefas_criadas} tarefas criadas com sucesso!`;
                        document.getElementById('emailForm').reset();
                    } else {
                        messageDiv.className = 'message error';
                        messageDiv.innerHTML = `✗ Erro: ${data.detail || 'Erro desconhecido'}`;
                    }
                } catch (err) {
                    const messageDiv = document.getElementById('message');
                    messageDiv.className = 'message error';
                    messageDiv.innerHTML = `✗ Erro ao enviar: ${err.message}`;
                    messageDiv.style.display = 'block';
                }
            });
            
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            document.getElementById('data_envio').value = now.toISOString().slice(0, 16);
        </script>
    </body>
    </html>
    """
    return html


@app.post("/create")
async def create_emails(
    destinatarios: str = Form(...),
    assunto: str = Form(...),
    mensagem: str = Form(...),
    data_envio: str = Form(...)
):
    """
    Cria tarefas de email em massa sem CSV.
    
    Args:
        destinatarios: Um ou mais emails (um por linha, formato: email ou nome|email)
        assunto: Assunto do email
        mensagem: Corpo do email
        data_envio: Data/hora para envio (ISO format)
    """
    logger.info(f"Criando emails em massa para {assunto}")
    db = SessionLocal()
    
    try:
        linhas = destinatarios.strip().split('\n')
        tarefas_criadas = 0
        erros = []
        
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
            
            try:
                if '|' in linha:
                    nome, email = linha.split('|', 1)
                    nome = nome.strip()
                    email = email.strip()
                else:
                    nome = linha.split('@')[0]
                    email = linha
                
                if '@' not in email or '.' not in email:
                    erros.append(f"Email inválido: {email}")
                    continue
                
                from datetime import datetime
                dt_envio = datetime.fromisoformat(data_envio.replace('Z', '+00:00'))
                
                tarefa = EmailTask(
                    email=email,
                    nome=nome,
                    assunto=assunto,
                    mensagem=mensagem,
                    data_envio=dt_envio
                )
                db.add(tarefa)
                tarefas_criadas += 1
                
            except Exception as e:
                erros.append(f"Erro ao processar linha: {linha} - {str(e)}")
                continue
        
        db.commit()
        logger.info(f"✓ {tarefas_criadas} tarefas criadas")
        
        return {
            "status": "ok",
            "tarefas_criadas": tarefas_criadas,
            "erros": erros if erros else None
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()