"""
Seed Script — Group Consensus Feature

Creates:
  - 3 AlloraUser accounts  
  - 3 TripGroups with mixed member compositions
  - 20 Group-enriched Destination records (with activity_tags, budget tiers, parallel_value_tags)
  - Pre-submitted preferences for all members

Run from the backend/ directory:
    python seed_groups.py

The script is idempotent — re-running does not create duplicates.
"""
from __future__ import annotations

import asyncio
import json
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(__file__))

# Load .env BEFORE importing database so DATABASE_URL is resolved correctly
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select, text
from database import async_session, engine, Base

from auth import hash_password
from group_models import AlloraUser, TripGroup, TripGroupMember, MemberPreferences


# ── Destination seed data (20 records enriched with group fields) ──────────────

GROUP_DESTINATIONS = [
    {
        "id": "gd-001", "name": "Bali", "country": "Indonesia", "continent": "Asia",
        "description": "Island of gods — beaches, temples, rice terraces, and world-class surf.",
        "tags": "beach,surf,culture,food,budget,relaxation",
        "avg_cost_usd": 1200,
        "activity_tags": json.dumps(["beach", "surf", "culture", "food", "budget", "relaxation"]),
        "budget_tier_min": 800, "budget_tier_max": 2500,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "fine-dining", "spa", "beach"]),
        "climate": "tropical", "best_season": "Apr-Oct", "latitude": -8.34, "longitude": 115.09,
    },
    {
        "id": "gd-002", "name": "Lisbon", "country": "Portugal", "continent": "Europe",
        "description": "Sun-soaked city of fado, pastéis, and Atlantic coastline.",
        "tags": "culture,food,urban,budget,beach,nightlife",
        "avg_cost_usd": 1800,
        "activity_tags": json.dumps(["culture", "food", "urban", "budget", "beach", "nightlife"]),
        "budget_tier_min": 1200, "budget_tier_max": 3500,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "michelin", "city-life", "day-trip"]),
        "climate": "mediterranean", "best_season": "Mar-Oct", "latitude": 38.71, "longitude": -9.14,
    },
    {
        "id": "gd-003", "name": "Kyoto", "country": "Japan", "continent": "Asia",
        "description": "Ancient capital of tea ceremonies, bamboo groves & 1,600 temples.",
        "tags": "culture,relaxation,food,budget,urban,nature",
        "avg_cost_usd": 2200,
        "activity_tags": json.dumps(["culture", "relaxation", "food", "urban", "nature"]),
        "budget_tier_min": 1500, "budget_tier_max": 4000,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "fine-dining", "spa", "day-trip"]),
        "climate": "temperate", "best_season": "Mar-May,Sep-Nov", "latitude": 35.01, "longitude": 135.76,
    },
    {
        "id": "gd-004", "name": "Tulum", "country": "Mexico", "continent": "North America",
        "description": "Mayan ruins meet Instagram-perfect cenotes and bohemian beach clubs.",
        "tags": "beach,adventure,luxury,culture,relaxation,food",
        "avg_cost_usd": 2500,
        "activity_tags": json.dumps(["beach", "adventure", "luxury", "culture", "relaxation"]),
        "budget_tier_min": 1500, "budget_tier_max": 5000,
        "parallel_value_tags": json.dumps(["hostel", "luxury-resort", "local-market", "fine-dining", "spa", "beach"]),
        "climate": "tropical", "best_season": "Dec-Apr", "latitude": 20.21, "longitude": -87.46,
    },
    {
        "id": "gd-005", "name": "Chiang Mai", "country": "Thailand", "continent": "Asia",
        "description": "Northern Thailand's mountain city — temples, trekking, street food.",
        "tags": "adventure,culture,food,budget,trekking,remote",
        "avg_cost_usd": 900,
        "activity_tags": json.dumps(["adventure", "culture", "food", "budget", "trekking", "remote"]),
        "budget_tier_min": 500, "budget_tier_max": 1800,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "hiking", "day-trip", "nature"]),
        "climate": "tropical", "best_season": "Nov-Feb", "latitude": 18.79, "longitude": 98.98,
    },
    {
        "id": "gd-006", "name": "Barcelona", "country": "Spain", "continent": "Europe",
        "description": "Gaudí's city — architecture, tapas, beaches, and electric nightlife.",
        "tags": "culture,food,beach,urban,nightlife,luxury",
        "avg_cost_usd": 2800,
        "activity_tags": json.dumps(["culture", "food", "beach", "urban", "nightlife", "luxury"]),
        "budget_tier_min": 1800, "budget_tier_max": 5000,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "city-life", "michelin", "beach", "day-trip"]),
        "climate": "mediterranean", "best_season": "Apr-Oct", "latitude": 41.38, "longitude": 2.17,
    },
    {
        "id": "gd-007", "name": "Queenstown", "country": "New Zealand", "continent": "Oceania",
        "description": "Adventure capital of the world — bungee, ski, skydive.",
        "tags": "adventure,skiing,trekking,remote,nature",
        "avg_cost_usd": 3500,
        "activity_tags": json.dumps(["adventure", "skiing", "trekking", "remote", "nature"]),
        "budget_tier_min": 2500, "budget_tier_max": 6000,
        "parallel_value_tags": json.dumps(["hiking", "boutique", "day-trip", "nature", "spa"]),
        "climate": "temperate", "best_season": "Dec-Feb,Jun-Aug", "latitude": -45.03, "longitude": 168.66,
    },
    {
        "id": "gd-008", "name": "Marrakech", "country": "Morocco", "continent": "Africa",
        "description": "Red city of souks, riads, and Saharan adventures.",
        "tags": "culture,food,budget,adventure,urban,remote",
        "avg_cost_usd": 1100,
        "activity_tags": json.dumps(["culture", "food", "budget", "adventure", "urban", "remote"]),
        "budget_tier_min": 600, "budget_tier_max": 2200,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "fine-dining", "day-trip", "nature"]),
        "climate": "arid", "best_season": "Mar-May,Sep-Nov", "latitude": 31.63, "longitude": -8.00,
    },
    {
        "id": "gd-009", "name": "Santorini", "country": "Greece", "continent": "Europe",
        "description": "Volcanic island of caldera sunsets, cave hotels, and azure domes.",
        "tags": "luxury,beach,relaxation,food,culture",
        "avg_cost_usd": 4500,
        "activity_tags": json.dumps(["luxury", "beach", "relaxation", "food", "culture"]),
        "budget_tier_min": 3000, "budget_tier_max": 8000,
        "parallel_value_tags": json.dumps(["boutique", "luxury-resort", "michelin", "beach", "spa", "fine-dining"]),
        "climate": "mediterranean", "best_season": "Jun-Sep", "latitude": 36.39, "longitude": 25.46,
    },
    {
        "id": "gd-010", "name": "Colombia — Medellín", "country": "Colombia", "continent": "South America",
        "description": "City of eternal spring, innovation, salsa, and vibrant street art.",
        "tags": "culture,food,budget,urban,adventure,nightlife",
        "avg_cost_usd": 1000,
        "activity_tags": json.dumps(["culture", "food", "budget", "urban", "adventure", "nightlife"]),
        "budget_tier_min": 600, "budget_tier_max": 2000,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "city-life", "day-trip", "nightlife"]),
        "climate": "subtropical", "best_season": "Dec-Feb,Jun-Jul", "latitude": 6.25, "longitude": -75.56,
    },
    {
        "id": "gd-011", "name": "Iceland — Reykjavik", "country": "Iceland", "continent": "Europe",
        "description": "Northern lights, geysers, glaciers, and midnight sun.",
        "tags": "adventure,nature,remote,culture",
        "avg_cost_usd": 4000,
        "activity_tags": json.dumps(["adventure", "nature", "remote", "culture"]),
        "budget_tier_min": 2800, "budget_tier_max": 7000,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "hiking", "day-trip", "nature", "spa"]),
        "climate": "subarctic", "best_season": "Jun-Aug,Dec-Feb", "latitude": 64.13, "longitude": -21.89,
    },
    {
        "id": "gd-012", "name": "Vietnam — Hội An", "country": "Vietnam", "continent": "Asia",
        "description": "Ancient trading port — lantern-lit streets, tailors, and river boats.",
        "tags": "culture,food,budget,beach,relaxation,urban",
        "avg_cost_usd": 700,
        "activity_tags": json.dumps(["culture", "food", "budget", "beach", "relaxation", "urban"]),
        "budget_tier_min": 400, "budget_tier_max": 1500,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "fine-dining", "beach", "day-trip"]),
        "climate": "tropical", "best_season": "Feb-Jul", "latitude": 15.88, "longitude": 108.33,
    },
    {
        "id": "gd-013", "name": "Dubai", "country": "UAE", "continent": "Asia",
        "description": "Desert megacity — Burj Khalifa, gold souks, and desert safaris.",
        "tags": "luxury,shopping,urban,adventure,food",
        "avg_cost_usd": 5000,
        "activity_tags": json.dumps(["luxury", "shopping", "urban", "adventure", "food"]),
        "budget_tier_min": 3500, "budget_tier_max": 10000,
        "parallel_value_tags": json.dumps(["boutique", "luxury-resort", "city-life", "michelin", "fine-dining", "day-trip"]),
        "climate": "desert", "best_season": "Nov-Mar", "latitude": 25.20, "longitude": 55.27,
    },
    {
        "id": "gd-014", "name": "Nepal — Pokhara", "country": "Nepal", "continent": "Asia",
        "description": "Gateway to Annapurna — lakeside serenity meets epic trekking.",
        "tags": "adventure,trekking,remote,nature,budget,relaxation",
        "avg_cost_usd": 600,
        "activity_tags": json.dumps(["adventure", "trekking", "remote", "nature", "budget", "relaxation"]),
        "budget_tier_min": 400, "budget_tier_max": 1200,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "hiking", "nature", "spa", "day-trip"]),
        "climate": "subtropical", "best_season": "Oct-Nov,Mar-Apr", "latitude": 28.21, "longitude": 83.99,
    },
    {
        "id": "gd-015", "name": "Cape Town", "country": "South Africa", "continent": "Africa",
        "description": "Mountain city flanked by two oceans — wildlife, wine, and Table Mountain.",
        "tags": "adventure,nature,culture,food,beach,urban",
        "avg_cost_usd": 2000,
        "activity_tags": json.dumps(["adventure", "nature", "culture", "food", "beach", "urban"]),
        "budget_tier_min": 1200, "budget_tier_max": 4000,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "fine-dining", "hiking", "beach"]),
        "climate": "mediterranean", "best_season": "Nov-Mar", "latitude": -33.92, "longitude": 18.42,
    },
    {
        "id": "gd-016", "name": "Georgia — Tbilisi", "country": "Georgia", "continent": "Europe",
        "description": "Ancient crossroads city of sulphur baths, cave monasteries, and vivid wine culture.",
        "tags": "culture,food,budget,adventure,urban,remote",
        "avg_cost_usd": 800,
        "activity_tags": json.dumps(["culture", "food", "budget", "adventure", "urban", "remote"]),
        "budget_tier_min": 500, "budget_tier_max": 1800,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "fine-dining", "day-trip", "spa"]),
        "climate": "continental", "best_season": "Apr-Jun,Sep-Oct", "latitude": 41.69, "longitude": 44.83,
    },
    {
        "id": "gd-017", "name": "Peru — Cusco", "country": "Peru", "continent": "South America",
        "description": "Inca heartland — Machu Picchu, Sacred Valley, and Andean cuisine.",
        "tags": "adventure,culture,trekking,budget,remote,food",
        "avg_cost_usd": 1300,
        "activity_tags": json.dumps(["adventure", "culture", "trekking", "budget", "remote", "food"]),
        "budget_tier_min": 800, "budget_tier_max": 2800,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "hiking", "day-trip", "nature"]),
        "climate": "highland", "best_season": "May-Sep", "latitude": -13.53, "longitude": -71.97,
    },
    {
        "id": "gd-018", "name": "Maldives", "country": "Maldives", "continent": "Asia",
        "description": "Overwater bungalows, neon coral reefs, and utter seclusion.",
        "tags": "luxury,beach,relaxation,remote,snorkeling",
        "avg_cost_usd": 7000,
        "activity_tags": json.dumps(["luxury", "beach", "relaxation", "remote", "snorkeling"]),
        "budget_tier_min": 5000, "budget_tier_max": 15000,
        "parallel_value_tags": json.dumps(["luxury-resort", "spa", "beach", "fine-dining", "boutique"]),
        "climate": "tropical", "best_season": "Nov-Apr", "latitude": 4.17, "longitude": 73.51,
    },
    {
        "id": "gd-019", "name": "Croatia — Dubrovnik", "country": "Croatia", "continent": "Europe",
        "description": "Walled city of the Adriatic — Game of Thrones backdrop, sailing, and seafood.",
        "tags": "culture,beach,food,urban,relaxation,luxury",
        "avg_cost_usd": 3000,
        "activity_tags": json.dumps(["culture", "beach", "food", "urban", "relaxation", "luxury"]),
        "budget_tier_min": 1800, "budget_tier_max": 5500,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "local-market", "fine-dining", "beach", "day-trip"]),
        "climate": "mediterranean", "best_season": "May-Sep", "latitude": 42.65, "longitude": 18.09,
    },
    {
        "id": "gd-020", "name": "Sri Lanka — Ella", "country": "Sri Lanka", "continent": "Asia",
        "description": "Tea-covered hills, Nine Arch Bridge, waterfalls, and epic hiking.",
        "tags": "adventure,nature,budget,trekking,culture,relaxation",
        "avg_cost_usd": 700,
        "activity_tags": json.dumps(["adventure", "nature", "budget", "trekking", "culture", "relaxation"]),
        "budget_tier_min": 400, "budget_tier_max": 1500,
        "parallel_value_tags": json.dumps(["hostel", "boutique", "hiking", "nature", "day-trip", "spa"]),
        "climate": "tropical", "best_season": "Jan-Mar,Jun-Sep", "latitude": 6.87, "longitude": 81.05,
    },
]

