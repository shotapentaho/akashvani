"""
Live Cricket Scores using SerpAPI
Real-time scores from Google Sports
Version: 1.0 | 2026-02-13
"""

import streamlit as st
from serpapi import GoogleSearch
import re

def get_live_cricket_scores(query="cricket"):
    """Get live cricket scores from SerpAPI"""
    try:
        api_key = st.secrets["serpapi"]["api_key"]
        
        params = {
            "engine": "google",
            "q": f"{query} live score cricket",
            "api_key": api_key,
            "num": 5
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "sports_results" in results:
            return _parse_sports_results(results["sports_results"])
        
        if "organic_results" in results:
            return _parse_organic_results(results["organic_results"][:3])
        
        return None
        
    except Exception as e:
        print(f"❌ SerpAPI error: {e}")
        return None


def _parse_sports_results(sports_results):
    """Parse structured sports results"""
    try:
        if not sports_results:
            return None
        
        match = sports_results.get("games", [{}])[0] if "games" in sports_results else sports_results
        teams = match.get("teams", [])
        
        if len(teams) < 2:
            return None
        
        return {
            "team1": teams[0].get("name", "Team 1"),
            "team1_score": teams[0].get("score", "N/A"),
            "team2": teams[1].get("name", "Team 2"),
            "team2_score": teams[1].get("score", "N/A"),
            "status": match.get("status", "Live"),
            "venue": match.get("venue", ""),
            "date": match.get("date", ""),
            "tournament": match.get("tournament", ""),
            "source": "Google Sports (via SerpAPI)",
            "url": ""
        }
        
    except Exception as e:
        print(f"Parse error: {e}")
        return None


def _parse_organic_results(organic_results):
    """Parse organic search results"""
    try:
        for result in organic_results:
            snippet = result.get("snippet", "")
            title = result.get("title", "")
            
            if any(word in snippet.lower() or word in title.lower() 
                   for word in ["score", "vs", "wicket", "runs"]):
                return {
                    "team1": "Check link",
                    "team1_score": "for details",
                    "team2": "",
                    "team2_score": "",
                    "status": "Match in progress",
                    "venue": "",
                    "date": "",
                    "tournament": "",
                    "snippet": snippet[:200],
                    "url": result.get("link", ""),
                    "source": "Google Search"
                }
        
        return None
        
    except Exception as e:
        print(f"Parse error: {e}")
        return None


def parse_score_for_speech(score_text):
    """Parse score to speech-friendly format"""
    pattern1 = r'(\d+)/(\d+)\s*\((\d+\.?\d*)\)'
    match = re.search(pattern1, str(score_text))
    if match:
        runs, wickets, overs = match.groups()
        return f"{runs} runs for {wickets} wickets in {overs} overs"
    
    pattern2 = r'(\d+)/(\d+)'
    match = re.search(pattern2, str(score_text))
    if match:
        runs, wickets = match.groups()
        return f"{runs} runs for {wickets} wickets"
    
    return str(score_text)


def display_cricket_score(match_data):
    """Display cricket score"""
    if not match_data:
        return
    
    st.markdown(f"### 🏏 {match_data['team1']} vs {match_data['team2']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        '>
            <h3 style='color: white; margin-bottom: 10px;'>{match_data['team1']}</h3>
            <h1 style='color: #2c3e50; font-size: 42px; margin: 0; background: white; padding: 10px; border-radius: 8px;'>{match_data['team1_score']}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
        '>
            <h3 style='color: white; margin-bottom: 10px;'>{match_data['team2']}</h3>
            <h1 style='color: #2c3e50; font-size: 42px; margin: 0; background: white; padding: 10px; border-radius: 8px;'>{match_data['team2_score']}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    st.info(f"""
    **Status:** {match_data['status']}  
    **Venue:** {match_data.get('venue', 'N/A')}  
    **Tournament:** {match_data.get('tournament', 'N/A')}  
    **Source:** {match_data['source']}
    """)


def create_cricket_score_speech(match_data):
    """Create speech-friendly text"""
    team1_score = parse_score_for_speech(match_data['team1_score'])
    team2_score = parse_score_for_speech(match_data['team2_score'])
    
    return f"""Cricket Score Update. 
{match_data['team1']} scored {team1_score}. 
{match_data['team2']} scored {team2_score}. 
Match status: {match_data['status']}."""
