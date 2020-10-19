FROM python:3.9.0-slim-buster

WORKDIR /scraper_api

RUN apt-get update && apt-get -y install cron

COPY job /etc/cron.d/job

COPY . .

RUN pip install --no-cache-dir -r requirements.txt \
	&& chmod +x /etc/cron.d/job \
	&& crontab /etc/cron.d/job \
	&& touch /var/log/cron.log



EXPOSE 5000

CMD python ./api/main.py \
	&& python scrape_n_fill.py \
	&& cron \
	&& tail -f /var/log/cron.log