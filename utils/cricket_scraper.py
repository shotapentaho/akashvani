"""
akashvani - Cricket Score Extractor from News
Extracts cricket scores from news articles (more reliable than scraping)
Enhanced patterns to catch various score formats from live tournaments
"""
from typing import Dict, List, Optional, Tuple
import re
import streamlit as st

def _normalize_team_name(team: str) -> str:
    """Normalize team names for matching."""
    team_mappings = {
        "ind": "india", "india": "india",
        "pak": "pakistan", "pakistan": "pakistan",
        "aus": "australia", "australia": "australia",
        "eng": "england", "england": "england",
        "sa": "south africa", "rsa": "south africa", "south africa": "south africa",
        "nz": "new zealand", "new zealand": "new zealand",
        "sl": "sri lanka", "sri lanka": "sri lanka",
        "ban": "bangladesh", "bangladesh": "bangladesh",
        "wi": "west indies", "west indies": "west indies",
        "afg": "afghanistan", "afghanistan": "afghanistan",
        "ire": "ireland", "ireland": "ireland",
        "zim": "zimbabwe", "zimbabwe": "zimbabwe",
        "usa": "united states", "united states": "united states", "us": "united states",
        "uae": "united arab emirates",
        # IPL teams
        "rcb": "royal challengers", "csk": "chennai super kings",
        "mi": "mumbai indians", "kkr": "kolkata knight riders",
        "dc": "delhi capitals", "rr": "rajasthan royals",
        "pbks": "punjab kings", "srh": "sunrisers hyderabad",
        "gt": "gujarat titans", "lsg": "lucknow super giants",
    }
    return team_mappings.get(team.lower().strip(), team.title())

