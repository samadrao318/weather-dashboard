import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime  #, timedeltad
import streamlit.components.v1 as components

# -------------------- App config --------------------
st.set_page_config(page_title="Pro Weather Dashboard", page_icon="🌦️", layout="wide")

# -------------------- Styles (Dark/Light) --------------------
def local_css(dark: bool = False):
    if dark:
        st.markdown("""
        <style>
        .stApp { background-color: #0f1724; color: #e6eef8; }
        .card { background: #0b1220; border-radius: 8px; padding: 12px; }
        .kpi { background: linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); padding:10px; border-radius:8px; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background-color: #f7fafc; color: #0b1220; }
        .card { background: #ffffff; border-radius: 8px; padding: 12px; box-shadow: 0 1px 4px rgba(12,18,22,0.06); }
        .kpi { background: linear-gradient(90deg, rgba(11,17,28,0.02), rgba(11,17,28,0.01)); padding:10px; border-radius:8px; }
        </style>
        """, unsafe_allow_html=True)

# -------------------- Helpers / API --------------------
@st.cache_data(ttl=600)
def get_coords(city: str):
    """Return (lat, lon, name) or None"""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 5}
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        if "results" in data and len(data["results"]) > 0:
            # pick the top result
            top = data["results"][0]
            return top["latitude"], top["longitude"], f"{top.get('name')}, {top.get('country')}"
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def fetch_weather(lat: float, lon: float, timezone: str = "UTC"):
    """Fetch current, hourly (48h) and daily (7d) from Open-Meteo"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "temperature_2m,apparent_temperature,relativehumidity_2m,winddirection_10m,windspeed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weathercode,sunrise,sunset",
        "timezone": timezone,
        "forecast_days": 7
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

# Simple weathercode -> icon + text mapping (basic)
WEATHER_CODE_MAP = {
    0: ("☀️", "Clear"),
    1: ("🌤️", "Mainly clear"),
    2: ("⛅", "Partly cloudy"),
    3: ("☁️", "Overcast"),
    45: ("🌫️", "Fog"),
    48: ("🌫️", "Depositing rime fog"),
    51: ("🌦️", "Light drizzle"),
    53: ("🌧️", "Moderate drizzle"),
    55: ("🌧️", "Dense drizzle"),
    61: ("🌧️", "Slight rain"),
    63: ("🌧️", "Moderate rain"),
    65: ("🌧️", "Heavy rain"),
    71: ("❄️", "Light snow"),
    73: ("❄️", "Moderate snow"),
    80: ("🌧️", "Rain showers"),
    95: ("⛈️", "Thunderstorm"),
}

def weather_icon(code: int):
    return WEATHER_CODE_MAP.get(code, ("🌈", "Unknown"))

# -------------------- Sidebar --------------------
with st.sidebar:
    st.title("🌦️ Weather")
    st.write("Search a city, add to favorites, toggle theme and units.")
    #city_input = st.selectbox("Search City", options=cities, index=0)
    
    
    
    with st.sidebar:
        st.header("🌦️ Weather Search")

        city_input = st.text_input("🔎 Search City", placeholder="Enter City Name")

        suggestions = []

        if city_input.strip() != "":
            # Fetch suggestions from Open-Meteo Geocoding API
            url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {"name":city_input , "count": 6}
            try:
                r = requests.get(url, params=params)
                data = r.json()

                if "results" in data:
                    suggestions = [
                        f"{item['name']}, {item.get('country','')}"
                        for item in data["results"]
                    ]
            except:
                st.error("Error fetching suggestions")

        # Show suggestions
        selected_city = None
        if suggestions:
            selected_city = st.selectbox("Suggested Cities", suggestions)

        # Final city after user clicks or selects suggestion
        if selected_city:
            final_city = selected_city
            st.success(f"Selected: {final_city}")
        else:
            final_city = None

    col_a, col_b = st.columns([2,1])
    with col_a:
        search = st.button("🔎 Search", type="primary")
    #with col_b:
    st.caption("Clear Fetch Data")
    clear = st.button("🧹 Clear", type= "primary")

    st.markdown("---")
    units = st.radio("Units", options=["Metric (°C)", "Imperial (°F)"], index=0)
    dark_mode = st.checkbox("Dark mode", value=False)

    st.markdown("---")
    st.subheader("Favorites")

    # Initialize favorites if not exists
    if "favorites" not in st.session_state:
        st.session_state.favorites = ["Pakpattan","Lahore", "Karachi", "Islamabad"]

    # ---- Selectbox to display favorites ----
    fav_city = st.selectbox(
        "Choose From Favorites",
        st.session_state.favorites,
        key="favorite_selector"
    )

    # When user picks a city → auto search
    if fav_city:
        city_input = fav_city
        search = True


    # ---- Add new favorite ----
    new_fav = st.text_input("Add Favorite" , placeholder="Add city")

    if st.button("➕ Add"):
        if new_fav and new_fav not in st.session_state.favorites:
            st.session_state.favorites.append(new_fav)
            st.rerun()  # Refresh to show updated list


    st.markdown("---")
    st.caption("Powered by Open-Meteo | Built By **Rao Samad**")

# Apply theme
local_css(dark=dark_mode)

# -------------------- Main --------------------

st.header("🌤️ Weather Dashboard")



if clear:
    # simple reset
    if "weather_data" in st.session_state:
        del st.session_state["weather_data"]
    if "location" in st.session_state:
        del st.session_state["location"]
    st.rerun()

if search:
    coords = get_coords(city_input)
    if not coords:
        st.error("City not found. Try another name or check spelling.")
    else:
        lat, lon, pretty_name = coords
        try:
            tz_name = "Asia/Karachi"
            weather = fetch_weather(lat, lon, timezone=tz_name)
            st.session_state["weather_data"] = weather
            st.session_state["location"] = {"lat": lat, "lon": lon, "name": pretty_name}
        except Exception as e:
            st.error("Failed to fetch weather data. Try again.")

# Load from session state if present
weather = st.session_state.get("weather_data")
location = st.session_state.get("location")

if weather and location:
    # Normalize data
    current = weather.get("current_weather", {})
    daily = weather.get("daily", {})
    hourly = weather.get("hourly", {})

    # KPIs Row
    st.subheader(f"Location: {location['name']}")
    k1, k2, k3, k4, k5 = st.columns([1.5,1.2,1.2,1.2,1.2])

    temp = current.get("temperature")
    wind = current.get("windspeed")
    wind_dir = current.get("winddirection")

    # approximate feels_like from hourly apparent_temperature at current hour if exists
    feels = None
    try:
        now_idx = hourly["time"].index(current.get("time"))
        feels = hourly.get("apparent_temperature")[now_idx]
    except Exception:
        feels = temp

    humidity = None
    try:
        humidity = hourly.get("relativehumidity_2m")[now_idx]
    except Exception:
        humidity = "-"

    # KPIs
    k1.metric(label="Temperature 🌡️", value=f"{temp} °C", delta=f"Feels {feels} °C")
    k2.metric(label="Wind Speed 💨", value=f"{wind} km/h")
    k3.metric(label="Wind Dir ↗️", value=f"{wind_dir}°")
    # Sunrise / Sunset
    try:
        sunrise = daily.get("sunrise")[0]
        sunset = daily.get("sunset")[0]
        k4.metric(label="Sunrise 🌅", value=datetime.fromisoformat(sunrise).strftime('%H:%M'))
        k5.metric(label="Sunset 🌄", value=datetime.fromisoformat(sunset).strftime('%H:%M'))
    except Exception:
        k4.metric(label="Sunrise 🌅", value="-")
        k5.metric(label="Sunset 🌄", value="-")

    st.markdown("---")

    # Two-column layout: left = forecast cards, right = charts
    left_col, right_col = st.columns([1.1,1.6])

    # Left: 7-day forecast cards
    with left_col:
        st.subheader("7-Day Forecast")
        days = daily.get("time", [])
        max_t = daily.get("temperature_2m_max", [])
        min_t = daily.get("temperature_2m_min", [])
        weather_codes = daily.get("weathercode", [])

        for i in range(len(days)):
            day_label = datetime.fromisoformat(days[i]).strftime('%a %d %b')
            icon, txt = weather_icon(weather_codes[i])
            st.markdown(f"<div class='card'><strong>{day_label}</strong>  &nbsp; {icon}  &nbsp; <em>{txt}</em><br>Max: {max_t[i]}°C  |  Min: {min_t[i]}°C</div>", unsafe_allow_html=True)
            
            
    with right_col:
        # --- 7-Day Selectable Hourly Forecast Chart ---

        st.subheader("Hourly Forecast (Select a Day)")

        # Prepare 7-day dates list
        days = daily.get("time", [])
        day_labels = [datetime.fromisoformat(d).strftime("%a %d %b") for d in days]
        col1 , col2 = st.columns(2)
        with col1:
            # Selectbox for picking a specific day
            selected_day = st.selectbox("Choose a day", day_labels)
        with col2:
            clock_html = """
            <div style="
                background-color:#dc2626;  /* Red box */
                color:white;
                border-radius:10px;
                padding:10px;
                width:100%;
                text-align:center;
                font-family:Arial, sans-serif;
                box-sizing:border-box;">
                <div style="font-size:14px;">Live Time</div>
                <div id="clock" style="font-size:20px; font-weight:bold; margin-top:5px;"></div>
            </div>

            <script>
            function updateClock() {
                var now = new Date();
                var timeString = now.toLocaleTimeString();
                document.getElementById("clock").innerHTML = timeString;
            }
            setInterval(updateClock, 1000);
            updateClock();
            </script>
            """
            components.html(clock_html, height=70)
            
                
                
        # Convert selected day back to index
        day_index = day_labels.index(selected_day)

        # Extract all hourly data
        h_df = pd.DataFrame({
            "time": hourly.get("time", []),
            "temp": hourly.get("temperature_2m", []),
            "apparent": hourly.get("apparent_temperature", []),
            "humidity": hourly.get("relativehumidity_2m", []),
            "windspeed": hourly.get("windspeed_10m", [])
        })

        # Convert time to datetime
        h_df["time"] = pd.to_datetime(h_df["time"])

        # Filtering data for selected day only
        selected_date = datetime.fromisoformat(days[day_index]).date()
        filtered_df = h_df[h_df["time"].dt.date == selected_date]

        st.write(f"### Hourly Weather — {selected_day}")

        if filtered_df.empty:
            st.warning("No hourly data available for this day.")
        else:
            # Plotly Chart for selected day
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=filtered_df['time'], 
                y=filtered_df['temp'], 
                mode='lines+markers', 
                name='Temp (°C)'
            ))

        fig.add_trace(go.Scatter(
            x=filtered_df['time'], 
            y=filtered_df['apparent'], 
            mode='lines', 
            name='Feels Like'
        ))

        fig.add_trace(go.Bar(
            x=filtered_df['time'], 
            y=filtered_df['windspeed'], 
            name='Wind (km/h)',
            yaxis='y2',
            opacity=0.3
        ))

        fig.update_layout(
            title=f"Hourly Forecast — {selected_day}",
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            yaxis2=dict(
                title='Wind (km/h)',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            hovermode="x unified",
            plot_bgcolor="white",
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        st.plotly_chart(fig, width='content')

    #  hourly chart + table
    
    st.subheader("Hourly Forecast ☂️")
    # prepare hourly df
    h_df = pd.DataFrame({
        "time": hourly.get("time", []),
        "temp": hourly.get("temperature_2m", []),
        "apparent": hourly.get("apparent_temperature", []),
        "humidity": hourly.get("relativehumidity_2m", []),
        "windspeed": hourly.get("windspeed_10m", [])
    })

    # convert time strings to datetime for plotting
    if not h_df.empty:
        h_df['time'] = pd.to_datetime(h_df['time'])

        # Plotly multi-line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=h_df['time'], y=h_df['temp'], mode='lines+markers', name='Temp (°C)'))
        fig.add_trace(go.Scatter(x=h_df['time'], y=h_df['apparent'], mode='lines', name='Feels Like'))
        fig.add_trace(go.Bar(x=h_df['time'], y=h_df['windspeed'], name='Wind (km/h)', yaxis='y2', opacity=0.3))

        # dual y axis layout
        fig.update_layout(
            title='7-Days Hourly Forecast',
            xaxis_title='Time',
            yaxis_title='Temperature (°C)',
            yaxis2=dict(title='Wind (km/h)', overlaying='y', side='right', showgrid=False),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            hovermode='x unified',
            plot_bgcolor='white'
        )

        st.plotly_chart(fig, width='stretch')

        st.subheader("☀️ Show hourly data:")
        st.dataframe(h_df.head(48), width='stretch')

    # Footer: attribution
    st.markdown("<hr>", unsafe_allow_html=True)

    footer_part1 = """
    <div style='text-align: center; line-height: 1.6;'>
        <p style='font-size: 20px; font-weight: bold; margin: 0;'>
            Developed by <span style='color:#4CAF50;'>Rao Samad</span>
        </p>
    """

    st.markdown(footer_part1, unsafe_allow_html=True)

    footer_part2 = """
        <p style='margin: 6px 0; font-size: 16px;'>
            📧 <a href='mailto:samadrao318@gmail.com' 
                style='text-decoration: none; color: #1E88E5;'>
                samadrao318@gmail.com
            </a>
        </p>

        <p style='margin: 6px 0; font-size: 16px;'>
            📞 <a href='tel:+923046503593' 
                style='text-decoration: none; color: #1E88E5;'>
                +92 3046503593
            </a>
        </p>
    """

    st.markdown(footer_part2, unsafe_allow_html=True)

    footer_part3 = """
        <p style='font-size: 13px; color: black; margin-top: 8px;'>
            © 2025 All Rights Reserved
        </p>
    </div>
    """

    st.markdown(footer_part3, unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)



else:
    st.info("Search a city from the sidebar to load weather data.")

# -------------------- End --------------------
