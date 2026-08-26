from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Response representation for a token."""

    access_token: str
    token_type: str = "bearer"
