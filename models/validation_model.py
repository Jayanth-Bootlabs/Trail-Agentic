from tortoise import fields, models

class ValidationSession(models.Model):
    id = fields.IntField(pk=True)

    user_input = fields.TextField()
    combined_input = fields.TextField(null=True)
    status = fields.CharField(max_length=50, default="in_progress")
    ai_response = fields.JSONField(null=True)
    is_completed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)