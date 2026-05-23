import random
from datetime import timedelta

from backend.database import Campaign, Lead, Message, Reply, SessionLocal, init_db, utc_now

NAMES = [
    ("Aarav Sharma", "male"),
    ("Priya Nair", "female"),
    ("Rohan Mehta", "male"),
    ("Ananya Rao", "female"),
    ("Karthik Iyer", "male"),
    ("Sneha Kapoor", "female"),
    ("Vikram Patel", "male"),
    ("Meera Menon", "female"),
    ("Aditya Joshi", "male"),
    ("Isha Gupta", "female"),
    ("Rahul Verma", "male"),
    ("Kavya Desai", "female"),
    ("Arjun Reddy", "male"),
    ("Nisha Jain", "female"),
    ("Siddharth Bose", "male"),
    ("Tanvi Shetty", "female"),
    ("Manish Kumar", "male"),
    ("Aditi Singh", "female"),
    ("Pranav Shah", "male"),
    ("Leena George", "female"),
    ("Gaurav Malhotra", "male"),
    ("Ritika Roy", "female"),
    ("Naveen Pillai", "male"),
    ("Shruti Anand", "female"),
    ("Mohit Saxena", "male"),
    ("Pallavi Nair", "female"),
    ("Akhil Menon", "male"),
    ("Bhavna Shah", "female"),
    ("Sunil Rao", "male"),
    ("Vidya Nair", "female"),
    ("Abhishek Yadav", "male"),
    ("Swati Mishra", "female"),
    ("Harish Naik", "male"),
    ("Divya Soni", "female"),
    ("Rakesh Sinha", "male"),
    ("Seema Goyal", "female"),
    ("Nitin Verma", "male"),
    ("Arpita Das", "female"),
    ("Rohit Jain", "male"),
    ("Lakshmi Iyer", "female"),
    ("Sanjay Kapoor", "male"),
    ("Jaya Prasad", "female"),
    ("Aman Joshi", "male"),
    ("Pooja Menon", "female"),
    ("Deepak Reddy", "male"),
    ("Neha Gupta", "female"),
    ("Varun Arora", "male"),
    ("Kiran Rao", "other"),
    ("Ankit Yadav", "male"),
    ("Maya Thomas", "female"),
]

INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]

PRODUCTS = [
    ("MacBook Air M3", "electronics"),
    ("Samsung Galaxy S24 Ultra", "electronics"),
    ("Sony WH-1000XM5 Headphones", "electronics"),
    ("Dell Inspiron 14 Laptop", "electronics"),
    ("Nike Air Max 270", "footwear"),
    ("Adidas Ultraboost Light", "footwear"),
    ("Puma RS-X Sneakers", "footwear"),
    ("Levi's 501 Jeans", "fashion"),
    ("H&M Linen Shirt", "fashion"),
    ("Fossil Gen 6 Smartwatch", "accessories"),
    ("Safari Cabin Trolley Bag", "accessories"),
    ("LG 7kg Front Load Washing Machine", "home_appliances"),
    ("Philips Air Fryer XL", "home_appliances"),
]

BROWSE_NOTES = [
    "Viewed 3 times in the last week",
    "Added to cart and abandoned at checkout",
    "Compared with 2 other products",
    "Spent 12 minutes on the product page",
    "Clicked ad and browsed reviews",
    "Wishlist add detected but no purchase",
    "Returned twice after price-drop notification",
    "Abandoned after checking delivery estimate",
]

HOT_REPLIES = [
    "Yes, is there a discount available if I buy today?",
    "Can you send the checkout link again? I want to purchase.",
    "Is this product available for delivery this week?",
    "I am interested. Do you have any card offer?",
    "Please share the final price and payment options.",
]

WARM_REPLIES = [
    "Maybe next week. Please remind me again.",
    "Can you send more details before I decide?",
    "I am comparing options. Keep me posted if the price drops.",
    "Interested, but I need to check with my family first.",
    "Can you tell me if EMI is available?",
]

COLD_REPLIES = [
    "Already bought from Amazon.",
    "The price is too high for me.",
    "Not interested right now.",
    "I bought a different model from Flipkart.",
    "No thanks, I was only browsing.",
]

