import requests

def fetch_quote(author=None):
    base_url = "https://api.quotable.kurokeita.dev/api/quotes/random"
    params = {}
    if author and isinstance(author, str): 
        params['author'] = author
        print(f"Fetching quote by {author}...")
    else:
        print("Fetching random quote...")
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if isinstance(data, dict) and 'quote' in data:
            quote_data = data['quote']
            return quote_data
        else:
            print(f"Unexpected API response format: {data}")
            return None

    except Exception as e:
        print(f"Error fetching quote from API: {e}")
        return None
