"""initial migration

Revision ID: a8d8e5f1b1c2
Revises: 
Create Date: 2026-06-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision = 'a8d8e5f1b1c2'
down_revision = None
branch_labels = None
depends_on = None

# Custom vector type definition to bypass local import blocks if pgvector python package isn't preinstalled
class VectorType(sa.types.UserDefinedType):
    def __init__(self, dim):
        self.dim = dim
    def get_col_spec(self, **kw):
        return f"vector({self.dim})"

def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create Permission Table
    op.create_table(
        'permission',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permission_name'), 'permission', ['name'], unique=True)

    # 3. Create Role Table
    op.create_table(
        'role',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_name'), 'role', ['name'], unique=True)

    # 4. Create Role-Permission Association Table
    op.create_table(
        'role_permission_association',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # 5. Create User Table
    op.create_table(
        'user',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)

    # 6. Create User-Role Association Table
    op.create_table(
        'user_role_association',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # 7. Create User Session Table
    op.create_table(
        'user_session',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('refresh_token', sa.String(length=512), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_session_refresh_token'), 'user_session', ['refresh_token'], unique=True)
    op.create_index(op.f('ix_user_session_user_id'), 'user_session', ['user_id'], unique=False)

    # 8. Create Student Table
    op.create_table(
        'student',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('matriculation_number', sa.String(length=50), nullable=True),
        sa.Column('profile_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_student_matriculation_number'), 'student', ['matriculation_number'], unique=True)

    # 9. Create Tutor Table
    op.create_table(
        'tutor',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bio', sa.String(length=1000), nullable=True),
        sa.Column('department', sa.String(length=150), nullable=True),
        sa.Column('max_workload', sa.Integer(), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_tutor_is_available'), 'tutor', ['is_available'], unique=False)

    # 10. Create Admin Table
    op.create_table(
        'admin',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('department', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )

    # 11. Create Course Table
    op.create_table(
        'course',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_course_code'), 'course', ['code'], unique=True)

    # 12. Create Enrollment Table
    op.create_table(
        'enrollment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'course_id', name='uq_student_course_enrollment')
    )
    op.create_index(op.f('ix_enrollment_course_id'), 'enrollment', ['course_id'], unique=False)
    op.create_index(op.f('ix_enrollment_student_id'), 'enrollment', ['student_id'], unique=False)

    # 13. Create Question Cluster Table
    op.create_table(
        'question_cluster',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_tutor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('summary', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_tutor_id'], ['tutor.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_cluster_assigned_tutor_id'), 'question_cluster', ['assigned_tutor_id'], unique=False)
    op.create_index(op.f('ix_question_cluster_course_id'), 'question_cluster', ['course_id'], unique=False)
    op.create_index(op.f('ix_question_cluster_priority_score'), 'question_cluster', ['priority_score'], unique=False)
    op.create_index(op.f('ix_question_cluster_status'), 'question_cluster', ['status'], unique=False)

    # 14. Create Question Table
    op.create_table(
        'question',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.String(length=10000), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('urgency_score', sa.Float(), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('upvotes_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['question_cluster.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_cluster_id'), 'question', ['cluster_id'], unique=False)
    op.create_index(op.f('ix_question_course_id'), 'question', ['course_id'], unique=False)
    op.create_index(op.f('ix_question_priority_score'), 'question', ['priority_score'], unique=False)
    op.create_index(op.f('ix_question_status'), 'question', ['status'], unique=False)
    op.create_index(op.f('ix_question_student_id'), 'question', ['student_id'], unique=False)

    # 15. Create Question Embedding Table (with 384-dimensional pgvector column)
    op.create_table(
        'question_embedding',
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding', VectorType(384), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['question.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('question_id')
    )

    # 16. Create Tutor Assignment logs table
    op.create_table(
        'tutor_assignment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tutor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cluster_id'], ['question_cluster.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutor.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tutor_assignment_cluster_id'), 'tutor_assignment', ['cluster_id'], unique=False)
    op.create_index(op.f('ix_tutor_assignment_tutor_id'), 'tutor_assignment', ['tutor_id'], unique=False)

    # 17. Create Chat Message Table
    op.create_table(
        'chat_message',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.String(length=5000), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cluster_id'], ['question_cluster.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_message_cluster_id'), 'chat_message', ['cluster_id'], unique=False)
    op.create_index(op.f('ix_chat_message_sender_id'), 'chat_message', ['sender_id'], unique=False)

    # 18. Create File Upload Table
    op.create_table(
        'file_upload',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('uploader_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['chat_message.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['question.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploader_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_upload_message_id'), 'file_upload', ['message_id'], unique=False)
    op.create_index(op.f('ix_file_upload_question_id'), 'file_upload', ['question_id'], unique=False)
    op.create_index(op.f('ix_file_upload_uploader_id'), 'file_upload', ['uploader_id'], unique=False)

    # 19. Create Notification Table
    op.create_table(
        'notification',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.String(length=1000), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recipient_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_is_read'), 'notification', ['is_read'], unique=False)
    op.create_index(op.f('ix_notification_recipient_id'), 'notification', ['recipient_id'], unique=False)

    # 20. Create Activity Log Table
    op.create_table(
        'activity_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_log_action'), 'activity_log', ['action'], unique=False)
    op.create_index(op.f('ix_activity_log_created_at'), 'activity_log', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_log_user_id'), 'activity_log', ['user_id'], unique=False)

    # 21. Create Analytics Snapshot Table
    op.create_table(
        'analytics_snapshot',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('snapshot_time', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytics_snapshot_course_id'), 'analytics_snapshot', ['course_id'], unique=False)
    op.create_index(op.f('ix_analytics_snapshot_metric_name'), 'analytics_snapshot', ['metric_name'], unique=False)
    op.create_index(op.f('ix_analytics_snapshot_snapshot_time'), 'analytics_snapshot', ['snapshot_time'], unique=False)

    # 22. Create Report Table
    op.create_table(
        'report',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['generated_by'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 23. Add special index for vector similarity search (HNSW index setup using cosine distance)
    # This requires pgvector to be installed in postgres.
    # If using local SQL DB without pgvector HNSW compile support, fallback executes gracefully.
    try:
        op.execute("CREATE INDEX idx_question_embedding_hnsw ON question_embedding USING hnsw (embedding vector_cosine_ops);")
    except Exception:
        # Gracefully handle environment where HNSW compiled support is not enabled yet
        pass


def downgrade() -> None:
    # Drop in reverse order of creation to prevent foreign key constraint issues
    op.drop_table('report')
    op.drop_index(op.f('ix_analytics_snapshot_snapshot_time'), table_name='analytics_snapshot')
    op.drop_index(op.f('ix_analytics_snapshot_metric_name'), table_name='analytics_snapshot')
    op.drop_index(op.f('ix_analytics_snapshot_course_id'), table_name='analytics_snapshot')
    op.drop_table('analytics_snapshot')
    op.drop_index(op.f('ix_activity_log_user_id'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_created_at'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_action'), table_name='activity_log')
    op.drop_table('activity_log')
    op.drop_index(op.f('ix_notification_recipient_id'), table_name='notification')
    op.drop_index(op.f('ix_notification_is_read'), table_name='notification')
    op.drop_table('notification')
    op.drop_index(op.f('ix_file_upload_uploader_id'), table_name='file_upload')
    op.drop_index(op.f('ix_file_upload_question_id'), table_name='file_upload')
    op.drop_index(op.f('ix_file_upload_message_id'), table_name='file_upload')
    op.drop_table('file_upload')
    op.drop_index(op.f('ix_chat_message_sender_id'), table_name='chat_message')
    op.drop_index(op.f('ix_chat_message_cluster_id'), table_name='chat_message')
    op.drop_table('chat_message')
    op.drop_index(op.f('ix_tutor_assignment_tutor_id'), table_name='tutor_assignment')
    op.drop_index(op.f('ix_tutor_assignment_cluster_id'), table_name='tutor_assignment')
    op.drop_table('tutor_assignment')
    op.drop_table('question_embedding')
    op.drop_index(op.f('ix_question_student_id'), table_name='question')
    op.drop_index(op.f('ix_question_status'), table_name='question')
    op.drop_index(op.f('ix_question_priority_score'), table_name='question')
    op.drop_index(op.f('ix_question_course_id'), table_name='question')
    op.drop_index(op.f('ix_question_cluster_id'), table_name='question')
    op.drop_table('question')
    op.drop_index(op.f('ix_question_cluster_status'), table_name='question_cluster')
    op.drop_index(op.f('ix_question_cluster_priority_score'), table_name='question_cluster')
    op.drop_index(op.f('ix_question_cluster_course_id'), table_name='question_cluster')
    op.drop_index(op.f('ix_question_cluster_assigned_tutor_id'), table_name='question_cluster')
    op.drop_table('question_cluster')
    op.drop_index(op.f('ix_enrollment_student_id'), table_name='enrollment')
    op.drop_index(op.f('ix_enrollment_course_id'), table_name='enrollment')
    op.drop_table('enrollment')
    op.drop_index(op.f('ix_course_code'), table_name='course')
    op.drop_table('course')
    op.drop_table('admin')
    op.drop_index(op.f('ix_tutor_is_available'), table_name='tutor')
    op.drop_table('tutor')
    op.drop_index(op.f('ix_student_matriculation_number'), table_name='student')
    op.drop_table('student')
    op.drop_index(op.f('ix_user_session_user_id'), table_name='user_session')
    op.drop_index(op.f('ix_user_session_refresh_token'), table_name='user_session')
    op.drop_table('user_session')
    op.drop_table('user_role_association')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_table('role_permission_association')
    op.drop_index(op.f('ix_role_name'), table_name='role')
    op.drop_table('role')
    op.drop_index(op.f('ix_permission_name'), table_name='permission')
    op.drop_table('permission')
    
    op.execute("DROP EXTENSION IF EXISTS vector;")
