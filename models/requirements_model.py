from tortoise import fields, models

class RequirementSession(models.Model):
    id = fields.IntField(pk=True)

    validation_session = fields.ForeignKeyField("models.ValidationSession",related_name="requirements")

    user_input = fields.TextField()
    status = fields.CharField(max_length=50, default="in_progress")
    ai_response = fields.JSONField(null=True)
    is_completed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "requirements"
        indexes = [
        ("validation_session_id", "is_completed", "created_at"),
    ]