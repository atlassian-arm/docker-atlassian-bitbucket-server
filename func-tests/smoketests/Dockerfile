FROM python:3.9
RUN pip install pipenv
WORKDIR /smoketests
COPY Pipfile* /smoketests/
RUN pipenv install --deploy --ignore-pipfile
COPY . /smoketests
CMD pipenv run pytest