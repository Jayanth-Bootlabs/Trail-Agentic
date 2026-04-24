from tortoise import fields, models

class RequirementSession(models.Model):
    id = fields.IntField(pk=True)
    prompt_session = fields.ForeignKeyField(
        "models.PromptSession",
        related_name="requirements",
        on_delete=fields.CASCADE
    )
    requirement_spec = fields.JSONField()
    is_completed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "requirement_sessions"