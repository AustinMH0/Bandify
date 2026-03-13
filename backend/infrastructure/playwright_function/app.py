import json
from search import BandcampSearch, BeatportSearch

def lambda_handler(event, context):
    
    artist = event.get("artist")
    track_name = event.get("track_name")

    if not artist or not track_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing artist or track_name"})
        }

    try:
        
        bandcamp_result = BandcampSearch().search_song(track_name, artist)
        beatport_result = BeatportSearch().search_song(track_name, artist)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "bandcamp": bandcamp_result,
                "beatport": beatport_result
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
