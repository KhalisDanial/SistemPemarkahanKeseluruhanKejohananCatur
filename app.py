import streamlit as st
import pandas as pd
import re
import io
import plotly.graph_objects as go
import base64
import textwrap
from pathlib import Path
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime

# Choose your secret password
PASSWORD = st.secrets["passwords"]["main"]

def check_password():
    def password_entered():
        if st.session_state["password"] == PASSWORD:
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Nama:", key="user_name")
        st.text_input("Sekolah/Institusi/Kelab:", key="user_school")
        st.text_input("Masukkan kata laluan:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Nama:", key="user_name")
        st.text_input("Sekolah/Institusi/Kelab:", key="user_school")
        st.text_input("Masukkan kata laluan:", type="password", on_change=password_entered, key="password")
        st.error("Kata laluan salah")
        return False
    else:
        # Successful login, show welcome page
        name = st.session_state.get("user_name", "Pengguna")
        school = st.session_state.get("user_school", "-")
        st.success(f"Selamat datang, **{name}** dari **{school}**!")
        return True

# -------------------
# Points logic
# -------------------
def assign_points(rank):
    return {
        1: 30, 2: 23, 3: 18, 4: 15, 5: 12,
        6: 11, 7: 10, 8: 9, 9: 8, 10: 7,
        11: 6, 12: 5, 13: 4, 14: 3, 15: 2, 16: 1
    }.get(rank, 0)

# -------------------
# Helper to find header row
# -------------------
def find_header_row(df, required_headers):
    for idx, row in df.iterrows():
        row_values = row.fillna('').astype(str).str.lower().str.strip()
        matches = [any(re.search(req.lower(), cell) for cell in row_values) for req in required_headers]
        if all(matches):
            return idx
    return None

# -------------------
# Set page config
# -------------------
st.set_page_config(page_title="Sistem Pemarkahan Keseluruhan Kejohanan Catur", layout="centered")

# -------------------
# Helper functions
# -------------------
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def load_and_process_excel(file, required_columns):
    raw_df = pd.read_excel(file, header=None)
    header_row_idx = find_header_row(raw_df, required_columns)
    if header_row_idx is None:
        raise ValueError("Could not find header row with required columns.")
    df = pd.read_excel(file, header=header_row_idx)
    df.columns = df.columns.str.strip()
    column_mapping, matched = {}, set()
    for col in df.columns:
        col_lower = col.lower()
        for req in required_columns:
            if req.lower() in col_lower and req not in matched:
                column_mapping[col] = req
                matched.add(req)
                break
    if set(column_mapping.values()) != set(required_columns):
        raise ValueError(f"Missing required columns after mapping. Found: {list(column_mapping.values())}")
    df = df.rename(columns=column_mapping)[required_columns]
    df["Points"] = df["Rank"].apply(assign_points)
    return df


