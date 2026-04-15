from tortoise import fields, models

class PromptSession(models.Model):
    id = fields.IntField(pk=True)
    
    user = fields.ForeignKeyField(
        "models.Users",
        related_name="prompt_sessions",
        on_delete=fields.CASCADE
    )

    user_input = fields.TextField()
    ai_response = fields.TextField()

    is_completed = fields.BooleanField(default=False)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "prompt_sessions"