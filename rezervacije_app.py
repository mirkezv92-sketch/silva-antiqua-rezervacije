import os
import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta

import pytz

# --- Prevodi (samo tekst koji korisnik vidi; baza i mejl ključevi ostaju isti) ---
prevodi = {
    "SRB": {
        "naslov": "Rezervacije termina",
        "info_naslov": "Muzejska poseta uz vodiča",
        "info_45min": "45 min",
        "info_klikni_adresu": "Klikni na adresu za navigaciju.",
        "info_vodjenja": "Vođenja u muzejiću Silva Antiqua organizuju se svakog vikenda (subota i nedelja).",
        "info_13h_eng": "Termin u 13:00 časova realizuje se na engleskom jeziku.",
        "info_ostali_srp": "Ostali termini su na srpskom jeziku.",
        "info_5min": "Molimo vas da dođete barem 5 minuta ranije, kako bi poseta mogla da započne na vreme.",
        "cena_po_osobi": "Cena ulaznice po osobi",
        "datum": "Datum",
        "datum_help": "Dostupni su samo vikend termini (subota i nedelja).",
        "datum_samo_vikend": "Molimo vas, izaberite subotu ili nedelju. Muzej je otvoren za posete samo vikendom.",
        "sezona_od": "Sezona rezervacija počinje od 14. marta 2026.",
        "termini": "Termini",
        "english_tour": "English tour",
        "prosao": "Prošao",
        "popunjeno": "Popunjeno",
        "slobodno": "Slobodno",
        "napomena_termin_eng": "Ovaj termin se održava isključivo na engleskom jeziku.",
        "note_english_only": "Note: This tour is conducted in English only.",
        "rezervisi_termin": "Rezerviši termin",
        "broj_osoba": "Broj osoba",
        "ime_prezime": "Ime i prezime",
        "ime_placeholder": "Unesite ime i prezime",
        "email_obavezno": "Email (obavezno)",
        "email_placeholder": "vas@email.com",
        "dodatna_napomena": "Dodatna napomena (opciono)",
        "napomena_placeholder": "Ostavite prazno ako nemate napomenu.",
        "gdpr_consent": "Slažem se sa obradom mojih podataka (ime i email) isključivo u svrhu potvrde rezervacije u muzeju Silva Antiqua u skladu sa GDPR pravilima.",
        "posalji_zahtev": "Pošalji zahtev",
        "morate_prihvatiti": "Morate prihvatiti uslove obrade podataka.",
        "unesite_ispravan_email": "Unesite ispravnu email adresu.",
        "unesite_ime_email": "Unesite ime i prezime i email.",
        "dialog_potvrda": "Potvrda rezervacije",
        "potvrdite_rezervaciju": "Potvrdite rezervaciju.",
        "odustani": "Odustani",
        "potvrdi": "POTVRDI",
        "sačekajte_email": "Molimo sačekajte, šaljemo potvrdu na vaš email...",
        "rezervacija_uspesna": "Rezervacija uspešna! Potvrda vam je poslata na email.",
        "za_osoba": "osoba",
        "admin_pregled": "Admin Pregled",
        "lozinka": "Lozinka",
        "sigurni_obrisati": "Da li ste sigurni da želite da obrišete ovu rezervaciju?",
        "da_obrisi": "Da, obriši",
        "ne": "Ne",
        "nema_rezervacija": "Nema rezervacija.",
        "pogresna_lozinka": "Pogrešna lozinka.",
        "otkazi_obrisi": "Otkaži (Obriši)",
        "id": "ID",
        "datum_col": "Datum",
        "termin_col": "Termin",
        "ime_col": "Ime i prezime",
        "email_col": "Email",
        "br_col": "Br.",
        "day_sat": "Subota",
        "day_sun": "Nedelja",
    },
    "ENG": {
        "naslov": "Booking",
        "info_naslov": "Guided museum visit",
        "info_45min": "45 min",
        "info_klikni_adresu": "Click on the address for directions.",
        "info_vodjenja": "Guided tours at Silva Antiqua take place every weekend (Saturday and Sunday).",
        "info_13h_eng": "The 13:00 slot is conducted in English.",
        "info_ostali_srp": "Other slots are in Serbian.",
        "info_5min": "Please arrive at least 5 minutes early so the visit can start on time.",
        "cena_po_osobi": "Admission per person",
        "datum": "Date",
        "datum_help": "Only weekend slots (Saturday and Sunday) are available.",
        "datum_samo_vikend": "Please select a Saturday or Sunday. The museum is open for visits on weekends only.",
        "sezona_od": "Booking season starts from March 14, 2026.",
        "termini": "Time slots",
        "english_tour": "English tour",
        "prosao": "Past",
        "popunjeno": "Full",
        "slobodno": "Available",
        "napomena_termin_eng": "This slot is conducted in English only.",
        "note_english_only": "Note: This tour is conducted in English only.",
        "rezervisi_termin": "Book slot",
        "broj_osoba": "Number of people",
        "ime_prezime": "Full name",
        "ime_placeholder": "Enter your full name",
        "email_obavezno": "Email (required)",
        "email_placeholder": "your@email.com",
        "dodatna_napomena": "Additional note (optional)",
        "napomena_placeholder": "Leave blank if none.",
        "gdpr_consent": "I agree to the processing of my data (name and email) solely for the purpose of booking confirmation at the Silva Antiqua museum in accordance with GDPR.",
        "posalji_zahtev": "Submit request",
        "morate_prihvatiti": "You must accept the data processing terms.",
        "unesite_ispravan_email": "Please enter a valid email address.",
        "unesite_ime_email": "Enter full name and email.",
        "dialog_potvrda": "Reservation confirmation",
        "potvrdite_rezervaciju": "Confirm your reservation.",
        "odustani": "Cancel",
        "potvrdi": "CONFIRM",
        "sačekajte_email": "Please wait, sending confirmation to your email...",
        "rezervacija_uspesna": "Booking successful! A confirmation has been sent to your email.",
        "za_osoba": "people",
        "admin_pregled": "Admin overview",
        "lozinka": "Password",
        "sigurni_obrisati": "Are you sure you want to delete this reservation?",
        "da_obrisi": "Yes, delete",
        "ne": "No",
        "nema_rezervacija": "No reservations.",
        "pogresna_lozinka": "Wrong password.",
        "otkazi_obrisi": "Cancel (Delete)",
        "id": "ID",
        "datum_col": "Date",
        "termin_col": "Time",
        "ime_col": "Full name",
        "email_col": "Email",
        "br_col": "No.",
        "day_sat": "Saturday",
        "day_sun": "Sunday",
    },
}

