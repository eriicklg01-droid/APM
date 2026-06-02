import requests
import pandas as pd
import base64

# Configuración del entorno de producción según el Swagger de APM
BASE_URL = "https://restapi-masair.apm.ch/prod-restapi"
CLIENT_ID = "M7API"
CLIENT_SECRET = "12345"

def obtener_token_oauth() -> str:
    """
    Solicita un token de acceso dinámico.
    Utiliza autenticación Basic (client_id:client_secret en Base64) y 
    pasa el grant_type en la URL para cumplir las reglas del servidor.
    """
    url_token = f"{BASE_URL}/oauth/token"
    
    # Codificación de credenciales maestras
    credenciales = f"{CLIENT_ID}:{CLIENT_SECRET}"
    credenciales_encoded = base64.b64encode(credenciales.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {credenciales_encoded}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    params = {"grant_type": "client_credentials"}
    
    try:
        response = requests.post(url_token, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Error de autenticación ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"Excepción en el flujo de autenticación: {e}")
        return None

def obtener_equipos_aeropuerto() -> pd.DataFrame:
    """
    Consulta los equipos de aeropuerto directamente en el endpoint verificado.
    Desempaqueta el JSON para retornar un DataFrame con los 11 registros reales.
    """
    token = obtener_token_oauth()
    if not token:
        df_error = pd.DataFrame(columns=["Error"], data=[["Fallo crítico al generar el Token OAuth2"]])
        return df_error
        
    endpoint = "/api/dictionaries/airport-equipments/values"
    url = f"{BASE_URL}{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            datos_json = response.json()
            
            # Caso 1: La API devuelve una lista directa de objetos JSON
            if isinstance(datos_json, list):
                return pd.DataFrame(datos_json)
                
            # Caso 2: Estructura jerárquica HAL JSON (Busca la lista dentro de '_embedded')
            elif isinstance(datos_json, dict) and "_embedded" in datos_json:
                llaves_internas = list(datos_json["_embedded"].keys())
                if llaves_internas:
                    prime_llave = llaves_internas[0] # Usualmente 'airportEquipmentDtoList' o similar
                    lista_equipos = datos_json["_embedded"][prime_llave]
                    return pd.DataFrame(lista_equipos)
            
            # Caso 3: Si viene un diccionario básico
            elif isinstance(datos_json, dict):
                return pd.DataFrame([datos_json])
                
            return pd.DataFrame()
        else:
            df_err = pd.DataFrame(columns=["Error"], data=[[f"Error del servidor APM: Status {response.status_code}"]])
            return df_err
            
    except Exception as e:
        df_exc = pd.DataFrame(columns=["Error"], data=[[f"Excepción de conexión: {e}"]])
        return df_exc