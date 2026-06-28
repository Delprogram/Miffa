from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import JoinRequest, Notification
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Vérifie les demandes d'adhésion en attente, envoie des rappels et supprime les comptes expirés."

    def handle(self, *args, **options):
        now = timezone.now()
        pending = JoinRequest.objects.filter(status='pending')

        for req in pending:
            age = now - req.created_at
            hours = age.total_seconds() / 3600

            # ─── Rappel 1 à 12h ───
            if hours >= 12 and req.reminder_count == 0:
                self.send_admin_reminder(req, 1)

            # ─── Rappel 2 à 18h ───
            elif hours >= 18 and req.reminder_count == 1:
                self.send_admin_reminder(req, 2)

            # ─── Suppression après 24h sans approbation ───
            if hours >= 24:
                self.expire_request(req)

    def send_admin_reminder(self, req, reminder_num):
        admins = User.objects.filter(family=req.family, role='admin')
        admin_url = f"{settings.SITE_URL}/accounts/admin-panel/"

        for admin in admins:
            Notification.objects.create(
                user=admin,
                type='join_reminder',
                message=f"Rappel {reminder_num}/2 : la demande de {req.user.first_name} {req.user.last_name} est toujours en attente.",
                link='/accounts/admin-panel/'
            )
            send_mail(
                subject=f"Rappel {reminder_num}/2 — Demande en attente",
                message=(
                    f"Bonjour {admin.first_name},\n\n"
                    f"La demande de {req.user.first_name} {req.user.last_name} attend toujours votre approbation.\n"
                    f"Sans action de votre part, le compte sera automatiquement supprimé sous peu.\n\n"
                    f"{admin_url}\n\n— MIFFA"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin.email] if admin.email else [],
                fail_silently=True,
            )
        req.reminder_count += 1
        req.save()
        self.stdout.write(f"Rappel {reminder_num} envoyé pour la demande de {req.user.username}")

    def expire_request(self, req):
        user = req.user
        family_name = req.family.name
        attempt = req.attempt_number

        if attempt >= 3:
            # 3ème tentative expirée → suppression définitive
            send_mail(
                subject="Compte définitivement supprimé — MIFFA",
                message=(
                    f"Bonjour {user.first_name},\n\n"
                    f"Après {attempt} tentatives, votre demande pour rejoindre {family_name} "
                    f"n'a pas été traitée à temps. Votre compte a été définitivement supprimé.\n\n— MIFFA"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email] if user.email else [],
                fail_silently=True,
            )
            self.stdout.write(self.style.WARNING(f"Compte supprimé définitivement : {user.username}"))
            user.delete()
        else:
            # Marque comme refusée mais le compte reste — il peut renvoyer une demande
            req.status = 'rejected'
            req.save()
            send_mail(
                subject="Votre demande a expiré — MIFFA",
                message=(
                    f"Bonjour {user.first_name},\n\n"
                    f"Votre demande pour rejoindre {family_name} n'a pas été traitée dans les 24h.\n"
                    f"Vous pouvez renvoyer une nouvelle demande depuis votre tableau de bord "
                    f"(tentative {attempt + 1} sur 3).\n\n— MIFFA"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email] if user.email else [],
                fail_silently=True,
            )
            self.stdout.write(f"Demande expirée (tentative {attempt}/3) : {user.username}")