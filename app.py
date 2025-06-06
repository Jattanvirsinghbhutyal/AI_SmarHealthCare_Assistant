import os
from openai import OpenAI
from flask import Flask, render_template, request, jsonify
import math
import requests
from dotenv import load_dotenv


load_dotenv() 


app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY) 


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/about-us")
def about():
    return render_template("about_us.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    user_input = request.json["message"]
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an advanced healthcare assistant designed to provide accurate and helpful medical advice. You assist users by predicting diseases based on their symptoms, recommending relevant tests, sharing detailed disease information, precautions, and treatment options. Additionally, you guide users to nearby healthcare facilities, including hospitals, clinics, pharmacies, diagnostic centers, and more, based on their preferences and location. If someone inquires about nearby facilities, direct them to visit the /nearby_facilities directory of the site. Since this assistant is designed for emergency situations, avoid messages like 'I am not a doctor; consult your doctor,' as this disclaimer is already displayed on the homepage/chatbot. Do not answer queries that are irrelevant to the healthcare domain. If faced with such queries, politely apologize and explain your purpose as a healthcare assistant, specifying the types of questions you can assist with."},
                {"role": "user", "content": user_input}
            ]
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = "I'm sorry, something went wrong. Please try again."
        print(f"Error: {e}")
    return jsonify({"reply": reply})





categories = {
    "Hospitals": "hospital",
    "Pharmacies": "pharmacy",
    "Diagnostic Centers": "doctor",
    "Rehabilitation Centers": "physiotherapist",
}



@app.route('/nearby_facilities')
def index():
    return render_template('nearby_facilities.html')

# Distance calculation function
def calculate_distance(user_location, facility_location):
    lat1, lon1 = user_location
    lat2, lon2 = facility_location
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

# Fetchs places by category
def fetch_places(location, radius, category_type):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{location[0]},{location[1]}",
        "radius": radius,
        "type": category_type,
        "key": GOOGLE_MAPS_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []


@app.route('/get_all_locations', methods=['GET'])
def get_all_locations():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    sort_by = request.args.get('sort_by', 'recommended')
    user_location = (lat, lon)
    radius = 8000  # Search radius in meters
    all_results = []

    for category_name, category_type in categories.items():
        places = fetch_places(user_location, radius, category_type)
        results = []
        
        for place in places:
            distance = calculate_distance(
                user_location, 
                [place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]]
            )
            if "photos" in place:
                photo_reference = place["photos"][0]["photo_reference"]
                image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"
            else:
                image_url = None

            results.append({
                "name": place.get("name"),
                "vicinity": place.get("vicinity"),
                "rating": place.get("rating", 0),
                "user_ratings_total": place.get("user_ratings_total", 0),
                "distance": distance,
                "image_url": image_url,
                "map_link": f"https://www.google.com/maps/search/?api=1&query_place_id={place['place_id']}&query={place.get('name')}"





            })

        # Sorting based on sorting criteria
        if sort_by == "rating":
            results.sort(key=lambda x: x["rating"], reverse=True)
        elif sort_by == "popularity":
            results.sort(key=lambda x: x["user_ratings_total"], reverse=True)
        elif sort_by == "nearby":
            results.sort(key=lambda x: x["distance"])
        elif sort_by == "recommended":
            if results:  # Ensure results have required fields for scoring
                max_distance = max(r.get("distance", 1) for r in results) or 1  # Avoid division by zero

                for r in results:
                    # Extract or default values
                    rating = r.get("rating", 0)
                    reviews = r.get("user_ratings_total", 0)
                    distance_km = r.get("distance", 1)  # Default distance to 1 km if not provided
                    has_image = bool(r.get("photos", []))  # Check if photos exist

                    # Recommedation formulla based on weightage
                    rating_reviews_score = 0.4 * (rating * reviews)
                    image_penalty = 0.3 if not has_image else 0
                    distance_score = 0.3 * (1 / distance_km if distance_km > 0 else 0)

                    # total score
                    r["total_score"] = rating_reviews_score - image_penalty + distance_score

                # Sort results by total score in descending order
                results.sort(key=lambda x: x["total_score"], reverse=True)

        all_results.append({"category": category_name, "results": results[:8]})

    return jsonify(all_results)





if __name__ == "__main__":
    app.run(debug=True)
