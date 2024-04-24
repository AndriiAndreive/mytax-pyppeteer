from pydantic import Field, BaseModel

class Account(BaseModel):
    email: str = Field(..., description="recipient email")
    name: str = Field(..., description="mytax name")
    password: str = Field(..., description="mytax password")