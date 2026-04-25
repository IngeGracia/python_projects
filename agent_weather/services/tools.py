import os
import requests


class Tools:
    def __init__(self):
        pass

    def obtener_clima(self, ciudad):
        print(f"⚙️ 🧠  Obteniendo coordenadas de: {ciudad}")

        if ciudad.lower() == "obregón":
            return f"La temperatura en {ciudad} es muy muy caliente!"
        elif ciudad.lower() == "monterrey":
            return f"La temperatura en {ciudad} es demasiado hermosa para ser verdad."
        else:
            # return f"No se encontró información del clima para la ciudad {ciudad}."
            return f"La temperatura en {ciudad} es horripilante."

    def obtener_clima_api(self, latitude: str, longitude: str):
        print(
            f"⚙️ 🧠  Obteniendo clima en coordenadas ({latitude}, {longitude})")

        if not latitude or not longitude:
            return f"ERROR: No se proporcionaron las coordenadas de latitud y longitud."

        api_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&timezone=America%2FLos_Angeles&current=temperature_2m"

        try:
            response = requests.get(api_url, timeout=30)
            # Para que marque un error si el servicio devuelve un Http de error.
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(
                f"Error en obtener_clima con latitude: {latitude} y longitud: {longitude}: {e}")
            return f"ERROR: no fue posible obtener el clima para {latitude}, {longitude}"

    def obtener_lat_long(self, ciudad):
        print(f"⚙️ 🧠  Obteniendo coordenadas de: {ciudad}")
        if not ciudad:
            return f"ERROR: No se proporcionó una ciudad."

        api_url = f"https://geocoding-api.open-meteo.com/v1/search?name={ciudad.lower()}&count=1&language=es&format=json"

        try:
            response = requests.get(api_url, timeout=30)
            # Para que marque un error si el servicio devuelve un Http de error.
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error en obtener_lat_long con ciudad: {ciudad}: {e}")
            return f"ERROR: no fue posible obtener las coordenadas de la ciudad {ciudad}"

    def currency_conversion(self, from_currency: str, to_currency: str, amount: float):
        print(
            f"⚙️🧠  Obteniendo conversión de monedas: de {amount} {from_currency} a {to_currency}")
        if not from_currency or not to_currency or not amount:
            return f"ERROR: No se proporcionaron los parámetros de la conversión de monedas."

        api_url = f"https://v6.exchangerate-api.com/v6/8f9d1aa541a2422c8cc7013b/pair/{from_currency.upper()}/{to_currency.upper()}/{amount}"

        try:
            response = requests.get(api_url, timeout=30)
            # Para que marque un error si el servicio devuelve un Http de error.
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(
                f"Error en currency_conversion con from_currency: {from_currency}, to_currency: {to_currency}, amount: {amount}: {e}")
            return f"ERROR: no fue posible obtener la conversión de divisas para {from_currency}, {to_currency}, {amount}"
