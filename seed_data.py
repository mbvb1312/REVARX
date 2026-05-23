import random
from datetime import datetime, timedelta

from backend.database import Campaign, Lead, Message, Reply, SessionLocal, init_db


NAMES = [
    "Priya Sharma",
    "Rahul Verma",
    "Ananya Rao",
    "Arjun Iyer",
    "Meera Nair",
    "Karthik Das",
    "Aditi Singh",
    "Vikram Patel",
    "Neha Gupta",
    "Rohan Mehta",
    "Suresh Kumar",
    "Pooja Menon",
    "Deepak Reddy",
    "Nisha Jain",
    "Ravi Bansal",
    "Isha Kulkarni",
    "Manish Kapoor",
    "Sneha Pillai",
    "Varun Arora",
    "Kavya Desai",
    "Aman Joshi",
    "Divya Soni",
    "Pranav Shah",
    "Leena George",
    "Gaurav Malhotra",
    "Ankit Yadav",
    "Ritika Bose",
    "Harish Naik",
    "Swati Mishra",
    "Abhishek Roy",
    "Tanvi Shetty",
    "Naveen Pillai",
    "Shruti Anand",
    "Kiran Rao",
    "Mohit Saxena",
    "Jaya Prasad",
    "Seema Goyal",
    "Akhil Menon",
    "Pallavi Nair",
    "Siddharth Rao",
    "Arpita Das",
    "Nitin Verma",
    "Anu Joseph",
    "Sanjay Kapoor",
    "Lakshmi Iyer",
    "Rakesh Sinha",
    "Bhavna Shah",
    "Sunil Rao",
    "Vidya Nair",
    "Rohit Jain",
]

PRODUCT_INTERESTS = [
    "CRM Software",
    "Inventory Management",
    "HR Platform",
    "E-commerce Enablement",
    "Productivity Suite",
]

NOTES = [
    "Attended webinar",
    "Requested pricing",
    "Trial expired",
    "Asked about integration",
    "Wanted a demo call",
]


HOT_REPLIES = [
    "Yes, I'm interested. Let's schedule a call this week.",
    "This looks great. Can you share pricing and next steps?",
    "I'm ready to move forward. When can we start?",
    "Sounds perfect. Please book a demo.",
    "We want to proceed. Can you send details today?",
]

WARM_REPLIES = [
    "Maybe next month. Please check back later.",
    "Not right now, but send more info.",
    "We are considering options. Follow up soon.",
    "Can you remind me in a few weeks?",
]

COLD_REPLIES = [
    "Not interested right now.",
    "We decided to go another direction.",
    "No, thanks.",
    "Please stop reaching out for now.",
]


def _random_date_string(days_back: int) -> str:
    date = datetime.utcnow() - timedelta(days=days_back)
    return date.strftime("%Y-%m-%d")


def _seed_leads(db) -> list:
    leads = []
    for idx, name in enumerate(NAMES[:50]):
        email = f"{name.lower().replace(' ', '.')}@example.com"
        lead = Lead(
            name=name,
            email=email,
            telegram_chat_id=None,
            product_interest=random.choice(PRODUCT_INTERESTS),
            last_contact_date=_random_date_string(random.randint(30, 180)),
            notes=random.choice(NOTES),
            status="cold",
        )
        db.add(lead)
        leads.append(lead)

    db.flush()
    return leads


def _seed_campaign(db) -> Campaign:
    campaign = Campaign(name="Reactivation Campaign Q2 2026", tone="friendly", channel="telegram")
    db.add(campaign)
    db.flush()
    return campaign


def _seed_messages(db, leads: list, campaign: Campaign) -> list:
    messages = []

    sent_count = 38
    pending_count = 12
    sent_leads = leads[:sent_count]
    pending_leads = leads[sent_count:sent_count + pending_count]

    sent_variants = list(("A",) * 23 + ("B",) * 15)
    random.shuffle(sent_variants)

    for lead, variant in zip(sent_leads, sent_variants):
        messages.append(
            Message(
                lead_id=lead.id,
                campaign_id=campaign.id,
                variant=variant,
                content=f"Hi {lead.name}, just checking in about {lead.product_interest}.",
                channel="telegram",
                tone=random.choice(["friendly", "professional", "urgent"]),
                status="sent",
                sent_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
            )
        )

    for lead in pending_leads:
        messages.append(
            Message(
                lead_id=lead.id,
                campaign_id=campaign.id,
                variant=random.choice(["A", "B"]),
                content=f"Hi {lead.name}, following up on {lead.product_interest}.",
                channel="telegram",
                tone=random.choice(["friendly", "professional", "urgent"]),
                status="pending",
                sent_at=None,
            )
        )

    db.add_all(messages)
    db.flush()
    return messages


def _seed_replies(db, messages: list, leads: list) -> None:
    sent_messages = [msg for msg in messages if msg.status == "sent"]

    a_messages = [msg for msg in sent_messages if msg.variant == "A"]
    b_messages = [msg for msg in sent_messages if msg.variant == "B"]

    selected_a = a_messages[:8]
    selected_b = b_messages[:3]

    reply_times = [10, 10, 11, 11, 12, 9, 10, 11, 10, 12, 10]

    replies = []
    hot_replies = HOT_REPLIES[:5]
    warm_replies = WARM_REPLIES[:4]
    cold_replies = COLD_REPLIES[:4]
    reply_texts = hot_replies + warm_replies + cold_replies

    for msg, reply_text, hour in zip(selected_a + selected_b, reply_texts, reply_times):
        received_at = datetime.utcnow().replace(hour=hour, minute=0, second=0, microsecond=0)
        classification = "hot" if reply_text in hot_replies else "warm" if reply_text in warm_replies else "cold"
        replies.append(
            Reply(
                lead_id=msg.lead_id,
                message_id=msg.id,
                content=reply_text,
                is_voice_note=False,
                classification=classification,
                received_at=received_at,
            )
        )

        lead = next(lead for lead in leads if lead.id == msg.lead_id)
        lead.status = classification

    # Add two extra replies without message_id to reach 13 total replies
    extra_replies = [
        "Thanks, got it. Will revisit later.",
        "Not now, maybe next quarter.",
    ]
    for extra_text in extra_replies:
        replies.append(
            Reply(
                lead_id=leads[-1].id,
                message_id=None,
                content=extra_text,
                is_voice_note=False,
                classification="warm",
                received_at=datetime.utcnow().replace(hour=10, minute=30, second=0, microsecond=0),
            )
        )

    db.add_all(replies)


def _apply_unsubscribed(leads: list) -> None:
    for lead in leads[-5:]:
        lead.status = "unsubscribed"


def seed() -> None:
    random.seed(42)
    init_db()
    db = SessionLocal()

    try:
        db.query(Reply).delete()
        db.query(Message).delete()
        db.query(Campaign).delete()
        db.query(Lead).delete()
        db.commit()

        leads = _seed_leads(db)
        campaign = _seed_campaign(db)
        messages = _seed_messages(db, leads, campaign)
        _seed_replies(db, messages, leads)
        _apply_unsubscribed(leads)

        db.commit()
        print("Seeded 50 leads, 50 messages, 13 replies.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
