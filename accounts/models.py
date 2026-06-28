from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('member', 'Membre'),
        # ('guest', 'Invité'),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(default='2000-01-01')
    profession = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    # Champs de confidentialité
    hide_email = models.BooleanField(default=False)
    hide_birth_date = models.BooleanField(default=False)
    hide_phone = models.BooleanField(default=False)
    hide_profession = models.BooleanField(default=False)
    hide_city = models.BooleanField(default=False)
    is_deceased = models.BooleanField(default=False)
    deceased_marked_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='marked_deceased'
    )
    deceased_at = models.DateTimeField(null=True, blank=True)
    relation_to_family = models.CharField(max_length=100, blank=True, default='')
    family = models.ForeignKey(
        'Family',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='members'
    )




class Family(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    banner = models.ImageField(upload_to='Bannieres/', null=True, blank=True)
    created_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL,
        null=True, related_name='created_families'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(uuid.uuid4()).upper()[:8]  # ex: A3F9B2C1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Relation(models.Model):
    RELATION_CHOICES = (
        ('parent', 'Parent'),
        ('enfant', 'Enfant'),
        ('conjoint', 'Conjoint(e)'),
        ('frere_soeur', 'Frère / Sœur'),
        ('cousin', 'Cousin(e)'),
        ('grand_parent', 'Grand-parent'),
        ('petit_enfant', 'Petit-enfant'),
        ('oncle_tante', 'Oncle / Tante'),
        ('neveu_niece', 'Neveu / Nièce'),
        ('autre', 'Autre'),
    )
    member = models.ForeignKey('User', on_delete=models.CASCADE, related_name='relations_from')
    related_member = models.ForeignKey('User', on_delete=models.CASCADE, related_name='relations_to')
    relation_type = models.CharField(max_length=20, choices=RELATION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('member', 'related_member')

    def __str__(self):
        return f"{self.member} → {self.related_member} ({self.relation_type})"


class RelationRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('accepted', 'Acceptée'),
        ('rejected', 'Refusée'),
    )
    from_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sent_relation_requests')
    to_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='received_relation_requests')
    relation_type = models.CharField(max_length=20, choices=Relation.RELATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.relation_type}) [{self.status}]"


class Post(models.Model):
    author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='posts')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def reaction_count(self):
        return self.reactions.count()

    @property
    def comment_count(self):
        return self.comments.count()


class Reaction(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('User', on_delete=models.CASCADE)
    content = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class Event(models.Model):
    EVENT_TYPES = (
        ('anniversaire', 'Anniversaire'),
        ('reunion', 'Réunion de famille'),
        ('fete', 'Fête'),
        ('autre', 'Autre'),
    )
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='events')
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=150)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='autre')
    created_at = models.DateTimeField(auto_now_add=True)


class RSVP(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=(('yes', 'Présent'), ('no', 'Absent')))

    class Meta:
        unique_together = ('event', 'user')


class Notification(models.Model):
    TYPE_CHOICES = (
        ('relation_request', 'Demande de relation'),
        ('relation_accepted', 'Relation acceptée'),
        ('relation_rejected', 'Relation refusée'),
        ('join_approved', 'Adhésion approuvée'),
        ('new_post', 'Nouvelle publication'),
        ('new_comment', 'Nouveau commentaire'),
        ('new_like', 'Nouveau like'),
        ('new_event', 'Nouvel événement'),
        ('birthday', 'Anniversaire'),
        ('removal_vote', 'Vote de retrait'),
        ('removal_vote_target', 'Vote de retrait — vous concerne'),
    )
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.type}"


class Album(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='albums')
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class MediaItem(models.Model):
    MEDIA_TYPES = (('image', 'Image'), ('video', 'Vidéo'), ('document', 'Document'))
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='items')
    uploaded_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='media_library/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']


class TimelineEvent(models.Model):
    EVENT_TYPES = (
        ('naissance', 'Naissance'),
        ('mariage', 'Mariage'),
        ('diplome', 'Diplôme'),
        ('demenagement', 'Déménagement'),
        ('deces', 'Décès'),
        ('autre', 'Autre'),
    )
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='timeline_events')
    member = models.ForeignKey('User', on_delete=models.CASCADE, related_name='timeline_events')
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='created_timeline_events')
    title = models.CharField(max_length=150)
    date = models.DateField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='autre')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']


class JoinRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Refusée'),
    )
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='join_requests')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='join_requests')
    relation = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reminder_count = models.IntegerField(default=0)
    attempt_number = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.user} → {self.family} ({self.status})"


class RelationChangeRequest(models.Model):
    ACTION_CHOICES = (('modify', 'Modification'), ('delete', 'Suppression'))
    STATUS_CHOICES = (('pending', 'En attente'), ('accepted', 'Acceptée'), ('rejected', 'Refusée'))

    relation = models.ForeignKey(Relation, on_delete=models.CASCADE, related_name='change_requests')
    requested_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='relation_change_requests')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    new_relation_type = models.CharField(max_length=20, choices=Relation.RELATION_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)


class GuestAccess(models.Model):
    PERMISSION_CHOICES = (
        ('members', 'Membres'),
        ('tree', 'Arbre généalogique'),
        ('timeline', 'Chronologie'),
        ('feed', 'Fil d\'actualité'),
        ('media', 'Médiathèque'),
        ('calendar', 'Calendrier'),
    )

    guest = models.ForeignKey('User', on_delete=models.CASCADE, related_name='guest_accesses')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='guest_accesses')
    invited_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='sent_invitations')
    permissions = models.JSONField(default=list)
    starts_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('guest', 'family')  # un seul accès actif par famille

    def __str__(self):
        return f"{self.guest} invité chez {self.family} jusqu'au {self.expires_at}"

    def has_permission(self, module):
        return self.is_active and module in self.permissions


class RemovalVote(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='removal_votes')
    target_member = models.ForeignKey('User', on_delete=models.CASCADE, related_name='removal_votes_against')
    initiated_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='removal_votes_initiated')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


class RemovalVoteEntry(models.Model):
    vote = models.ForeignKey(RemovalVote, on_delete=models.CASCADE, related_name='entries')
    voter = models.ForeignKey('User', on_delete=models.CASCADE)
    approved = models.BooleanField()  # True = approuve la suppression
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('vote', 'voter')


class DirectAddRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('accepted', 'Acceptée'),
        ('rejected', 'Refusée'),
    )
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='direct_add_requests')
    target_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='received_add_requests')
    invited_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='sent_add_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('family', 'target_user')

    def __str__(self):
        return f"{self.target_user} invité dans {self.family} [{self.status}]"
