import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import random
import json
from data import tasks

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("No TELEGRAM_BOT_TOKEN found!")
    exit(0)

bot = telebot.TeleBot(TOKEN)

users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "current_task_idx": None,
            "current_q_idx": 0,
            "errors_by_task": {i: 0 for i in range(len(tasks))},
            "total_solved": 0,
            "total_errors": 0,
            "last_task_idx": None,
            "session_correct": 0,
            "session_mistakes": [],
            "mistakes_mode": False,
            "mistakes_queue": [],
            "mistakes_idx": 0
        }
    return users[user_id]

@bot.message_handler(commands=['start'])
def start_msg(message):
    uid = message.chat.id
    user = get_user(uid)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚀 Решать задачи", callback_data="next_task"))
    markup.add(InlineKeyboardButton("👤 Мой профиль", callback_data="profile"))
    
    bot.send_message(
        uid, 
        "Привет! 👋 Я бот для подготовки к ГИА.\n\n"
        "Я буду отправлять тебе случайную задачу со всеми 12 вопросами (по одному). Варианты ответов перемешаны. "
        "А также я буду писать тебе, если ты ошибся, и правильный ответ. Твои ошибки влияют на шансы выпадения задач!",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "start_menu")
def start_menu_call(call):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚀 Решать задачи", callback_data="next_task"))
    markup.add(InlineKeyboardButton("👤 Мой профиль", callback_data="profile"))
    bot.edit_message_text("Главное меню бота:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile_call(call):
    uid = call.message.chat.id
    user = get_user(uid)
    
    txt = f"👤 **Твой профиль**\n\n"
    txt += f"✅ Решено верно: {user['total_solved']}\n"
    txt += f"❌ Допущено ошибок: {user['total_errors']}\n\n"
    txt += "📊 Ошибки по задачам (влияют на вероятность их выпадения):\n"
    for i, t in enumerate(tasks):
        txt += f"{t['category_name']}: {user['errors_by_task'][i]} ошибок\n"
        
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚀 Решать задачи", callback_data="next_task"))
    markup.add(InlineKeyboardButton("🔄 В меню", callback_data="start_menu"))
    
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "next_task")
def next_task_call(call):
    uid = call.message.chat.id
    user = get_user(uid)
    
    # Adaptive probability
    weights = []
    for i in range(len(tasks)):
        if i == user.get("last_task_idx"):
            weights.append(0)
        else:
            w = 1 + (user['errors_by_task'][i] * 15)
            weights.append(w)
        
    chosen_task_idx = random.choices(range(len(tasks)), weights=weights, k=1)[0]
    
    user["last_task_idx"] = chosen_task_idx
    user["current_task_idx"] = chosen_task_idx
    user["current_q_idx"] = 0
    user["session_correct"] = 0
    user["session_mistakes"] = []
    user["mistakes_mode"] = False
    
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except:
        pass
    
    send_question(call.message.chat.id, None, user)

@bot.callback_query_handler(func=lambda call: call.data == "work_mistakes")
def work_mistakes_call(call):
    uid = call.message.chat.id
    user = get_user(uid)
    
    user["mistakes_mode"] = True
    user["mistakes_queue"] = list(user["session_mistakes"])
    user["mistakes_idx"] = 0
    
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except:
        pass
        
    send_question(call.message.chat.id, None, user)

@bot.callback_query_handler(func=lambda call: call.data == "next_question")
def next_question_call(call):
    uid = call.message.chat.id
    user = get_user(uid)
    
    if user["current_task_idx"] is None:
        bot.answer_callback_query(call.id, "Задача не найдена, начни заново.")
        return
        
    if user.get("mistakes_mode"):
        user["mistakes_idx"] += 1
    else:
        user["current_q_idx"] += 1
    send_question(call.message.chat.id, call.message.message_id, user)

