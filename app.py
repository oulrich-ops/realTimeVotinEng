import os
import time
import streamlit as st
import psycopg2
from streamlit_autorefresh import st_autorefresh
from kafka import KafkaConsumer
import json
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np


def create_kafka_consumer(topic_name):
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8')))
    return consumer


def plot_colored_bar_chart(results):
    data_type = results['candidate_name']
    
    colors = ['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff']
    colors = colors[:len(data_type)]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(data_type, results['total_votes'], color=colors, edgecolor='white', linewidth=1.5)
    ax.set_xlabel('Candidat', fontsize=11, color='#374151')
    ax.set_ylabel('Votes', fontsize=11, color='#374151')
    ax.set_title('Votes par candidat', fontsize=13, fontweight='500', color='#1f2937', pad=15)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#e5e7eb')
    ax.spines['bottom'].set_color('#e5e7eb')
    ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.5)
    plt.tight_layout()
    return fig


def plot_donut_chart(data: pd.DataFrame, title='Distribution des votes', type='candidate'):
    if type == 'candidate':
        labels = list(data['candidate_name'])
    elif type == 'gender':
        labels = list(data['gender'])

    sizes = list(data['total_votes'])

    colors = ['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff']
    colors = colors[:len(labels)]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                        startangle=140, colors=colors,
                                        textprops={'fontsize': 10, 'color': '#374151'},
                                        wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    
    # Style du texte
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('500')
        autotext.set_fontsize(9)
    
    # Cercle central pour effet donut
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)
    
    ax.axis('equal')
    plt.title(title, fontsize=13, fontweight='500', color='#1f2937', pad=15)
    plt.tight_layout()
    return fig


@st.cache_data
def fetch_voting_stats():
    conn = psycopg2.connect("host=localhost dbname=voting user=postgres password=postgres")
    cur = conn.cursor()

    cur.execute("""
        SELECT count(*) voters_count FROM voters
    """)
    voters_count = cur.fetchone()[0]

    cur.execute("""
        SELECT count(*) candidates_count FROM candidates
    """)
    candidates_count = cur.fetchone()[0]

    return voters_count, candidates_count


def fetch_data_from_kafka(consumer):
    messages = consumer.poll(timeout_ms=1000)
    data = []
    for message in messages.values():
        for sub_message in message:
            data.append(sub_message.value)
    return data


