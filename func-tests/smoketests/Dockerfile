FROM python:3.9
RUN pip install pipenv==2020.11.15
WORKDIR /smoketests
COPY Pipfile* /smoketests/
RUN pipenv install --deploy --ignore-pipfile
COPY . /smoketests
CMD pipenv run pytest