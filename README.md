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
* **Deploy sugerido:** Railway ou Render

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
             ↓           ↓
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

6. **Subir o bot**
   ```bash
   python main.py
   ```
   Na primeira execução, as tabelas são criadas automaticamente.

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
├── .env                    # NÃO comitar
├── .gitignore
├── main.py                 # Entrada da aplicação
├── README.md
└── requirements.txt
```
### Dicas rápidas
* **Personalização:** ajuste a “voz” do bot em `bot/core/dialogs.py`.
* **Novas features:** dá para evoluir para notificações, cálculo de médias, ou integrar IA mantendo o padrão atual.
* **Testes:** antes de mandar para `main`, teste localmente com o bot de testes.

Curtiu a ideia? Se algo estiver confuso ou você tiver uma forma melhor de fazer, abre uma *issue* ou manda bala num *PR*. 
