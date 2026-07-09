# 1. Grab a lightweight Python base
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy your requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application code into the image (Cloud safety net!)
COPY . .

# 5. Open the port Streamlit uses
EXPOSE 8501

# 6. The command to start your app
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]