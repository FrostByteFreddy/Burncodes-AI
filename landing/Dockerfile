# The public landing page: plain files, no build step, so search engines get the full text
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html robots.txt sitemap.xml styles.css /usr/share/nginx/html/
COPY fonts /usr/share/nginx/html/fonts
COPY img /usr/share/nginx/html/img

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
