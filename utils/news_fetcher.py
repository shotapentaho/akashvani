import requests
import json

class NewsFetcher:
    def __init__(self, source, fallback_source):
        self.source = source
        self.fallback_source = fallback_source

    def fetch_cricket_scores(self):
        try:
            response = requests.get(self.source)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            data = response.json()
            return self.parse_scores(data)
        except Exception:
            print('Error fetching from primary source, attempting fallback...')
            return self.fetch_from_fallback()

    def fetch_from_fallback(self):
        try:
            response = requests.get(self.fallback_source)
            response.raise_for_status()
            data = response.json()
            return self.parse_scores(data)
        except Exception as e:
            print('Fallback source failed:', e)
            return None

    def parse_scores(self, data):
        scores = []  # implement parsing logic based on the received JSON structure
        # Example of parsing logic, assuming a specific structure:
        for match in data.get('matches', []):
            scores.append({
                'team1': match['team1'],
                'team2': match['team2'],
                'score': match['score'],
                'status': match['status']
            })
        return scores

if __name__ == '__main__':
    primary_source = 'https://api.espncricinfo.com/v2/scores/'
    fallback_source = 'https://api.alternatecricket.com/scores/'  # Placeholder for actual fallback API
    fetcher = NewsFetcher(primary_source, fallback_source)
    scores = fetcher.fetch_cricket_scores()
    if scores:
        print('Cricket Scores:', scores)
    else:
        print('No scores available.');