if check_password():

    # Get user info
    name = st.session_state.get("user_name", "Pengguna")
    school = st.session_state.get("user_school", "-")

    # Log user info to Google Sheets
    try:
        gcp_secrets = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(
    gcp_secrets,
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
        ]
    )

        client = gspread.authorize(creds)
        SPREADSHEET_NAME = "Users Logs"  # <-- Change to your sheet name
        sheet = client.open(SPREADSHEET_NAME).sheet1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, name, school])
    except Exception as e:
        st.error(f"Gagal merekod data ke Google Sheets: {e}")

    # -------------------
    # Paths & encode images
    # -------------------


    BASE_DIR = Path(__file__).parent  # folder where app.py is located

    logo_path = BASE_DIR / "media" / "logo baharu mssperak.jpg"
    pattern_path = BASE_DIR / "media" / "photo-1625750331870-624de6fd3452.jpeg"

    encoded_logo = get_base64_image(logo_path)
    encoded_pattern = get_base64_image(pattern_path)

    # -------------------
    # Set bg colour
    # -------------------
    st.markdown(f"""
        <style>
            .stApp {{
                position: relative;
                background-color: #0D0D0D;
                background-image: url("data:image/png;base64,{encoded_pattern}");
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
                color: #FFFFFF;  /* force default text to white */
            }}
            .stApp::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);  /* adjust 0.5 to make darker/lighter */
                z-index: 0;
            }}
            /* Make sure content stays above the overlay */
            .stApp > * {{
                position: relative;
                z-index: 1;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #FF7F0E;  /* orange headings */
            }}
            p, span, div {{
                color: #FFFFFF;  /* force paragraphs, spans, and div text to white */
            }}
            .stButton>button {{
                background-color: #FF7F0E;
                color: black;
                border: none;
                border-radius: 8px;
                padding: 0.5em 1em;
            }}
            .stButton>button:hover {{
                background-color: #e66f00;
            }}
            .stDataFrame {{
                background-color: #1A1A1A;
                color: white;
                border-radius: 8px;
            }}
        </style>
    """, unsafe_allow_html=True)




    st.markdown(f"""
        <div style='text-align: center;'>
            <img src='data:image/png;base64,{encoded_logo}' 
                style='width: 150px; height: 150px; object-fit: cover; border-radius: 50%; border: 2px solid #ccc; margin-bottom: 10px;'>
            <h1 style='margin-bottom: 5px; text-shadow: 2px 2px 4px rgba(0,0,0,0.6);'>🏆 CATUR MSSPK 🏆</h1>
            <h2 style='margin-top: 0; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Chess Championship Overall Scoring <br> (Excel Import)</h2>
            <p style="font-size:20px; font-weight:normal;">Pemarkahan Keseluruhan Kejohanan Catur</p>
        </div>
    """, unsafe_allow_html=True)




    # -------------------
    # File upload & processing
    # -------------------
    uploaded_files = st.file_uploader(
        "Upload Excel Files (L12,P12,L15,P15,L18,P18) / Muat Naik fail Excel",
        type=["xlsx"],
        accept_multiple_files=True
    )

    required_columns = ["Rank", "Name", "Club"]
    all_results = []

    if uploaded_files:
        st.subheader("📊 Category-wise Standings / Berdasarkan Kategori")
        cols = st.columns(2)

        for i, uploaded_file in enumerate(uploaded_files):
            category_name = uploaded_file.name.replace(".xlsx", "")
            try:
                df = load_and_process_excel(uploaded_file, required_columns)
                df["Category"] = category_name
                all_results.append(df)

                with cols[i % 2]:
                    st.markdown(f"### 🏅 {category_name} Standings")
                    st.dataframe(df.sort_values(by="Points", ascending=False))

                st.info(f"✅ Processed '{uploaded_file.name}' successfully.")

            except Exception as e:
                st.error(f"❌ Error reading {uploaded_file.name}: {e}")

    def wrap_label(label, width=12):
        """
        Wrap label into multiple lines if too long.
        """
        return "<br>".join(textwrap.wrap(label, width=width))

    # -------------------
    # Combined scores & Podium chart
    # -------------------
    if all_results:
        st.subheader("🏘️ Combined Club Scores/Markah Gabungan Klub")

        final_df = pd.concat(all_results, ignore_index=True)
        club_summary = (
            final_df.groupby("Club")["Points"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        st.dataframe(club_summary)

        # -------------------
        # Podium chart (Top 5 only, fixed heights)
        # -------------------
        st.subheader("🏆 Podium")

        # Define fixed heights for the podium steps (4th, 2nd, 1st, 3rd, 5th)
        fixed_heights = [40, 70, 100, 55, 30]

        # Get top 5 clubs and arrange in podium order
        top_5 = club_summary.head(5).reset_index(drop=True)

        # Create list of total points in the same order as ordered_clubs
        ordered_points = [
            top_5.iloc[3]["Points"],  # 4th place
            top_5.iloc[1]["Points"],  # 2nd place
            top_5.iloc[0]["Points"],  # champion
            top_5.iloc[2]["Points"],  # 3rd place
            top_5.iloc[4]["Points"],  # 5th place
        ]

        ordered_clubs = [
            top_5.iloc[3]["Club"],  # 4th place
            top_5.iloc[1]["Club"],  # 2nd place
            top_5.iloc[0]["Club"],  # 1st place (champion)
            top_5.iloc[2]["Club"],  # 3rd place
            top_5.iloc[4]["Club"],  # 5th place
        ]

        # Numeric positions on x-axis for better control
        x_positions = [0, 1, 2, 3, 4]

        # Labels inside bars
        labels = [
            "Tempat<br>Ke-4",
            "Naib<br>Johan",
            "Johan",
            "Ketiga",
            "Tempat<br>Ke-5",
        ]

        # Colors for the bars: muted gray for 4th & 5th, silver, gold, bronze for podium
        colors = ["#708090", "#C0C0C0", "#FFAE00", "#CD7F32", "#708090"]

        # Create figure
        fig = go.Figure()

        # Add bars at numeric positions
        fig.add_trace(
            go.Bar(
                x=x_positions,
                y=fixed_heights,
                marker_color=colors,
                insidetextanchor='middle',
                width=0.95,
            )
        )


        # Add medal emojis as large annotations
        medals = ["", "🥈", "🥇", "🥉", ""]  # empty for 4th and 5th

        for idx, medal in enumerate(medals):
            if medal:  # skip empty ones
                fig.add_annotation(
                    x=x_positions[idx],
                    y=fixed_heights[idx] - 9,   # middle of the bar (or adjust higher/lower)
                    text=medal,
                    showarrow=False,
                    font=dict(size=40),  # bigger size
                    align='center'
                )

        for idx, club in enumerate(ordered_clubs):
            wrapped = wrap_label(club, width=10)  # adjust width to fit visually

            # Shadow
            fig.add_annotation(
                x=x_positions[idx]+0.02,
                y=fixed_heights[idx]+19.3,
                text=f"<b>{wrapped}</b>",
                showarrow=False,
                font=dict(size=20, color="rgba(0,0,0,0.6)"),
                align='center'
            )
            # Real text
            fig.add_annotation(
                x=x_positions[idx],
                y=fixed_heights[idx]+19.5,
                text=f"<b>{wrapped}</b>",
                showarrow=False,
                font=dict(size=20, color="white"),
                align='center'
            )




            # Total points (under club name)
            fig.add_annotation(
                x=x_positions[idx],
                y=fixed_heights[idx] + 4,  # just below club name
                text=f"{ordered_points[idx]} pts",
                showarrow=False,
                font=dict(size=20, color='whitesmoke'),
                align='center'
            )

            # Shadow (under label)
            fig.add_annotation(
                x=x_positions[idx],
                y=(fixed_heights[idx]/2)-1,  # just below club name
                text=f"{labels[idx]}",
                showarrow=False,
                font=dict(size=20, color='grey', family='Arial Black'),
                align='center'
            )
            # Shadow (under label)
            fig.add_annotation(
                x=x_positions[idx],
                y=fixed_heights[idx]/2,  # just below club name
                text=f"{labels[idx]}",
                showarrow=False,
                font=dict(size=20, color="white", family='Arial Black'),
                # align='center'
            )



        fig.update_layout(
            xaxis=dict(
                showticklabels=False,   # no labels
                showgrid=False,         # no grid lines
                zeroline=False,         # no zero line
                showline=False          # no axis line
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False,
                showline=False
            ),
            paper_bgcolor="#361A00",
            plot_bgcolor="#1A1A1A",
            margin=dict(t=50, b=20, l=20, r=20)
        )


        fig.add_annotation(
            text="🏆 Podium Keseluruhan 🏆",
            xref="paper", yref="paper",
            x=0.5, y=1.13,        # adjust y to place it above plot
            showarrow=False,
            font=dict(size=25, family='Montserrat', color='#FF7F0E'),
            xanchor='center'
        )

        st.plotly_chart(fig, use_container_width=True)
    st.write("Main app content here...")