# ── Sample Users ───────────────────────────────────────────────────────────────

SEED_USERS = [
    {"id": "seed-user-001", "username": "alice_traveler", "email": "alice@allora-demo.com",
     "display_name": "Alice Chen", "avatar_emoji": "🌊", "password": "demo1234"},
    {"id": "seed-user-002", "username": "bob_backpacker", "email": "bob@allora-demo.com",
     "display_name": "Bob Marsh", "avatar_emoji": "🎒", "password": "demo1234"},
    {"id": "seed-user-003", "username": "carol_luxe", "email": "carol@allora-demo.com",
     "display_name": "Carol Lin", "avatar_emoji": "✨", "password": "demo1234"},
    {"id": "seed-user-004", "username": "dave_adventure", "email": "dave@allora-demo.com",
     "display_name": "Dave Osei", "avatar_emoji": "⛰️", "password": "demo1234"},
    {"id": "admin-user-001", "username": "admin", "email": "admin@allora-demo.com",
     "display_name": "Admin", "avatar_emoji": "🛡️", "password": "admin_secure_2025"},
]

# ── Sample Groups with Pre-submitted Preferences ───────────────────────────────

SEED_GROUPS = [
    {
        "id": "seed-group-001",
        "name": "Bali Squad 2025 🌴",
        "members": [
            {
                "user_id": "seed-user-001", "role": "owner",
                "prefs": {"tags": ["beach", "food", "budget"], "bmin": 800, "bmax": 2500, "days": 7, "region": "Asia"},
            },
            {
                "user_id": "seed-user-002", "role": "member",
                "prefs": {"tags": ["budget", "adventure", "culture"], "bmin": 500, "bmax": 1500, "days": 5, "region": "Asia"},
            },
            {
                "user_id": "seed-user-003", "role": "member",
                "prefs": {"tags": ["luxury", "beach", "relaxation"], "bmin": 3000, "bmax": 8000, "days": 10, "region": "Asia"},
            },
        ],
    },
    {
        "id": "seed-group-002",
        "name": "Euro Summer Crew 🇪🇺",
        "members": [
            {
                "user_id": "seed-user-002", "role": "owner",
                "prefs": {"tags": ["budget", "culture", "food"], "bmin": 600, "bmax": 2000, "days": 7, "region": "Europe"},
            },
            {
                "user_id": "seed-user-004", "role": "member",
                "prefs": {"tags": ["adventure", "urban", "culture"], "bmin": 1200, "bmax": 3000, "days": 10, "region": "Europe"},
            },
        ],
    },
    {
        "id": "seed-group-003",
        "name": "Adventure Bros 🧗",
        "members": [
            {
                "user_id": "seed-user-004", "role": "owner",
                "prefs": {"tags": ["adventure", "trekking", "remote"], "bmin": 1000, "bmax": 3500, "days": 14, "region": None},
            },
            {
                "user_id": "seed-user-001", "role": "member",
                "prefs": {"tags": ["beach", "relaxation", "food"], "bmin": 1000, "bmax": 3000, "days": 7, "region": None},
            },
            {
                "user_id": "seed-user-002", "role": "member",
                "prefs": {"tags": ["budget", "culture", "adventure"], "bmin": 500, "bmax": 1800, "days": 7, "region": None},
            },
        ],
    },
]