DB_PATH = "rezervacije.db"
TZ_BELGRADE = pytz.timezone("Europe/Belgrade")


def now_belgrade():
    """Trenutno vreme u Beogradu."""
    return datetime.now(TZ_BELGRADE)


def today_belgrade():
    """Današnji datum po beogradskoj vremenskoj zoni."""
    return now_belgrade().date()


def slot_has_passed(slot: str, booking_date: date) -> bool:
    """True ako je termin već prošao tog dana (za danas u Beogradu)."""
    if booking_date != today_belgrade():
        return False
    parts = slot.strip().split(":")
    if len(parts) != 2:
        return False
    h, m = int(parts[0]), int(parts[1])
    slot_dt = TZ_BELGRADE.localize(datetime(booking_date.year, booking_date.month, booking_date.day, h, m))
    return now_belgrade() >= slot_dt
CAPACITY_PER_SLOT = 6
CENA_ULAZNICE_RSD = 750  # samo za prikaz cene po osobi na stranici

# --- Moje info (SMTP / Gmail App Password) ---
EMAIL_ADDRESS = "silva.antiqua@gmail.com"
EMAIL_PASSWORD = "fwen vtdy dhpj fich"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- Baza ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            num_people INTEGER NOT NULL DEFAULT 1,
            napomena TEXT
        )
    """)
    try:
        cur.execute("ALTER TABLE reservations ADD COLUMN napomena TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE reservations ADD COLUMN num_people INTEGER NOT NULL DEFAULT 1")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE reservations ADD COLUMN email TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()


def get_slot_occupancy(booking_date: str):
    """Vraća rečnik: slot -> ukupan broj rezervisanih mesta (suma num_people)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT slot, COALESCE(SUM(num_people), 0) FROM reservations WHERE booking_date = ? GROUP BY slot",
        (booking_date,)
    )
    rows = cur.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def save_reservation(slot: str, booking_date: str, name: str, email: str, num_people: int, napomena: str = ""):
    napomena_val = (napomena.strip() if napomena else "") or "Nema napomene"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reservations (slot, booking_date, name, phone, email, num_people, napomena) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (slot, booking_date, name, "", email.strip(), num_people, napomena_val)
    )
    conn.commit()
    conn.close()


