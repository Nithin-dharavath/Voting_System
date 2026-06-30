from pydantic import BaseModel, field_validator


class VoteSubmit(BaseModel):
    candidate_application_id: int


class VerificationSubmit(BaseModel):
    verification_type: str

    @field_validator("verification_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("SELFIE", "SIGNATURE"):
            raise ValueError("verification_type must be SELFIE or SIGNATURE.")
        return v
