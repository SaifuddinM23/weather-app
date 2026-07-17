from django.shortcuts import render
from django.conf import settings
import json
import urllib.request
import urllib.parse
import urllib.error

def index(request):
    city = None
    error_message = None
    weather_data = {}
    
    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        if not city:
            error_message = "Please enter a city name."
    elif request.method == 'GET' and 'city' in request.GET:
        city = request.GET.get('city', '').strip()
        if not city:
            error_message = "Please enter a city name."

    # Retrieve search history from session
    search_history = request.session.get('search_history', [])

    if city and not error_message:
        try:
            # URL encode the city name to handle spaces/special characters
            encoded_city = urllib.parse.quote(city)
            
            # Fetch OpenWeather API key from settings
            api_key = getattr(settings, 'OPENWEATHER_API_KEY', '').strip()
            if not api_key:
                raise ValueError("API Key is missing. Please configure OPENWEATHER_API_KEY in your environment.")
            
            url = f'http://api.openweathermap.org/data/2.5/weather?q={encoded_city}&appid={api_key}'
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                source = response.read()
            
            list_of_data = json.loads(source)
            
            # Parse temperatures and perform calculations
            temp_k = float(list_of_data['main']['temp'])
            temp_c = round(temp_k - 273.15, 1)
            temp_f = round((temp_k - 273.15) * 9/5 + 32, 1)
            
            feels_like_k = float(list_of_data['main'].get('feels_like', temp_k))
            feels_like_c = round(feels_like_k - 273.15, 1)
            feels_like_f = round((feels_like_k - 273.15) * 9/5 + 32, 1)
            
            weather_data = {
                "cityname": list_of_data['name'],
                "country_code": str(list_of_data['sys']['country']),
                "coordinate": f"{list_of_data['coord']['lon']}, {list_of_data['coord']['lat']}",
                "temp_k": f"{temp_k:.1f} K",
                "temp_c": f"{temp_c:.1f}",
                "temp_f": f"{temp_f:.1f}",
                "feels_like_c": f"{feels_like_c:.1f}",
                "feels_like_f": f"{feels_like_f:.1f}",
                "pressure": str(list_of_data['main']['pressure']),
                "humidity": str(list_of_data['main']['humidity']),
                "wind_speed": f"{list_of_data['wind']['speed']} m/s",
                "clouds": f"{list_of_data['clouds']['all']}%",
                "description": list_of_data['weather'][0]['description'].capitalize(),
                "icon": list_of_data['weather'][0]['icon'],
            }
            
            # Update search history in session
            clean_city_name = list_of_data['name']
            if clean_city_name in search_history:
                search_history.remove(clean_city_name)
            search_history.insert(0, clean_city_name)
            search_history = search_history[:5]
            request.session['search_history'] = search_history
            request.session.modified = True
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                error_message = f"City '{city}' not found. Please verify the name and try again."
            elif e.code == 401:
                error_message = "Weather service unauthorized. The API key might be invalid or expired."
            else:
                error_message = f"Weather service error (HTTP {e.code}): {e.reason}."
        except Exception as e:
            error_message = f"Failed to retrieve weather details: {str(e)}"

    context = {
        "weather": weather_data,
        "error_message": error_message,
        "search_history": search_history,
        "searched_city": city
    }
    return render(request, "main/index.html", context)
