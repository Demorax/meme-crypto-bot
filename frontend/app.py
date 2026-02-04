import os
import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Crypto Prediction Dashboard",
    page_icon="📈",
    layout="wide"
)


def init_session_state():
    if 'simulation_data' not in st.session_state:
        st.session_state.simulation_data = []
    if 'is_running' not in st.session_state:
        st.session_state.is_running = False
    if 'current_prediction' not in st.session_state:
        st.session_state.current_prediction = None


def get_tokens():
    try:
        response = requests.get(f"{API_URL}/tokens", timeout=5)
        response.raise_for_status()
        return response.json().get("tokens", [])
    except requests.exceptions.RequestException as e:
        st.error(f"API connection failed: {e}")
        return []


def create_chart(data: list) -> go.Figure:
    if not data:
        return go.Figure()

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
        subplot_titles=("Market Cap", "Confidence")
    )

    # hlavní čára
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['marketCap'],
            mode='lines',
            name='Market Cap',
            line=dict(color='gray', width=1)
        ),
        row=1, col=1
    )

    # BUY signály
    buy_mask = df['prediction'] == 'BUY'
    if buy_mask.any():
        fig.add_trace(
            go.Scatter(
                x=df.loc[buy_mask, 'timestamp'],
                y=df.loc[buy_mask, 'marketCap'],
                mode='markers',
                name='BUY',
                marker=dict(color='green', size=8, symbol='triangle-up')
            ),
            row=1, col=1
        )

    # NO BUY
    no_buy_mask = df['prediction'] == 'NO BUY'
    if no_buy_mask.any():
        fig.add_trace(
            go.Scatter(
                x=df.loc[no_buy_mask, 'timestamp'],
                y=df.loc[no_buy_mask, 'marketCap'],
                mode='markers',
                name='NO BUY',
                marker=dict(color='red', size=6, symbol='circle')
            ),
            row=1, col=1
        )

    # confidence bary
    colors = ['green' if p == 'BUY' else 'red' for p in df['prediction']]
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['confidence'],
            name='Confidence',
            marker_color=colors
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    fig.update_yaxes(title_text="Market Cap ($)", row=1, col=1)
    fig.update_yaxes(title_text="Confidence", range=[0, 1], row=2, col=1)

    return fig


def display_prediction(container, tick):
    if tick is None:
        return
    color = "green" if tick['prediction'] == 'BUY' else "red"
    container.markdown(
        f"### Current Signal\n"
        f"<h1 style='color: {color}; text-align: center;'>{tick['prediction']}</h1>",
        unsafe_allow_html=True
    )


def display_stats(conf_container, stats_container, tick, all_data):
    if tick:
        conf_container.metric("Confidence", f"{tick['confidence'] * 100:.1f}%")

    if all_data:
        buy_count = sum(1 for d in all_data if d['prediction'] == 'BUY')
        total = len(all_data)
        pct = f"{buy_count/total*100:.1f}%" if total > 0 else "0%"
        stats_container.metric("Buy Signals", f"{buy_count}/{total}", pct)


def run_simulation(mint: str, speed: int, placeholders: dict):
    st.session_state.simulation_data = []
    st.session_state.is_running = True

    placeholders['status'].info("Starting simulation...")

    try:
        response = requests.get(
            f"{API_URL}/simulate",
            params={"mint": mint, "speed": speed},
            stream=True,
            timeout=300
        )

        for line in response.iter_lines():
            if not st.session_state.is_running:
                placeholders['status'].info("Stopped")
                break

            if not line:
                continue

            line_str = line.decode('utf-8')
            if not line_str.startswith('data: '):
                continue

            try:
                tick = json.loads(line_str[6:])
            except json.JSONDecodeError:
                continue

            if tick.get('done'):
                placeholders['status'].success("Done!")
                break

            if tick.get('error'):
                placeholders['status'].error(f"Error: {tick['error']}")
                break

            st.session_state.simulation_data.append(tick)
            st.session_state.current_prediction = tick

            display_prediction(placeholders['prediction'], tick)
            display_stats(
                placeholders['confidence'],
                placeholders['stats'],
                tick,
                st.session_state.simulation_data
            )

            # chart - posledních 200 bodů
            fig = create_chart(st.session_state.simulation_data[-200:])
            placeholders['chart'].plotly_chart(
                fig,
                use_container_width=True,
                key=f"chart_{len(st.session_state.simulation_data)}"
            )

            # tabulka
            recent = st.session_state.simulation_data[-10:][::-1]
            if recent:
                df = pd.DataFrame(recent)[['timestamp', 'symbol', 'marketCap', 'prediction', 'confidence']]
                placeholders['table'].dataframe(df, use_container_width=True)

    except requests.exceptions.RequestException as e:
        placeholders['status'].error(f"Connection error: {e}")
        st.session_state.is_running = False


def main():
    init_session_state()

    st.title("Crypto Buy Signal Prediction")

    # sidebar
    with st.sidebar:
        st.header("Settings")

        tokens = get_tokens()

        if tokens:
            token_options = {
                f"{t['symbol']} - {t['name'][:20]}... ({t['data_points']} pts)": t['mint']
                for t in tokens
            }
            selected_label = st.selectbox("Select Token", options=list(token_options.keys()))
            selected_mint = token_options[selected_label]
        else:
            st.warning("No tokens. Is the API running?")
            selected_mint = None

        speed = st.slider("Speed", min_value=1, max_value=50, value=10)

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            start_btn = st.button("Start", type="primary", disabled=selected_mint is None, use_container_width=True)
        with col2:
            stop_btn = st.button("Stop", disabled=not st.session_state.is_running, use_container_width=True)

        st.divider()
        st.markdown("""
        ### Návod
        1. Vyber token
        2. Nastav rychlost
        3. Klikni Start

        ### Legenda
        - Zelená = BUY
        - Červená = NO BUY
        """)

    # main area
    col1, col2, col3 = st.columns(3)

    placeholders = {
        'prediction': col1.empty(),
        'confidence': col2.empty(),
        'stats': col3.empty(),
        'chart': st.empty(),
        'table': st.empty(),
        'status': st.empty(),
    }

    if stop_btn:
        st.session_state.is_running = False

    if start_btn and selected_mint:
        run_simulation(selected_mint, speed, placeholders)

    elif st.session_state.simulation_data:
        # zobraz existující data
        display_prediction(placeholders['prediction'], st.session_state.current_prediction)
        display_stats(
            placeholders['confidence'],
            placeholders['stats'],
            st.session_state.current_prediction,
            st.session_state.simulation_data
        )

        fig = create_chart(st.session_state.simulation_data[-200:])
        placeholders['chart'].plotly_chart(fig, use_container_width=True)

        recent = st.session_state.simulation_data[-10:][::-1]
        if recent:
            df = pd.DataFrame(recent)[['timestamp', 'symbol', 'marketCap', 'prediction', 'confidence']]
            placeholders['table'].dataframe(df, use_container_width=True)

    else:
        st.info("Vyber token a klikni Start pro spuštění simulace.")


if __name__ == "__main__":
    main()
