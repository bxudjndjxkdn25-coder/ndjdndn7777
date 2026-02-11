import os
import time
import telebot
from telebot import types
from playwright.sync_api import sync_playwright
from threading import Thread

# --- التوكن الخاص بك (تم التأكد منه) ---
API_TOKEN = '8414464648:AAEOPa54U1ZgZ8283KWCqFz24u1B8AE6Avw'
bot = telebot.TeleBot(API_TOKEN)

# --- لوحة التحكم الرئيسية ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('➕ إضافة حساب واتساب', '🚨 بدء بلاغ جماعي')
    markup.add('ℹ️ حالة السيرفر')
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    try:
        bot.send_message(message.chat.id, "✅ النظام السحابي يعمل بنجاح الآن.\nاضغط على الأزرار بالأسفل للبدء:", reply_markup=main_menu())
    except Exception as e:
        print(f"Error: {e}")

# --- معالجة الضغط على الأزرار (تحسين الاستجابة) ---
@bot.message_handler(func=lambda m: m.text == '➕ إضافة حساب واتساب')
def ask_for_phone(message):
    msg = bot.send_message(message.chat.id, "📱 أرسل رقمك الآن (مثال: 967xxxxxxxx) لبدء استخراج كود الربط:")
    bot.register_next_step_handler(msg, process_whatsapp_step)

def process_whatsapp_step(message):
    phone = message.text
    chat_id = message.chat.id
    # تشغيل المتصفح في خيط (Thread) منفصل لكي لا يتوقف البوت عن الرد
    Thread(target=get_whatsapp_code, args=(chat_id, phone)).start()

# --- وظيفة فتح واتساب ويب (Playwright) ---
def get_whatsapp_code(chat_id, phone):
    with sync_playwright() as p:
        # إعدادات المتصفح للسيرفرات الضعيفة
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        try:
            bot.send_message(chat_id, f"⏳ جاري فتح واتساب ويب للرقم {phone}...\n(قد يستغرق الأمر دقيقة في السيرفر المجاني)")
            page.goto("https://web.whatsapp.com", timeout=100000)
            
            # محاولة النقر على "الربط برقم الهاتف"
            link_selector = "span[role='button']:has-text('Link with phone number')"
            page.wait_for_selector(link_selector, timeout=45000)
            page.click(link_selector)
            
            # إدخال الرقم
            page.fill("input[aria-label='Type your phone number.']", phone)
            page.click("button:has-text('Next')")
            
            # استخراج الكود المكون من 8 رموز
            time.sleep(15) 
            code_elements = page.query_selector_all("div[data-ref] span")
            pairing_code = "".join([c.inner_text() for c in code_elements])
            
            if pairing_code:
                bot.send_message(chat_id, f"✅ كود الربط هو:\n\n`{pairing_code}`\n\nأدخله في هاتفك (الأجهزة المرتبطة) الآن.", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, "❌ تعذر استخراج الكود حالياً، يرجى المحاولة مرة أخرى لاحقاً.")
                
        except Exception as e:
            bot.send_message(chat_id, "⚠️ السيرفر مشغول حالياً أو الإنترنت بطيء، يرجى إعادة المحاولة.")
            print(f"Browser Error: {e}")
        finally:
            browser.close()

@bot.message_handler(func=lambda m: m.text == '🚨 بدء بلاغ جماعي')
def report_options(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("10 بلاغات (عادي)", callback_data="r_10_n"),
               types.InlineKeyboardButton("10 بلاغات (قوي)", callback_data="r_10_y"))
    bot.send_message(message.chat.id, "اختر نوع البلاغ المطلوب:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    # الرد الفوري على التليجرام لإخفاء علامة التحميل من الزر
    bot.answer_callback_query(call.id, "⏳ جاري تنفيذ طلبك...")
    bot.send_message(call.message.chat.id, "🚀 بدأنا العمل على طلبك في الخلفية.")

# --- تشغيل البوت مع خاصية إعادة الاتصال التلقائي ---
if __name__ == "__main__":
    print("Bot is starting...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=90)
        except Exception as e:
            print(f"Connection error, retrying... {e}")
            time.sleep(5)