def send_question(chat_id, message_id, user):
    task_idx = user["current_task_idx"]
    
    if user.get("mistakes_mode"):
        if user["mistakes_idx"] >= len(user["mistakes_queue"]):
            user["mistakes_mode"] = False
            user["current_task_idx"] = None
            user["current_q_idx"] = 0
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🚀 Новая задача", callback_data="next_task"))
            markup.add(InlineKeyboardButton("👤 Мой профиль", callback_data="profile"))
            msg = "🎉 Работа над ошибками завершена!"
            if message_id:
                bot.edit_message_text(msg, chat_id, message_id, reply_markup=markup)
            else:
                bot.send_message(chat_id, msg, reply_markup=markup)
            return
            
        real_q_idx = user["mistakes_queue"][user["mistakes_idx"]]
        mode_text = "[Работа над ошибками] "
    else:
        real_q_idx = user["current_q_idx"]
        mode_text = ""
        task = tasks[task_idx]
        
        if real_q_idx >= len(task["questions"]):
            total_q = len(task["questions"])
            correct_cnt = user["session_correct"]
            percent = int((correct_cnt / total_q) * 100) if total_q > 0 else 100
            
            wrong_str = ""
            if len(user["session_mistakes"]) > 0:
                wrong_nums = [str(x + 1) for x in user["session_mistakes"]]
                wrong_str = f"Ошибки в вопросах: {', '.join(wrong_nums)}"
            else:
                user["errors_by_task"][task_idx] = 0
                
            msg = f"🎉 Ты завершил задачу!\n\n"
            msg += f"✅ Результат: {correct_cnt}/{total_q} ({percent}%)\n"
            if wrong_str:
                msg += f"❌ {wrong_str}\n"
                
            markup = InlineKeyboardMarkup(row_width=1)
            if wrong_str:
                markup.add(InlineKeyboardButton("🛠️ Работа над ошибками", callback_data="work_mistakes"))
            markup.add(InlineKeyboardButton("🚀 Новая задача", callback_data="next_task"))
            markup.add(InlineKeyboardButton("👤 Мой профиль", callback_data="profile"))
            
            user["current_task_idx"] = None
            user["current_q_idx"] = 0
            
            if message_id:
                bot.edit_message_text(msg, chat_id, message_id, reply_markup=markup)
            else:
                bot.send_message(chat_id, msg, reply_markup=markup)
            return

    task = tasks[task_idx]
    q = task["questions"][real_q_idx]
    
    # Shuffle options
    options = list(q["options"])
    correct_val = options[q["correct_index"]]
    random.shuffle(options)
    
    markup = InlineKeyboardMarkup(row_width=2)
    labels = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
    
    text = f"📝 **{mode_text}{task['category_name']}** (Вопрос {real_q_idx + 1}/12)\n\n"
    text += f"📖 **Условие:**\n{task['condition']}\n\n"
    text += f"❓ **Вопрос:**\n{q['question']}\n\n"
    
    buttons = []
    for i, opt in enumerate(options):
        is_corr = 1 if opt == correct_val else 0
        data = f"ans_{task_idx}_{real_q_idx}_{is_corr}"
        label = labels[i] if i < len(labels) else f"{i+1}️⃣"
        text += f"{label} {opt}\n\n"
        buttons.append(InlineKeyboardButton(label, callback_data=data))
        
    markup.add(*buttons)

    
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
        except telebot.apihelper.ApiTelegramException:     # if message is exactly the same, or we start fresh...
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("ans_"))
def handle_answer(call):
    uid = call.message.chat.id
    user = get_user(uid)
    
    parts = call.data.split("_")
    task_idx = int(parts[1])
    q_idx = int(parts[2])
    is_corr = int(parts[3])
    
    task = tasks[task_idx]
    q = task["questions"][q_idx]
    
    if user.get("mistakes_mode"):
        expected_q_idx = user["mistakes_queue"][user["mistakes_idx"]]
        is_last = user["mistakes_idx"] >= len(user["mistakes_queue"]) - 1
        mode_text = "[Работа над ошибками] "
    else:
        expected_q_idx = user["current_q_idx"]
        is_last = q_idx >= len(task["questions"]) - 1
        mode_text = ""
        
    # Verify we are on the same question
    if user["current_task_idx"] != task_idx or q_idx != expected_q_idx:
        bot.answer_callback_query(call.id, "Этот вопрос уже неактуален.", show_alert=True)
        return
        
    correct_text = q["options"][q["correct_index"]]
    
    if is_corr == 1:
        user["total_solved"] += 1
        if not user.get("mistakes_mode"):
            if user["errors_by_task"][task_idx] > 0:
                user["errors_by_task"][task_idx] -= 1
            user["session_correct"] += 1
        result_str = f"✅ **Верно!**\n\nМолодец, правильный ответ: **{correct_text}**"
    else:
        user["total_errors"] += 1
        user["errors_by_task"][task_idx] += 1
        if not user.get("mistakes_mode"):
            user["session_mistakes"].append(q_idx)
        result_str = f"❌ **Неверно.**\n\nПравильный ответ: **{correct_text}**"
        
    markup = InlineKeyboardMarkup()
    if is_last:
        if user.get("mistakes_mode"):
             markup.add(InlineKeyboardButton("🏁 Завершить работу над ошибками", callback_data="next_question"))
        else:
             markup.add(InlineKeyboardButton("🏁 Завершить задачу", callback_data="next_question"))
        markup.add(InlineKeyboardButton("👤 Мой профиль", callback_data="profile"))
    else:
        markup.add(InlineKeyboardButton("➡️ Следующий вопрос", callback_data="next_question"))
        
    text = f"📝 **{mode_text}{task['category_name']}** (Вопрос {q_idx + 1}/12)\n\n"
    text += f"📖 **Условие:**\n{task['condition']}\n\n"
    text += f"❓ **Вопрос:**\n{q['question']}\n\n"
    text += "------------------------\n"
    text += result_str
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

if __name__ == "__main__":
    print("Starting Telegram Bot...")
    bot.infinity_polling()
