FROM python:3.11-alpine as base

RUN apk add --no-cache build-base libffi-dev libressl-dev


FROM base AS python-deps

# Install compilation dependencies and pipenv 
RUN pip install pipenv

# Install python dependencies in /.venv
COPY ./Pipfile .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy


FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Create and switch to a new user
RUN adduser -D appuser
WORKDIR /home/appuser
USER appuser

# Install application into container
COPY . .

# Run the application
ENTRYPOINT ["python", "src/main.py"]
