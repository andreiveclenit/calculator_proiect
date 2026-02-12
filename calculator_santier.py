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
    .big-font { font-size: 20px !important; font-weight: bold; }
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
    total_required_hours = st.number_input("Total Ore Necesare (Manoperă Muncitori)", min_value=10, value=1000)
    
    st.markdown("### 💰 Tarife Manoperă")
    worker_rate = st.number_input("Tarif Muncitor - Lucru (€/oră)", value=10.0)
    supervisor_rate = st.number_input("Tarif Supervizor - Lucru (€/oră)", value=15.0)
    
    st.markdown("### 🚌 Transport & Logistică (Drumuri Mari)")
    trip_cost = st.number_input("Preț Combustibil / Drum (€)", value=100.0)
    worker_travel_rate = st.number_input("Tarif Muncitor - Drum (€/oră)", value=5.0)
    supervisor_travel_rate = st.number_input("Tarif Supervizor - Drum (€/oră)", value=8.0)
    seats_per_car = st.number_input("Locuri în mașină", min_value=1, value=4)

    st.markdown("### 🏠 Logistică Șantier (Cazare & Local)")
    accom_cost_worker = st.number_input("Cazare Muncitor (€/noapte)", value=30.0)
    accom_cost_supervisor = st.number_input("Cazare Supervizor (€/noapte)", value=50.0)
    local_transport_worker = st.number_input("Transport Local Muncitor (€/zi lucratoare)", value=5.0)
    local_transport_supervisor = st.number_input("Transport Local Supervizor (€/zi lucratoare)", value=10.0)

    st.markdown("### 📋 Alte Costuri & Materiale")
    pm_daily_rate = st.number_input("Project Management (€/zi lucrătoare)", value=50.0)
    tpl_daily_rate = st.number_input("TPL - Third Party Liability (€/zi lucrătoare)", value=20.0)
    consumables_pct = st.number_input("Consumabile (% din Manoperă Muncitori)", min_value=0.0, max_value=100.0, value=5.0, step=0.5)

# --- LOGICA DE CALCUL ---

# 1. Calcul Durată
days_total_duration = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
weeks_count_real = math.ceil(days_total_duration / 7)
is_odd_duration = (weeks_count_real % 2 != 0)

# 2. Identificarea zilelor speciale (Trip-uri Intermediare)
home_trip_fridays = []
return_trip_mondays = []

temp_date = pd.to_datetime(start_date)
while temp_date.weekday() != 4: # Găsim prima vineri
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
total_work_hours_per_worker = 0 # Ore productive per om
working_days_count = 0 # Zile efective de lucru
accommodation_nights_count = 0 # Nopti de cazare necesare
calendar_data = []