def get_all_reservations():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, slot, booking_date, name, phone, email, num_people, napomena FROM reservations ORDER BY booking_date, slot"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_reservation(reservation_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    conn.commit()
    conn.close()


def send_confirmation_email(to_email: str, name: str, slot: str, booking_date: str, num_people: int, is_english_slot: bool) -> bool:
    """Šalje potvrdni email. Vraća True ako je uspešno poslato."""
    if is_english_slot:
        reminder = "Podsetnik: Ovaj termin se održava isključivo na engleskom jeziku.\n\n"
    else:
        reminder = ""
    body = f"""{reminder}Poštovani/a {name},

Hvala Vam na rezervaciji!

Detalji Vašeg termina:

• Datum: {booking_date}
• Vreme: {slot}
• Broj osoba: {num_people}

Radujemo se Vašem dolasku!

Ukoliko niste u mogućnosti da dođete, molimo Vas odgovorite na ovaj email kako bismo oslobodili termin za druge posetioce.
Ukoliko želite da otkažete, samo odgovorite na ovaj mejl.

Srdačan pozdrav,
Silva Antiqua
"""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = f"Potvrda rezervacije - {booking_date} u {slot}"
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception:
        return False


# Nazivi dana na srpskom za admin mejl
WEEKDAY_NAMES = ["Ponedeljak", "Utorak", "Sreda", "Četvrtak", "Petak", "Subota", "Nedelja"]


def send_admin_notification_email(name: str, slot: str, booking_date: str, num_people: int, customer_email: str, napomena: str = "") -> bool:
    """Šalje vlasniku (EMAIL_ADDRESS) mejl o novoj rezervaciji. Vraća True ako je uspešno poslato."""
    d = datetime.strptime(booking_date, "%Y-%m-%d").date()
    day_name = WEEKDAY_NAMES[d.weekday()]
    datum_i_vreme = f"{day_name}, {slot}h"
    napomena_tekst = (napomena.strip() if napomena else "") or "Nema napomene"
    body = f"""Nova rezervacija stigla je preko aplikacije.

Datum i vreme: {datum_i_vreme}
Broj osoba: {num_people} osoba
Email korisnika: {customer_email}
Dodatna napomena: {napomena_tekst}

Srdačan pozdrav,
Silva Antiqua
"""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS
    msg["Subject"] = f"🔔 NOVA REZERVACIJA: {name}"
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg.as_string())
        return True
    except Exception:
        return False


# --- Termini: tačno ova četiri ---
SLOTS = ["13:00", "14:00", "15:30", "17:00"]
ENGLISH_SLOT = "13:00"  # termin isključivo na engleskom
MIN_BOOKING_DATE = date(2026, 3, 14)  # sezona rezervacija počinje od ovog datuma


def get_weekend_dates(count=52 * 2):
    """Lista samo subota i nedelja od danas, da korisnik može da bira samo vikend."""
    out = []
    d = today_belgrade()
    if d.weekday() < 5:
        d += timedelta(days=(5 - d.weekday()))
    elif d.weekday() == 6:
        d += timedelta(days=6)
    while len(out) < count:
        if d.weekday() == 5:
            out.append((d, f"Subota, {d.strftime('%d.%m.%Y')}"))
        elif d.weekday() == 6:
            out.append((d, f"Nedelja, {d.strftime('%d.%m.%Y')}"))
        d += timedelta(days=1)
    return out


def to_weekend_date(d: date) -> date:
    """Ako je d radni dan, vraća narednu subotu; inače vraća d (subota ili nedelja)."""
    w = d.weekday()
    if w < 5:
        return d + timedelta(days=5 - w)
    return d


# --- Page config: bez default opcija u meniju (gornji desni ugao) ---
st.set_page_config(menu_items={})

