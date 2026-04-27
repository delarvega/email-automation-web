# Email Automation Web
Sistema completo de automação de emails com FastAPI, envio via Gmail, anexos, agendamento e logs.
# Email Automation Web

Aplicação web desenvolvida para automatizar o envio de emails utilizando Gmail SMTP, com suporte a anexos, agendamento automático e gestão de logs.  
O sistema permite carregar ficheiros CSV com listas de destinatários, configurar mensagens e acompanhar o histórico de envios através de uma interface simples e funcional.

---

## 🚀 Funcionalidades

- Upload de ficheiros CSV com dados de envio  
- Envio de emails via Gmail SMTP  
- Suporte a anexos  
- Agendamento automático de envios  
- Base de dados local (SQLite) para gestão das tarefas  
- Logs de envios acessíveis pela interface web  
- Interface simples construída com HTML, CSS e FastAPI (Jinja2)

---

## 🛠️ Tecnologias Utilizadas

- **Python 3**  
- **FastAPI**  
- **SQLite**  
- **SQLAlchemy**  
- **Jinja2**  
- **Schedule**  
- **Pandas**  
- **Gmail SMTP**  
- **HTML / CSS / JavaScript**

---

## 📁 Estrutura do Projeto

```
email-automation-web/
│
├── app/
│   ├── main.py
│   ├── scheduler.py
│   ├── mailer.py
│   ├── database.py
│   ├── models.py
│   ├── templates/
│   │     ├── index.html
│   │     ├── upload.html
│   │     ├── schedule.html
│   │     └── logs.html
│   └── static/
│         ├── style.css
│         └── script.js
│
├── config/
│     └── settings_example.env
│
├── data/
│     ├── uploads/
│     └── logs/
│           └── .gitkeep
│
├── tests/
│     └── test_mailer.py
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

## ⚙️ Configuração

1. Crie um ficheiro `.env` baseado em `settings_example.env`:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_app_password
```

> Para Gmail, é necessário gerar uma **App Password** na conta Google.

---

## ▶️ Como executar localmente

1. Instale as dependências:

```
pip install -r requirements.txt
```

2. Inicie o servidor FastAPI:

```
uvicorn app.main:app --reload
```

3. Aceda no navegador:

```
http://localhost:8000
```

---

## 📦 Como utilizar

### **1. Preparar o CSV**
O ficheiro deve conter as colunas:

- `email`  
- `nome`  
- `assunto`  
- `mensagem`  
- `data_envio` (formato ISO: `2024-05-01 10:30:00`)  
- `anexo` (opcional, caminho do ficheiro)

### **2. Fazer upload**
Aceda à página de upload e envie o CSV.

### **3. Agendamento automático**
O sistema verifica periodicamente as tarefas e envia os emails na data/hora definida.

### **4. Consultar logs**
A página de logs mostra todos os envios concluídos.

---

## 🧪 Testes

O projeto inclui testes básicos para o módulo de envio de emails:

```
pytest
```

---

## 👤 Autor

Desenvolvido por **Thiago**.

