import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime

import pytz

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
PRICE_PER_PERSON_RSD = 750  # cenovnik: fiksna cena po osobi

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
            phone TEXT NOT NULL,
            email TEXT,
            num_people INTEGER NOT NULL DEFAULT 1
        )
    """)
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


def save_reservation(slot: str, booking_date: str, name: str, phone: str, email: str, num_people: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reservations (slot, booking_date, name, phone, email, num_people) VALUES (?, ?, ?, ?, ?, ?)",
        (slot, booking_date, name, phone, email.strip(), num_people)
    )
    conn.commit()
    conn.close()


def get_all_reservations():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, slot, booking_date, name, phone, email, num_people FROM reservations ORDER BY booking_date, slot"
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

Ukupna cena Vaše rezervacije za {num_people} osoba iznosi {num_people * PRICE_PER_PERSON_RSD} RSD. Plaćanje ćete izvršiti prilikom dolaska u muzej.

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


def send_admin_notification_email(name: str, slot: str, booking_date: str, num_people: int, phone: str, customer_email: str) -> bool:
    """Šalje vlasniku (EMAIL_ADDRESS) mejl o novoj rezervaciji. Vraća True ako je uspešno poslato."""
    d = datetime.strptime(booking_date, "%Y-%m-%d").date()
    day_name = WEEKDAY_NAMES[d.weekday()]
    datum_i_vreme = f"{day_name}, {slot}h"
    ukupna_cena = num_people * PRICE_PER_PERSON_RSD
    body = f"""Nova rezervacija stigla je preko aplikacije.

Datum i vreme: {datum_i_vreme}
Broj osoba: {num_people} osoba
Kontakt telefon: {phone}
Email korisnika: {customer_email}
Ukupna cena: {ukupna_cena} RSD

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

# --- Styling ---
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


@st.dialog("Potvrda rezervacije", dismissible=False)
def confirm_reservation_dialog():
    """Pop-up sa sumarom; POTVRDI odmah onemogućava dugme i pokreće slanje."""
    name = st.session_state.get("confirm_name", "")
    slot = st.session_state.get("confirm_slot", "")
    booking_date_str = st.session_state.get("confirm_booking_date", "")
    num_people = st.session_state.get("confirm_num_people", 1)
    ukupan_iznos = num_people * PRICE_PER_PERSON_RSD
    d = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
    datum_str = f"{WEEKDAY_NAMES[d.weekday()]}, {d.strftime('%d.%m.%Y')}"
    st.markdown(
        f"**Potvrda rezervacije:** {datum_str} u **{slot}**. "
        f"Za **{num_people}** osoba, ukupno **{ukupan_iznos} RSD**."
    )
    st.caption("Potvrdite rezervaciju.")
    if not st.session_state.get("confirm_clicked"):
        col_odustani, col_potvrdi = st.columns([1, 1])
        with col_odustani:
            if st.button("Odustani", key="dialog_cancel_btn"):
                for key in [
                    "show_confirm_dialog", "confirm_clicked",
                    "confirm_name", "confirm_email", "confirm_phone", "confirm_num_people",
                    "confirm_slot", "confirm_booking_date",
                ]:
                    st.session_state.pop(key, None)
                st.rerun()
        with col_potvrdi:
            if st.button("POTVRDI", type="primary", key="dialog_confirm_btn"):
                st.session_state.confirm_clicked = True
                st.rerun()
    else:
        st.button("POTVRDI", type="primary", key="dialog_confirm_btn", disabled=True)
        with st.spinner("Molimo sačekajte, šaljemo potvrdu na vaš email..."):
            save_reservation(
                st.session_state.confirm_slot,
                st.session_state.confirm_booking_date,
                st.session_state.confirm_name,
                st.session_state.confirm_phone,
                st.session_state.confirm_email,
                st.session_state.confirm_num_people,
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
                st.session_state.confirm_phone,
                st.session_state.confirm_email,
            )
        st.success("Rezervacija uspešna! Potvrda vam je poslata na email.")
        for key in [
            "selected_slot", "free_places", "show_confirm_dialog", "confirm_clicked",
            "confirm_name", "confirm_email", "confirm_phone", "confirm_num_people",
            "confirm_slot", "confirm_booking_date",
        ]:
            st.session_state.pop(key, None)
        st.rerun()


