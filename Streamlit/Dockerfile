# Pull the base docker image of python with tag 3.9.13
FROM python:3.8.10

RUN pip install --upgrade pip

# Change the working dir inside the container - cd /app
WORKDIR /Streamlit

COPY . /Streamlit
# COPY Login_Page.py pages/Forgot_Password.py pages/Register_Page.py /pages/Stock_Dashboard.py pages/Stock_Recommendation.py pages/Upgrade_Plan.py requirements.txt /Streamlit
# Copy main.py as source cod and req.txt as dependency

# Install the dependency
RUN pip install -r requirements.txt

### Container Env same as local at this point
EXPOSE 8050

CMD ["streamlit", "run", "Login_Page.py", "--server.port", "8050"]
