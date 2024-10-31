from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)
import random

# Dictionary untuk menyimpan pasangan pengguna
user_pair = {}

# Dictionary untuk menyimpan jenis kelamin dan preferensi pengguna
user_gender = {}
user_mode = {}

# List antrian pengguna yang menunggu pasangan sesuai mode
waiting_list = {
    'cari_teman': [],
    'cari_jodoh': [],
    'kesepian': [],
    'pengen_ngobrol': [],
    'sleepcall': []
}

# Fungsi untuk memulai bot dengan menampilkan menu utama
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Cari Teman", callback_data='cari_teman')],
        [InlineKeyboardButton("Cari Jodoh", callback_data='cari_jodoh')],
        [InlineKeyboardButton("Kesepian", callback_data='kesepian')],
        [InlineKeyboardButton("Pengen Ngobrol", callback_data='pengen_ngobrol')],
        [InlineKeyboardButton("Sleepcall", callback_data='sleepcall')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selamat datang! Pilih mode yang kamu inginkan:", reply_markup=reply_markup)

# Fungsi untuk menangani pilihan dari menu utama
async def mode_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    selected_mode = query.data

    user_mode[user_id] = selected_mode
    await query.answer(f"Kamu memilih mode: {selected_mode.replace('_', ' ').title()}")

    # Arahkan pengguna untuk memilih jenis kelamin
    keyboard = [
        [InlineKeyboardButton("Pria", callback_data='male')],
        [InlineKeyboardButton("Wanita", callback_data='female')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Pilih jenis kelamin Anda:", reply_markup=reply_markup)

# Fungsi untuk menangani pilihan jenis kelamin
async def gender_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == 'male':
        user_gender[user_id] = "pria"
    elif query.data == 'female':
        user_gender[user_id] = "wanita"

    await query.answer(f"Jenis kelamin Anda disimpan sebagai {user_gender[user_id]}.")
    await query.edit_message_text("Jenis kelamin Anda telah disimpan. Ketik /join untuk mulai mencari pasangan chat.")

# Fungsi untuk pengguna bergabung dalam antrian
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Cek apakah pengguna sudah memilih mode dan jenis kelamin
    if user_id not in user_mode or user_id not in user_gender:
        await update.message.reply_text("Silakan pilih mode dan jenis kelamin terlebih dahulu dengan mengetik /start.")
        return

    # Dapatkan mode yang dipilih pengguna
    mode = user_mode[user_id]

    if user_id in waiting_list[mode]:
        await update.message.reply_text("Anda sudah dalam antrian menunggu.")
    else:
        waiting_list[mode].append(user_id)
        await update.message.reply_text("Anda telah bergabung dalam antrian. Menunggu pasangan...")

    # Cek jika ada pengguna lain dalam antrian di mode yang sama
    if len(waiting_list[mode]) >= 2:
        # Ambil dua pengguna dari antrian
        user1 = waiting_list[mode].pop(0)
        user2 = waiting_list[mode].pop(0)
        
        # Pasangkan mereka
        user_pair[user1] = user2
        user_pair[user2] = user1
        
        # Kirim pesan pemberitahuan ke masing-masing pengguna, termasuk informasi jenis kelamin
        await context.bot.send_message(chat_id=user1, text=f"Pasangan ditemukan! Anda bertemu dengan {'wanita' if user_gender[user2] == 'wanita' else 'pria'}. Mulai chat sekarang.")
        await context.bot.send_message(chat_id=user2, text=f"Pasangan ditemukan! Anda bertemu dengan {'wanita' if user_gender[user1] == 'wanita' else 'pria'}. Mulai chat sekarang.")

# Fungsi untuk menangani pesan antar pengguna
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_pair:
        # Kirim pesan ke pasangan
        partner_id = user_pair[user_id]
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
    else:
        await update.message.reply_text("Anda belum terhubung dengan pasangan. Ketik /join untuk mencari pasangan.")

# Fungsi untuk keluar dari chat
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_pair:
        # Hapus pasangan
        partner_id = user_pair[user_id]
        del user_pair[user_id]
        del user_pair[partner_id]
        
        # Kirim pesan ke masing-masing pengguna
        await context.bot.send_message(chat_id=user_id, text="Anda telah keluar dari chat.")
        await context.bot.send_message(chat_id=partner_id, text="Pasangan Anda telah meninggalkan chat.")
    elif user_id in waiting_list.get(user_mode.get(user_id, ''), []):
        waiting_list[user_mode[user_id]].remove(user_id)
        await update.message.reply_text("Anda telah keluar dari antrian.")
    else:
        await update.message.reply_text("Anda tidak sedang dalam chat atau antrian.")

# Fungsi utama untuk menjalankan bot
def main():
    # Ganti 'YOUR_API_TOKEN' dengan token bot Anda
    application = Application.builder().token("YOUR_API_TOKEN").build()

    # Tambahkan handler untuk setiap perintah dan pesan
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("leave", leave))
    application.add_handler(CallbackQueryHandler(mode_choice, pattern='^(cari_teman|cari_jodoh|kesepian|pengen_ngobrol|sleepcall)$'))
    application.add_handler(CallbackQueryHandler(gender_choice, pattern='^(male|female)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Mulai bot
    application.run_polling()

if __name__ == '__main__':
    main()