# Trip calculation
trip_segments = 2 # Start + End
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
    hours_worked_productive = 0 
    hours_paid_work = 0        
    hours_paid_travel = 0      
    needs_accommodation = True # Presupunem ca dorm acolo, apoi eliminam cazurile contrare

    # 1. TRAVEL DAYS
    if is_start or is_end or is_home_friday or is_return_monday:
        d_type = "Travel ✈️"
        css_class = "travel-day"
        hours_paid_travel = 10 
        
        if is_home_friday: 
            d_type = "Travel (Plecare)"
            needs_accommodation = False # Pleaca acasa seara
        if is_return_monday: 
            d_type = "Travel (Întoarcere)"
            # needs_accommodation ramane True (dorm acolo seara cand ajung)
        if is_start: 
            d_type = "Travel (Start)"
            # needs_accommodation ramane True
        if is_end: 
            d_type = "Travel (End)"
            needs_accommodation = False # Pleaca acasa

    # 2. WEEKEND ACASĂ
    elif is_home_weekend:
        d_type = "Pauză (Acasă) 🏠"
        css_class = "rest-day"
        needs_accommodation = False # Sunt acasa

    # 3. ZILE DE LUCRU (ȘANTIER)
    else:
        wd = day.weekday()
        if wd < 5: # Luni-Vineri
            d_type = "Lucru (L-V) 🔨"
            css_class = "work-mon-fri"
            hours_worked_productive = 10
            hours_paid_work = 10
            working_days_count += 1 
        elif wd == 5: # Sâmbătă
            d_type = "Lucru (Sâmbătă) 🚧"
            css_class = "work-sat"
            hours_worked_productive = 6
            hours_paid_work = 6 # Tarif normal
            working_days_count += 1 
        else: # Duminică
            d_type = "Pauză (Duminică) ☕"
            css_class = "rest-day"
            # needs_accommodation ramane True

    total_work_hours_per_worker += hours_worked_productive
    if needs_accommodation:
        accommodation_nights_count += 1
    
    calendar_data.append({
        "Data": day_date.strftime("%d-%m-%Y"),
        "Zi": day.day_name(),
        "Tip": d_type,
        "Culoare": css_class,
        "Ore Muncă (Prod)": hours_worked_productive,
        "Ore Plată (Lucru)": hours_paid_work,
        "Ore Plată (Drum)": hours_paid_travel,
        "Cazare": "DA" if needs_accommodation else "NU"
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
total_manhours_project = 0 

for row in calendar_data:
    # Cost Lucru 
    total_labor_work_workers += row["Ore Plată (Lucru)"] * num_workers * worker_rate
    total_labor_work_supervisors += row["Ore Plată (Lucru)"] * num_supervisors * supervisor_rate
    
    # Cost Drum (Plată ore travel)
    total_labor_travel_workers += row["Ore Plată (Drum)"] * num_workers * worker_travel_rate
    total_labor_travel_supervisors += row["Ore Plată (Drum)"] * num_supervisors * supervisor_travel_rate

    # Ore efective
    total_manhours_project += row["Ore Muncă (Prod)"] * num_workers

# Cost Combustibil (Transport Mare)
cars_workers = math.ceil(num_workers / seats_per_car)
cars_supervisors = math.ceil(num_supervisors / seats_per_car)
fuel_cost_total = (cars_workers + cars_supervisors) * trip_cost * trip_segments

# Cost Cazare
cost_accom_workers = accommodation_nights_count * num_workers * accom_cost_worker
cost_accom_supervisors = accommodation_nights_count * num_supervisors * accom_cost_supervisor
total_cost_accom = cost_accom_workers + cost_accom_supervisors

# Cost Transport Local
cost_local_trans_workers = working_days_count * num_workers * local_transport_worker
cost_local_trans_supervisors = working_days_count * num_supervisors * local_transport_supervisor
total_cost_local_trans = cost_local_trans_workers + cost_local_trans_supervisors

# Costuri Diverse (PM, TPL, Consumabile, Argon)
cost_pm = working_days_count * pm_daily_rate
cost_tpl = working_days_count * tpl_daily_rate
cost_consumables = total_labor_work_workers * (consumables_pct / 100.0)

# MODIFICARE: Rotunjire in sus (Ceiling) pentru Butelii
argon_cylinders = math.ceil(total_manhours_project / 40.0)

# Totaluri Pe Categorii
grand_total_transport_trip = total_labor_travel_workers + total_labor_travel_supervisors + fuel_cost_total
grand_total_logistics_local = total_cost_accom + total_cost_local_trans
grand_total_others = cost_pm + cost_tpl + cost_consumables

# Total General
grand_total_project = (total_labor_work_workers + total_labor_work_supervisors + 
                       grand_total_transport_trip + grand_total_logistics_local + grand_total_others)

# Rata All Inclusive
if total_manhours_project > 0:
    all_inclusive_rate = grand_total_project / total_manhours_project
else:
    all_inclusive_rate = 0

# --- AFIȘARE REZULTATE ---

# INFO BAR
st.info(f"📅 Durată: **{weeks_count_real} săpt.** | Zile Total: {days_total_duration} | Zile Lucru: {working_days_count} | Nopți Cazare: {accommodation_nights_count}")

# METRICS DE BAZĂ
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Muncitori Necesar", f"{num_workers}", f"din {raw_workers:.2f}")
c2.metric("Mașini Muncitori", f"{cars_workers}")
c3.metric("Mașini Supervizori", f"{cars_supervisors}")
c4.metric("Total Trip-uri", f"{trip_segments}")
c5.metric("Argon (Butelii)", f"{int(argon_cylinders)}", help="Total ore manoperă / 40 (Rotunjit în sus)")

st.markdown("---")
st.header("📊 Detaliere Costuri")

# 4 COLOANE PENTRU DETALIERE
col_work, col_trip, col_local, col_others = st.columns(4)

with col_work:
    st.subheader("🛠️ Manoperă")
    st.caption("Ore lucrate pe șantier")
    st.text_input("Muncitori (€)", value=f"{total_labor_work_workers:,.2f}", disabled=True)
    st.text_input("Supervizori (€)", value=f"{total_labor_work_supervisors:,.2f}", disabled=True)
    st.markdown(f"**Subtotal:** :green[{total_labor_work_workers + total_labor_work_supervisors:,.2f} €]")

with col_trip:
    st.subheader("🚌 Trips (Mari)")
    st.caption("Ore drum + Combustibil")
    st.text_input("Plată Drum Muncitori (€)", value=f"{total_labor_travel_workers:,.2f}", disabled=True)
    st.text_input("Plată Drum Supervizori (€)", value=f"{total_labor_travel_supervisors:,.2f}", disabled=True)
    st.text_input("Combustibil (€)", value=f"{fuel_cost_total:,.2f}", disabled=True)
    st.markdown(f"**Subtotal:** :orange[{grand_total_transport_trip:,.2f} €]")

with col_local:
    st.subheader("🏠 Logistică Locală")
    st.caption("Cazare + Transport Zilnic")
    st.text_input("Cazare Total (€)", value=f"{total_cost_accom:,.2f}", disabled=True, help=f"Muncitori: {cost_accom_workers:.0f} + Supervizori: {cost_accom_supervisors:.0f}")
    st.text_input("Transp. Local Total (€)", value=f"{total_cost_local_trans:,.2f}", disabled=True, help=f"Muncitori: {cost_local_trans_workers:.0f} + Supervizori: {cost_local_trans_supervisors:.0f}")
    st.markdown(f"**Subtotal:** :violet[{grand_total_logistics_local:,.2f} €]")

with col_others:
    st.subheader("📋 Alte Taxe")
    st.caption("PM, TPL, Materiale")
    st.text_input(f"PM ({working_days_count} zile)", value=f"{cost_pm:,.2f}", disabled=True)
    st.text_input(f"TPL ({working_days_count} zile)", value=f"{cost_tpl:,.2f}", disabled=True)
    st.text_input(f"Consumabile ({consumables_pct}%)", value=f"{cost_consumables:,.2f}", disabled=True)
    st.markdown(f"**Subtotal:** :blue[{grand_total_others:,.2f} €]")

st.markdown("---")

# FINAL RESULTS AREA
st.markdown("### 🏁 Rezultate Finale")
res_col1, res_col2 = st.columns(2)

with res_col1:
    st.markdown(f"## 💰 TOTAL GENERAL: :red[{grand_total_project:,.2f} €]")

with res_col2:
    st.markdown(f"## 📉 Rata All Inclusive: :violet[{all_inclusive_rate:,.2f} €/oră]")
    st.caption("Cost Total Proiect / Total Ore Manoperă Efectivă Muncitori")

# --- CALENDAR VIZUAL ---
with st.expander("📅 Vezi Calendar Detaliat & Cazare", expanded=False):
    df_cal = pd.DataFrame(calendar_data)

    def color_rows(row):
        color_map = {
            "travel-day": "background-color: #3498db; color: white", 
            "work-mon-fri": "background-color: #f1c40f; color: black", 
            "work-sat": "background-color: #2ecc71; color: white", 
            "rest-day": "background-color: #e67e22; color: white", 
        }
        return [color_map.get(row["Culoare"], "")] * len(row)

    st.dataframe(df_cal.style.apply(color_rows, axis=1), use_container_width=True, height=500)