hide_st_style = '''
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            div[data-testid="stStatusWidget"] {display: none;}
            .stAppDeployButton {display: none !important;}
            [data-testid="stToolbar"] {display: none !important;}
            section[data-testid="stSidebar"] [data-testid="stToolbar"] {display: none !important;}
            /* Ovo sakriva sivu liniju i ikonice na dnu */
            div[data-testid="stDecoration"] {display: none !important;}
            div[data-testid="stActionButtonIcon"] {display: none !important;}
            footer {display: none !important;}
            </style>
            '''
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- Styling: dugmad i slot box ---
st.markdown("""
<style>
    .stButton > button[kind="primary"] {
        background-color: #2e7d32;
        color: white;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1b5e20;
    }
    .stButton > button:disabled {
        background-color: #c62828 !important;
        color: white !important;
    }
    .past-slot-box {
        background-color: #9e9e9e;
        color: #fff;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        text-align: center;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

init_db()

if "selected_slot" not in st.session_state:
    st.session_state.selected_slot = None
if "booking_date" not in st.session_state:
    st.session_state.booking_date = str(today_belgrade())
if "pending_delete_id" not in st.session_state:
    st.session_state.pending_delete_id = None
if "show_confirm_dialog" not in st.session_state:
    st.session_state.show_confirm_dialog = False
if "confirm_clicked" not in st.session_state:
    st.session_state.confirm_clicked = False
if "lang" not in st.session_state:
    st.session_state.lang = "SRB"
if "admin_secret_clicked" not in st.session_state:
    st.session_state.admin_secret_clicked = False

t = prevodi[st.session_state.lang]

with st.sidebar:
    st.radio("Jezik / Language", options=["SRB", "ENG"], index=0 if st.session_state.lang == "SRB" else 1, key="lang")
    # Diskretan ulaz za admina — skroz na dno sidebara
    st.markdown("<div style='margin-top: 50vh;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button(".", key="sidebar_admin_trigger", help=""):
        st.session_state.admin_secret_clicked = True
        st.rerun()
    if st.session_state.admin_secret_clicked:
        st.text_input(t["lozinka"], type="password", key="admin_pass")
        admin_pass_val = st.session_state.get("admin_pass", "")
        if admin_pass_val and admin_pass_val != st.secrets["admin_password"]:
            st.error(t["pogresna_lozinka"])

# --- Logo i naslov centrirani jedan ispod drugog (logo diskretno 150–200px) ---
LOGO_PATH = "logo.png"
LOGO_WIDTH = 170
head_col1, head_col2, head_col3 = st.columns([1, 2, 1])
with head_col2:
    if os.path.isfile(LOGO_PATH):
        st.image(LOGO_PATH, width=LOGO_WIDTH)
    else:
        st.markdown(
            f"""<div style="text-align:center; padding:1.5rem; background:#f0f0f0; border-radius:8px; color:#888; max-width:{LOGO_WIDTH}px; margin:0 auto;">Logo</div>""",
            unsafe_allow_html=True,
        )
    st.title(t["naslov"])

@st.dialog(t["dialog_potvrda"], dismissible=False)
def confirm_reservation_dialog():
    """Pop-up sa sumarom; POTVRDI odmah onemogućava dugme i pokreće slanje."""
    name = st.session_state.get("confirm_name", "")
    slot = st.session_state.get("confirm_slot", "")
    booking_date_str = st.session_state.get("confirm_booking_date", "")
    num_people = st.session_state.get("confirm_num_people", 1)
    d = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
    day_name = t["day_sun"] if d.weekday() == 6 else t["day_sat"]
    datum_str = f"{day_name}, {d.strftime('%d.%m.%Y')}"
    st.markdown(
        f"**{t['dialog_potvrda']}:** {datum_str} u **{slot}**. Za **{num_people}** {t['za_osoba']}."
    )
    st.caption(t["potvrdite_rezervaciju"])
    if not st.session_state.get("confirm_clicked"):
        col_odustani, col_potvrdi = st.columns([1, 1])
        with col_odustani:
            if st.button(t["odustani"], key="dialog_cancel_btn"):
                for key in [
                    "show_confirm_dialog", "confirm_clicked",
                    "confirm_name", "confirm_email", "confirm_num_people", "confirm_napomena",
                    "confirm_slot", "confirm_booking_date",
                ]:
                    st.session_state.pop(key, None)
                st.rerun()
        with col_potvrdi:
            if st.button(t["potvrdi"], type="primary", key="dialog_confirm_btn"):
                st.session_state.confirm_clicked = True
                st.rerun()
    else:
        st.button(t["potvrdi"], type="primary", key="dialog_confirm_btn", disabled=True)
        with st.spinner(t["sačekajte_email"]):
            save_reservation(
                st.session_state.confirm_slot,
                st.session_state.confirm_booking_date,
                st.session_state.confirm_name,
                st.session_state.confirm_email,
                st.session_state.confirm_num_people,
                st.session_state.get("confirm_napomena", ""),
            )
            send_confirmation_email(
                st.session_state.confirm_email,
                st.session_state.confirm_name,
                st.session_state.confirm_slot,
                st.session_state.confirm_booking_date,
                st.session_state.confirm_num_people,
                is_english_slot=(st.session_state.confirm_slot == ENGLISH_SLOT),
            )
            send_admin_notification_email(
                st.session_state.confirm_name,
                st.session_state.confirm_slot,
                st.session_state.confirm_booking_date,
                st.session_state.confirm_num_people,
                st.session_state.confirm_email,
                st.session_state.get("confirm_napomena", ""),
            )
        st.success(t["rezervacija_uspesna"])
        for key in [
            "selected_slot", "free_places", "show_confirm_dialog", "confirm_clicked",
            "confirm_name", "confirm_email", "confirm_num_people", "confirm_napomena",
            "confirm_slot", "confirm_booking_date",
        ]:
            st.session_state.pop(key, None)
        st.rerun()


# Informativni blok (Calendly-style) — odmah iznad kalendara
# URL ?q= koordinate forsira Google Maps da postavi crveni pin tačno na to mesto; target="_blank" otvara u novom tabu
MAPS_URL = "https://www.google.com/maps?q=44.825028,20.457778"
st.markdown(f"""
<div style="
  background-color: #e8f4fc;
  border: 1px solid #bee5eb;
  border-radius: 0.5rem;
  padding: 1rem 1.5rem;
  margin-bottom: 1rem;
  color: #0c5460;
">
<h3 style="margin-top: 0; color: inherit;">{t["info_naslov"]}</h3>
<p>🕒 {t["info_45min"]}</p>
<p>📍 <a href="{MAPS_URL}" target="_blank" rel="noopener noreferrer" style="color: #0d6efd; font-weight: 500;">Braće Baruh br. 2, Dorćol, Beograd</a><br>
<em>({t["info_klikni_adresu"]})</em></p>
<p>{t["info_vodjenja"]}<br>
{t["info_13h_eng"]}<br>
{t["info_ostali_srp"]}</p>
<p>{t["info_5min"]}</p>
<p><strong>{t["cena_po_osobi"]}: {CENA_ULAZNICE_RSD} RSD</strong></p>
</div>
""", unsafe_allow_html=True)
st.divider()

# Izbor datuma: klasičan kalendar (min 14.03.2026, samo vikend)
today = today_belgrade()
min_value = max(today, MIN_BOOKING_DATE)
first_available = to_weekend_date(min_value)
st.caption(t["sezona_od"])
booking_date = st.date_input(
    t["datum"],
    value=first_available,
    min_value=MIN_BOOKING_DATE,
    key="date_picker",
    help=t["datum_help"],
)
is_weekend = booking_date.weekday() in (5, 6)
if not is_weekend:
    st.warning(t["datum_samo_vikend"])

if is_weekend:
    booking_date_str = booking_date.isoformat()
    occupancy = get_slot_occupancy(booking_date_str)

    # Grid termina (prošli termini za danas u Beogradu su sivi i nedostupni)
    st.subheader(t["termini"])
    cols = st.columns(3)
    for i, slot in enumerate(SLOTS):
        taken = occupancy.get(slot, 0)
        free = CAPACITY_PER_SLOT - taken
        slot_label = f"{slot} ({t['english_tour']})" if slot == ENGLISH_SLOT else slot
        past = slot_has_passed(slot, booking_date)
        with cols[i % 3]:
            if past:
                st.markdown(
                    f'<div class="past-slot-box">{slot_label}<br><small>({t["prosao"]})</small></div>',
                    unsafe_allow_html=True,
                )
            elif free <= 0:
                btn_text = f" {slot_label} ({t['popunjeno']}) " if slot == ENGLISH_SLOT else f" {slot} ({t['popunjeno']}) "
                st.button(
                    btn_text,
                    key=f"btn_{booking_date_str}_{slot}",
                    disabled=True,
                )
            else:
                label = f" {slot_label} ({t['slobodno']}: {free}/{CAPACITY_PER_SLOT}) " if slot == ENGLISH_SLOT else f" {slot} ({t['slobodno']}: {free}/{CAPACITY_PER_SLOT}) "
                if st.button(label, key=f"btn_{booking_date_str}_{slot}", type="primary"):
                    st.session_state.selected_slot = slot
                    st.session_state.booking_date = booking_date_str
                    st.session_state.free_places = free

    # Forma za rezervaciju (samo za vikend)
    if st.session_state.selected_slot:
        slot = st.session_state.selected_slot
        booking_date_for_slot = date.fromisoformat(st.session_state.booking_date)
        if slot_has_passed(slot, booking_date_for_slot):
            st.session_state.selected_slot = None
            st.rerun()
        occupancy_now = get_slot_occupancy(st.session_state.booking_date)
        taken_now = occupancy_now.get(slot, 0)
        free_places = max(0, CAPACITY_PER_SLOT - taken_now)
        if free_places == 0:
            st.session_state.selected_slot = None
            st.rerun()
        st.divider()
        if slot == ENGLISH_SLOT:
            st.info(f"**{t['napomena_termin_eng']}**\n\n*{t['note_english_only']}*")
        st.subheader(f"{t['rezervisi_termin']} {slot}")
        num_people = st.selectbox(
            t["broj_osoba"],
            options=list(range(1, free_places + 1)) if free_places else [1],
            index=0,
            key="num_people_select",
        )
        name = st.text_input(t["ime_prezime"], placeholder=t["ime_placeholder"], key="form_name")
        email = st.text_input(t["email_obavezno"], placeholder=t["email_placeholder"], type="default", key="form_email")
        napomena = st.text_area(t["dodatna_napomena"], placeholder=t["napomena_placeholder"], key="form_napomena")
        data_consent = st.checkbox(t["gdpr_consent"], key="form_consent")
        submitted = st.button(t["posalji_zahtev"], type="primary", disabled=not data_consent, key="form_submit")
        if submitted:
            name_ok = name.strip()
            email_ok = email.strip()
            if not data_consent:
                st.error(t["morate_prihvatiti"])
            elif name_ok and email_ok:
                if "@" not in email_ok or "." not in email_ok.split("@")[-1]:
                    st.warning(t["unesite_ispravan_email"])
                else:
                    st.session_state.confirm_name = name_ok
                    st.session_state.confirm_email = email_ok
                    st.session_state.confirm_napomena = napomena.strip() if napomena else ""
                    st.session_state.confirm_num_people = num_people
                    st.session_state.confirm_slot = slot
                    st.session_state.confirm_booking_date = st.session_state.booking_date
                    st.session_state.show_confirm_dialog = True
                    st.session_state.confirm_clicked = False
                    st.rerun()
            else:
                st.warning(t["unesite_ime_email"])

        if st.session_state.get("show_confirm_dialog"):
            confirm_reservation_dialog()

# --- Admin Pregled: prikaži samo ako je u sidebaru kliknuto "." i lozinka tačna ---
if st.session_state.admin_secret_clicked and st.session_state.get("admin_pass") == st.secrets["admin_password"]:
    st.divider()
    st.subheader(t["admin_pregled"])
    # Potvrda pre brisanja
    if st.session_state.pending_delete_id is not None:
        pid = st.session_state.pending_delete_id
        st.warning(t["sigurni_obrisati"])
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button(t["da_obrisi"], key="confirm_del_yes"):
                delete_reservation(pid)
                st.session_state.pending_delete_id = None
                st.rerun()
        with col_no:
            if st.button(t["ne"], key="confirm_del_no"):
                st.session_state.pending_delete_id = None
                st.rerun()
        st.stop()

    rows = get_all_reservations()
    if rows:
        # Zaglavlje tabele (bez telefona i bez kolone Cena)
        h1, h2, h3, h4, h5, h6, h_btn = st.columns([0.5, 0.8, 1, 2, 2, 0.5, 1])
        h1.write(f"**{t['id']}**")
        h2.write(f"**{t['datum_col']}**")
        h3.write(f"**{t['termin_col']}**")
        h4.write(f"**{t['ime_col']}**")
        h5.write(f"**{t['email_col']}**")
        h6.write(f"**{t['br_col']}**")
        h_btn.write("")
        st.divider()
        for r in rows:
            rid = r[0]
            # r: id, slot, booking_date, name, phone, email, num_people
            email_val = (r[5] if len(r) > 5 else "")
            num_people_val = (r[6] if len(r) > 6 else (r[5] if len(r) > 5 else 1))
            c1, c2, c3, c4, c5, c6, c_btn = st.columns([0.5, 0.8, 1, 2, 2, 0.5, 1])
            c1.write(rid)
            c2.write(r[2])
            c3.write(r[1])
            c4.write(r[3])
            c5.write(email_val)
            c6.write(num_people_val)
            with c_btn:
                if st.button(t["otkazi_obrisi"], key=f"del_{rid}"):
                    st.session_state.pending_delete_id = rid
                    st.rerun()
    else:
        st.info(t["nema_rezervacija"])
