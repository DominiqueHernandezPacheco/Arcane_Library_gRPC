🌾 Arcane Library - Sistema Distribuido gRPC

Este proyecto es una tienda de libros distribuida que utiliza gRPC para la comunicación entre el cliente y el servidor, y Streamlit para una interfaz de usuario moderna con estética Cottagecore.

🚀 Arquitectura del Sistema

Backend (Servidor): Corre localmente utilizando Python y gRPC. Utiliza ngrok para exponer el puerto 50051 a internet.

Frontend (Cliente): Desplegado en Streamlit Cloud. Se conecta al backend mediante el túnel TCP de ngrok.

Sincronización: El sistema implementa un control de versiones de inventario. Si un producto se agota, todos los clientes conectados ven la carátula en gris y el estado "AGOTADO" en tiempo real.

🛠️ Requisitos

Python 3.9+

gRPC y Protocol Buffers

Streamlit

📦 Instalación y Uso local

Instalar dependencias: pip install -r requirements.txt

Iniciar el servidor: python servidor.py

Iniciar la interfaz: streamlit run cliente_ui.py

🌐 Despliegue

La interfaz está disponible públicamente gracias a Streamlit Cloud. El servidor debe estar activo en la máquina host para procesar las peticiones.