# ── Main Seed Logic ────────────────────────────────────────────────────────────

async def seed():
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    async with async_session() as session:
        print("🌱 Seeding Allora group feature data...")

        # ── Ensure new Destination columns exist ──
        async with engine.begin() as conn:
            for stmt in [
                "ALTER TABLE destinations ADD COLUMN IF NOT EXISTS activity_tags TEXT",
                "ALTER TABLE destinations ADD COLUMN IF NOT EXISTS budget_tier_min INTEGER",
                "ALTER TABLE destinations ADD COLUMN IF NOT EXISTS budget_tier_max INTEGER",
                "ALTER TABLE destinations ADD COLUMN IF NOT EXISTS parallel_value_tags TEXT",
                "ALTER TABLE destinations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",
            ]:
                try:
                    await conn.execute(text(stmt))
                except Exception:
                    pass

        # ── Seed Destinations ──
        from models import Destination
        for d in GROUP_DESTINATIONS:
            existing = await session.execute(
                select(Destination).where(Destination.id == d["id"])
            )
            dest = existing.scalar_one_or_none()
            if dest:
                # Update group-specific fields on existing record
                dest.activity_tags = d["activity_tags"]
                dest.budget_tier_min = d["budget_tier_min"]
                dest.budget_tier_max = d["budget_tier_max"]
                dest.parallel_value_tags = d["parallel_value_tags"]
            else:
                dest = Destination(
                    id=d["id"], name=d["name"], country=d["country"],
                    continent=d["continent"], description=d["description"],
                    tags=d["tags"], avg_cost_usd=d["avg_cost_usd"],
                    climate=d["climate"], best_season=d["best_season"],
                    latitude=d["latitude"], longitude=d["longitude"],
                    activity_tags=d["activity_tags"],
                    budget_tier_min=d["budget_tier_min"],
                    budget_tier_max=d["budget_tier_max"],
                    parallel_value_tags=d["parallel_value_tags"],
                )
                session.add(dest)
        print(f"  ✅ {len(GROUP_DESTINATIONS)} destinations seeded")

        # ── Seed Users ──
        from group_models import AlloraUser
        for u in SEED_USERS:
            existing = await session.execute(
                select(AlloraUser).where(AlloraUser.id == u["id"])
            )
            if not existing.scalar_one_or_none():
                session.add(AlloraUser(
                    id=u["id"],
                    username=u["username"],
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    display_name=u["display_name"],
                    avatar_emoji=u["avatar_emoji"],
                ))
        print(f"  ✅ {len(SEED_USERS)} users seeded")
        await session.flush()

        # ── Seed Groups ──
        from group_models import TripGroup, TripGroupMember, MemberPreferences
        for g in SEED_GROUPS:
            existing = await session.execute(
                select(TripGroup).where(TripGroup.id == g["id"])
            )
            if existing.scalar_one_or_none():
                continue

            group = TripGroup(
                id=g["id"],
                name=g["name"],
                created_by=g["members"][0]["user_id"],
                status="active",
            )
            session.add(group)
            await session.flush()

            for m in g["members"]:
                member_id = str(uuid.uuid4())
                member = TripGroupMember(
                    id=member_id,
                    group_id=g["id"],
                    user_id=m["user_id"],
                    role=m["role"],
                    preferences_submitted_at=now,
                )
                session.add(member)
                await session.flush()

                prefs = MemberPreferences(
                    id=str(uuid.uuid4()),
                    group_member_id=member_id,
                    budget_min=m["prefs"]["bmin"],
                    budget_max=m["prefs"]["bmax"],
                    trip_duration_days=m["prefs"]["days"],
                    region_preference=m["prefs"]["region"],
                    submitted_at=now,
                )
                prefs.preference_tags = m["prefs"]["tags"]
                session.add(prefs)

        print(f"  ✅ {len(SEED_GROUPS)} groups seeded")
        await session.commit()
        print("✨ Seed complete!\n")
        print("Demo credentials:")
        for u in SEED_USERS:
            print(f"  {u['username']} / {u['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
