import telebot
from telebot import types
import psycopg2
import os
import datetime
import random
import string
import os

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7879820766
CHANNEL_ID = -1003759028487

bot = telebot.TeleBot(TOKEN)
@bot.middleware_handler(update_types=['message'])
def check_bot(bot_instance, call):
    if call.message.from_user.is_bot:
        bot.reply_to(call.message, "❌ Bot tidak diizinkan!")
        raise Exception("Bot detected")

def db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def setup():
    conn = db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS akun (id SERIAL PRIMARY KEY, penjual_id BIGINT, penjual_nama TEXT, rank TEXT, hero INTEGER, skin INTEGER, harga INTEGER, info TEXT, status TEXT, tgl TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS trx (id SERIAL PRIMARY KEY, trx_id TEXT, buyer_id BIGINT, buyer_nama TEXT, seller_id BIGINT, akun_id INTEGER, harga INTEGER, status TEXT, tgl TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned (id SERIAL PRIMARY KEY, user_id BIGINT, tgl TEXT)''')
    conn.commit()
    c.execute('''CREATE TABLE IF NOT EXISTS votes (
            id SERIAL PRIMARY KEY,
            trx_id TEXT,
            user_id BIGINT,
            vote TEXT,
            tgl TEXT
        )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE,
            nama TEXT,
            username TEXT,
            email TEXT,
            saldo INTEGER DEFAULT 0,
            poin INTEGER DEFAULT 0,
            foto TEXT,
            tgl TEXT
        )''')
    conn.commit()
    conn.close()
    conn.close()
    conn2 = db()
    c2 = conn2.cursor()
    try:
        c2.execute("ALTER TABLE akun ADD COLUMN foto TEXT")
        c2.execute("ALTER TABLE users ADD COLUMN refferal_by BIGINT")
        c2.execute("ALTER TABLE users ADD COLUMN kode_refferal TEXT")
       
        conn2.commit()
    except:
        pass
    conn2.close()
setup()

def buat_trx():
    return "TRX" + ''.join(random.choices(string.digits, k=8))

def is_banned(uid):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id FROM banned WHERE user_id=%s", (uid,))
    r = c.fetchone()
    conn.close()
    return r is not None
    def tambah_poin(uid, jumlah):
        conn = db()
    c = conn.cursor()
    tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO users (user_id,poin,tgl) VALUES (%s,%s,%s) ON CONFLICT (user_id) DO UPDATE SET poin = users.poin + %s",
        (uid, jumlah, tgl, jumlah))
    conn.commit()
    conn.close()

def menu(uid):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(types.KeyboardButton("Katalog"), types.KeyboardButton("Jual Akun"))
    m.row(types.KeyboardButton("Transaksi"), types.KeyboardButton("Profil"))
    m.row(types.KeyboardButton("Testimoni"), types.KeyboardButton("CS"))
    m.row(types.KeyboardButton("📢 Info Channel"))  # ← tambah di sini
    if uid == ADMIN_ID:
        m.row(types.KeyboardButton("Admin Panel"))
    return m

state = {}

@bot.message_handler(commands=['start'])
def start(msg):
    if is_banned(msg.from_user.id):
        bot.reply_to(msg, "Akun dibanned! Hubungi CS.")
        return
    uid = msg.from_user.id
    nama = msg.from_user.first_name
    tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Cek apakah ada kode referral
    parts = msg.text.split()
    if len(parts) > 1:
        kode_ref = parts[1]
        conn = db()
        c = conn.cursor()
        # Cek user sudah pernah join belum
        c.execute("SELECT id FROM users WHERE user_id=%s", (uid,))
        sudah_ada = c.fetchone()
        if not sudah_ada:
            # Cari pemilik kode referral
            c.execute("SELECT user_id FROM users WHERE kode_referral=%s", (kode_ref,))
            pemilik = c.fetchone()
            if pemilik and pemilik[0] != uid:
                c.execute("INSERT INTO users (user_id,nama,username,referral_by,tgl) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO NOTHING",
                    (uid, nama, msg.from_user.username, pemilik[0], tgl))
                conn.commit()
                conn.close()
                tambah_poin(pemilik[0], 50)
                try:
                    bot.send_message(pemilik[0], "🎉 Teman kamu " + nama + " join lewat referralmu!\n⭐ Kamu dapat 50 poin!")
                except:
                    pass
            else:
                conn.close()
        else:
            conn.close()
    
    bot.reply_to(msg,
        "ML ACCOUNT STORE\n"
        "================\n"
        "Halo " + nama + "!\n\n"
        "- Rekber Otomatis\n"
        "- Garansi 24 Jam\n"
        "- Anti Penipuan\n"
        "- Proses Cepat\n"
        "================\n"
        "Pilih menu di bawah!",
        reply_markup=menu(msg.from_user.id))

@bot.message_handler(commands=['id'])
def get_id(msg):
    bot.reply_to(msg, "ID kamu: " + str(msg.from_user.id))

@bot.message_handler(func=lambda m: m.text == "Katalog")
def katalog(msg):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM akun WHERE status='tersedia'")
    list_akun = c.fetchall()
    conn.close()
    if not list_akun:
        bot.reply_to(msg, "KATALOG AKUN ML\n================\nBelum ada akun!\nTitipkan akun kamu!", reply_markup=menu(msg.from_user.id))
        return
    teks = "KATALOG AKUN ML\n================\n\n"
    for a in list_akun:
        teks += "ID    : #" + str(a[0]) + "\n"
        teks += "Rank  : " + str(a[3]) + "\n"
        teks += "Hero  : " + str(a[4]) + " hero\n"
        teks += "Skin  : " + str(a[5]) + " skin\n"
        teks += "Harga : Rp " + str(a[6]) + "\n"
        teks += "Info  : " + str(a[7]) + "\n"
        teks += "================\n\n"
    teks += "Beli? Ketik /beli [ID]\nContoh: /beli 1"
    bot.reply_to(msg, teks, reply_markup=menu(msg.from_user.id))

@bot.message_handler(func=lambda m: m.text == "Jual Akun")
def jual(msg):
    if is_banned(msg.from_user.id):
        bot.reply_to(msg, "Akun dibanned!")
        return
    state[msg.from_user.id] = {'step': 'rank'}
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(types.KeyboardButton("Master"), types.KeyboardButton("Grandmaster"))
    m.row(types.KeyboardButton("Epic"), types.KeyboardButton("Legend"))
    m.row(types.KeyboardButton("Mythic"), types.KeyboardButton("Mythical Honor"))
    m.row(types.KeyboardButton("Mythical Glory"), types.KeyboardButton("Mythical Immortal"))
    m.row(types.KeyboardButton("Batal"))
    bot.reply_to(msg, "FORM JUAL AKUN ML\n================\nStep 1/6\nPilih rank:", reply_markup=m)

@bot.message_handler(func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'rank')
def step_rank(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    valid = ["Master","Grandmaster","Epic","Legend","Mythic","Mythical Honor","Mythical Glory","Mythical Immortal"]
    if msg.text not in valid:
        bot.reply_to(msg, "Pilih rank yang tersedia!")
        return
    state[msg.from_user.id]['rank'] = msg.text
    if msg.text == "Master":
        state[msg.from_user.id]['step'] = 'divisi'
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.row(types.KeyboardButton("Master I"), types.KeyboardButton("Master II"))
        m.row(types.KeyboardButton("Master III"), types.KeyboardButton("Master IV"))
        m.row(types.KeyboardButton("Batal"))
        bot.reply_to(msg, "Rank: Master\nStep 2/6\nPilih Divisi:", reply_markup=m)
    elif msg.text == "Grandmaster":
        state[msg.from_user.id]['step'] = 'divisi'
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.row(types.KeyboardButton("GM I"), types.KeyboardButton("GM II"))
        m.row(types.KeyboardButton("GM III"), types.KeyboardButton("GM IV"))
        m.row(types.KeyboardButton("GM V"))
        m.row(types.KeyboardButton("Batal"))
        bot.reply_to(msg, "Rank: Grandmaster\nStep 2/6\nPilih Divisi:", reply_markup=m)
    elif msg.text == "Epic":
        state[msg.from_user.id]['step'] = 'divisi'
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.row(types.KeyboardButton("Epic I"), types.KeyboardButton("Epic II"))
        m.row(types.KeyboardButton("Epic III"), types.KeyboardButton("Epic IV"))
        m.row(types.KeyboardButton("Epic V"))
        m.row(types.KeyboardButton("Batal"))
        bot.reply_to(msg, "Rank: Epic\nStep 2/6\nPilih Divisi:", reply_markup=m)
    elif msg.text == "Legend":
        state[msg.from_user.id]['step'] = 'divisi'
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.row(types.KeyboardButton("Legend I"), types.KeyboardButton("Legend II"))
        m.row(types.KeyboardButton("Legend III"), types.KeyboardButton("Legend IV"))
        m.row(types.KeyboardButton("Legend V"))
        m.row(types.KeyboardButton("Batal"))
        bot.reply_to(msg, "Rank: Legend\nStep 2/6\nPilih Divisi:", reply_markup=m)
    elif msg.text == "Mythic":
        state[msg.from_user.id]['step'] = 'bintang'
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.row(types.KeyboardButton("1-5 bintang"), types.KeyboardButton("6-10 bintang"))
        m.row(types.KeyboardButton("11-15 bintang"), types.KeyboardButton("16-20 bintang"))
        m.row(types.KeyboardButton("21-25 bintang"))
        m.row(types.KeyboardButton("Batal"))
        bot.reply_to(msg, "Rank: Mythic\nStep 2/6\nPilih range bintang:", reply_markup=m)
    elif msg.text == "Mythical Honor":
        state[msg.from_user.id]['step'] = 'bintang'
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.row(types.KeyboardButton("25-30 bintang"), types.KeyboardButton("31-40 bintang"))
        m.row(types.KeyboardButton("41-50 bintang"))
        m.row(types.KeyboardButton("Batal"))
        bot.reply_to(msg, "Rank: Mythical Honor\nStep 2/6\nPilih range bintang:", reply_markup=m)
    elif msg.text == "Mythical Glory":
        state[msg.from_user.id]['step'] = 'bintang'
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.row(types.KeyboardButton("50-60 bintang"), types.KeyboardButton("61-70 bintang"))
        m.row(types.KeyboardButton("71-80 bintang"), types.KeyboardButton("81-90 bintang"))
        m.row(types.KeyboardButton("91-100 bintang"))
        m.row(types.KeyboardButton("Batal"))
        bot.reply_to(msg, "Rank: Mythical Glory\nStep 2/6\nPilih range bintang:", reply_markup=m)
    elif msg.text == "Mythical Immortal":
        state[msg.from_user.id]['step'] = 'bintang'
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.row(types.KeyboardButton("100-150 bintang"), types.KeyboardButton("151-200 bintang"))
        m.row(types.KeyboardButton("201-300 bintang"), types.KeyboardButton("300+ bintang"))
        m.row(types.KeyboardButton("Batal"))
        bot.reply_to(msg, "Rank: Mythical Immortal\nStep 2/6\nPilih range bintang:", reply_markup=m)

@bot.message_handler(func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'divisi')
def step_divisi(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    state[msg.from_user.id]['divisi'] = msg.text
    state[msg.from_user.id]['step'] = 'bintang'
    rank = state[msg.from_user.id]['rank']
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if rank == "Master":
        m.row(types.KeyboardButton("1 bintang"), types.KeyboardButton("2 bintang"))
        m.row(types.KeyboardButton("3 bintang"), types.KeyboardButton("4 bintang"))
    else:
        m.row(types.KeyboardButton("1 bintang"), types.KeyboardButton("2 bintang"))
        m.row(types.KeyboardButton("3 bintang"), types.KeyboardButton("4 bintang"))
        m.row(types.KeyboardButton("5 bintang"))
    m.row(types.KeyboardButton("Batal"))
    bot.reply_to(msg, "Divisi: " + msg.text + "\nStep 3/6\nPilih jumlah bintang:", reply_markup=m)

@bot.message_handler(func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'bintang')
def step_bintang(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    state[msg.from_user.id]['bintang'] = msg.text
    state[msg.from_user.id]['step'] = 'hero'
    rank = state[msg.from_user.id]['rank']
    divisi = state[msg.from_user.id].get('divisi', '')
    if divisi:
        rank_full = divisi + " " + msg.text
    else:
        rank_full = rank + " " + msg.text
    state[msg.from_user.id]['rank_full'] = rank_full
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(types.KeyboardButton("Batal"))
    bot.reply_to(msg, "Rank: " + rank_full + "\nStep 4/6\nJumlah hero? (ketik angka)", reply_markup=m)

@bot.message_handler(func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'hero')
def step_hero(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    try:
        hero = int(msg.text)
        if hero < 1 or hero > 132:
            raise ValueError
    except:
        bot.reply_to(msg, "Masukkan angka 1-132!")
        return
    state[msg.from_user.id]['hero'] = hero
    state[msg.from_user.id]['step'] = 'skin'
    bot.reply_to(msg, "Hero: " + str(hero) + "\nStep 5/6\nJumlah skin? (ketik angka)")

@bot.message_handler(func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'skin')
def step_skin(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    try:
        skin = int(msg.text)
        if skin < 0 or skin > 500:
            raise ValueError
    except:
        bot.reply_to(msg, "Masukkan angka yang valid!")
        return
    state[msg.from_user.id]['skin'] = skin
    state[msg.from_user.id]['step'] = 'harga'
    bot.reply_to(msg, "Skin: " + str(skin) + "\nStep 6/6\nHarga jual? (Rupiah)\nContoh: 500000")

@bot.message_handler(func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'harga')
def step_harga(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    try:
        harga = int(msg.text)
        if harga < 10000:
            bot.reply_to(msg, "Harga minimal Rp 10.000!")
            return
    except:
        bot.reply_to(msg, "Masukkan angka!")
        return
    state[msg.from_user.id]['harga'] = harga
    state[msg.from_user.id]['step'] = 'info'
    bot.reply_to(msg, "Harga: Rp " + str(harga) + "\nTulis deskripsi akun!\nContoh: Akun sultan, hero lengkap!")

@bot.message_handler(func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'info')
def step_info(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    data = state[msg.from_user.id]
    data['info'] = msg.text
    data['step'] = 'foto'
    rank_full = data.get('rank_full', data.get('rank', ''))
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("Submit", callback_data="submit_jual"), types.InlineKeyboardButton("Batal", callback_data="batal_jual"))
    bot.reply_to(msg, "Step 7/7\nKirim foto screenshot akun ML kamu!")

@bot.callback_query_handler(func=lambda c: True)
def callback(call):
    uid = call.from_user.id
    nama = call.from_user.first_name
    if call.data == "submit_jual":
        if uid not in state:
            bot.answer_callback_query(call.id, "Session habis!")
            return
            conn_cek = db()
            c_cek = conn_cek.cursor()
            c_cek.execute("SELECT COUNT(*) FROM akun WHERE penjual_id=%s AND status IN ('menunggu_verifikasi','tersedia','pending')", (uid,))
            jumlah_akun = c_cek.fetchone()[0]
            conn_cek.close()
            if jumlah_akun >= 3:
                bot.answer_callback_query(call.id, "Maksimal 3 akun aktif!")
                bot.send_message(uid, "❌ Kamu sudah punya 3 akun aktif!\nTunggu akun terjual dulu sebelum submit lagi.")
                return
            
        data = state[uid]
        rank_full = data.get('rank_full', data.get('rank', ''))
        tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = db()
        c = conn.cursor()
        foto_id = data.get('foto', None)
        c.execute("INSERT INTO akun (penjual_id,penjual_nama,rank,hero,skin,harga,info,status,tgl,foto) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (uid, nama, rank_full, data['hero'], data['skin'], data['harga'], data['info'], 'menunggu_verifikasi', tgl, foto_id))
        c.execute("SELECT lastval()")
        akun_id = c.fetchone()[0]
        conn.commit()
        conn.close()
        state[uid]['akun_id'] = akun_id
        state.pop(uid, None)
        if foto_id:
            bot.send_photo(ADMIN_ID, foto_id, caption="Akun baru!\nID: #" + str(akun_id) + "\nPenjual: " + nama + "\nRank: " + rank_full + "\n/verif " + str(akun_id) + "\n/tolak " + str(akun_id))
        else:
            bot.send_message(ADMIN_ID, "Akun baru!\nID: #" + str(akun_id) + "\nPenjual: " + nama + "\nRank: " + rank_full + "\n/verif " + str(akun_id) + "\n/tolak " + str(akun_id))
            mk_vote_jual = types.InlineKeyboardMarkup()
        mk_vote_jual.row(
            types.InlineKeyboardButton("✅ Layak", callback_data="votejual_layak_" + str(akun_id)),
            types.InlineKeyboardButton("❌ Tidak Layak", callback_data="votejual_tolak_" + str(akun_id))
        )
        bot.send_message(CHANNEL_ID,
            "🆕 AKUN BARU MASUK!\n"
            "================\n"
            "ID: #" + str(akun_id) + "\n"
            "Penjual: " + nama + "\n"
            "Rank: " + rank_full + "\n"
            "Harga: Rp " + str(data['harga']) + "\n"
            "================\n"
            "Vote minimal 10 orang!\n"
            "Voter dapat 5 poin!",
            reply_markup=mk_vote_jual
            )
        bot.send_message(uid, "Kembali ke menu!", reply_markup=menu(uid))
    elif call.data == "batal_jual":
        state.pop(uid, None)
        bot.edit_message_text("Dibatalkan!", call.message.chat.id, call.message.message_id)
        bot.send_message(uid, "Kembali ke menu!", reply_markup=menu(uid))
    elif call.data.startswith("beli_"):
        akun_id = int(call.data.split("_")[1])
        conn = db()
        c = conn.cursor()
        c.execute("SELECT * FROM akun WHERE id=%s AND status='tersedia'", (akun_id,))
        akun = c.fetchone()
        conn.close()
        if not akun:
            bot.answer_callback_query(call.id, "Akun tidak tersedia!")
            return
        tid = buat_trx()
        tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = db()
        c = conn.cursor()
        c.execute("INSERT INTO trx (trx_id,buyer_id,buyer_nama,seller_id,akun_id,harga,status,tgl) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (tid, uid, nama, akun[1], akun_id, akun[6], 'menunggu_bayar', tgl))
        c.execute("UPDATE akun SET status='pending' WHERE id=%s", (akun_id,))
        conn.commit()
        conn.close()
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_photo(
            call.message.chat.id,
            open('qris.jpg', 'rb'),
            caption="📷 STRUK ORDER\n================\nID: " + tid + "\nAkun: #" + str(akun_id) + " " + str(akun[3]) + "\nHarga: Rp " + str(akun[6]) + "\n================\nTransfer ke:\nDANA: 085649642594\nGoPay: 085649642594\n================\nScan QRIS di atas untuk pembayaran!\n================\nSetelah transfer ketik:\n/bayar " + tid
        )
        if ADMIN_ID != 0:
            bot.send_message(ADMIN_ID, "Ada pembeli!\nID: " + tid + "\nPembeli: " + nama + "\nAkun: #" + str(akun_id) + "\nHarga: Rp " + str(akun[6]))
            bot.send_message(CHANNEL_ID, "🛒 TRANSAKSI BARU!\n================\nID: " + tid + "\nPembeli: " + nama + "\nAkun: #" + str(akun_id) + "\nHarga: Rp " + str(akun[6]) + "\nStatus: Menunggu Pembayaran ⏳")
            mk_vote = types.InlineKeyboardMarkup()
        mk_vote.row(
            types.InlineKeyboardButton("✅ Lanjut", callback_data="vote_lanjut_" + tid),
            types.InlineKeyboardButton("❌ Batalkan", callback_data="vote_batal_" + tid)
        )
        bot.send_message(CHANNEL_ID,
            "🔔 VOTE TRANSAKSI!\n"
            "================\n"
            "ID: " + tid + "\n"
            "Akun: #" + str(akun_id) + " " + str(akun[3]) + "\n"
            "Harga: Rp " + str(akun[6]) + "\n"
            "================\n"
            "Vote minimal 10 orang dalam 1 jam!\n"
            "Voter dapat reward 3% dari transaksi!",
            reply_markup=mk_vote
        )
    elif call.data.startswith("beli_"):
        if ADMIN_ID != 0:
            bot.send_message(ADMIN_ID, "Ada pembeli!\nID: " + tid + "\nPembeli: " + nama + "\nAkun: #" + str(akun_id) + "\nHarga: Rp " + str(akun[6]))
    elif call.data.startswith("oke_"):
        tid = call.data.split("_")[1]
        conn = db()
        c = conn.cursor()
        c.execute("UPDATE trx SET status='selesai' WHERE trx_id=%s", (tid,))
        conn.commit()
        conn.close()
        bot.edit_message_text("Transaksi Selesai!\nID: " + tid + "\nTerima kasih!", call.message.chat.id, call.message.message_id)
        tambah_poin(trx[2], 100)  # ← tambah di sini
        try:
            bot.send_message(trx[2], "⭐ Kamu dapat 100 poin dari pembelian!")
        except:
            pass
        if ADMIN_ID != 0:
            bot.send_message(ADMIN_ID, "Transaksi " + tid + " selesai!")
            bot.send_message(CHANNEL_ID, "✅ TRANSAKSI SELESAI!\n================\nID: " + tid + "\nStatus: Selesai ✅")
    elif call.data.startswith("masalah_"):
        tid = call.data.split("_")[1]
        conn = db()
        c = conn.cursor()
        c.execute("UPDATE trx SET status='dispute' WHERE trx_id=%s", (tid,))
        conn.commit()
        conn.close()
        bot.edit_message_text("Laporan diterima!\nID: " + tid + "\nAdmin investigasi 1x24 jam!", call.message.chat.id, call.message.message_id)
        if ADMIN_ID != 0:
            bot.send_message(ADMIN_ID, "DISPUTE!\nTransaksi: " + tid + "\nSegera investigasi!")
            bot.send_message(CHANNEL_ID, "⚠️ TRANSAKSI BERMASALAH!\n================\nID: " + tid + "\nStatus: Dalam Investigasi ⚠️")
    elif call.data.startswith("vote_"):
        parts = call.data.split("_")
        vote_type = parts[1]
        tid = parts[2]
        uid = call.from_user.id
        tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = db()
        c = conn.cursor()
        c.execute("SELECT id FROM votes WHERE trx_id=%s AND user_id=%s", (tid, uid))
        if c.fetchone():
            bot.answer_callback_query(call.id, "Kamu sudah vote!")
            conn.close()
            return
        c.execute("INSERT INTO votes (trx_id,user_id,vote,tgl) VALUES (%s,%s,%s,%s)", (tid, uid, vote_type, tgl))
        c.execute("SELECT COUNT(*) FROM votes WHERE trx_id=%s AND vote='lanjut'", (tid,))
        total_lanjut = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM votes WHERE trx_id=%s AND vote='batal'", (tid,))
        total_batal = c.fetchone()[0]
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Vote kamu tercatat! ✅")
        bot.answer_callback_query(call.id, "Vote kamu tercatat! ✅")  # baris 441
        tambah_poin(uid, 5)  # ← tambah di sini
        try:
            bot.send_message(uid, "⭐ Kamu dapat 5 poin dari vote!")
        except:
            pass
        mk_update = types.InlineKeyboardMarkup()
        mk_update.row(
            types.InlineKeyboardButton("✅ Lanjut (" + str(total_lanjut) + ")", callback_data="vote_lanjut_" + tid),
            types.InlineKeyboardButton("❌ Batalkan (" + str(total_batal) + ")", callback_data="vote_batal_" + tid)
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=mk_update)
    elif call.data.startswith("votejual_"):
        parts = call.data.split("_")
        vote_type = parts[1]
        akun_id = parts[2]
        uid = call.from_user.id
        tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = db()
        c = conn.cursor()
        c.execute("SELECT id FROM votes WHERE trx_id=%s AND user_id=%s", ("jual_"+akun_id, uid))
        if c.fetchone():
            bot.answer_callback_query(call.id, "Kamu sudah vote!")
            conn.close()
            return
        c.execute("INSERT INTO votes (trx_id,user_id,vote,tgl) VALUES (%s,%s,%s,%s)",
            ("jual_"+akun_id, uid, vote_type, tgl))
        c.execute("SELECT COUNT(*) FROM votes WHERE trx_id=%s AND vote='layak'", ("jual_"+akun_id,))
        total_layak = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM votes WHERE trx_id=%s AND vote='tolak'", ("jual_"+akun_id,))
        total_tolak = c.fetchone()[0]
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Vote kamu tercatat! ✅")
        tambah_poin(uid, 5)
        try:
            bot.send_message(uid, "⭐ Kamu dapat 5 poin dari vote akun!")
        except:
            pass
        mk_update = types.InlineKeyboardMarkup()
        mk_update.row(
            types.InlineKeyboardButton("✅ Layak (" + str(total_layak) + ")", callback_data="votejual_layak_" + akun_id),
            types.InlineKeyboardButton("❌ Tidak Layak (" + str(total_tolak) + ")", callback_data="votejual_tolak_" + akun_id)
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=mk_update)
        if total_layak >= 10:
            conn2 = db()
            c2 = conn2.cursor()
            c2.execute("UPDATE akun SET status='tersedia' WHERE id=%s", (akun_id,))
            c2.execute("SELECT penjual_id FROM akun WHERE id=%s", (akun_id,))
            penjual = c2.fetchone()
            conn2.commit()
            conn2.close()
            bot.edit_message_text(
                "✅ AKUN DISETUJUI KOMUNITAS!\n"
                "================\n"
                "ID: #" + akun_id + "\n"
                "Sudah masuk katalog!",
                call.message.chat.id, call.message.message_id
            )
            if penjual:
                bot.send_message(penjual[0], "✅ Akun kamu #")
@bot.message_handler(commands=['beli'])
def beli(msg):
    state.pop(msg.from_user.id, None)
    try:
        akun_id = int(msg.text.split()[1])
    except:
        bot.reply_to(msg, "Format: /beli [ID]\nContoh: /beli 1")
        return
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM akun WHERE id=%s AND status='tersedia'", (akun_id,))
    akun = c.fetchone()
    conn.close()
    if not akun:
        bot.reply_to(msg, "Akun tidak ditemukan!")
        return
    if msg.from_user.id == akun[1]:
        bot.reply_to(msg, "Tidak bisa beli akun sendiri!")
        return
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("Lanjut Beli", callback_data="beli_" + str(akun_id)), types.InlineKeyboardButton("Batal", callback_data="batal"))
    bot.reply_to(msg, "DETAIL AKUN ML\n================\nRank  : " + str(akun[3]) + "\nHero  : " + str(akun[4]) + " hero\nSkin  : " + str(akun[5]) + " skin\nHarga : Rp " + str(akun[6]) + "\nInfo  : " + str(akun[7]) + "\n================\nLanjutkan pembelian?", reply_markup=mk)

@bot.message_handler(commands=['bayar'])
def bayar(msg):
    try:
        tid = msg.text.split()[1]
    except:
        bot.reply_to(msg, "Format: /bayar [ID Transaksi]")
        return
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM trx WHERE trx_id=%s AND buyer_id=%s", (tid, msg.from_user.id))
    trx = c.fetchone()
    conn.close()
    if not trx:
        bot.reply_to(msg, "Transaksi tidak ditemukan!")
        return
    state[msg.from_user.id] = {'step': 'bukti', 'trx_id': tid}
    bot.reply_to(msg, "KONFIRMASI BAYAR\n================\nID: " + tid + "\nHarga: Rp " + str(trx[6]) + "\n================\nKirim foto bukti transfer!")

@bot.message_handler(content_types=['photo'], func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'bukti')
def bukti(msg):
    tid = state[msg.from_user.id]['trx_id']
    nama = msg.from_user.first_name
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM trx WHERE trx_id=%s", (tid,))
    trx = c.fetchone()
    c.execute("UPDATE trx SET status='menunggu_admin' WHERE trx_id=%s", (tid,))
    conn.commit()
    conn.close()
    state.pop(msg.from_user.id, None)
    bot.reply_to(msg, "Bukti diterima!\nID: " + tid + "\nMenunggu konfirmasi admin!", reply_markup=menu(msg.from_user.id))
    if ADMIN_ID != 0:
        foto_id = msg.photo[-1].file_id
        bot.send_photo(ADMIN_ID, foto_id, caption="Bukti Bayar!\nID: " + tid + "\nPembeli: " + nama + "\nHarga: Rp " + str(trx[6]) + "\nKetik /konfirm " + tid)

@bot.message_handler(func=lambda m: m.text == "Admin Panel")
def admin_panel(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.reply_to(msg, "Bukan admin!")
        return
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM akun WHERE status='tersedia'")
    stok = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM akun WHERE status='menunggu_verifikasi'")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM trx WHERE status='menunggu_admin'")
    bayar_pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM trx WHERE status='selesai'")
    selesai = c.fetchone()[0]
    conn.close()
    bot.reply_to(msg, "ADMIN PANEL\n================\nStok: " + str(stok) + "\nPending: " + str(pending) + "\nBayar pending: " + str(bayar_pending) + "\nSelesai: " + str(selesai) + "\n================\n/verif [ID]\n/tolak [ID]\n/konfirm [TRX]\n/kirim [TRX] [detail]\n/ban [ID]")

@bot.message_handler(commands=['tolak'])
def tolak(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        akun_id = int(msg.text.split()[1])
    except:
        bot.reply_to(msg, "Format: /tolak [ID]")
        return
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE akun SET status='ditolak' WHERE id=%s", (akun_id,))
    c.execute("SELECT penjual_id FROM akun WHERE id=%s", (akun_id,))
    penjual = c.fetchone()
    bot.send_message(CHANNEL_ID, "❌ AKUN DITOLAK!\n================\nID: #" + str(akun_id) + "\nStatus: Ditolak Admin ❌")
    conn.close()
    bot.reply_to(msg, "Akun #" + str(akun_id) + " ditolak!")
    if penjual:
        bot.send_message(penjual[0], "Akun kamu #" + str(akun_id) + " ditolak!")

@bot.message_handler(commands=['konfirm'])
def konfirm(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        tid = msg.text.split()[1]
    except:
        bot.reply_to(msg, "Format: /konfirm [TRX_ID]")
        return
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM trx WHERE trx_id=%s", (tid,))
    trx = c.fetchone()
    if not trx:
        bot.reply_to(msg, "Transaksi tidak ditemukan!")
        conn.close()
        return
    c.execute("UPDATE trx SET status='menunggu_akun' WHERE trx_id=%s", (tid,))
    conn.commit()
    conn.close()
    bot.reply_to(msg, "Bayar " + tid + " dikonfirmasi!\n/kirim " + tid + " [detail]")
    bot.send_message(trx[2], "Pembayaran dikonfirmasi!\nID: " + tid + "\nAkun sedang disiapkan!")

@bot.message_handler(commands=['kirim'])
def kirim(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(None, 2)
        tid = parts[1]
        detail = parts[2]
    except:
        bot.reply_to(msg, "Format:\n/kirim [TRX] [detail]")
        return
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM trx WHERE trx_id=%s", (tid,))
    trx = c.fetchone()
    if not trx:
        bot.reply_to(msg, "Transaksi tidak ditemukan!")
        conn.close()
        return
    c.execute("UPDATE trx SET status='akun_terkirim' WHERE trx_id=%s", (tid,))
    conn.commit()
    conn.close()
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("Akun Oke!", callback_data="oke_" + tid), types.InlineKeyboardButton("Ada Masalah", callback_data="masalah_" + tid))
    bot.send_message(trx[2], "Detail Akun ML!\n================\nID: " + tid + "\n================\n" + detail + "\n================\nSegera ganti password!\nAkun sudah sesuai?", reply_markup=mk)
    bot.reply_to(msg, "Detail akun terkirim!")

@bot.message_handler(commands=['ban'])
def ban(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        target = int(msg.text.split()[1])
    except:
        bot.reply_to(msg, "Format: /ban [USER_ID]")
        return
    tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO banned (user_id,tgl) VALUES (%s,%s)", (target, tgl))
    conn.commit()
    conn.close()
    bot.reply_to(msg, "User " + str(target) + " dibanned!")

@bot.message_handler(func=lambda m: m.text == "Transaksi")
def transaksi(msg):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM trx WHERE buyer_id=%s ORDER BY id DESC LIMIT 5", (msg.from_user.id,))
    list_trx = c.fetchall()
    conn.close()
    if not list_trx:
        bot.reply_to(msg, "Belum ada transaksi!", reply_markup=menu(msg.from_user.id))
        return
    teks = "TRANSAKSI TERAKHIR\n================\n\n"
    for t in list_trx:
        teks += "ID: " + str(t[1]) + "\nHarga: Rp " + str(t[6]) + "\nStatus: " + str(t[7]) + "\n================\n"
    bot.reply_to(msg, teks, reply_markup=menu(msg.from_user.id))

@bot.message_handler(func=lambda m: m.text == "Profil")
def profil(msg):
    uid = msg.from_user.id
    tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO users (user_id,nama,username,tgl) VALUES (%s,%s,%s,%s) ON CONFLICT (user_id) DO NOTHING",
        (uid, msg.from_user.first_name, msg.from_user.username, tgl))
    c.execute("SELECT * FROM users WHERE user_id=%s", (uid,))
    user = c.fetchone()
    c.execute("SELECT COUNT(*) FROM trx WHERE buyer_id=%s AND status='selesai'", (uid,))
    beli = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM akun WHERE penjual_id=%s AND status='terjual'", (uid,))
    jual = c.fetchone()[0]
    conn.commit()
    conn.close()
    saldo = user[6] if user else 0
    poin = user[7] if user else 0
    kode = "REF" + str(uid)
    # Simpan kode refferal kalau belum ada
    conn3 = db()
    c3 = conn3.cursor()
    c3.execute("UPDATE users SET kode_refferal=%s WHERE user_id=%s AND kode_refferal IS NULL",
        (kode, uid))
    conn3.commit()
    conn3.close()
    
    bot.reply_to(msg,
        "Nama: " + msg.from_user.first_name + "\n"
        "ID: " + str(uid) + "\n"
        "================\n"
        "💰 Saldo: Rp " + str(saldo) + "\n"
        "⭐ Poin: " + str(poin) + "\n"
        "================\n"
        "Total Beli: " + str(beli) + "\n"
        "Total Jual: " + str(jual) + "\n"
        "================\n"
        "🔗 Link Refferal:\nt.me/@JBAZ_bot?start=" + kode,
        reply_markup=menu(uid))

@bot.message_handler(func=lambda m: m.text == "Testimoni")
def testimoni(msg):
    bot.reply_to(msg, "TESTIMONI\n================\nBudi - Akun sesuai!\nSari - Terpercaya!\nAndi - 3x beli aman!\n================\nJadilah pembeli berikutnya!", reply_markup=menu(msg.from_user.id))

@bot.message_handler(func=lambda m: m.text == "CS")
def cs(msg):
    bot.reply_to(msg, "CUSTOMER SERVICE\n================\nJam: 08.00-22.00 WIB\nTelegram: @FXT82828\n================\nBot aktif 24 jam!", reply_markup=menu(msg.from_user.id))

@bot.message_handler(func=lambda m: m.text == "📢 Info Channel")
def info_channel(msg):
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/transasksijbaz"))
    bot.reply_to(msg,
        "INFO CHANNEL\n================\n"
        "✅ Update stok terbaru\n"
        "✅ Notif transaksi\n"
        "✅ Promo eksklusif\n"
        "================\n"
        "Klik tombol di bawah!",
        reply_markup=mk
    )
@bot.callback_query_handler(func=lambda c: c.data.startswith("vote_"))
def handle_vote(call):
    parts = call.data.split("_")
    vote_type = parts[1]
    tid = parts[2]
    uid = call.from_user.id
    tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = db()
    c = conn.cursor()

    # Cek sudah vote belum
    c.execute("SELECT id FROM votes WHERE trx_id=%s AND user_id=%s", (tid, uid))
    if c.fetchone():
        bot.answer_callback_query(call.id, "Kamu sudah vote!")
        conn.close()
        return

    # Simpan vote
    c.execute("INSERT INTO votes (trx_id,user_id,vote,tgl) VALUES (%s,%s,%s,%s)",
        (tid, uid, vote_type, tgl))

    # Hitung vote
    c.execute("SELECT COUNT(*) FROM votes WHERE trx_id=%s AND vote='lanjut'", (tid,))
    total_lanjut = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM votes WHERE trx_id=%s AND vote='batal'", (tid,))
    total_batal = c.fetchone()[0]
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, "Vote kamu tercatat! ✅")

    # Update tombol dengan jumlah vote
    mk_update = types.InlineKeyboardMarkup()
    mk_update.row(
        types.InlineKeyboardButton("✅ Lanjut (" + str(total_lanjut) + ")", callback_data="vote_lanjut_" + tid),
        types.InlineKeyboardButton("❌ Batalkan (" + str(total_batal) + ")", callback_data="vote_batal_" + tid)
    )
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=mk_update)

    # Kalau sudah 10 vote lanjut
    if total_lanjut >= 10:
        conn2 = db()
        c2 = conn2.cursor()
        c2.execute("SELECT harga FROM trx WHERE trx_id=%s", (tid,))
        hasil = c2.fetchone()
        if hasil:
            harga = hasil[0]
            reward_total = int(harga * 0.03)
            reward_per_orang = reward_total // 10
            c2.execute("SELECT user_id FROM votes WHERE trx_id=%s AND vote='lanjut' LIMIT 10", (tid,))
            voters = c2.fetchall()
            for v in voters:
                try:
                    bot.send_message(v[0],
                        "🎉 Transaksi " + tid + " dilanjutkan!\n"
                        "Reward kamu: Rp " + str(reward_per_orang)
                    )
                except:
                    pass
        conn2.commit()
        conn2.close()

        bot.edit_message_text(
            "✅ TRANSAKSI DILANJUTKAN!\n"
            "================\n"
            "ID: " + tid + "\n"
            "Total Vote: " + str(total_lanjut) + "\n"
            "Reward dibagi ke 10 voter!",
            call.message.chat.id, call.message.message_id
    )
@bot.message_handler(content_types=['photo'], func=lambda m: m.from_user.id in state and state[m.from_user.id].get('step') == 'foto')
def step_foto(msg):
    if msg.text == "Batal":
        state.pop(msg.from_user.id, None)
        bot.reply_to(msg, "Dibatalkan!", reply_markup=menu(msg.from_user.id))
        return
    foto_id = msg.photo[-1].file_id
    state[msg.from_user.id]['foto'] = foto_id
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE akun SET foto=%s WHERE id=(SELECT id FROM akun WHERE penjual_id=%s AND status='menunggu_verifikasi' ORDER BY id DESC LIMIT 1)", (foto_id, msg.from_user.id))
    conn.commit()
    conn.close()
    state[msg.from_user.id]['step'] = 'done'
    data = state[msg.from_user.id]
    rank_full = data.get('rank_full', data.get('rank', ''))
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("Submit", callback_data="submit_jual"), types.InlineKeyboardButton("Batal", callback_data="batal"))
    bot.reply_to(msg, "KONFIRMASI AKUN\n================\nRank : " + rank_full + "\nHero : " + str(data['hero']) + " hero\nSkin : " + str(data['skin']) + " skin\nHarga : Rp " + str(data['harga']) + "\nInfo  : " + str(data['info']) + "\n================\nData sudah benar?", reply_markup=mk)
bot.delete_webhook()
import time
time.sleep(2)
print("ML Store Bot aktif!")
print("Ketik /id untuk dapat ID admin!")
bot.polling(none_stop=True)