def _extract_teams_from_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract team names from query."""
    q_lower = query.lower().strip()
    vs_pattern = r'(\w+(?:\s+\w+)?)\s+(?:vs|versus|v/s)\s+(\w+(?:\s+\w+)?)'
    match = re.search(vs_pattern, q_lower)
    if match:
        return (_normalize_team_name(match.group(1)), _normalize_team_name(match.group(2)))
    return (None, None)

def extract_score_from_article(article: Dict) -> Optional[Dict]:
    """
    Extract cricket score from news article title/description.
    Enhanced to catch multiple score formats:
    - "India 285/4, Australia 125"
    - "India beat USA by 50 runs"
    - "USA 125 all out, India 126/3"
    - "India won by 7 wickets"
    - "India 185/6 (20 ov) beat USA 123/9 (20 ov)"
    """
    title = article.get('title', '')
    desc = article.get('description', '')
    content = f"{title} {desc}"
    
    if not content.strip():
        return None
    
    # Try multiple extraction patterns
    
    # Pattern 1: "Team1 XXX/X (overs), Team2 YYY/Y" or "Team1 XXX, Team2 YYY"
    pattern1 = r'(\w+(?:\s+\w+)?)\s+(\d{1,3}(?:/\d{1,2})?(?:\s*\(\d+\.?\d*\s*ov\))?)[,\s]+(?:and\s+)?(\w+(?:\s+\w+)?)\s+(\d{1,3}(?:/\d{1,2})?(?:\s*\(\d+\.?\d*\s*ov\))?)'
    match1 = re.search(pattern1, content, re.IGNORECASE)
    
    if match1:
        team1 = _normalize_team_name(match1.group(1))
        score1 = match1.group(2).strip()
        team2 = _normalize_team_name(match1.group(3))
        score2 = match1.group(4).strip()
        
        # Filter out non-team words
        if team1 not in ['the', 'by', 'beat', 'defeat', 'won'] and \
           team2 not in ['the', 'by', 'beat', 'defeat', 'won']:
            return {
                'team1': team1,
                'team2': team2,
                'team1_score': score1,
                'team2_score': score2,
                'source': article.get('source', 'News'),
                'url': article.get('url', ''),
                'title': article.get('title', ''),
                'published': article.get('published_at', ''),
            }
    
    # Pattern 2: "Team1 beat Team2 by X runs/wickets" - extract from title context
    pattern2 = r'(\w+(?:\s+\w+)?)\s+(?:beat|defeat|won|outplayed)\s+(\w+(?:\s+\w+)?)\s+by\s+(\d+)\s+(runs?|wickets?)'
    match2 = re.search(pattern2, content, re.IGNORECASE)
    
    if match2:
        team1 = _normalize_team_name(match2.group(1))
        team2 = _normalize_team_name(match2.group(2))
        margin = match2.group(3)
        margin_type = match2.group(4)
        
        if team1 not in ['the', 'by', 'at'] and team2 not in ['the', 'by', 'at']:
            # Try to find actual scores in the content
            score_pattern = r'(\d{1,3}(?:/\d{1,2})?(?:\s*\(\d+\.?\d*\s*ov\))?)'
            scores = re.findall(score_pattern, content)
            
            score1 = scores[0] if len(scores) > 0 else f"Won by {margin} {margin_type}"
            score2 = scores[1] if len(scores) > 1 else "Lost"
            
            return {
                'team1': team1,
                'team2': team2,
                'team1_score': score1,
                'team2_score': score2,
                'source': article.get('source', 'News'),
                'url': article.get('url', ''),
                'title': article.get('title', ''),
                'published': article.get('published_at', ''),
            }
    
    # Pattern 3: "India vs USA: IND 185/6, USA 123/9" (with colon separator)
    pattern3 = r'(\w+(?:\s+\w+)?)\s+vs\s+(\w+(?:\s+\w+)?)[:\s]+(?:\w+\s+)?(\d{1,3}(?:/\d{1,2})?)[,\s]+(?:\w+\s+)?(\d{1,3}(?:/\d{1,2})?)'
    match3 = re.search(pattern3, content, re.IGNORECASE)
    
    if match3:
        team1 = _normalize_team_name(match3.group(1))
        team2 = _normalize_team_name(match3.group(2))
        score1 = match3.group(3).strip()
        score2 = match3.group(4).strip()
        
        return {
            'team1': team1,
            'team2': team2,
            'team1_score': score1,
            'team2_score': score2,
            'source': article.get('source', 'News'),
            'url': article.get('url', ''),
            'title': article.get('title', ''),
            'published': article.get('published_at', ''),
        }
    
    # Pattern 4: Just team names with "vs" and look for any numbers
    pattern4 = r'(\w+(?:\s+\w+)?)\s+vs\s+(\w+(?:\s+\w+)?)'
    match4 = re.search(pattern4, content, re.IGNORECASE)
    
    if match4:
        team1 = _normalize_team_name(match4.group(1))
        team2 = _normalize_team_name(match4.group(2))
        
        # Look for scores anywhere in title/description
        score_pattern = r'\b(\d{1,3}(?:/\d{1,2})?(?:\s*\(\d+\.?\d*\s*ov\))?)\b'
        scores = re.findall(score_pattern, content)
        
        if len(scores) >= 2:
            return {
                'team1': team1,
                'team2': team2,
                'team1_score': scores[0],
                'team2_score': scores[1],
                'source': article.get('source', 'News'),
                'url': article.get('url', ''),
                'title': article.get('title', ''),
                'published': article.get('published_at', ''),
            }
    
    return None

def find_match_by_teams(query: str) -> Optional[Dict]:
    """Returns None - scores will be extracted from news articles directly."""
    return None

def get_all_live_scores() -> List[Dict]:
    """Returns empty list - scores will be extracted from news articles directly."""
    return []

def format_score_display(match: Dict) -> str:
    """Format match score for display."""
    team1 = match.get('team1', 'Team 1')
    team2 = match.get('team2', 'Team 2')
    score1 = match.get('team1_score', 'N/A')
    score2 = match.get('team2_score', 'N/A')
    
    return f"**{team1}** {score1} vs **{team2}** {score2}"
