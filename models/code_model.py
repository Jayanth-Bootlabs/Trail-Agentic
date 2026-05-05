from tortoise import fields, models

class GeneratedCode(models.Model):
    id = fields.IntField(pk=True)

    user = fields.ForeignKeyField("models.Users",related_name="generated_codes",on_delete=fields.CASCADE)

    session = fields.ForeignKeyField("models.ValidationSession",related_name="generated_codes",on_delete=fields.CASCADE)

    code_json = fields.JSONField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "generated_code"