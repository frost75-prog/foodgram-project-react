FROM nginx:1.22.1
COPY nginx.conf /etc/nginx/templates/default.conf.template
RUN ["mkdir", "/var/docs"]
ADD docs/ /var/docs/
COPY ingredients.csv /var/docs/