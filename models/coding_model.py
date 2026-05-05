from tortoise import fields, models


class CodingSession(models.Model):
    id = fields.IntField(pk=True)

    requirement_session = fields.ForeignKeyField(
        "models.RequirementSession",
        related_name="coding_sessions",
        on_delete=fields.CASCADE
    )

    requirements_input = fields.JSONField(null=True)
    status = fields.CharField(max_length=50, default="in_progress")
    ai_response = fields.JSONField(null=True)
    is_completed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)