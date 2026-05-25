from tortoise import fields, models


class GeneratedCode(models.Model):
    id = fields.IntField(pk=True)

    requirement = fields.ForeignKeyField("models.RequirementSession",related_name="generated_codes",on_delete=fields.CASCADE)

    code_json = fields.JSONField()
    is_completed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "generated_code"
        indexes = [
        ("requirement_id", "is_completed", "created_at"),
    ]