st.title("Rezervacije termina")

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
<h3 style="margin-top: 0; color: inherit;">Muzejska poseta uz vodiča</h3>
<p>🕒 45 min</p>
<p>📍 <a href="{MAPS_URL}" target="_blank" rel="noopener noreferrer" style="color: #0d6efd; font-weight: 500;">Braće Baruh br. 2, Dorćol, Beograd</a><br>
<em>(Klikni na adresu za navigaciju.)</em></p>
<p>Vođenja u muzejiću Silva Antiqua organizuju se svakog vikenda (subota i nedelja).<br>
Termin u 13:00 časova realizuje se na engleskom jeziku.<br>
Ostali termini su na srpskom jeziku.</p>
<p>Molimo vas da dođete barem 5 minuta ranije, kako bi poseta mogla da započne na vreme.</p>
</div>
""", unsafe_allow_html=True)
st.divider()

# Vizuelni kalendar (klik na broj). Prvi dan u nedelji = ponedeljak (first_weekday=0) zavisi od
# locale u browseru; za vikend skroz desno podesite jezik pregledača na srpski/evropski.
booking_date = st.date_input(
    "Datum",
    value=today_belgrade(),
    key="date_picker",
    help="Izaberite subotu ili nedelju.",
)
booking_date_str = booking_date.isoformat()

# Ako korisnik izabere radni dan (pon–pet), samo poruka — termini se ne prikazuju
if booking_date.weekday() < 5:
    st.error("⚠️ Molimo izaberite subotu ili nedelju.")
    st.stop()

occupancy = get_slot_occupancy(booking_date_str)

# Grid termina (prošli termini za danas u Beogradu su sivi i nedostupni)
st.subheader("Termini")
cols = st.columns(3)
for i, slot in enumerate(SLOTS):
    taken = occupancy.get(slot, 0)
    free = CAPACITY_PER_SLOT - taken
    slot_label = f"{slot} (English tour)" if slot == ENGLISH_SLOT else slot
    past = slot_has_passed(slot, booking_date)
    with cols[i % 3]:
        if past:
            st.markdown(
                f'<div class="past-slot-box">{slot_label}<br><small>(Prošao)</small></div>',
                unsafe_allow_html=True,
            )
        elif free <= 0:
            btn_text = f" {slot_label} (Popunjeno) " if slot == ENGLISH_SLOT else f" {slot} (Popunjeno) "
            st.button(
                btn_text,
                key=f"btn_{booking_date_str}_{slot}",
                disabled=True,
            )
        else:
            label = f" {slot_label} (Slobodno: {free}/{CAPACITY_PER_SLOT}) " if slot == ENGLISH_SLOT else f" {slot} (Slobodno: {free}/{CAPACITY_PER_SLOT}) "
            if st.button(label, key=f"btn_{booking_date_str}_{slot}", type="primary"):
                st.session_state.selected_slot = slot
                st.session_state.booking_date = booking_date_str
                st.session_state.free_places = free

# Forma za rezervaciju
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
        st.info(
            "**Napomena:** Ovaj termin se održava isključivo na engleskom jeziku.\n\n"
            "*Note: This tour is conducted in English only.*"
        )
    st.subheader(f"Rezerviši termin {slot}")
    # Broj osoba i cena van forme da se odmah osvežavaju pri promeni izbora
    num_people = st.selectbox(
        "Broj osoba",
        options=list(range(1, free_places + 1)) if free_places else [1],
        index=0,
        key="num_people_select",
    )
    ukupan_iznos = num_people * PRICE_PER_PERSON_RSD
    st.success(f"**Ukupan iznos za plaćanje u muzeju: {ukupan_iznos} RSD**")
    st.caption("Plaćanje se vrši isključivo na licu mesta (u muzeju).")
    with st.form("rezervacija_form"):
        name = st.text_input("Ime i prezime", placeholder="Unesite ime i prezime")
        email = st.text_input("Email (obavezno)", placeholder="vas@email.com", type="default")
        phone = st.text_input("Telefon", placeholder="Unesite broj telefona")
        submitted = st.form_submit_button("Pošalji zahtev")
        if submitted:
            name_ok = name.strip()
            email_ok = email.strip()
            phone_ok = phone.strip()
            if name_ok and phone_ok and email_ok:
                if "@" not in email_ok or "." not in email_ok.split("@")[-1]:
                    st.warning("Unesite ispravnu email adresu.")
                else:
                    st.session_state.confirm_name = name_ok
                    st.session_state.confirm_email = email_ok
                    st.session_state.confirm_phone = phone_ok
                    st.session_state.confirm_num_people = num_people
                    st.session_state.confirm_slot = slot
                    st.session_state.confirm_booking_date = st.session_state.booking_date
                    st.session_state.show_confirm_dialog = True
                    st.session_state.confirm_clicked = False
                    st.rerun()
            else:
                st.warning("Unesite ime i prezime, email i telefon.")

    if st.session_state.get("show_confirm_dialog"):
        confirm_reservation_dialog()

# --- Admin Pregled ---
st.divider()
st.subheader("Admin Pregled")
admin_pass = st.text_input("Lozinka", type="password", key="admin_pass")
if admin_pass:
    if admin_pass == "admin123":
        # Potvrda pre brisanja
        if st.session_state.pending_delete_id is not None:
            pid = st.session_state.pending_delete_id
            st.warning("Da li ste sigurni da želite da obrišete ovu rezervaciju?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Da, obriši", key="confirm_del_yes"):
                    delete_reservation(pid)
                    st.session_state.pending_delete_id = None
                    st.rerun()
            with col_no:
                if st.button("Ne", key="confirm_del_no"):
                    st.session_state.pending_delete_id = None
                    st.rerun()
            st.stop()

        rows = get_all_reservations()
        if rows:
            # Zaglavlje tabele (dodata kolona Cena)
            h1, h2, h3, h4, h5, h6, h7, h8, h_btn = st.columns([0.5, 0.8, 1, 2, 1.5, 2, 0.5, 0.7, 1])
            h1.write("**ID**")
            h2.write("**Datum**")
            h3.write("**Termin**")
            h4.write("**Ime i prezime**")
            h5.write("**Telefon**")
            h6.write("**Email**")
            h7.write("**Br.**")
            h8.write("**Cena**")
            h_btn.write("")
            st.divider()
            for r in rows:
                rid = r[0]
                email_val = (r[5] if len(r) > 6 else "")
                num_people_val = (r[6] if len(r) > 6 else (r[5] if len(r) > 5 else 1))
                cena_rsd = num_people_val * PRICE_PER_PERSON_RSD
                c1, c2, c3, c4, c5, c6, c7, c8, c_btn = st.columns([0.5, 0.8, 1, 2, 1.5, 2, 0.5, 0.7, 1])
                c1.write(rid)
                c2.write(r[2])
                c3.write(r[1])
                c4.write(r[3])
                c5.write(r[4])
                c6.write(email_val)
                c7.write(num_people_val)
                c8.write(f"{cena_rsd} RSD")
                with c_btn:
                    if st.button("Otkaži (Obriši)", key=f"del_{rid}"):
                        st.session_state.pending_delete_id = rid
                        st.rerun()
        else:
            st.info("Nema rezervacija.")
    else:
        st.error("Pogrešna lozinka.")
