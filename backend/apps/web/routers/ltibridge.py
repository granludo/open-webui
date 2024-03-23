from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi import Depends, FastAPI, HTTPException, status
from datetime import datetime, timedelta
from typing import List, Union

from fastapi import APIRouter, status
from pydantic import BaseModel
import time
import uuid
import re


from apps.web.models.auths import (
    SigninForm,
    SignupForm,
    UpdateProfileForm,
    UpdatePasswordForm,
    UserResponse,
    SigninResponse,
    Auths,
)
from apps.web.models.users import Users

from utils.utils import (
    get_password_hash,
    get_current_user,
    get_admin_user,
    create_token,
)
from utils.misc import parse_duration, validate_email_format
from constants import ERROR_MESSAGES

router = APIRouter()

@router.post("/signin", response_class=HTMLResponse)
async def signin(request: Request,
                 email: str = Form(...), 
                 password: str = Form(...)):
    form_data = SigninForm(email=email, password=password)  # Manually instantiate your Pydantic model

    print("Signin form data:", form_data)

    user = Auths.authenticate_user(form_data.email.lower(), form_data.password)
    if user:
        token = create_token(
            data={"id": user.id},
            expires_delta=parse_duration(request.app.state.JWT_EXPIRES_IN),
        )

        # Construct the HTML content with embedded JavaScript
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sign In Successful</title>
    <script>
        window.onload = function() {{
            // Store the token and other user data in localStorage
            localStorage.setItem('token', '{token}');
            localStorage.setItem('token_type', 'Bearer');
            localStorage.setItem('id', '{user.id}');
            localStorage.setItem('email', '{user.email}');
            localStorage.setItem('name', '{user.name}');
            localStorage.setItem('role', '{user.role}');
            localStorage.setItem('profile_image_url', '{user.profile_image_url}');

            // Optionally, redirect after setting localStorage
            window.location.href = '/auth'; // Adjust as necessary
        }};
    </script>
</head>
<body>
    <p>If you are not redirected, <a href="/auth">click here</a>.</p>
</body>
</html>
        """
        return HTMLResponse(content=html_content)
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")