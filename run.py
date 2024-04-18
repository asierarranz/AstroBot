import requests
from kerykeion import Report, AstrologicalSubject

# Function to create an astrological chart
def create_astro_chart(name, year, month, day, hour, minute, location):
    subject = AstrologicalSubject(name, year, month, day, hour, minute, location)
    report = Report(subject)
    return report.get_full_report()

# Function to call the OpenAI API with the astrological chart
def get_astrological_prediction(name, location, chart):
    api_key = 'sk-proj-qB50VcbkJBZdzm5dXV9PT3BlbkFJBAK619TeTVNu76CPHaM8'
    endpoint = 'https://api.openai.com/v1/chat/completions'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    prompt = f"""
    Eres una bruja que sabe leer a las personas muy bien, hazme el análisis de este perfil, te dejo su carta astral:

    {chart}

    La persona se llama {name}, dirígete en segunda persona, por su nombre deberías saber su sexo para dirigirte a él o ella, como si le hablaras directamente, intenta, en base a tu análisis, adivinar sus aficiones y lo que más valora en la vida y en el día a día. Es de {location}.
    """

    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'system', 'content': 'You are a highly skilled witch who excels at reading people based on their astrological chart. Provide a cold reading.'},
                     {'role': 'user', 'content': prompt}]
    }

    response = requests.post(endpoint, headers=headers, json=data)
    prediction_response = response.json()
    content = prediction_response['choices'][0]['message']['content']
    return content

# Create the astrological chart
name = "Asier"
location = "Bilbao"
chart = create_astro_chart(name, 1984, 6, 16, 22, 30, location)

# Print the astrological chart
print(chart)

# Get the astrological prediction
prediction_content = get_astrological_prediction(name, location, chart)
print(prediction_content)