"""E'lonlar va e'lon rasmlari

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tstamp(name: str) -> sa.Column:
    """now() standarti bilan vaqt tomir ustuni."""
    return sa.Column(
        name, sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "listings",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("seller_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1000), server_default="", nullable=False),
        sa.Column("price", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("price_type", sa.Text(), nullable=False),
        sa.Column("condition", sa.Text(), nullable=False),
        sa.Column(
            "location",
            Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("district_id", sa.Integer(), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="active", nullable=False),
        sa.Column("moderation", sa.Text(), server_default="auto_ok", nullable=False),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        _tstamp("bumped_at"),
        _tstamp("created_at"),
        _tstamp("updated_at"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["seller_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_listings_seller_id"), "listings", ["seller_id"])
    op.create_index(op.f("ix_listings_category_id"), "listings", ["category_id"])
    op.create_index(op.f("ix_listings_district_id"), "listings", ["district_id"])

    op.create_table(
        "listing_images",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("listing_id", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_listing_images_listing_id"), "listing_images", ["listing_id"])

    # Lenta va qidiruv uchun indexlar (dizayn hujjatidagi DDL bilan bir xil).
    op.create_index("ix_listings_location", "listings", ["location"], postgresql_using="gist")
    op.create_index(
        "ix_listings_search",
        "listings",
        [sa.text("search_text gin_trgm_ops")],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_listings_feed",
        "listings",
        ["status", sa.text("bumped_at DESC")],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_listings_feed", table_name="listings")
    op.drop_index("ix_listings_search", table_name="listings", postgresql_using="gin")
    op.drop_index("ix_listings_location", table_name="listings", postgresql_using="gist")
    op.drop_index(op.f("ix_listing_images_listing_id"), table_name="listing_images")
    op.drop_table("listing_images")
    op.drop_index(op.f("ix_listings_district_id"), table_name="listings")
    op.drop_index(op.f("ix_listings_category_id"), table_name="listings")
    op.drop_index(op.f("ix_listings_seller_id"), table_name="listings")
    op.drop_table("listings")
