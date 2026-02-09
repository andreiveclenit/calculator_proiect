import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta

# --- CONFIGURARE ---
st.set_page_config(page_title="Calculator Costuri Șantier", layout="wide", page_icon="🏗️")

# --- STILIZARE CSS ---
st.markdown("""
    <style>
    .travel-day { background-color: #3498db; color: white; padding: 5px; border-radius: 5px; }
    .work-mon-fri { background-color: #f1c40f; color: black; padding: 5px; border-radius: 5px; }
    .work-sat { background-color: #2ecc71; color: white; padding: 5px; border-radius: 5px; }
    .rest-day { background-color: #e67e22; color: white; padding: 5px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- INTERFAȚA ---
st.title("🏗️ Calculator Avansat Project Management")
st.markdown("---")

# 1. INPUT DATA
with st.sidebar:
    st.header("⚙️ Parametri Proiect")

    start_date = st.date_input("Start Date", datetime.now())
    end_date = st.date_input("End Date", datetime.now() + timedelta(days=32))

    if start_date >= end_date:
        st.error("Data de sfârșit trebuie să fie după data de început!")
        st.stop()

    num_supervisors = st.number_input("Număr Supervizori", min_value=1, value=1)
    total_required_hours = st.number_input("Total Ore Necesare (Manoperă)", min_value=10, value=1000)

    st.markdown("### 💰 Tarife Manoperă (Lucru)")
    worker_rate = st.number_input("Tarif Muncitor - Lucru (€/oră)", value=10.0)
    supervisor_rate = st.number_input("Tarif Supervizor - Lucru (€/oră)", value=15.0)

    st.markdown("### 🚌 Tarife Transport & Drum")
    trip_cost = st.number_input("Preț Combustibil / Drum (€)", value=100.0, help="Costul per mașină per sens")
    worker_travel_rate = st.number_input("Tarif Muncitor - Drum (€/oră)", value=5.0)
    supervisor_travel_rate = st.number_input("Tarif Supervizor - Drum (€/oră)", value=8.0)

    st.markdown("### 🚗 Logistică")
    seats_per_car = st.number_input("Locuri în mașină", min_value=1, value=4)

# --- LOGICA DE CALCUL ---

# 1. Calcul Durată în Săptămâni (Roundup)
days_total_duration = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
weeks_count_real = math.ceil(days_total_duration / 7)
is_odd_duration = (weeks_count_real % 2 != 0)

# 2. Identificarea zilelor speciale (Trip-uri Intermediare)
home_trip_fridays = []
return_trip_mondays = []

temp_date = pd.to_datetime(start_date)
while temp_date.weekday() != 4:  # Găsim prima vineri
    temp_date += timedelta(days=1)

friday_list = []
while temp_date < pd.to_datetime(end_date):
    friday_list.append(temp_date)
    temp_date += timedelta(days=7)

for i, friday in enumerate(friday_list):
    week_num_of_friday = int((friday - pd.to_datetime(start_date)).days / 7) + 1

    if week_num_of_friday % 2 == 0:
        weeks_remaining = weeks_count_real - week_num_of_friday
        if is_odd_duration and weeks_remaining < 3:
            pass
        else:
            home_trip_fridays.append(friday)
            return_trip_mondays.append(friday + timedelta(days=3))

# 3. Iterarea zi cu zi
days = pd.date_range(start_date, end_date)
total_work_hours_per_worker = 0  # Ore productive
calendar_data = []

# Trip calculation
trip_segments = 2  # Start + End
trip_segments += len(home_trip_fridays) * 2

for day in days:
    day_date = day.date()

    is_start = (day_date == start_date)
    is_end = (day_date == end_date)
    is_home_friday = (day in home_trip_fridays)
    is_return_monday = (day in return_trip_mondays)

    is_home_weekend = False
    for f in home_trip_fridays:
        sat = f + timedelta(days=1)
        sun = f + timedelta(days=2)
        if day == sat or day == sun:
            is_home_weekend = True
            break

    # -- LOGICA ORELOR --
    hours_worked_productive = 0  # Ore care scad din necesarul proiectului
    hours_paid_work = 0  # Ore plătite la tariful de lucru
    hours_paid_travel = 0  # Ore plătite la tariful de drum

    # 1. TRAVEL DAYS
    if is_start or is_end or is_home_friday or is_return_monday:
        d_type = "Travel ✈️"
        css_class = "travel-day"

        hours_worked_productive = 0
        hours_paid_work = 0
        hours_paid_travel = 10  # Regula nouă: Orice zi de drum = 10 ore plată drum

        if is_home_friday: d_type = "Travel (Plecare)"
        if is_return_monday: d_type = "Travel (Întoarcere)"
        if is_start: d_type = "Travel (Start)"
        if is_end: d_type = "Travel (End)"

    # 2. WEEKEND ACASĂ
    elif is_home_weekend:
        d_type = "Pauză (Acasă) 🏠"
        css_class = "rest-day"
        hours_worked_productive = 0
        hours_paid_work = 0
        hours_paid_travel = 0

    # 3. ZILE DE LUCRU (ȘANTIER)
    else:
        wd = day.weekday()
        if wd < 5:  # Luni-Vineri
            d_type = "Lucru (L-V) 🔨"
            css_class = "work-mon-fri"
            hours_worked_productive = 10
            hours_paid_work = 10
            hours_paid_travel = 0
        elif wd == 5:  # Sâmbătă
            d_type = "Lucru (Sâmbătă) 🚧"
            css_class = "work-sat"
            hours_worked_productive = 6
            hours_paid_work = 12  # Pontat Dublu la lucru
            hours_paid_travel = 0
        else:  # Duminică
            d_type = "Pauză (Duminică) ☕"
            css_class = "rest-day"
            hours_worked_productive = 0
            hours_paid_work = 0
            hours_paid_travel = 0

    total_work_hours_per_worker += hours_worked_productive

    calendar_data.append({
        "Data": day_date.strftime("%d-%m-%Y"),
        "Zi": day.day_name(),
        "Tip": d_type,
        "Culoare": css_class,
        "Ore Muncă (Prod)": hours_worked_productive,
        "Ore Plată (Lucru)": hours_paid_work,
        "Ore Plată (Drum)": hours_paid_travel
    })

# 4. Calcule Finale
if total_work_hours_per_worker == 0:
    st.error("Intervalul nu permite ore de muncă. Mărește perioada!")
    st.stop()

raw_workers = total_required_hours / total_work_hours_per_worker
num_workers = math.ceil(raw_workers)

# -- CALCUL COSTURI --
total_labor_work_workers = 0
total_labor_work_supervisors = 0
total_labor_travel_workers = 0
total_labor_travel_supervisors = 0

for row in calendar_data:
    # Cost Lucru (Manoperă Efectivă)
    total_labor_work_workers += row["Ore Plată (Lucru)"] * num_workers * worker_rate
    total_labor_work_supervisors += row["Ore Plată (Lucru)"] * num_supervisors * supervisor_rate

    # Cost Drum (Plata orelor pe drum)
    total_labor_travel_workers += row["Ore Plată (Drum)"] * num_workers * worker_travel_rate
    total_labor_travel_supervisors += row["Ore Plată (Drum)"] * num_supervisors * supervisor_travel_rate

# Cost Combustibil
cars_workers = math.ceil(num_workers / seats_per_car)
cars_supervisors = math.ceil(num_supervisors / seats_per_car)
fuel_cost_total = (cars_workers + cars_supervisors) * trip_cost * trip_segments

# Agregare Total Transport
grand_total_transport = total_labor_travel_workers + total_labor_travel_supervisors + fuel_cost_total

# Total General
grand_total_project = total_labor_work_workers + total_labor_work_supervisors + grand_total_transport

# --- AFIȘARE REZULTATE ---

# INFO BAR
st.info(f"📅 Durată Proiect: **{weeks_count_real} săptămâni** | Zile Calendaristice: {days_total_duration}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Muncitori Necesar", f"{num_workers}", f"Calculat din {raw_workers:.2f}")
c2.metric("Mașini Muncitori", f"{cars_workers}")
c3.metric("Mașini Supervizori", f"{cars_supervisors}")
c4.metric("Total Trip-uri (sens)", f"{trip_segments}")

st.markdown("---")
st.header("📊 Detaliere Costuri")

col_work, col_transp = st.columns(2)

with col_work:
    st.subheader("🛠️ Costuri Manoperă (Șantier)")
    st.markdown("Plata orelor lucrate efectiv (inclusiv sâmbăta dublă).")
    st.text_input("Manoperă Muncitori (€)", value=f"{total_labor_work_workers:,.2f}", disabled=True)
    st.text_input("Manoperă Supervizori (€)", value=f"{total_labor_work_supervisors:,.2f}", disabled=True)
    st.markdown(f"**Subtotal Manoperă:** :green[{total_labor_work_workers + total_labor_work_supervisors:,.2f} €]")

with col_transp:
    st.subheader("🚛 Cost Total Transport")
    st.markdown("Include plata orelor de drum + combustibil.")

    st.text_input("Tarif Muncitori Drum (€)", value=f"{total_labor_travel_workers:,.2f}", disabled=True,
                  help="Ore drum * Tarif drum * Nr Muncitori")
    st.text_input("Tarif Supervizori Drum (€)",
                  value=f"{total_labor_travel_travel_supervisors:,.2f}" if 'total_labor_travel_travel_supervisors' in locals() else f"{total_labor_travel_supervisors:,.2f}",
                  disabled=True)
    st.text_input("Preț Combustibil (€)", value=f"{fuel_cost_total:,.2f}", disabled=True)

    st.markdown(f"**Subtotal Transport & Logistică:** :orange[{grand_total_transport:,.2f} €]")

st.markdown("---")
st.markdown(f"## 💰 TOTAL GENERAL PROIECT: :blue[{grand_total_project:,.2f} €]")

# --- CALENDAR VIZUAL ---
st.markdown("### 📅 Calendar Detaliat")

df_cal = pd.DataFrame(calendar_data)


def color_rows(row):
    color_map = {
        "travel-day": "background-color: #3498db; color: white",
        "work-mon-fri": "background-color: #f1c40f; color: black",
        "work-sat": "background-color: #2ecc71; color: white",
        "rest-day": "background-color: #e67e22; color: white",
    }
    return [color_map.get(row["Culoare"], "")] * len(row)


st.dataframe(df_cal.style.apply(color_rows, axis=1), use_container_width=True, height=600)