"""WTForms definitions with server-side validation (CSRF is added by Flask-WTF)."""
from __future__ import annotations

import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from .extensions import db
from .models import User

_COMMON_PASSWORDS = {
    "password", "password1", "password12", "password123", "12345678", "123456789", "1234567890", "qwertyui",
    "qwerty123", "iloveyou", "admin123", "welcome1", "welcome123", "letmein123", "abc12345", "11111111",
    "passw0rd", "p@ssw0rd", "changeme", "resumeiq", "resumeiq1", "monkey123", "dragon123", "football1",
}


def _strip(value):
    return value.strip() if isinstance(value, str) else value


def _email(value):
    return value.strip().lower() if isinstance(value, str) else value


def password_problem(password: str, email: str = "", name: str = "") -> str | None:
    """Return a human-readable reason a password is unacceptable, or None."""
    if len(password) < 8:
        return "Use at least 8 characters."
    if len(password) > 128:
        return "Use at most 128 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Include at least one letter and one number."
    if password.lower() in _COMMON_PASSWORDS:
        return "That password is too common. Choose something harder to guess."
    local = (email or "").split("@")[0].lower()
    if len(local) >= 4 and local in password.lower():
        return "Your password should not contain your e-mail name."
    return None


class RegisterForm(FlaskForm):
    name = StringField("Full name", filters=[_strip],
                       validators=[DataRequired("Enter your name."), Length(min=2, max=80, message="Use 2–80 characters.")])
    email = StringField("Work email", filters=[_email],
                        validators=[DataRequired("Enter your email address."), Length(max=254),
                                    Email("Enter a valid email address.", check_deliverability=False)])
    password = PasswordField("Password", validators=[DataRequired("Choose a password.")])
    confirm = PasswordField("Confirm password",
                            validators=[DataRequired("Confirm your password."),
                                        EqualTo("password", message="Passwords do not match.")])

    def validate_email(self, field):
        if db.session.execute(db.select(User.id).filter_by(email=field.data)).first():
            raise ValidationError("An account with this email already exists. Try logging in.")

    def validate_password(self, field):
        problem = password_problem(field.data or "", self.email.data or "", self.name.data or "")
        if problem:
            raise ValidationError(problem)


class LoginForm(FlaskForm):
    email = StringField("Email", filters=[_email], validators=[DataRequired("Enter your email address.")])
    password = PasswordField("Password", validators=[DataRequired("Enter your password.")])
    remember = BooleanField("Keep me signed in")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired("Enter your current password.")])
    new_password = PasswordField("New password", validators=[DataRequired("Choose a new password.")])
    confirm = PasswordField("Confirm new password",
                            validators=[DataRequired("Confirm the new password."),
                                        EqualTo("new_password", message="Passwords do not match.")])

    def __init__(self, user: User, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_current_password(self, field):
        if not self.user.check_password(field.data or ""):
            raise ValidationError("Your current password is incorrect.")

    def validate_new_password(self, field):
        problem = password_problem(field.data or "", self.user.email, self.user.name)
        if problem:
            raise ValidationError(problem)
        if self.user.check_password(field.data or ""):
            raise ValidationError("Choose a password different from your current one.")


class DeleteAccountForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired("Enter your password to confirm.")])

    def __init__(self, user: User, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_password(self, field):
        if not self.user.check_password(field.data or ""):
            raise ValidationError("Incorrect password.")
