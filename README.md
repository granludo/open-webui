This Readme is just for the LTI-LLMentor-Integration Branch

* To work properly with LLMentor we need serveral changes:

# Docker-compose changes
1) The docker file will be changed so the /app/backend is hosted on the host directory... wich means also /app/backed/data is right there


somethink like 
```
version: '3.8'

services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    environment:
      OPENAI_API_BASE_URL: "http://mockai:5002/v1"
      OPENAI_API_KEY: "xxxx"
    ports:
      - "8080:8080" # Assuming the Web UI runs on port 80, adjust if needed
    volumes:
      - ./backend:/app/backend
    restart: always
```


# TSugi auth service added 

backend/web/main.py needs to add:

```
from apps.web.routers import   ltibridge

app.include_router(ltibridge.router, prefix="/ltibridge", tags=["ltibridge"])
```

On backend/web/routers add the file ltibridge.py

And enerything will be happiness and joy


