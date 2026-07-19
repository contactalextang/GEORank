"""Remove the bundled author homepage releases and default to the company list.

This fork ships no built-in marketing homepage. Any built-in release rows seeded
by earlier migrations are removed, and the homepage runtime is reset to the
neutral "default" mode so `/` falls back to the company directory.

Revision ID: 017_remove_builtin_homepage
Revises: 016_merge_platform_iterations
Create Date: 2026-07-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "017_remove_builtin_homepage"
down_revision = "016_merge_platform_iterations"
branch_labels = None
depends_on = None


# Author-branded built-in homepage releases seeded by migrations 012/014/016.
BUILTIN_RELEASE_IDS = (
    "f7e16e7c-e1aa-4e39-951b-4c274dd05175",
    "43a461f6-6be2-4931-9dbb-f1d56576292a",
    "9fe4a087-42bc-423a-bc59-fc020018a6f9",
)


def upgrade() -> None:
    connection = op.get_bind()

    # Drop the bundled built-in homepage releases if they are still present.
    connection.execute(
        sa.text(
            "DELETE FROM homepage_releases WHERE id = ANY(CAST(:ids AS uuid[]))"
        ),
        {"ids": list(BUILTIN_RELEASE_IDS)},
    )

    # Reset the runtime pointer to the neutral default (company directory) when it
    # still targets one of the removed built-in releases.
    connection.execute(
        sa.text(
            """
            UPDATE settings
            SET value = jsonb_set(
                jsonb_set(value, '{mode}', '"default"'::jsonb, true),
                '{active_release_id}', 'null'::jsonb, true
            )
            WHERE key = 'homepage_runtime'
              AND (
                  value ->> 'active_release_id' = ANY(CAST(:ids AS text[]))
                  OR value ->> 'active_release_id' IS NULL
              )
            """
        ),
        {"ids": list(BUILTIN_RELEASE_IDS)},
    )


def downgrade() -> None:
    # Forward-only cleanup: the bundled homepage assets no longer exist in this
    # fork, so there is nothing to restore.
    pass
