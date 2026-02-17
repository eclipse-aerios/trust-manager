FROM python:3.9-slim

# Set working directory
WORKDIR /manager

# Install dependencies
COPY requirements/manager.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ src/

# Create configs directory for mounting config later
RUN mkdir -p configs

# Expose default FastAPI port
EXPOSE 3000

# Run the app
#CMD [ "python", "src/start.py" ]
CMD ["sh", "-c", "sleep 15 && python src/start.py"]