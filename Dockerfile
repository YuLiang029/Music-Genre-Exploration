FROM python:3.7         
ADD . /todo
WORKDIR /todo
EXPOSE 5001
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "app.py"]
CMD ["app.py"]