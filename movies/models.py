from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField()
    genre = models.CharField(max_length=100)
    rating = models.CharField(max_length=10)
    release_date = models.DateField()
    poster_image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
