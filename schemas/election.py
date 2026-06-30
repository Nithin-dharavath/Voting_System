from datetime import datetime

from pydantic import BaseModel, model_validator


class ElectionCreate(BaseModel):
    title: str
    description: str | None = None
    start_time: str
    end_time: str

    @model_validator(mode="after")
    def validate_times(self):
        if not self.title or not self.start_time or not self.end_time:
            raise ValueError("Title, start time, and end time are required.")
        try:
            s_time = datetime.strptime(self.start_time, "%Y-%m-%dT%H:%M")
            e_time = datetime.strptime(self.end_time, "%Y-%m-%dT%H:%M")
        except ValueError:
            raise ValueError("Invalid date/time format. Use YYYY-MM-DDTHH:MM.")
        if e_time <= s_time:
            raise ValueError("End time must be after start time.")
        return self


class ElectionUpdate(BaseModel):
    title: str
    description: str | None = None
    start_time: str
    end_time: str

    @model_validator(mode="after")
    def validate_times(self):
        if not self.title or not self.start_time or not self.end_time:
            raise ValueError("Title, start time, and end time are required.")
        try:
            s_time = datetime.strptime(self.start_time, "%Y-%m-%dT%H:%M")
            e_time = datetime.strptime(self.end_time, "%Y-%m-%dT%H:%M")
        except ValueError:
            raise ValueError("Invalid date/time format. Use YYYY-MM-DDTHH:MM.")
        if e_time <= s_time:
            raise ValueError("End time must be after start time.")
        return self