UNSUB_REPLIES = [
    "Stop emailing me.",
    "Unsubscribe me from these emails.",
    "Please remove me from your list.",
]


def _email_for(name: str) -> str:
    return f"{name.lower().replace(' ', '.')}@example.com"


def _seed_leads(db) -> list[Lead]:
    leads = []
    for idx, (name, gender) in enumerate(NAMES):
        product, category = PRODUCTS[idx % len(PRODUCTS)]
        lead = Lead(
            name=name,
            email=_email_for(name),
            telegram_chat_id=None,
            product_interest=product,
            product_viewed=product,
            product_category=category,
            age=random.randint(18, 55),
            gender=gender,
            state=INDIAN_STATES[idx % len(INDIAN_STATES)],
            last_contact_date=(utc_now() - timedelta(days=random.randint(1, 21))).strftime("%Y-%m-%d"),
            notes=random.choice(BROWSE_NOTES),
            status="new",
        )
        db.add(lead)
        leads.append(lead)

    db.flush()
    return leads


def _seed_campaign(db) -> Campaign:
    campaign = Campaign(name="Seeded E-commerce Recovery Campaign", tone="ab-test", channel="email")
    db.add(campaign)
    db.flush()
    return campaign


def _message_body(lead: Lead, variant: str) -> str:
    if variant == "A":
        return (
            f"Dear {lead.name}, we noticed you were browsing {lead.product_viewed}. "
            "You can return to your selection and review current availability, delivery options, and active offers."
        )
    return (
        f"Hey {lead.name}, that {lead.product_viewed} you were eyeing is still waiting. "
        "Take one more look whenever you are ready."
    )


def _seed_messages(db, leads: list[Lead], campaign: Campaign) -> list[Message]:
    messages = []
    sent_count = 42
    variants = list(("A",) * 22 + ("B",) * 20)
    random.shuffle(variants)

    for lead, variant in zip(leads[:sent_count], variants):
        lead.ab_preference = variant
        lead.status = "pending"
        msg = Message(
            lead_id=lead.id,
            campaign_id=campaign.id,
            variant=variant,
            content=_message_body(lead, variant),
            channel="email",
            tone="professional" if variant == "A" else "friendly",
            status="sent",
            sent_at=utc_now() - timedelta(hours=random.randint(2, 96)),
            llm_used=random.choice(["Groq llama-3.1-8b-instant", "SambaNova Meta-Llama-3.3-70B-Instruct", "REVARX Local Template"]),
        )
        db.add(msg)
        messages.append(msg)

    for lead in leads[sent_count:]:
        lead.status = "new"

    db.flush()
    return messages


def _seed_replies(db, messages: list[Message], leads: list[Lead]) -> None:
    reply_plan = []
    reply_plan.extend(("hot", text) for text in HOT_REPLIES)
    reply_plan.extend(("warm", text) for text in WARM_REPLIES)
    reply_plan.extend(("cold", text) for text in COLD_REPLIES)
    reply_plan.extend(("unsubscribe", text) for text in UNSUB_REPLIES)

    random.shuffle(reply_plan)

    for msg, (classification, text) in zip(messages[: len(reply_plan)], reply_plan):
        lead = next(lead for lead in leads if lead.id == msg.lead_id)
        lead.status = "unsubscribed" if classification == "unsubscribe" else classification
        db.add(
            Reply(
                lead_id=lead.id,
                message_id=msg.id,
                content=text,
                is_voice_note=False,
                classification=classification,
                received_at=utc_now() - timedelta(hours=random.randint(1, 48)),
                llm_used=random.choice(["Groq llama-3.1-8b-instant", "SambaNova Meta-Llama-3.3-70B-Instruct", "REVARX Local Heuristics"]),
            )
        )

    for msg in messages[len(reply_plan) : len(reply_plan) + 10]:
        lead = next(lead for lead in leads if lead.id == msg.lead_id)
        lead.status = "no_response"


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

        db.commit()
        print("Seeded 50 e-commerce customers, 42 recovery emails, and realistic replies.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
