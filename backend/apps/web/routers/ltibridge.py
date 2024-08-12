from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi import Depends, FastAPI, HTTPException, status
from datetime import datetime, timedelta
from typing import List, Union, Optional 

from fastapi import APIRouter, status
from pydantic import BaseModel
import time
import uuid
import re
import os


# Class Basemodel changes SingupForm to add_api_key for SingupX 
class SignupFormX(BaseModel):
    name: str
    email: str
    password: str
    api_key: str
    profile_image_url: Optional[str] = "/user.png"

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
// AÑADIR MODELS !!! 
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
    


@router.post("/signupx", response_model=SigninResponse)
async def signup(request: Request, form_data: SignupFormX):
    # Retrieve LTI_SECRET from the environment
    lti_secret = os.getenv('LTI_SECRET')

    print(f"LTI_SECRET from env: {lti_secret}")  # Debug print
     
     # Check if the username starts with the LTI_SECRET
    if not form_data.name.startswith(lti_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid secret prefix in username"
        )
    
    # Remove the secret prefix from the username to get the actual username
    actual_username = form_data.name[len(lti_secret):]
  
    if not request.app.state.ENABLE_SIGNUP:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.ACCESS_PROHIBITED
        )

    if not validate_email_format(form_data.email.lower()):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.INVALID_EMAIL_FORMAT
        )

    if Users.get_user_by_email(form_data.email.lower()):
        raise HTTPException(450, detail="User already exists")

    try:
        role = (
            "admin"
            if Users.get_num_users() == 0
            else "user"
        )
        hashed = get_password_hash(form_data.password)
        user = Auths.insert_new_auth(
            form_data.email.lower(), hashed, actual_username, role
        )

        if user:
            token = create_token(
                data={"id": user.id},
                expires_delta=parse_duration(request.app.state.JWT_EXPIRES_IN),
            )
            Users.update_user_role_by_id(user.id, "user") 
            Users.update_user_api_key_by_id(user.id, form_data.api_key)
            # response.set_cookie(key='token', value=token, httponly=True)

            
            
            return {
                "token": token,
                "token_type": "Bearer",
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_image_url": user.profile_image_url,
            }
        else:
            raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)
    except Exception as err:
        print(f"Exception occurred: {err}")  # Debug print
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))



@router.post("/signup", response_model=SigninResponse)
async def signup(request: Request, form_data: SignupForm):
    if not request.app.state.ENABLE_SIGNUP:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.ACCESS_PROHIBITED
        )

    # Retrieve LTI_SECRET from the environment

    lti_secret = os.getenv('LTI_SECRET')

    # Check if the username starts with the LTI_SECRET
    if not form_data.name.startswith(lti_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid secret prefix in username"
        )
    
    # Remove the secret prefix from the username to get the actual username
    actual_username = form_data.name[len(lti_secret):]

    if not validate_email_format(form_data.email.lower()):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.INVALID_EMAIL_FORMAT
        )

    if Users.get_user_by_email(form_data.email.lower()):
        raise HTTPException(400, detail=ERROR_MESSAGES.EMAIL_TAKEN)

    try:
        role = (
            "admin"
            if Users.get_num_users() == 0
            else "user"
        )
        hashed = get_password_hash(form_data.password)
        user = Auths.insert_new_auth(
            form_data.email.lower(), hashed, actual_username, role
        )
        # // añadir api key de mockai 

        if user:
            token = create_token(
                data={"id": user.id},
                expires_delta=parse_duration(request.app.state.JWT_EXPIRES_IN),
            )
            # response.set_cookie(key='token', value=token, httponly=True)

            if request.app.state.WEBHOOK_URL:
                post_webhook(
                    request.app.state.WEBHOOK_URL,
                    WEBHOOK_MESSAGES.USER_SIGNUP(user.name),
                    {
                        "action": "signup",
                        "message": WEBHOOK_MESSAGES.USER_SIGNUP(user.name),
                        "user": user.model_dump_json(exclude_none=True),
                    },
                )

            return {
                "token": token,
                "token_type": "Bearer",
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_image_url": user.profile_image_url,
            }
        else:
            raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)
    except Exception as err:
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))
