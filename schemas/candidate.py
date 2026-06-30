from pydantic import BaseModel, field_validator


class CandidateApplicationCreate(BaseModel):
    election_id: int
    manifesto: str

    @field_validator("manifesto")
    @classmethod
    def validate_manifesto(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Manifesto cannot be empty.")
        return v.strip()
