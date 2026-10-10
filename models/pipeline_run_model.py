from tortoise import fields, models


class PipelineRun(models.Model):
    id = fields.IntField(pk=True)

    user = fields.ForeignKeyField(
        "models.Users",
        related_name="pipeline_runs",
        on_delete=fields.CASCADE,
    )

    user_input = fields.TextField()

    combined_input = fields.TextField(null=True)

    status = fields.CharField(
        max_length=50,
        default="running",
        index=True,
    )

    clarification_question = fields.TextField(null=True)

    pending_reply = fields.TextField(null=True)

    validation_session_id = fields.IntField(null=True)

    requirement_session_id = fields.IntField(null=True)

    code_id = fields.IntField(null=True)

    unit_test_id = fields.IntField(null=True)

    insight_id = fields.IntField(null=True)

    doc_id = fields.IntField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "pipeline_runs"

        indexes = [
            ("user_id", "status", "created_at"),
        ]


class PipelineStep(models.Model):
    id = fields.IntField(pk=True)

    run = fields.ForeignKeyField(
        "models.PipelineRun",
        related_name="steps",
        on_delete=fields.CASCADE,
    )

    stage = fields.CharField(max_length=50)

    status = fields.CharField(max_length=50, default="pending")

    attempt = fields.IntField(default=0)

    artifact_id = fields.IntField(null=True)

    error = fields.TextField(null=True)

    started_at = fields.DatetimeField(null=True)

    finished_at = fields.DatetimeField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "pipeline_steps"

        unique_together = (("run", "stage"),)

        indexes = [
            ("run_id", "stage"),
        ]