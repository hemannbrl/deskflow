"""Seed the database with demo users and tickets in every lifecycle state.

Destructive: wipes existing tickets (and their events/comments) first.
Demo users all get the password `deskflow123`.
"""

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import Comment, Ticket
from tickets.sla import due_at

User = get_user_model()

PASSWORD = "deskflow123"

USERS = [
    ("demo_requester", "requester"),
    ("sara", "requester"),
    ("liam", "requester"),
    ("demo_agent", "agent"),
    ("mike", "agent"),
    ("demo_manager", "manager"),
]

# (title, description, priority, category)
TICKETS = [
    ("VPN keeps disconnecting", "Drops every ~10 minutes since this morning.", "high", "network"),
    ("Laptop won't boot", "Black screen with a blinking cursor.", "urgent", "hardware"),
    ("Need access to billing dashboard", "Joining the finance team next week.", "normal", "access"),
    ("Outlook rules stopped working", "Mail isn't sorted into folders anymore.", "low", "email"),
    ("Wi-Fi dead in meeting room B", "No SSID visible on any device there.", "high", "network"),
    ("Second monitor not detected", "Worked Friday; dock power-cycled.", "normal", "hardware"),
    ("Password reset for HR portal", "Locked out after too many attempts.", "urgent", "access"),
    ("Excel crashes opening large files", "Anything over ~50MB dies.", "normal", "software"),
    ("Printer on floor 3 jams constantly", "Every duplex job jams.", "low", "hardware"),
    ("Shared drive permission denied", "Access denied since the migration.", "high", "access"),
    ("Slack notifications delayed", "Messages arrive 15+ minutes late.", "low", "software"),
    ("New starter laptop setup", "Starts Monday — needs the dev image.", "normal", "hardware"),
    ("Phishing email reported", "Suspicious invoice mail sent to the team.", "urgent", "email"),
    ("Zoom audio echo in board room", "Remote side hears themselves.", "normal", "hardware"),
    ("Install PostgreSQL locally", "Need admin rights or a packaged install.", "low", "software"),
    ("Badge reader rejects my card", "Front entrance only; side door works.", "normal", "access"),
    ("Website staging cert expired", "Browsers show a TLS warning.", "high", "software"),
    ("Mouse double-clicks on single click", "Drag and drop nearly impossible.", "low", "hardware"),
    ("Can't join analytics mailing list", "Subscribe link errors with a 500.", "low", "email"),
    ("File server slow every afternoon", "Transfers crawl mid-afternoon.", "normal", "network"),
    ("Docker Desktop license needed", "Needed for the build pipeline.", "normal", "software"),
    ("Conference TV shows no signal", "HDMI and wireless casting both fail.", "low", "hardware"),
    ("Remove leaver's accounts", "Contractor finished — full offboarding.", "high", "access"),
    ("Calendar invites show wrong timezone", "Events off by three hours.", "normal", "software"),
    ("Laptop fan at full speed constantly", "Loud even when idle; CPU fine.", "low", "hardware"),
    ("Git push rejected from office network", "Works from home, not in office.", "high", "network"),
]

COMMENT_EXCHANGES = [
    ("Any update on this?", False),
    ("Looking into it now — will report back shortly.", False),
    ("Reproduced on a test machine, suspect the latest driver update.", True),
    ("Vendor ticket opened, reference #48213.", True),
    ("This should be fixed now — can you confirm?", False),
]


class Command(BaseCommand):
    help = "Wipe tickets and seed demo users, tickets, comments, and audit history."

    def handle(self, *args, **options):
        random.seed(42)
        now = timezone.now()

        users = {}
        for username, role in USERS:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(PASSWORD)
                user.save()
            user.profile.role = role
            user.profile.save()
            users[username] = user
        requesters = [users["demo_requester"], users["sara"], users["liam"]]
        agents = [users["demo_agent"], users["mike"]]
        manager = users["demo_manager"]

        deleted, _ = Ticket.objects.all().delete()
        self.stdout.write(f"cleared {deleted} old ticket rows")

        tickets = []
        for title, description, priority, category in TICKETS:
            ticket = Ticket.objects.create(
                title=title,
                description=description,
                priority=priority,
                category=category,
                requester=random.choice(requesters),
            )
            created_at = now - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
            Ticket.objects.filter(pk=ticket.pk).update(
                created_at=created_at, sla_due_at=due_at(priority, created_at)
            )
            ticket.refresh_from_db()
            tickets.append(ticket)

        # Walk a spread of tickets through the lifecycle via the real transitions,
        # so every state change writes an audit event.
        for ticket in tickets[:6]:  # closed
            agent = random.choice(agents)
            ticket.assign(agent, actor=manager)
            ticket.resolve(actor=agent)
            ticket.close(actor=ticket.requester)
        for ticket in tickets[6:10]:  # resolved, awaiting confirmation
            agent = random.choice(agents)
            ticket.assign(agent, actor=agent)
            ticket.resolve(actor=agent)
        for ticket in tickets[10:12]:  # escalated by the SLA job
            ticket.escalate(actor=None, note="sla breach")
        for ticket in tickets[12:13]:  # escalated manually
            ticket.assign(agents[0], actor=manager)
            ticket.escalate(actor=manager, note="blocking the finance team")
        for ticket in tickets[13:19]:  # assigned, in progress
            agent = random.choice(agents)
            ticket.assign(agent, actor=random.choice([agent, manager]))
        # tickets[19:] stay open; make two of them overdue
        for ticket in tickets[19:21]:
            Ticket.objects.filter(pk=ticket.pk).update(sla_due_at=now - timedelta(hours=3))

        comment_count = 0
        for ticket in random.sample(tickets, 12):
            agent = random.choice(agents)
            for body, is_internal in random.sample(
                COMMENT_EXCHANGES, random.randint(1, len(COMMENT_EXCHANGES))
            ):
                author = agent if is_internal else random.choice([ticket.requester, agent])
                Comment.objects.create(
                    ticket=ticket, author=author, body=body, is_internal=is_internal
                )
                comment_count += 1

        by_status = {
            status: Ticket.objects.filter(status=status).count()
            for status, _ in Ticket.Status.choices
        }
        self.stdout.write(
            self.style.SUCCESS(
                f"seeded {len(tickets)} tickets {by_status}, {comment_count} comments, "
                f"{len(USERS)} users (password: {PASSWORD})"
            )
        )
