# blog/management/commands/seed.py
#
# Populates the database with realistic test data.
# Run: python manage.py seed

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
from blog.models import Post

fake = Faker()


class Command(BaseCommand):
    help = "Seeds the database with 500 posts across 3 users."

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database...")

        # Create 3 test users
        users = []
        credentials = [
            ("alice", "password123"),
            ("bob", "password123"),
            ("carol", "password123"),
        ]

        for username, password in credentials:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f"Created user: {username} / {password}")
            else:
                self.stdout.write(f"User already exists: {username}")
            users.append(user)

        # Create 500 posts — mix of published and drafts
        posts_to_create = []
        for i in range(500):
            status = Post.STATUS_DRAFT if i % 5 == 0 else Post.STATUS_PUBLISHED
            posts_to_create.append(
                Post(
                    title=fake.sentence(nb_words=6),
                    content=fake.paragraphs(nb=4, ext_word_list=None).__str__(),
                    author=users[i % len(users)],
                    status=status,
                )
            )

        Post.objects.bulk_create(posts_to_create)
        self.stdout.write(f"Created 500 posts ({Post.objects.filter(status='draft').count()} drafts)")
        self.stdout.write(self.style.SUCCESS("\n Done! Database seeded successfully."))
        self.stdout.write("\nTest credentials:")
        for username, password in credentials:
            self.stdout.write(f"  {username} / {password}")
