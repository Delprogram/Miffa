from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('member', 'Membre'),
        ('guest', 'Invité'),
    )

    first_name = models.CharField(max_length=150)
    last_name  = models.CharField(max_length=150)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    photo      = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio        = models.TextField(blank=True)
    birth_date = models.DateField(default='2000-01-01')
    relation_to_family = models.CharField(max_length=100, blank=True, default='')
    family     = models.ForeignKey(
        'Family',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='members'
    )


import uuid

class Family(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    banner     = models.ImageField(upload_to='Bannieres/', null=True, blank=True)
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


class JoinRequest(models.Model):
    STATUS_CHOICES = (
        ('pending',  'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Refusée'),
    )
    user     = models.ForeignKey('User',   on_delete=models.CASCADE, related_name='join_requests')
    family   = models.ForeignKey(Family,   on_delete=models.CASCADE, related_name='join_requests')
    relation = models.CharField(max_length=100, blank=True, default='')
    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} → {self.family} ({self.status})"



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
        ('pending',  'En attente'),
        ('accepted', 'Acceptée'),
        ('rejected', 'Refusée'),
    )
    from_user    = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sent_relation_requests')
    to_user      = models.ForeignKey('User', on_delete=models.CASCADE, related_name='received_relation_requests')
    relation_type = models.CharField(max_length=20, choices=Relation.RELATION_CHOICES)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at   = models.DateTimeField(auto_now_add=True)

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
        ('relation_request',  'Demande de relation'),
        ('relation_accepted', 'Relation acceptée'),
        ('relation_rejected', 'Relation refusée'),
        ('join_approved',     'Adhésion approuvée'),
        ('new_post',          'Nouvelle publication'),
        ('new_comment', 'Nouveau commentaire'),
        ('new_like', 'Nouveau like'),
        ('new_event',         'Nouvel événement'),
        ('birthday',          'Anniversaire'),
    )
    user       = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message    = models.CharField(max_length=255)
    link       = models.CharField(max_length=200, blank=True)
    is_read    = models.BooleanField(default=False)
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