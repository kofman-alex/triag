FROM python:3.8

# Install dependencies
COPY requirements.txt ./
RUN set -ex; \
    pip install -r requirements.txt; 

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY ./*.py ./

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 rule_service:app