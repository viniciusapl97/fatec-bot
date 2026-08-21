# Jovis — seu assistente acadêmico no Telegram 🎓

### O que é
O Jovis é um bot de Telegram para organizar a vida na faculdade em um lugar só. Em vez de planilhas, apps diferentes e notas perdidas, você conversa com o bot e registra matérias, provas, trabalhos, faltas e notas. A ideia é ser simples de usar no dia a dia.

O tom do bot foi inspirado em um professor querido: direto, gentil e que puxa para o foco quando precisa.

### O que ele faz
* **Matérias:** cadastrar, editar, excluir e ver a grade (nome, professor, sala, semestre, horários).
* **Atividades:** separar Trabalhos e Provas com data e observações.
* **Faltas:** registrar ausências por matéria e ajustar quando necessário.
* **Notas:** lançar P1, P2, trabalhos e outras avaliações.
* **Relatórios:**
    * `/hoje`: aulas e entregas do dia.
    * `/semana`: visão dos próximos 7 dias.
    * `/relatorio`: dossiê de uma matéria (dados, atividades, notas e faltas).
* **Importação em massa:** comando opcional `/import` (para admin) que lê um JSON com todas as matérias do semestre.
* **Acesso controlado:** whitelist para uso em desenvolvimento.
* **Navegação:** menu principal via `/start`.

### Stack
* **Python 3.11+**
* **`python-telegram-bot` v20+**
* **PostgreSQL**
* **SQLAlchemy 2.0**
* `psycopg2-binary`, `python-dotenv`

### Como o projeto está organizado
Usei uma organização em camadas para separar responsabilidades e facilitar manutenção:

* **Handlers (`bot/handlers/`):** recebem comandos e cliques e chamam os serviços.
* **Services (`bot/services/`):** regras de negócio (ex.: criar/atualizar uma matéria).
* **Models (`bot/db/models.py`):** estruturas das tabelas/entidades.
* **Infra (`bot/db/`, `bot/core/`):** conexão com o banco, configurações e textos do bot.

```
Telegram
   ↓
Handlers  →  Services  →  Models
             ↓           
           DB / Core
```
Todos os textos enviados pelo bot estão centralizados em `bot/core/dialogs.py`, então personalizar a “voz” do Jovis é simples.

### Como rodar localmente
**Pré-requisitos**
* Git
* Python 3.10+
* PostgreSQL funcionando

**Passo a passo**

1. **Clonar o repositório**
   ```bash
   git clone <URL_DO_SEU_REPOSITORIO>
   cd nome-da-pasta-do-projeto
   ```

2. **Criar e ativar a venv**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Instalar dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Preparar o banco e o bot**
   * Crie um bot de teste no @BotFather e pegue o token.
   * Crie um banco no PostgreSQL (ex.: `jovis_db_dev`) e um usuário/senha.

5. **Criar o `.env` na raiz do projeto**
   ```dotenv
   # Token do seu bot de TESTE
   TELEGRAM_TOKEN="TOKEN_DO_SEU_BOT_DE_TESTES"

   # Seu ID de Telegram como admin (número)
   ADMIN_USER_IDS="SEU_ID_NUMERICO_AQUI"

   # Banco local
   DB_USER="seu_usuario_db"
   DB_PASSWORD="sua_senha_db"
   DB_HOST="localhost"
   DB_PORT="5432"
   DB_NAME="jovis_db_dev"

   # (Opcional) E-mail p/ receber relatórios de bug
   EMAIL_HOST="smtp.gmail.com"
   EMAIL_PORT=587
   EMAIL_SENDER="seu-email-remetente@gmail.com"
   EMAIL_SENDER_PASSWORD="sua-senha-de-app-de-16-digitos"
   EMAIL_RECEIVER="seu-email-de-destino@exemplo.com"
   ```

6. **Criar as tabelas (migrations)**
   ```bash
   alembic upgrade head
   ```
   O schema do banco é versionado com [Alembic](https://alembic.sqlalchemy.org/) (pasta `migrations/`) — não é mais criado automaticamente ao subir o bot. Se você já tinha um banco criado antes disso existir (via `Base.metadata.create_all()`), rode `alembic stamp head` no lugar de `upgrade head` na primeira vez — isso marca o banco como atualizado sem tentar recriar as tabelas que já existem. Depois disso, é sempre `alembic upgrade head`.

7. **Subir o bot**
   ```bash
   python main.py
   ```

### Estrutura de pastas
```
/
├── bot/
│   ├── core/
│   │   ├── dialogs.py      # Textos do bot
│   │   └── settings.py     # Variáveis de ambiente
│   ├── db/
│   │   ├── base.py         # Engine / sessão do SQLAlchemy
│   │   └── models.py       # Tabelas (User, Subject, etc.)
│   ├── handlers/           # Interação com o usuário
│   │   ├── common.py       # /start, /help, menus
│   │   └── ...             # subject_handler.py etc.
│   ├── services/           # Regras de negócio
│   └── decorators.py       # Ex.: @admin_only
├── migrations/             # Migrations do banco (Alembic) — ver "Migrations" abaixo
├── tests/                  # Testes unitários (pytest) dos services
├── alembic.ini
├── .env                    # NÃO comitar
├── .gitignore
├── main.py                 # Entrada da aplicação
├── README.md
├── requirements.txt
└── requirements-dev.txt    # requirements.txt + pytest
```

### Migrations (Alembic)
O schema do banco é versionado em `migrations/versions/` — `bot/db/models.py` continua sendo a fonte da verdade (SQLAlchemy), mas qualquer mudança de coluna/tabela precisa de uma migration pra ser aplicada em qualquer banco (dev, produção etc.):
```bash
# depois de mudar um model em bot/db/models.py, gera a migration automaticamente
alembic revision --autogenerate -m "descreva a mudança"

# revise o arquivo gerado em migrations/versions/ antes de aplicar!

# aplica as migrations pendentes
alembic upgrade head

# desfaz a última migration, se precisar
alembic downgrade -1
```
`migrations/env.py` já lê a `DATABASE_URL` das mesmas variáveis de ambiente do resto do projeto (via `bot/core/settings.py`) — não precisa configurar nada em `alembic.ini`.
### Rodando os testes
Os testes cobrem a camada de `bot/services/` e usam SQLite em memória, sem precisar de Postgres nem de token do Telegram de verdade:
```bash
pip install -r requirements-dev.txt
pytest
```

### Dicas rápidas
* **Personalização:** ajuste a “voz” do bot em `bot/core/dialogs.py`.
* **Testes:** rode `pytest` (cobre os `services/`) e, antes de mandar para `main`, teste também manualmente com o bot de testes.

Curtiu a ideia? Se algo estiver confuso ou você tiver uma forma melhor de fazer, abre uma *issue* ou manda bala num *PR*. 
