import streamlit as st
import pandas as pd
import altair as alt

# Init session state
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

# Data
df = pd.read_csv("EE_Orders_Demo.csv")

# ------------------------
# Sidebar menu
# ------------------------
st.sidebar.title("Easy Ergonomics Demo")
page = st.sidebar.radio(
    "Ga naar:",
    ["Home", "Forecast", "Voorraad", "Besteladvies & Scenario’s", "Uitleg & Begrippen", "Over"],
    index=["Home", "Forecast", "Voorraad", "Besteladvies & Scenario’s", "Uitleg & Begrippen", "Over"].index(st.session_state["page"])
)
st.session_state["page"] = page  # sync sidebar keuze

# ------------------------
# Home pagina
# ------------------------
if page == "Home":
    st.title("Easy Ergonomics Demo – Forecasting & Voorraadbeheer")
    st.write(
        """
        Dit prototype laat zien hoe forecasting en voorraadbeheer inzichtelijk gemaakt kunnen worden.

        👉 Doel: inspiratie geven en samen bepalen wat waardevol is voor Easy Ergonomics.
        """
    )

    st.subheader("Pagina's in deze demo")

    # Custom CSS voor kaarten
    st.markdown(
        """
        <style>
        .card {
            background-color: #f9f9f9;
            padding: 15px 20px;
            border-radius: 12px;
            border: 1px solid #e0e0e0;
            box-shadow: 1px 1px 6px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }
        .card h4 {
            margin-top: 0;
            margin-bottom: 5px;
        }
        .card p {
            margin: 0;
            color: #555;
            font-size: 0.9em;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Eerste rij
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="card">
                <h4>Forecast</h4>
                <p>Voorspellingen op basis van historische data en scenario’s.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="card">
                <h4>Voorraad</h4>
                <p>Actuele voorraad & verloop per categorie of product.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="card">
                <h4>Besteladvies & Scenario’s</h4>
                <p>Simulatie met EOQ, ROP en effecten van acties of levertijd.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Tweede rij
    col4, col5 = st.columns(2)

    with col4:
        st.markdown(
            """
            <div class="card">
                <h4>Uitleg & Begrippen</h4>
                <p>Korte uitleg van kernbegrippen zoals EOQ, ROP en safety stock.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col5:
        st.markdown(
            """
            <div class="card">
                <h4>Over</h4>
                <p>Achtergrondinformatie en contactgegevens.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )






elif page == "Forecast":
    st.title("Forecast & Acties")
    st.write("Op basis van 3000 willekeurig gegenereerde orders van Jan - Jul 2025 wordt de historische data weergegeven. /n" \
    "Met behulp van exponential smoothing en de order historie worden orders voorspelt. /n" \
    "Hieronder kunnen parameters aangepast worden om scenario’s op de forecast toe te passen.")

    import altair as alt
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    # -----------------------
    # Data voorbereiden
    # -----------------------
    df["order_datum"] = pd.to_datetime(df["order_datum"])
    df["week"] = df["order_datum"].dt.to_period("W").apply(lambda r: r.start_time)

    categorie = st.selectbox("Kies categorie", df["categorie"].unique())
    producten = df[df["categorie"] == categorie]["product_id"].unique()
    product = st.selectbox("Kies product", ["Alle producten"] + list(producten))

    if product == "Alle producten":
        weekly = df[df["categorie"] == categorie].groupby("week")["aantal"].sum()
    else:
        weekly = (
            df[(df["categorie"] == categorie) & (df["product_id"] == product)]
            .groupby("week")["aantal"]
            .sum()
        )

    # -----------------------
    # Forecast baseline (Holt, direct op ruwe data)
    # -----------------------
    forecast_horizon = st.slider("Forecast horizon (weken)", 8, 24, 16)

    if len(weekly) >= 3:
        holt_model = ExponentialSmoothing(weekly, trend="add").fit(optimized=True)
        holt_forecast = holt_model.forecast(forecast_horizon)

        # Forecast index → echte datums
        start = weekly.index[-1] + pd.offsets.Week(1)
        holt_forecast.index = pd.date_range(start=start, periods=forecast_horizon, freq="W")
    else:
        holt_forecast = pd.Series(dtype=float)

    # -----------------------
    # Actie simulatie
    # -----------------------
    st.subheader("📈 Actie simulatie")

    korting_pct = st.slider("Korting (%)", 0, 50, 0)
    elasticiteit = st.slider("Elasticiteit", 0.5, 2.0, 1.2, 0.1)

    if not holt_forecast.empty:
        actie_start = st.date_input("Actie start", holt_forecast.index[0].date())
        actie_einde = st.date_input(
            "Actie einde",
            holt_forecast.index[min(3, len(holt_forecast) - 1)].date(),
        )
    else:
        actie_start = st.date_input("Actie start", pd.Timestamp.today().date())
        actie_einde = st.date_input("Actie einde", pd.Timestamp.today().date())

    uplift = elasticiteit * (korting_pct / 100)
    scenario_forecast = holt_forecast.copy()
    if not scenario_forecast.empty:
        mask = (scenario_forecast.index >= pd.to_datetime(actie_start)) & (
            scenario_forecast.index <= pd.to_datetime(actie_einde)
        )
        scenario_forecast.loc[mask] = scenario_forecast.loc[mask] * (1 + uplift)

    # -----------------------
    # Forecast grafiek (3 lijnen)
    # -----------------------
    chart_parts = []
    if not weekly.empty:
        chart_parts.append(
            pd.DataFrame(
                {"week": weekly.index, "waarde": weekly.values, "Serie": "Historisch"}
            )
        )
    if not holt_forecast.empty:
        chart_parts.append(
            pd.DataFrame(
                {"week": holt_forecast.index, "waarde": holt_forecast.values, "Serie": "Forecast (baseline)"}
            )
        )
    if not scenario_forecast.empty:
        chart_parts.append(
            pd.DataFrame(
                {"week": scenario_forecast.index, "waarde": scenario_forecast.values, "Serie": "Forecast (met actie)"}
            )
        )

    if chart_parts:
        chart_df = pd.concat(chart_parts)
        chart = (
            alt.Chart(chart_df)
            .mark_line()
            .encode(
                x=alt.X("week:T", title="Maand", axis=alt.Axis(format="%b %Y", labelAngle=-45)),
                y=alt.Y("waarde:Q", title="Verkochte stuks"),
                color=alt.Color("Serie:N", legend=alt.Legend(title="Legenda")),
            )
            .properties(
                title=f"Forecast – {product if product != 'Alle producten' else categorie}"
            )
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Niet genoeg data om een forecast te tonen.")




# ------------------------
# Pagina 3: Forecast & Acties
# ------------------------
elif page == "Forecast & Acties":
    st.title("🔮 Forecast & Besteladvies")

    import numpy as np
    import altair as alt
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    # --- NL labels voor tijd-as ---
    alt.renderers.set_embed_options(
        timeFormatLocale={
            "dateTime": "%A, %e %B %Y %X",
            "date": "%d-%m-%Y",
            "time": "%X",
            "periods": ["AM", "PM"],
            "days": ["zondag","maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag"],
            "shortDays": ["zo","ma","di","wo","do","vr","za"],
            "months": ["januari","februari","maart","april","mei","jun","jul","aug","sep","okt","nov","dec"],
            "shortMonths": ["jan","feb","mrt","apr","mei","jun","jul","aug","sep","okt","nov","dec"]
        }
    )

    # -----------------------
    # Data voorbereiden
    # -----------------------
    df["order_datum"] = pd.to_datetime(df["order_datum"])
    df["week"] = df["order_datum"].dt.to_period("W").apply(lambda r: r.start_time)

    categorie = st.selectbox("Kies categorie", df["categorie"].unique())
    weekly = df[df["categorie"] == categorie].groupby("week")["aantal"].sum()

    weekly_smooth = weekly.rolling(window=4).mean().dropna()
    forecast_horizon = st.slider("Forecast horizon (weken)", 8, 24, 16)

    # -----------------------
    # Cache Holt-Winters fit per categorie
    # -----------------------
    @st.cache_data
    def fit_holt(cat: str, series_values: tuple):
        model = ExponentialSmoothing(series_values, trend="add").fit(optimized=True)
        return model

    holt_model = fit_holt(categorie, tuple(weekly_smooth.values))
    holt_forecast = holt_model.forecast(forecast_horizon)

    # -----------------------
    # Parameters (expander)
    # -----------------------
    with st.expander("⚙️ Parameters"):
        col1, col2 = st.columns(2)
        with col1:
            S = st.number_input("Bestelkosten per order (€)", value=100, step=10)
            opslag_pct = st.slider("Opslagkosten (% van prijs/jaar)", 5, 30, 20)
            levertijd = st.number_input("Levertijd (weken)", value=2, step=1, min_value=1)
            safety_weken = st.slider("Safety stock (weken dekking)", 0.0, 6.0, 1.0, 0.5)
        with col2:
            voorraad_start = st.number_input("Startvoorraad (stuks)", value=500, step=50)
            korting_pct = st.slider("Korting (%)", 0, 50, 0)
            elasticiteit = st.slider("Elasticiteit (gevoeligheid)", 0.5, 2.0, 1.2, 0.1)

    # -----------------------
    # Actie periode (expander)
    # -----------------------
    with st.expander("📈 Actie simulatie"):
        actie_start = st.date_input("Actie start", holt_forecast.index[0])
        actie_einde = st.date_input("Actie einde", holt_forecast.index[min(3, len(holt_forecast)-1)])

    # Gemiddelde prijs & opslagkosten
    gem_prijs = float(df[df["categorie"] == categorie]["prijs"].mean())
    prijs_met_korting = gem_prijs * (1 - korting_pct / 100)
    H = prijs_met_korting * (opslag_pct / 100)  # €/jaar per stuk

    # Forecast aanpassen met actie
    uplift = elasticiteit * (korting_pct / 100)
    scenario_forecast = holt_forecast.copy()
    mask = (holt_forecast.index >= pd.to_datetime(actie_start)) & (holt_forecast.index <= pd.to_datetime(actie_einde))
    scenario_forecast.loc[mask] = scenario_forecast.loc[mask] * (1 + uplift)

    # -----------------------
    # EOQ, ROP & Safety stock
    # -----------------------
    d = float(scenario_forecast.mean())   # stuks per week
    EOQ = float(np.sqrt((2 * d * 52 * S) / max(H, 1e-6)))
    SS = d * safety_weken
    ROP = d * levertijd + SS
    Q = max(EOQ, d * levertijd + SS)

    # -----------------------
    # Voorraad simulatie
    # -----------------------
    vraag_reeks = list(weekly.values) + list(scenario_forecast.values)
    weken = pd.to_datetime(list(weekly.index) + list(scenario_forecast.index))

    on_hand = voorraad_start
    in_transit = []
    voorraad_rows, order_rows = [], []

    for i, week in enumerate(weken):
        # leveringen
        arrivals = [x for x in in_transit if x["week"] == week]
        if arrivals:
            on_hand += sum(x["qty"] for x in arrivals)
        in_transit = [x for x in in_transit if x["week"] > week]

        # vraag
        vraag = vraag_reeks[i]
        on_hand = max(on_hand - vraag, 0)

        # check reorder
        if on_hand <= ROP:
            arr_week = week + pd.Timedelta(weeks=int(levertijd))
            in_transit.append({"week": arr_week, "qty": Q})
            order_rows.append({"week": week, "voorraad": on_hand, "hoeveelheid": Q})

        voorraad_rows.append({"week": week, "voorraad": on_hand})

    voorraad_df = pd.DataFrame(voorraad_rows)
    bestellingen_df = pd.DataFrame(order_rows)

    gem_voorraad = voorraad_df["voorraad"].mean()
    aantal_orders = len(bestellingen_df)

    # -----------------------
    # KPI’s
    # -----------------------
    st.subheader("📊 KPI’s")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("EOQ (Q)", f"{Q:.0f}")
    c2.metric("ROP", f"{ROP:.0f}")
    c3.metric("Safety stock", f"{SS:.0f}")
    c4.metric("# Orders", f"{aantal_orders}")
    c5.metric("Gem. voorraad", f"{gem_voorraad:.0f}")

    if not bestellingen_df.empty:
        st.success(
            f"📅 Eerste bestelling geplaatst op {bestellingen_df.iloc[0]['week'].strftime('%d-%m-%Y')} "
            f"van {Q:.0f} stuks (levering na {int(levertijd)} weken)."
        )

    # -----------------------
    # Grafieken (onder elkaar)
    # -----------------------
    # Forecast
    chart_df = pd.DataFrame({
        "week": list(weekly.index) + list(holt_forecast.index) + list(scenario_forecast.index),
        "waarde": list(weekly.values) + list(holt_forecast.values) + list(scenario_forecast.values),
        "Serie": (["Historisch"] * len(weekly))
                 + (["Forecast (baseline)"] * len(holt_forecast))
                 + (["Forecast (met actie)"] * len(scenario_forecast))
    })
    chart = alt.Chart(chart_df).mark_line().encode(
        x=alt.X("week:T", title="Maand", axis=alt.Axis(format="%b %Y", labelAngle=-45)),
        y=alt.Y("waarde:Q", title="Verkochte stuks"),
        color="Serie:N"
    ).properties(title="Verkoop Forecast per maand")
    st.altair_chart(chart, use_container_width=True)

    # Voorraad
    legend_df = pd.DataFrame({
        "week": list(voorraad_df["week"]) * 2,
        "waarde": list(voorraad_df["voorraad"]) + [ROP] * len(voorraad_df),
        "Serie": ["Voorraadniveau"] * len(voorraad_df) + ["ROP"] * len(voorraad_df)
    })

    chart2 = alt.Chart(legend_df).mark_line().encode(
        x=alt.X("week:T", title="Maand", axis=alt.Axis(format="%b %Y", labelAngle=-45)),
        y=alt.Y("waarde:Q", title="Voorraadniveau"),
        color=alt.Color("Serie:N",
                        scale=alt.Scale(domain=["Voorraadniveau", "ROP"],
                                        range=["purple", "orange"]),
                        legend=alt.Legend(title="Legenda"))
    ).properties(title="Voorraadniveau")
    st.altair_chart(chart2, use_container_width=True)



# ------------------------
# Pagina 4: Multi-platform
# ------------------------
elif page == "Multi-platform":
    st.title("🌍 Multi-platform overzicht")
    st.write("Verdeling van orders over verschillende verkoopkanalen.")

    verkopen_per_kanaal = df.groupby("kanaal")["aantal"].sum()
    st.bar_chart(verkopen_per_kanaal)
