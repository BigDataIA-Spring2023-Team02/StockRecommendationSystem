# Pull the base docker image of python with tag 3.9.13
FROM python:3.8.10

RUN pip install --upgrade pip

# Change the working dir inside the container - cd /app
WORKDIR /Streamlit

COPY . /Streamlit

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the .env file to the container
COPY .env ./

# Expose the port for the container
EXPOSE 8050

CMD ["streamlit", "run", "Login_Page.py", "--server.port", "8050"]
