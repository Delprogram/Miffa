from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from accounts.models import JoinRequest, Notification, User


class Command(BaseCommand):
    help = "Vérifie les demandes d'adhésion en attente, envoie des rappels et supprime les comptes expirés."

    def handle(self, *args, **options):
        now = timezone.now()
        pending = JoinRequest.objects.filter(status='pending')

        for req in pending:
            age = now - req.created_at
            hours = age.total_seconds() / 3600

            # ─── Rappels à 24h et 36h (avant la suppression à 48h... mais ici on dit "24h" comme limite) ───
            if hours >= 12 and req.reminder_count == 0:
                self.send_reminder(req, 1)
            elif hours >= 18 and req.reminder_count == 1:
                self.send_reminder(req, 2)

            # ─── Suppression après 24h sans approbation ───
            if hours >= 24:
                self.expire_request(req)

    def send_reminder(self, req, reminder_num):
        admins = User.objects.filter(family=req.family, role='admin')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                type='join_reminder',
                message=f"Rappel {reminder_num}/2 : la demande de {req.user.first_name} {req.user.last_name} est toujours en attente.",
                link='/accounts/admin-panel/'
            )
            send_mail(
                subject=f"Rappel — Demande en attente ({reminder_num}/2)",
                message=(
                    f"Bonjour {admin.first_name},\n\n"
                    f"La demande de {req.user.first_name} {req.user.last_name} attend toujours votre approbation.\n"
                    f"Sans action de votre part, le compte sera automatiquement supprimé.\n\n"
                    f"http://127.0.0.1:8000/accounts/admin-panel/\n\n— MIFFA"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin.email] if admin.email else [],
                fail_silently=True,
            )
        req.reminder_count += 1
        req.save()

    def expire_request(self, req):
        user_email = req.user.email
        user_name = f"{req.user.first_name} {req.user.last_name}"
        family_name = req.family.name

        send_mail(
            subject="Votre demande a expiré — MIFFA",
            message=(
                f"Bonjour {req.user.first_name},\n\n"
                f"Votre demande pour rejoindre {family_name} n'a pas été traitée à temps "
                f"et votre compte a été automatiquement supprimé.\n\n— MIFFA"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email] if user_email else [],
            fail_silently=True,
        )

        self.stdout.write(f"Compte supprimé : {user_name} ({family_name})")
        req.user.delete()  # supprime le compte (cascade supprime aussi la JoinRequest)
