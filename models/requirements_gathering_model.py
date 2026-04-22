from tortoise import fields, models

class RequirementSession(models.Model):
    id = fields.IntField(pk=True)
    prompt_session = fields.ForeignKeyField(
        "models.PromptSession",
        related_name="requirements",
        on_delete=fields.CASCADE
    )
    validated_output = fields.JSONField()
    requirement_spec = fields.TextField()
    status = fields.CharField(max_length=50, default="PENDING")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "requirement_sessions"