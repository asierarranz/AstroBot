
    # Chatbot de Astrología
    
    Este bot de Telegram, llamado "Miralunas", utiliza el poder de la astrología para generar cartas astrales personalizadas y predicciones para sus usuarios. Construido con la biblioteca `python-telegram-bot` e integrado con la biblioteca `kerykeion` para astrología, este bot interactúa con los usuarios en una conversación para recopilar sus detalles de nacimiento y ubicación, generando un informe astrológico detallado.
    
    ## Características
    
    - **Interacción Personal**: Interactúa con los usuarios de manera conversacional para recopilar información personal de forma segura.
    - **Predicciones Astrológicas**: Genera cartas astrales personalizadas utilizando los detalles de nacimiento del usuario.
    - **Conversaciones Dinámicas**: Utiliza el `ConversationHandler` de `python-telegram-bot` para manejar estados conversacionales complejos.
    - **Localización y Ajustes de Tiempo**: Convierte tiempos y maneja ubicaciones para producir datos astrológicos precisos.
    - **Enfoque en la Privacidad**: Asegura que los datos del usuario se manejen de manera segura y privada, utilizados solo para generar perspectivas astrológicas.
    
    ## Cómo Funciona
    
    1. **Iniciando la Conversación**: Los usuarios comienzan proporcionando su nombre.
    2. **Recopilación de Detalles de Nacimiento**: El bot recoge el año, mes, día y hora exacta de nacimiento del usuario.
    3. **Datos de Ubicación**: Los usuarios proporcionan su lugar de nacimiento para considerar las influencias astrológicas locales.
    4. **Generación de la Carta**: El bot utiliza `kerykeion` para generar una carta astral basada en los datos proporcionados.
    5. **Obtención de Predicciones**: Utiliza la API de OpenAI para generar lecturas astrológicas divertidas y personalizadas.
    6. **Manejo de Repeticiones**: Los usuarios pueden elegir generar otro informe o terminar la conversación.
    
    ## Configuración
    
    1. **Clonar el Repositorio**: 
       ```bash
       git clone https://github.com/tunombredeusuario/astrology-chatbot.git
       cd astrology-chatbot
       ```
    
    2. **Instalar Dependencias**:
       ```bash
       pip install python-telegram-bot kerykeion requests
       ```
    
    3. **Configuración**: Reemplaza los tokens y claves de API de los marcadores de posición en el script por tu Token de Bot de Telegram real y tu clave API de OpenAI.
    
    4. **Ejecutar el Bot**:
       ```bash
       python bot.py
       ```
    
    ## Comandos
    
    - `/start` - Comienza la conversación con el bot.
    - `/cancel` - Termina inmediatamente la conversación y sale de cualquier análisis astrológico actual.
    
    ## Dependencias
    
    - `python-telegram-bot` - Para gestionar las interacciones del bot.
    - `kerykeion` - Para generar cartas astrales.
    - `requests` - Para llamar a APIs externas para funcionalidades adicionales.
    
 
    
    ---
    
    ¡Disfruta explorando las estrellas y los destinos personales con tu propio Miralunas, el chatbot de astrología!
    ```
