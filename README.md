This Readme is just for the LTI-LLMentor-Integration Branch

* To work properly with LLMentor we need serveral changes:

# Docker-compose changes
1) The docker file will be changed so the /app/backend is hosted on the host directory... wich means also /app/backed/data is right there



# TSugi auth service added 

backend/web/main.py needs to add:

```
from apps.web.routers import   ltibridge

app.include_router(ltibridge.router, prefix="/ltibridge", tags=["ltibridge"])
```


