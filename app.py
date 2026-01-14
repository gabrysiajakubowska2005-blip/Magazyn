import streamlit as st
from supabase import create_client, Client

# 1. Konfiguracja połączenia z Supabase
# Upewnij się, że te dane są w Streamlit Cloud -> Settings -> Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd konfiguracji Secrets. Sprawdź czy dodałeś SUPABASE_URL i SUPABASE_KEY.")
    st.stop()

st.title("📦 System Magazynowy")

# --- SEKCJA 1: DODAWANIE KATEGORII ---
st.header("1. Dodaj nową kategorię")
with st.form("category_form", clear_on_submit=True):
    kat_kod = st.text_input("Kod kategorii (np. AGD-01)")
    kat_nazwa = st.text_input("Nazwa kategorii")
    kat_opis = st.text_area("Opis")
    
    submit_kat = st.form_submit_button("Zapisz kategorię")
    
    if submit_kat:
        if kat_kod and kat_nazwa:
            data = {"kod": kat_kod, "nazwa": kat_nazwa, "opis": kat_opis}
            try:
                supabase.table("Kategoria").insert(data).execute()
                st.success(f"Dodano kategorię: {kat_nazwa}")
            except Exception as e:
                st.error(f"Błąd bazy danych: {e}")
        else:
            st.warning("Kod i nazwa są wymagane!")

# Linia oddzielająca (zastępuje <hr>)
st.divider()

# --- SEKCJA 2: DODAWANIE PRODUKTÓW ---
st.header("2. Dodaj nowy produkt")

# Pobieranie listy kategorii do rozwijanego menu
try:
    kategorie_res = supabase.table("Kategoria").select("id, nazwa").execute()
    # Tworzymy słownik {Nazwa: ID}, aby użytkownik widział nazwę, a baza dostała ID
    kategorie_dict = {item['nazwa']: item['id'] for item in kategorie_res.data}
except Exception as e:
    kategorie_dict = {}
    st.error("Nie można pobrać kategorii. Dodaj najpierw przynajmniej jedną kategorię.")

with st.form("product_form", clear_on_submit=True):
    prod_nazwa = st.text_input("Nazwa produktu")
    prod_liczba = st.number_input("Liczba sztuk", min_value=0, step=1)
    prod_cena = st.number_input("Cena (w zł)", min_value=0.0, format="%.2f")
    
    wybor_kat = st.selectbox("Wybierz kategorię", options=list(kategorie_dict.keys()))
    
    submit_prod = st.form_submit_button("Zapisz produkt")
    
    if submit_prod:
        if prod_nazwa and wybor_kat:
            nowy_produkt = {
                "nazwa": prod_nazwa,
                "liczba": prod_liczba,
                "cena": prod_cena,
                "kategoria_id": kategorie_dict[wybor_kat]
            }
            try:
                supabase.table("produkt").insert(nowy_produkt).execute()
                st.success(f"Produkt '{prod_nazwa}' został dodany!")
            except Exception as e:
                st.error(f"Błąd podczas zapisu produktu: {e}")
        else:
            st.warning("Wypełnij nazwę produktu i wybierz kategorię.")

st.divider()

# --- SEKCJA 3: PODGLĄD DANYCH ---
st.header("3. Aktualny stan magazynu")
if st.button("Odśwież listę"):
    try:
        # Pobieramy produkty wraz z nazwą kategorii (tzw. join)
        res = supabase.table("produkt").select("nazwa, liczba, cena, Kategoria(nazwa)").execute()
        if res.data:
            st.dataframe(res.data)
        else:
            st.info("Baza danych jest pusta.")
    except Exception as e:
        st.error(f"Błąd podglądu: {e}")
        # --- SEKCJA 4: ANALIZA DANYCH (WYKRESY) ---
st.header("Analityka Zapasów")

# Pobieramy dane do wykresu
produkty_query = supabase.table("produkty").select("nazwa, liczba").execute()
df_produkty = produkty_query.data

if df_produkty:
    # Przygotowanie danych do formatu czytelnego dla wykresu
    import pandas as pd
    df = pd.DataFrame(df_produkty)
    
    # Ustawienie nazwy jako indeksu, aby oś X była opisana nazwami produktów
    df = df.set_index("nazwa")

    st.subheader("Liczba sztuk na magazynie")
    st.bar_chart(df["liczba"])
    
    # Opcjonalnie: Wykres kołowy (wymaga plotly: pip install plotly)
    # import plotly.express as px
    # fig = px.pie(df.reset_index(), values='liczba', names='nazwa', title='Udział produktów w magazynie')
    # st.plotly_chart(fig)
else:
    st.info("Brak danych do wyświetlenia wykresu.")