@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.loc[i: i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df


def paginate_table(table_data):
    top_menu = st.columns(3)
    with top_menu[0]:
        sort = st.radio("Trier les données", options=["Oui", "Non"], horizontal=1, index=1)
    if sort == "Oui":
        with top_menu[1]:
            sort_field = st.selectbox("Trier par", options=table_data.columns)
        with top_menu[2]:
            sort_direction = st.radio(
                "Direction", options=["⬆️", "⬇️"], horizontal=True
            )
        table_data = table_data.sort_values(
            by=sort_field, ascending=sort_direction == "⬆️", ignore_index=True
        )
    pagination = st.container()

    bottom_menu = st.columns((4, 1, 1))
    with bottom_menu[2]:
        batch_size = st.selectbox("Taille de page", options=[10, 25, 50, 100])
    with bottom_menu[1]:
        total_pages = (
            int(len(table_data) / batch_size) if int(len(table_data) / batch_size) > 0 else 1
        )
        current_page = st.number_input(
            "Page", min_value=1, max_value=total_pages, step=1
        )
    with bottom_menu[0]:
        st.markdown(f"Page **{current_page}** sur **{total_pages}** ")

    pages = split_frame(table_data, batch_size)
    pagination.dataframe(data=pages[current_page - 1], use_container_width=True)


def display_top_3_podium(results_df):
    """Affiche un podium épuré pour le top 3 des candidats"""
    
    st.markdown("### Top 3 -- Le trio de tête")
    
    # Trier par votes et prendre les 3 premiers
    top_3 = results_df.nlargest(3, 'total_votes').reset_index(drop=True)
    
    if len(top_3) == 0:
        st.warning("Aucune donnée disponible")
        return
    
    # Médailles simples
    medals = ["1", "2", "3"]
    
    # Créer 3 colonnes pour le podium
    cols = st.columns(3)
    
    for idx, col in enumerate(cols):
        if idx < len(top_3):
            candidate = top_3.iloc[idx]
            
            with col:
                
                # Numéro de position discret
                st.markdown(f"""
                    <div style='
                        display: inline-block;
                        width: 32px;
                        height: 32px;
                        background: #3b82f6;
                        color: white;
                        border-radius: 50%;
                        line-height: 32px;
                        font-weight: 600;
                        font-size: 16px;
                        text-align: center;
                        margin-bottom: 15px;
                    '>{medals[idx]}</div>
                """, unsafe_allow_html=True)
                
                # Photo du candidat
                if 'photo_url' in candidate and pd.notna(candidate['photo_url']):
                    image_path = candidate["photo_url"]
                    image_path = image_path.lstrip("./")
                    st.image(
    image_path,
    width=250,
    caption=candidate.get("voter_name", ""),
)
                    
                else:
                    # Avatar simple
                    st.markdown(f"""
                        <div style='text-align: center; margin: 15px 0;'>
                            <div style='
                                width: 100px; 
                                height: 100px; 
                                border-radius: 50%; 
                                border: 3px solid #f3f4f6;
                                background: #e5e7eb;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                margin: 0 auto;
                            '>
                                <span style='font-size: 40px; color: #9ca3af;'>👤</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Informations
                st.markdown(
    f"<span style='font-size:24px; font-weight:bold;'>{candidate['candidate_name']}</span>", 
    unsafe_allow_html=True
)
                st.caption(candidate['party'])
                
                # Stats simples
                total = results_df['total_votes'].sum()
                percentage = (candidate['total_votes'] / total * 100) if total > 0 else 0
                
                st.markdown(f"""
                    <div style='margin-top: 12px;'>
                        <div style='font-size: 24px; font-weight: 600; color: #1f2937;'>
                            {int(candidate['total_votes']):,}
                        </div>
                        <div style='font-size: 14px; color: #6b7280;'>
                            {percentage:.1f}% des votes
                        </div>
                    </div>
                """, unsafe_allow_html=True)


def display_all_candidates_grid(results_df):
    """Affiche tous les candidats en grille de 3 par ligne - version épurée"""
    
    st.markdown("### Tous les candidats")
    
    # Trier par nombre de votes (décroissant)
    sorted_results = results_df.sort_values('total_votes', ascending=False).reset_index(drop=True)
    
    # Calculer le total des votes pour les pourcentages
    total_votes = sorted_results['total_votes'].sum()
    
    # Créer des lignes de 3 colonnes
    num_candidates = len(sorted_results)
    num_rows = (num_candidates + 2) // 3  # Arrondi supérieur
    
    for row in range(num_rows):
        cols = st.columns(4)
        
        for col_idx, col in enumerate(cols):
            candidate_idx = row * 4 + col_idx
            
            if candidate_idx < num_candidates:
                candidate = sorted_results.iloc[candidate_idx]
                percentage = (candidate['total_votes'] / total_votes * 100) if total_votes > 0 else 0
                
                with col:
                    # Container simple et propre
                    st.markdown(f"""
                        <div style='
                            background: white;
                            padding: 8px 15px;
                            border-radius: 5px;
                            text-align: center;
                            margin-bottom: 15px;
                            border: 1px solid #e5e7eb;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
                        '>
                    """, unsafe_allow_html=True)
                    
                    # Photo du candidat
                    if 'photo_url' in candidate and pd.notna(candidate['photo_url']):
                            st.image(
    candidate['photo_url'],
    width=150,
    caption=candidate.get("voter_name", ""),
)
                    else:
                        # Avatar simple
                        st.markdown(f"""
                            <div style='text-align: center; margin: 10px 0 15px 0;'>
                                <div style='
                                    width: 80px; 
                                    height: 80px; 
                                    border-radius: 50%; 
                                    border: 2px solid #f3f4f6;
                                    background: #e5e7eb;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    margin: 0 auto;
                                '>
                                    <span style='font-size: 32px; color: #9ca3af;'>👤</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Informations
                    st.markdown(f"<span style='font-size:24px; font-weight:bold;'>{candidate['candidate_name']}</span>", 
    unsafe_allow_html=True
)
                    st.caption(candidate['party'])
                    
                    if 'campaign_promises' in candidate and pd.notna(candidate['campaign_promises']):
                        promises = candidate['campaign_promises']
                        # Limiter à 100 caractères si trop long
                        if len(promises) > 100:
                            promises = promises[:97] + "..."
                        st.markdown(f"""
                            <div style='
                                background: #f9fafb; 
                                padding: 8px 10px; 
                                border-radius: 6px; 
                                margin: 10px 0;
                                border-left: 3px solid #3b82f6;
                            '>
                                <div style='font-size: 14px; color: #6b7280; font-style: italic;'>
                                    "{promises}"
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    # Stats épurées
                    st.markdown(f"""
                        <div style='margin-top: 10px; padding-top: 10px; border-top: 1px solid #f3f4f6;'>
                            <div style='font-size: 20px; font-weight: 600; color: #1f2937;'>
                                {int(candidate['total_votes']):,}
                            </div>
                            <div style='font-size: 13px; color: #6b7280; margin-top: 2px;'>
                                {percentage:.1f}% des votes
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)


def update_data():
    # Placeholder to display last refresh time
    last_refresh = st.empty()
    last_refresh.caption(f"Dernière mise à jour: {time.strftime('%H:%M:%S')}")

    # Fetch voting statistics
    voters_count, candidates_count = fetch_voting_stats()
    
    consumer = create_kafka_consumer("aggregated_votes_per_candidate")
    data = fetch_data_from_kafka(consumer)
    results = pd.DataFrame(data)

    results = results.loc[results.groupby('candidate_id')['total_votes'].idxmax()]
    results = results.sort_values('total_votes', ascending=False)
    
    total_votes = results['total_votes'].sum()
    participation_rate = (total_votes / voters_count * 100) if voters_count > 0 else 0


    # Display total voters and candidates metrics - version épurée
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style='background: white; padding: 20px; border-radius: 10px; 
                        border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.06);'>
                <div style='color: #6b7280; font-size: 13px; text-transform: uppercase; 
                            letter-spacing: 0.5px; margin-bottom: 8px;'>Électeurs inscrits</div>
                <div style='color: #1f2937; font-size: 32px; font-weight: 600;'>{:,}</div>
            </div>
        """.format(voters_count), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='background: white; padding: 20px; border-radius: 10px; 
                        border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.06);'>
                <div style='color: #6b7280; font-size: 13px; text-transform: uppercase; 
                            letter-spacing: 0.5px; margin-bottom: 8px;'>Candidats</div>
                <div style='color: #1f2937; font-size: 32px; font-weight: 600;'>{}</div>
            </div>
        """.format(candidates_count), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='background: white; padding: 20px; border-radius: 10px; 
                        border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.06);'>
                <div style='color: #6b7280; font-size: 13px; text-transform: uppercase; 
                            letter-spacing: 0.5px; margin-bottom: 8px;'>Taux de participation</div>
                <div style='color: #1f2937; font-size: 32px; font-weight: 600;'>{:.2f}%</div>
            </div>
        """.format(participation_rate), unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Fetch data from Kafka on aggregated votes per candidate
    consumer = create_kafka_consumer("aggregated_votes_per_candidate")
    data = fetch_data_from_kafka(consumer)
    results = pd.DataFrame(data)

    # Identify the leading candidate
    results = results.loc[results.groupby('candidate_id')['total_votes'].idxmax()]
    results = results.sort_values('total_votes', ascending=False)
    
    display_top_3_podium(results)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    display_all_candidates_grid(results)

    # Display statistics and visualizations
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### Statistiques")
    
    col1, col2 = st.columns(2)

    # Display bar chart and donut chart
    with col1:
        bar_fig = plot_colored_bar_chart(results)
        st.pyplot(bar_fig)

    with col2:
        donut_fig = plot_donut_chart(results, title='Distribution des Votes')
        st.pyplot(donut_fig)

    # Display table with candidate statistics
    st.markdown("### Résultats détaillés")
    display_results = results[['candidate_name', 'party', 'total_votes']].copy()
    display_results.columns = ['Candidat', 'Parti', 'Votes']
    display_results = display_results.reset_index(drop=True)
    display_results.index = display_results.index + 1
    st.dataframe(display_results, use_container_width=True)

    # Fetch data from Kafka on aggregated turnout by location
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Localisation des électeurs")
    
    location_consumer = create_kafka_consumer("aggregated_turnout_by_location")
    location_data = fetch_data_from_kafka(location_consumer)
    location_result = pd.DataFrame(location_data)

    if not location_result.empty:
        # Identify locations with maximum turnout
        location_result = location_result.loc[location_result.groupby('country')['count'].idxmax()]
        location_result = location_result.reset_index(drop=True)

        # Display location-based voter information with pagination
        paginate_table(location_result)

    # Update the last refresh time
    st.session_state['last_update'] = time.time()


def sidebar():
    if st.session_state.get('last_update') is None:
        st.session_state['last_update'] = time.time()

    st.sidebar.markdown("### Paramètres")
    
    refresh_interval = st.sidebar.slider("Rafraîchissement (secondes)", 5, 60, 10)
    st_autorefresh(interval=refresh_interval * 1000, key="auto")

    if st.sidebar.button('Rafraîchir', use_container_width=True):
        update_data()
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Kafka • Spark • Streamlit")


# Configuration de la page
st.set_page_config(
    page_title="Dashboard Électoral -- Election inclusive et démocratique au TechLand!",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling CSS minimaliste
st.markdown("""
    <style>
    .main {
        background-color: #f9fafb;
    }
    h1 {
        color: #1f2937;
        font-weight: 600;
    }
    h2, h3 {
        color: #374151;
        font-weight: 500;
    }
    /* Boutons plus petits et discrets */
    .stButton button {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 400;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: #2563eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Radio buttons plus discrets */
    .stRadio > div {
        gap: 0.5rem;
    }
    .stRadio label {
        font-size: 13px;
    }
    /* Selectbox plus sobre */
    .stSelectbox label {
        font-size: 13px;
        color: #6b7280;
    }
    /* Number input plus petit */
    .stNumberInput label {
        font-size: 13px;
        color: #6b7280;
    }
    /* Slider plus discret */
    .stSlider label {
        font-size: 13px;
        color: #6b7280;
    }
    </style>
""", unsafe_allow_html=True)

# Titre principal simple
st.markdown("""
    <div style='background: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; 
                border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.06);'>
        <h1 style='margin: 0; font-size: 2em; text-align: center;'>Dashboard Électoral</h1>
        <p style='text-align: center; color: #6b7280; margin: 8px 0 0 0; font-size: 1em;'>
            Résultats en temps réel
        </p>
    </div>
""", unsafe_allow_html=True)

topic_name = 'aggregated_votes_per_candidate'

sidebar()
update_data()
