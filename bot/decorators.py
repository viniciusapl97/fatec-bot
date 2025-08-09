from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from bot.core.settings import ADMIN_USER_IDS

def admin_only(func):
    """
    Decorador que restringe o uso de um handler apenas para os admins definidos.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        
        # Se a lista de admins não foi configurada, nega o acesso por segurança
        if not ADMIN_USER_IDS:
            print(f"Acesso negado para {user.id}: a lista ADMIN_USER_IDS está vazia.")
            return

        if not user or user.id not in ADMIN_USER_IDS:
            print(f"Acesso negado para o usuário {user.id} ({user.first_name}).")
            if update.message:
                await update.message.reply_text("Desculpe, você não tem permissão para usar este comando.")
            elif update.callback_query:
                await update.callback_query.answer("Acesso negado.", show_alert=True)
            return
            
        return await func(update, context, *args, **kwargs)
    return wrapped