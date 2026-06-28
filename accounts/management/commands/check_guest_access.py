from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import GuestAccess, Notification


class Command(BaseCommand):
    help = "Désactive les accès invité expirés."

    def handle(self, *args, **options):
        now = timezone.now()
        expired = GuestAccess.objects.filter(is_active=True, expires_at__lte=now)

        for access in expired:
            access.is_active = False
            access.save()

            guest = access.guest
            family_name = access.family.name

            Notification.objects.create(
                user=guest,
                type='join_approved',
                message=f"Votre accès invité à la famille {family_name} a expiré.",
                link='/accounts/dashboard/'
            )
            send_mail(
                subject="Votre accès invité a expiré — MIFFA",
                message=(
                    f"Bonjour {guest.first_name},\n\n"
                    f"Votre période d'accès en tant qu'invité à {family_name} est terminée.\n"
                    f"Vous gardez l'historique de cette visite dans votre compte.\n\n— MIFFA"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[guest.email] if guest.email else [],
                fail_silently=True,
            )
            self.stdout.write(f"Accès expiré : {guest.username} ({family_name})")